# Data Platform Pipeline

Cloud-native end-to-end enterprise data engineering platform using Apache Airflow, MinIO, PostgreSQL, dbt, Great Expectations, DataHub, Kafka, OpenSearch, and FastAPI for automated ingestion, validation, transformation, lineage tracking, metadata governance, analytics serving, and secure API access.

---

# Architecture

```text
                                ┌────────────────────┐
                                │   FMP Stock API    │
                                └─────────┬──────────┘
                                          │

┌────────────────────┐                    │
│ PostgreSQL Source  │                    │
│  - products        │                    │
│  - sales           │                    │
│  - reviews         │                    │
└─────────┬──────────┘                    │
          │                               │
          ▼                               ▼

                    ┌───────────────────────────┐
                    │      Apache Airflow       │
                    │     ETL Orchestration     │
                    └────────────┬──────────────┘
                                 │

        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼

┌────────────────┐   ┌────────────────────┐   ┌────────────────────┐
│ MinIO Landing  │   │ MinIO Raw Zone     │   │ Great Expectations │
│ Zone           │   │ Delta Lake Format  │   │ Data Validation    │
└──────┬─────────┘   └─────────┬──────────┘   └──────────┬─────────┘
       │                       │                         │
       └───────────────────────┴─────────────────────────┘
                                 │
                                 ▼

                    ┌───────────────────────────┐
                    │            dbt            │
                    │   Data Transformations    │
                    │    fact_daily_sales       │
                    └────────────┬──────────────┘
                                 │
                                 ▼

                    ┌───────────────────────────┐
                    │ PostgreSQL Warehouse      │
                    │ Analytics Data Warehouse  │
                    └────────────┬──────────────┘
                                 │
               ┌─────────────────┼──────────────────┐
               ▼                 ▼                  ▼

     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │    FastAPI     │ │    DataHub     │ │ Kafka + Schema │
     │ JWT + RBAC API │ │ Metadata Layer │ │ Registry       │
     └────────────────┘ └──────┬─────────┘ └────────────────┘
                                │
                                ▼

                      ┌────────────────────┐
                      │     OpenSearch     │
                      │ Metadata Search    │
                      │ Lineage Indexing   │
                      └────────────────────┘
```

---

# Technologies Used

- Apache Airflow
- PostgreSQL
- MinIO
- dbt
- Great Expectations
- FastAPI
- Docker & Docker Compose
- JWT Authentication
- RBAC Authorization
- Kafka
- Schema Registry
- OpenSearch
- DataHub
- Pytest
- Python

---

# Features

- Automated ETL orchestration
- Delta Lake raw data storage
- Metadata governance & lineage
- Data quality validation
- Analytics warehouse
- dbt transformations
- JWT-secured APIs
- Role-based access control
- Automated backups
- Data catalog integration
- Column-level lineage
- Dockerized infrastructure
- Automated testing

---

# Services

| Service | Port | Purpose |
|---|---|---|
| postgres-source | 5432 | Source transactional database |
| postgres-warehouse | 5433 | Analytics warehouse |
| postgres-airflow | Internal | Airflow metadata database |
| minio | 9000 / 9001 | Object storage data lake |
| airflow-webserver | 8083 | Airflow UI |
| airflow-scheduler | Internal | DAG scheduler |
| kafka | 9093 | Event streaming |
| schema-registry | 8081 | Schema management |
| opensearch | 9201 | Metadata indexing |
| data-api | 8000 | Secure analytics APIs |
| datahub | 9002 | Metadata catalog & lineage |

---

# Project Structure

```text
data-platform/
│
├── airflow/
│   └── dags/
│       └── data_platform_pipeline.py
│
├── backups/
│
├── data_api/
│
├── dbt_project/
│
├── great_expectations/
│
├── seeds/
│   ├── source_db/
│   │   └── 01_init.sql
│   └── minio_files/
│       └── customer_reviews.csv
│
├── tests/
│
├── docker-compose.yml
├── Dockerfile.airflow
├── requirements.txt
├── .env.example
└── README.md
```

---

# Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/Laharisrikotipalli/data-platform.git
cd data-platform
```

---

## 2. Configure Environment Variables

```bash
cp .env.example .env
```

---

## 3. Start Platform

```bash
docker compose down -v
docker volume prune -f
docker compose up -d --build
```

Wait approximately 3–5 minutes for all services to initialize.

---

## 4. Start DataHub

```bash
datahub docker quickstart
```

---

# Access Services

## Airflow UI

```text
http://localhost:8083
```

Credentials:

```text
Username: admin
Password: admin
```

---

## MinIO Console

```text
http://localhost:9001
```

Credentials:

```text
Username: minioadmin
Password: minioadmin
```

---

## FastAPI Swagger Docs

```text
http://localhost:8000/docs
```

---

## DataHub UI

```text
http://localhost:9002
```

---

# Source Database Verification

## Connect to Source Database

```bash
docker exec -it postgres-source psql -U sourceuser -d sourcedb
```

---

## Verify Tables

```sql
\dt
```

Expected:

```text
products
sales
reviews
```

---

## Verify Sample Data

```sql
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM sales;
SELECT COUNT(*) FROM reviews;
```

Expected:
- 10+ products
- 10+ sales
- 10+ reviews

---

# MinIO Data Lake

## Landing Zone

```text
landing-zone/
   customer_reviews.csv
```

---

## Raw Zone

```text
raw-zone/
   products/
   sales/
   reviews/
   stocks/
```

---

## Processed Zone

```text
processed-zone/
```

---

## Curated Zone

```text
curated-zone/
```

---

# Airflow DAG Pipeline

## DAG ID

```text
data_platform_pipeline
```

---

# DAG Workflow

```text
start
   │
   ├── ingest_postgres
   │      ├─ products
   │      ├─ sales
   │      └─ reviews
   │
   ├── ingest_api
   │      └─ AAPL stock data
   │
   ├── ingest_files
   │      └─ customer_reviews.csv
   │
   ▼
validate_data_quality
   │
   ▼
transform_data_dbt
   │
   ▼
load_to_warehouse
   │
   ▼
update_data_catalog
   │
   ▼
end
```

---

# Great Expectations Validation

## Validation Rules

- Required column validation
- Null checks
- Quantity > 0 validation
- Schema validation

---

## Failure Testing

Insert bad data:

```sql
INSERT INTO sales
VALUES (999, NULL, NOW(), 1, 100);
```

Re-run DAG.

Expected:
- validate_data_quality task fails
- pipeline stops

---

# dbt Transformations

## Enter Airflow Container

```bash
docker exec -it airflow-webserver bash
```

---

## Run dbt

```bash
cd /opt/airflow/dbt_project

dbt deps
dbt run
dbt test
dbt docs generate
```

---

# Warehouse Verification

## Connect to Warehouse

```bash
docker exec -it postgres-warehouse psql -U warehouseuser -d warehousedb
```

---

## Verify Warehouse Tables

```sql
\dt public.*
```

Expected:

```text
fact_daily_sales
```

---

## Query Analytics Table

```sql
SELECT * FROM fact_daily_sales LIMIT 10;
```

---

# DataHub Metadata Ingestion

## Install Connectors

```bash
pip install "acryl-datahub[postgres,s3,dbt]"
```

---

## Warehouse Metadata Ingestion

```bash
datahub ingest -c warehouse_ingestion.yml
```

---

## MinIO Metadata Ingestion

```bash
datahub ingest -c minio_ingestion.yml
```

---

## dbt Lineage Ingestion

```bash
datahub ingest -c dbt_ingestion.yml
```

---

# DataHub Verification

Search inside DataHub UI:

```text
fact_daily_sales
sales
products
reviews
stocks
```

---

# Lineage Verification

Open:

```text
fact_daily_sales
→ Lineage
```

Expected:
- upstream raw datasets
- dbt transformation lineage
- column-level lineage

---

# FastAPI Endpoints

## Health Check

```text
GET /health
```

---

## POST `/login`

### Analyst Login

```json
{
  "username": "analyst",
  "password": "analyst123"
}
```

---

### Admin Login

```json
{
  "username": "admin",
  "password": "admin123"
}
```

---

# GET `/api/v1/sales/daily`

Accessible By:
- analyst
- admin

Returns transformed warehouse analytics data.

Example:

```json
{
  "data": [
    {
      "date": "2026-05-20",
      "product_name": "Laptop Pro 15",
      "total_revenue": 1299.99
    }
  ],
  "count": 1
}
```

---

# GET `/api/v1/reviews/raw`

Accessible By:
- admin only

Returns raw customer review text.

---

# RBAC Rules

| Role | Access |
|---|---|
| No Token | 401 Unauthorized |
| Analyst | Sales endpoints only |
| Admin | Full access |

---

# Automated Testing

## Run All Tests

```bash
pytest tests -v
```

---

## Expected Result

```text
53 passed
1 xfailed
0 failed
```

---

# Backup Strategy

## Create Warehouse Backup

```bash
docker compose exec postgres-warehouse \
bash /backups/backup.sh
```

---

## Backup Output

```text
./backups/
```

Example:

```text
warehouse_backup_2026_05_20_14_30_01.sql
```

---

## Restore Warehouse

```bash
docker exec -i postgres-warehouse \
psql -U warehouseuser -d warehousedb < backups/warehouse_backup.sql
```

---

# Security

- JWT token validation
- JWT expiration checks
- RBAC authorization
- Environment-based secrets
- `.env` excluded from Git
- Secure API access

---

# Challenges Faced

- Docker orchestration
- Airflow dependency management
- dbt warehouse integration
- DataHub metadata ingestion
- OpenSearch configuration
- Kafka service coordination
- MinIO Delta Lake management
- JWT authentication
- Dependency compatibility handling

---

# Future Enhancements

- Kubernetes deployment
- CI/CD pipelines
- Real-time Kafka streaming
- Spark transformations
- Monitoring dashboards
- Prometheus/Grafana
- AWS cloud deployment
- Automated lineage refresh

---

# Conclusion

This project demonstrates a complete enterprise-style modern data engineering platform using orchestration, object storage, transformation, validation, metadata governance, lineage tracking, analytics warehousing, secure APIs, automated testing, and containerized infrastructure.