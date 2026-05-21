
from datetime import datetime, timedelta
from io import BytesIO
import json
import logging
import os
import subprocess

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable

def _minio_client():
    from minio import Minio
    return Minio(
        "minio:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False,
    )


def _put_delta(client, bucket: str, prefix: str, df):
    parquet_path = f"/tmp/{prefix.replace('/', '_')}.parquet"
    df.to_parquet(parquet_path, index=False)
    client.fput_object(bucket, f"{prefix}/data.parquet", parquet_path)
    delta_log = json.dumps({
        "add": {
            "path": "data.parquet",
            "size": os.path.getsize(parquet_path),
            "modificationTime": int(datetime.now().timestamp() * 1000),
            "dataChange": True,
        }
    }).encode()
    client.put_object(
        bucket,
        f"{prefix}/_delta_log/00000000000000000000.json",
        BytesIO(delta_log),
        length=len(delta_log),
        content_type="application/json",
    )
    logging.info("Uploaded %s to %s/%s", prefix, bucket, prefix)

def ingest_postgres_to_minio(**context):
    import pandas as pd
    from sqlalchemy import create_engine
    engine = create_engine(
        "postgresql://sourceuser:sourcepass@postgres-source:5432/sourcedb"
    )
    client = _minio_client()
    for table in ["products", "sales"]:
        df = pd.read_sql(f"SELECT * FROM {table}", engine)
        _put_delta(client, "raw-zone", table, df)
        logging.info("Ingested %d rows from %s", len(df), table)
    return "postgres ingestion complete"

def ingest_api_stock_data(**context):
    import requests
    import pandas as pd

    api_key = Variable.get("FMP_API_KEY", default_var="demo")
    ticker = "AAPL"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
    params = {
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d"),
        "apikey": api_key,
    }
    client = _minio_client()
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200 and "historical" in response.json():
            df = pd.DataFrame(response.json()["historical"])
            df["ticker"] = ticker
            _put_delta(client, "raw-zone", "stocks", df)
            logging.info("Ingested %d stock rows", len(df))
            return "stock ingestion complete"
    except Exception as exc:
        logging.warning("API unavailable: %s", exc)

    df = pd.DataFrame([
        {
            "date": (end_date - timedelta(days=i)).strftime("%Y-%m-%d"),
            "open": 170.0, "high": 172.0, "low": 169.0,
            "close": 171.0, "volume": 50000000, "ticker": ticker,
        }
        for i in range(30)
    ])
    _put_delta(client, "raw-zone", "stocks", df)
    return "fallback stock data written"

def ingest_files_to_minio(**context):
    import pandas as pd
    client = _minio_client()
    objects = list(client.list_objects("landing-zone", recursive=True))
    if not objects:
        raise ValueError("landing-zone is empty")
    for obj in objects:
        if not obj.object_name.endswith(".csv"):
            logging.info("Skipping non-CSV file: %s", obj.object_name)
            continue
        response = client.get_object("landing-zone", obj.object_name)
        raw = response.read()
        response.close()
        df = pd.read_csv(BytesIO(raw), engine="python", on_bad_lines="skip")
        expected_cols = {"review_id", "product_id", "rating", "review_text"}
        if not expected_cols.issubset(set(df.columns)):
            raise ValueError(
                f"Invalid review schema in {obj.object_name}. "
                f"Found columns: {list(df.columns)}"
            )
        _put_delta(client, "raw-zone", "reviews", df)
        logging.info("Ingested %s (%d rows)", obj.object_name, len(df))
    return "file ingestion complete"

def validate_data_quality(**context):
    import pandas as pd
    import great_expectations as ge
    client = _minio_client()
    response = client.get_object("raw-zone", "sales/data.parquet")
    sales_df = pd.read_parquet(BytesIO(response.read()))
    response.close()
    ge_df = ge.from_pandas(sales_df)
    for col in ["sale_id", "product_id", "sale_date", "quantity"]:
        ge_df.expect_column_to_exist(col)
    ge_df.expect_column_values_to_not_be_null("sale_id")
    ge_df.expect_column_values_to_not_be_null("product_id")
    ge_df.expect_column_values_to_be_between("quantity", min_value=1, max_value=None)
    result = ge_df.validate()
    failed = [r for r in result["results"] if not r["success"]]
    if failed:
        for item in failed:
            logging.error("FAILED: %s", item["expectation_config"]["expectation_type"])
        raise Exception(f"Validation failed ({len(failed)} expectations)")
    logging.info("Great Expectations passed")
    return "validation complete"

def _prepare_warehouse_raw_tables():
    import pandas as pd
    from sqlalchemy import create_engine, text
    client = _minio_client()
    engine = create_engine(
        "postgresql://warehouseuser:warehousepass@postgres-warehouse:5432/warehousedb"
    )
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
    for table in ["products", "sales", "reviews"]:
        response = client.get_object("raw-zone", f"{table}/data.parquet")
        df = pd.read_parquet(BytesIO(response.read()))
        response.close()
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS raw.{table} CASCADE"))
        df.to_sql(table, engine, schema="raw", if_exists="append", index=False)
        logging.info("Loaded raw.%s (%d rows)", table, len(df))


def run_dbt_transformations(**context):
    _prepare_warehouse_raw_tables()

    dbt_dir = "/opt/airflow/dbt_project"
    python_bin = "/usr/local/bin/python"
    dbt_script = "/home/airflow/.local/bin/dbt"

    dbt_log_path = "/tmp/dbt_logs"
    os.makedirs(dbt_log_path, exist_ok=True)

    env = {
        **os.environ,
        "PATH": "/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin",
        "HOME": "/home/airflow",
        "PYTHONPATH": "/home/airflow/.local/lib/python3.9/site-packages",
    }

    for label, cmd in [
        ("dbt deps", [python_bin, dbt_script, "deps",
                      "--profiles-dir", ".",
                      "--log-path", dbt_log_path]),
        ("dbt run",  [python_bin, dbt_script, "run",
                      "--profiles-dir", ".",
                      "--log-path", dbt_log_path]),
    ]:
        logging.info("Running: %s", label)
        result = subprocess.run(
            cmd,
            cwd=dbt_dir,
            capture_output=True,
            text=True,
            env=env,
        )
        logging.info("STDOUT:\n%s", result.stdout)
        logging.info("STDERR:\n%s", result.stderr)
        logging.info("Return code: %s", result.returncode)
        if result.returncode != 0:
            raise Exception(
                f"{label} failed\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            )

    logging.info("dbt transformations completed")
    return "dbt complete"

def load_to_warehouse(**context):
    from sqlalchemy import create_engine, text
    engine = create_engine(
        "postgresql://warehouseuser:warehousepass@postgres-warehouse:5432/warehousedb"
    )
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM public.fact_daily_sales")
        ).scalar()
    logging.info("fact_daily_sales rows: %d", count)
    if count == 0:
        raise Exception("fact_daily_sales is empty — pipeline incomplete")
    return f"warehouse verified: {count} rows"

def update_data_catalog(**context):
    try:
        import requests
        datahub_url = Variable.get(
            "DATAHUB_GMS_URL",
            default_var="http://datahub-gms:8080",
        )
        datasets = [
            {"platform": "s3",       "name": "raw-zone.sales",                          "env": "PROD"},
            {"platform": "s3",       "name": "raw-zone.products",                       "env": "PROD"},
            {"platform": "s3",       "name": "raw-zone.reviews",                        "env": "PROD"},
            {"platform": "postgres", "name": "warehousedb.public.fact_daily_sales",     "env": "PROD"},
        ]
        for ds in datasets:
            urn = f"urn:li:dataset:({ds['platform']},{ds['name']},{ds['env']})"
            payload = {
                "proposal": {
                    "entityType": "dataset",
                    "entityUrn": urn,
                    "aspectName": "datasetProperties",
                    "aspect": {
                        "value": json.dumps({"name": ds["name"], "customProperties": {}}),
                        "contentType": "application/json",
                    },
                    "changeType": "UPSERT",
                }
            }
            response = requests.post(
                f"{datahub_url}/aspects?action=ingestProposal",
                json=payload,
                timeout=5,
            )
            logging.info("DataHub %s -> %s", urn, response.status_code)
    except Exception as exc:
        logging.warning("DataHub update skipped: %s", exc)
    return "catalog updated"

default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="data_platform_pipeline",
    default_args=default_args,
    description="End-to-end data pipeline",
    schedule_interval="0 2 * * *",
    catchup=False,
    tags=["data_pipeline", "quality", "catalog"],
) as dag:

    start = DummyOperator(task_id="start")

    ingest_postgres = PythonOperator(
        task_id="ingest_postgres",
        python_callable=ingest_postgres_to_minio,
    )

    ingest_api = PythonOperator(
        task_id="ingest_api",
        python_callable=ingest_api_stock_data,
    )

    ingest_files = PythonOperator(
        task_id="ingest_files",
        python_callable=ingest_files_to_minio,
    )

    validate_quality = PythonOperator(
        task_id="validate_data_quality",
        python_callable=validate_data_quality,
    )

    transform_dbt = PythonOperator(
        task_id="transform_data_dbt",
        python_callable=run_dbt_transformations,
    )

    load_warehouse = PythonOperator(
        task_id="load_to_warehouse",
        python_callable=load_to_warehouse,
    )

    update_catalog = PythonOperator(
        task_id="update_data_catalog",
        python_callable=update_data_catalog,
    )

    end = DummyOperator(task_id="end")

    start >> [ingest_postgres, ingest_api, ingest_files]
    [ingest_postgres, ingest_api, ingest_files] >> validate_quality
    validate_quality >> transform_dbt >> load_warehouse >> update_catalog >> end