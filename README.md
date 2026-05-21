# Data Platform Pipeline

Cloud-native end-to-end data engineering platform using Apache Airflow, MinIO, PostgreSQL, dbt, Great Expectations, and FastAPI for automated ingestion, transformation, validation, storage, and analytics serving.

---

# Architecture

```text
                        ┌────────────────────┐
                        │   FMP Stock API    │
                        └─────────┬──────────┘
                                  │

┌────────────────────┐            │
│ PostgreSQL Source  │            │
│  - products        │            │
│  - sales           │            │
│  - reviews         │            │
└─────────┬──────────┘            │
          │                       │
          ▼                       ▼

                ┌────────────────────────┐
                │     Apache Airflow     │
                │   ETL Orchestration    │
                └──────────┬─────────────┘
                           │

        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼

┌───────────────┐  ┌───────────────┐  ┌────────────────┐
│ MinIO Landing │  │ MinIO Raw     │  │ Great          │
│ Zone          │  │ Zone          │  │ Expectations   │
│ CSV ingestion │  │ Delta/Parquet │  │ Data Validation│
└──────┬────────┘  └──────┬────────┘  └────────┬───────┘
       │                  │                    │
       └──────────────────┴────────────────────┘
                           │
                           ▼

                ┌────────────────────────┐
                │          dbt           │
                │ Data Transformations   │
                │ fact_daily_sales       │
                └──────────┬─────────────┘
                           │
                           ▼

                ┌────────────────────────┐
                │ PostgreSQL Warehouse   │
                │ Analytics Data Store   │
                └──────────┬─────────────┘
                           │
                           ▼

                ┌────────────────────────┐
                │       FastAPI          │
                │ JWT + RBAC APIs        │
                └────────────────────────┘
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
- Pytest
- Python

---

# Features

- Automated ETL pipelines
- Object storage data lake
- Analytics warehouse
- Data quality validation
- dbt transformations
- JWT-secured REST APIs
- RBAC authorization
- Automated testing
- Timestamped backups
- Dockerized deployment

---

# Services

| Service | Port | Purpose |
|---|---|---|
| postgres-source | 5432 | Transactional source database |
| postgres-warehouse | 5433 | Analytics warehouse |
| postgres-airflow | Internal | Airflow metadata database |
| minio | 9000 / 9001 | Object storage data lake |
| airflow-webserver | 8080 | Workflow orchestration UI |
| airflow-scheduler | Internal | DAG scheduler |
| data-api | 8000 | Secure analytics APIs |

---

# Quick Start

## 1. Clone Repository

```bash
git clone <repository-url>
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

Wait approximately 2–3 minutes for all services to initialize.

---

# Access Services

## Airflow UI

URL:

```text
http://localhost:8080
```

Credentials:

```text
Username: admin
Password: admin
```

Trigger DAG:

```text
data_platform_pipeline
```

---

## MinIO Console

URL:

```text
http://localhost:9001
```

Credentials:

```text
Username: minioadmin
Password: minioadmin
```

---

## FastAPI Swagger Documentation

URL:

```text
http://localhost:8000/docs
```

---

# Source Database Verification

## Connect to Source Database

```bash
docker exec -it postgres-source psql -U sourceuser -d sourcedb
```

---

## Check Source Tables

```sql
\dt
```

Expected Output:

```text
products
sales
reviews
```

---

## Verify Sample Data

```sql
SELECT * FROM products LIMIT 5;
SELECT * FROM sales LIMIT 5;
SELECT * FROM reviews LIMIT 5;
```

---

# Airflow DAG Pipeline

## DAG Name

```text
data_platform_pipeline
```

---

## DAG Workflow

```text
start
   │
   ├── ingest_postgres
   │      ├─ products
   │      ├─ sales
   │      └─ reviews
   │
   ├── ingest_api
   │      └─ stock market data
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

# MinIO Data Lake Verification

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

## Verify Buckets

Open MinIO Console and verify:

```text
landing-zone
raw-zone
```

---

# Great Expectations Validation

## Validation Task

```text
validate_data_quality
```

---

## Validation Rules

- Null checks
- Quantity > 0 checks
- Required column validation
- Schema validation

---

## Validation Success Logs

Example:

```text
7 expectation(s) included in expectation_suite
Great Expectations passed
validation complete
```

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
```

---

## Run dbt Tests

```bash
dbt test
```

Expected Output:

```text
PASS
```

---

# Warehouse Verification

## Connect to Warehouse

```bash
docker exec -it postgres-warehouse psql -U warehouseuser -d warehousedb
```

---

## Check Warehouse Tables

```sql
\dt public.*
```

Expected:

```text
fact_daily_sales
```

---

## Query Analytics Data

```sql
SELECT * FROM public.fact_daily_sales LIMIT 10;
```

---

# FastAPI Endpoints

## Health Check

```text
GET /health
```

Example:

```json
{
  "status": "healthy"
}
```

---

## POST `/login`

Returns JWT access token.

### Analyst Login

```json
{
  "username": "analyst",
  "password": "analyst123"
}
```

### Admin Login

```json
{
  "username": "admin",
  "password": "admin123"
}
```

---

## GET `/api/v1/sales/daily`

Accessible By:

- analyst
- admin

Returns transformed warehouse analytics data.

Example:

```json
{
  "data": [
    {
      "date": "2026-04-20",
      "product_name": "Laptop Pro 15",
      "total_revenue": 1299.99
    }
  ],
  "count": 1
}
```

---

## GET `/api/v1/reviews/raw`

Accessible By:

- admin only

Returns raw review records.

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

## Final Test Result

```text
53 passed
1 xfailed
0 failed
```

---

# Backup Strategy

## Create Database Backups

```bash
bash backup.sh
```

Creates timestamped PostgreSQL backups inside:

```text
./backups/
```

Example:

```text
warehouse_backup_2026_05_20_14_30_01.sql
```

---

## Restore Source Database

```bash
docker exec -i postgres-source psql -U sourceuser -d sourcedb < backups/source_backup.sql
```

---

## Restore Warehouse Database

```bash
docker exec -i postgres-warehouse psql -U warehouseuser -d warehousedb < backups/warehouse_backup.sql
```

---

# Data Catalog

The Airflow task:

```text
update_data_catalog
```

logs metadata, lineage, and warehouse dataset information.

DataHub integration was removed from the default stack to reduce resource usage and improve local stability.

---

# Environment Variables

See:

```text
.env.example
```

for required configuration values.

---

# Challenges Faced

- Docker orchestration
- PostgreSQL initialization order
- Airflow dependency management
- MinIO automation
- dbt warehouse integration
- Great Expectations configuration
- JWT-secured API implementation
- Container networking
- Dependency compatibility issues

---

# Future Enhancements

- AWS deployment
- Kubernetes orchestration
- CI/CD pipelines
- Kafka streaming ingestion
- Monitoring dashboards
- Real-time analytics
- Full metadata catalog integration
- Spark transformations

---

# Conclusion

This project demonstrates a scalable modern data engineering architecture using industry-standard tools for orchestration, ingestion, storage, transformation, validation, analytics serving, automated testing, security, and backup management.