import os
import math
import logging

import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, text

from auth import create_token, require_role

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Data Platform API",
    version="1.0.0",
    description="REST API for the data platform warehouse",
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://warehouseuser:warehousepass@postgres-warehouse:5432/warehousedb",
)

engine = create_engine(DATABASE_URL)

USERS = {
    "analyst": {"password": "analyst123", "role": "analyst"},
    "admin":   {"password": "admin123",   "role": "admin"},
}


@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/login")
def login(data: dict):
    username = data.get("username", "")
    password = data.get("password", "")

    user = USERS.get(username)

    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(username, user["role"])

    return {"access_token": token, "token_type": "bearer", "role": user["role"]}

@app.get("/api/v1/sales/daily")
def get_daily_sales(token=Depends(require_role("analyst", "admin"))):
    try:
        df = pd.read_sql(
            "SELECT date, product_name, total_revenue FROM public.fact_daily_sales LIMIT 100",
            engine,
        )
    except Exception as exc:
        logging.error("DB error: %s", exc)
        raise HTTPException(status_code=503, detail="Data not available yet — run the pipeline first")

    records = []
    for row in df.to_dict(orient="records"):
        records.append({
            "date": str(row.get("date", "")),
            "product_name": str(row.get("product_name", "")),
            "total_revenue": float(row["total_revenue"])
            if not math.isnan(float(row["total_revenue"] or 0))
            else 0.0,
        })

    return {"data": records, "count": len(records)}

@app.get("/api/v1/reviews/raw")
def get_raw_reviews(token=Depends(require_role("admin"))):
    try:
        df = pd.read_sql("SELECT * FROM raw.reviews LIMIT 100", engine)
    except Exception as exc:
        logging.error("DB error: %s", exc)
        raise HTTPException(status_code=503, detail="Reviews not available yet — run the pipeline first")

    records = []
    for row in df.to_dict(orient="records"):
        clean = {k: ("" if pd.isna(v) else str(v)) for k, v in row.items()}
        records.append(clean)

    return {"data": records, "count": len(records)}
