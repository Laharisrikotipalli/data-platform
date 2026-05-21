import json
import os
import sys
import types
from io import BytesIO
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "airflow",
        "dags"
    )
)

AIRFLOW_STUBS = {
    "airflow": {
        "DAG": MagicMock()
    },

    "airflow.models": {
        "Variable": MagicMock()
    },

    "airflow.operators": {},

    "airflow.operators.python": {
        "PythonOperator": MagicMock()
    },

    "airflow.operators.empty": {
        "EmptyOperator": MagicMock()
    },

    "airflow.operators.dummy": {
        "DummyOperator": MagicMock()
    }
}

for module_name, attrs in AIRFLOW_STUBS.items():

    module = types.ModuleType(module_name)

    for key, value in attrs.items():
        setattr(module, key, value)

    sys.modules[module_name] = module

import data_platform_pipeline as pipeline


def _minio_for(df: pd.DataFrame):

    buf = BytesIO()

    df.to_parquet(buf, index=False)

    buf.seek(0)

    mock_resp = MagicMock()

    mock_resp.read.return_value = buf.read()

    client = MagicMock()

    client.get_object.return_value = mock_resp

    return client


VALID_DF = pd.DataFrame([
    {
        "sale_id": 1,
        "product_id": 1,
        "sale_date": "2026-05-19",
        "quantity": 2,
        "total_amount": 59.98
    },
    {
        "sale_id": 2,
        "product_id": 2,
        "sale_date": "2026-05-19",
        "quantity": 1,
        "total_amount": 29.99
    }
])


class TestPutDelta:

    _df = pd.DataFrame([
        {"id": 1},
        {"id": 2}
    ])

    def _run_put_delta(self, tmp_path):

        win_path = str(
            tmp_path / "products.parquet"
        )

        c = MagicMock()

        c.bucket_exists.return_value = True

        def fake_to_parquet(
            df_self,
            *args,
            **kwargs
        ):

            kwargs.pop("index", None)

            import pyarrow as pa
            import pyarrow.parquet as pq

            pq.write_table(
                pa.Table.from_pandas(df_self),
                win_path
            )

        with patch.object(
            pd.DataFrame,
            "to_parquet",
            fake_to_parquet
        ), patch(
            "data_platform_pipeline.os.path.getsize",
            return_value=512
        ):

            pipeline._put_delta(
                c,
                "raw-zone",
                "products",
                self._df
            )

        return c

    def test_uploads_parquet_with_correct_key(
        self,
        tmp_path
    ):

        c = self._run_put_delta(tmp_path)

        bucket, key = c.fput_object.call_args[0][:2]

        assert bucket == "raw-zone"

        assert key == "products/data.parquet"

    def test_uploads_delta_log(
        self,
        tmp_path
    ):

        c = self._run_put_delta(tmp_path)

        assert "_delta_log" in c.put_object.call_args[0][1]

    def test_delta_log_json_has_add_key(
        self,
        tmp_path
    ):

        c = self._run_put_delta(tmp_path)

        raw = c.put_object.call_args[0][2]

        assert "add" in json.loads(raw.read())


class TestIngestPostgres:

    def test_ingests_products_and_sales(self):

        mock_engine = MagicMock()

        sample = pd.DataFrame([
            {"col": "val"}
        ])

        with patch.object(
            pipeline,
            "_minio_client",
            return_value=MagicMock()
        ), patch.object(
            pipeline,
            "_put_delta"
        ) as mock_put:

            import sqlalchemy as _sa
            import pandas as _pd

            orig_ce = getattr(
                _sa,
                "create_engine",
                None
            )

            orig_rs = _pd.read_sql

            _sa.create_engine = MagicMock(
                return_value=mock_engine
            )

            _pd.read_sql = MagicMock(
                return_value=sample
            )

            try:

                pipeline.ingest_postgres_to_minio()

            finally:

                _sa.create_engine = orig_ce
                _pd.read_sql = orig_rs

        tables = [
            c[0][2]
            for c in mock_put.call_args_list
        ]

        assert "products" in tables

        assert "sales" in tables

    def test_returns_complete(self):

        mock_engine = MagicMock()

        sample = pd.DataFrame([
            {"col": "val"}
        ])

        import sqlalchemy as _sa
        import pandas as _pd

        orig_ce = _sa.create_engine

        orig_rs = _pd.read_sql

        _sa.create_engine = MagicMock(
            return_value=mock_engine
        )

        _pd.read_sql = MagicMock(
            return_value=sample
        )

        try:

            with patch.object(
                pipeline,
                "_minio_client",
                return_value=MagicMock()
            ), patch.object(
                pipeline,
                "_put_delta"
            ):

                result = pipeline.ingest_postgres_to_minio()

        finally:

            _sa.create_engine = orig_ce
            _pd.read_sql = orig_rs

        assert "complete" in result.lower()


class TestIngestApiStockData:

    def _ok(self):

        r = MagicMock()

        r.status_code = 200

        r.json.return_value = {
            "historical": [
                {
                    "date": "2026-05-19",
                    "close": 192.5
                },
                {
                    "date": "2026-05-18",
                    "close": 189.0
                }
            ]
        }

        return r

    def test_uses_real_data_on_success(self):

        import requests as _req

        orig = _req.get

        _req.get = MagicMock(
            return_value=self._ok()
        )

        try:

            with patch.object(
                pipeline,
                "_minio_client",
                return_value=MagicMock()
            ), patch.object(
                pipeline,
                "_put_delta"
            ) as mock_put:

                result = pipeline.ingest_api_stock_data()

        finally:

            _req.get = orig

        assert "complete" in result.lower()

        assert "ticker" in mock_put.call_args[0][3].columns

    def test_fallback_on_network_error(self):

        import requests as _req

        orig = _req.get

        _req.get = MagicMock(
            side_effect=Exception("down")
        )

        try:

            with patch.object(
                pipeline,
                "_minio_client",
                return_value=MagicMock()
            ), patch.object(
                pipeline,
                "_put_delta"
            ):

                result = pipeline.ingest_api_stock_data()

        finally:

            _req.get = orig

        assert "fallback" in result.lower()


class TestValidateDataQuality:

    def test_passes_with_valid_data(self):

        with patch.object(
            pipeline,
            "_minio_client",
            return_value=_minio_for(
                VALID_DF
            )
        ):

            result = pipeline.validate_data_quality()

        assert "complete" in result.lower()

    def test_fails_when_column_missing(self):

        with patch.object(
            pipeline,
            "_minio_client",
            return_value=_minio_for(
                VALID_DF.drop(
                    columns=["sale_id"]
                )
            )
        ):

            with pytest.raises(
                Exception,
                match="sale_id"
            ):

                pipeline.validate_data_quality()

    def test_fails_when_sale_id_null(self):

        bad = VALID_DF.copy().astype({
            "sale_id": object
        })

        bad.loc[0, "sale_id"] = None

        with patch.object(
            pipeline,
            "_minio_client",
            return_value=_minio_for(
                bad
            )
        ):

            with pytest.raises(
                Exception,
                match="Validation failed"
            ):

                pipeline.validate_data_quality()


class TestUpdateDataCatalog:

    def test_returns_complete(self):

        assert "catalog updated" in pipeline.update_data_catalog().lower()