import os
import sys
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data_api"))

from auth import create_token

with patch("sqlalchemy.create_engine"):
    import main as api_main

client = TestClient(api_main.app, raise_server_exceptions=False)


def _auth_header(role: str) -> dict:
    token = create_token("testuser", role)
    return {"Authorization": f"Bearer {token}"}


SAMPLE_SALES_DF = pd.DataFrame([
    {"date": "2026-05-19", "product_name": "Laptop Pro 15",        "total_revenue": 1299.99},
    {"date": "2026-05-19", "product_name": "Wireless Mouse",       "total_revenue": 59.98},
    {"date": "2026-05-18", "product_name": "Ergonomic Desk Chair", "total_revenue": 249.99},
])

SAMPLE_REVIEWS_DF = pd.DataFrame([
    {"review_id": 1, "product_id": 1, "rating": 5, "review_text": "Excellent laptop"},
    {"review_id": 2, "product_id": 2, "rating": 4, "review_text": "Good mouse"},
])

class TestHealth:
    def test_returns_200(self):
        assert client.get("/health").status_code == 200

    def test_body_is_healthy(self):
        assert client.get("/health").json() == {"status": "healthy"}

    def test_no_auth_required(self):
        # No Authorization header — should still succeed
        assert client.get("/health").status_code == 200

class TestLogin:
    def test_analyst_login_succeeds(self):
        r = client.post("/login", json={"username": "analyst", "password": "analyst123"})
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["role"] == "analyst"

    def test_admin_login_succeeds(self):
        r = client.post("/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

    def test_wrong_password_returns_401(self):
        assert client.post("/login", json={"username": "analyst", "password": "wrong"}).status_code == 401

    def test_unknown_user_returns_401(self):
        assert client.post("/login", json={"username": "ghost", "password": "x"}).status_code == 401

    def test_empty_credentials_returns_401(self):
        assert client.post("/login", json={"username": "", "password": ""}).status_code == 401

    def test_token_is_non_empty_string(self):
        r = client.post("/login", json={"username": "admin", "password": "admin123"})
        token = r.json()["access_token"]
        assert isinstance(token, str) and len(token) > 10

class TestSalesDaily:
    # FastAPI HTTPBearer returns 401 for both missing and invalid tokens
    # and 401 when the token is present but invalid.
    def test_no_token_returns_401(self):
        r = client.get("/api/v1/sales/daily")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self):
        r = client.get(
            "/api/v1/sales/daily",
            headers={"Authorization": "Bearer notavalidtoken"},
        )
        assert r.status_code == 401

    def test_analyst_can_access(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_SALES_DF):
            r = client.get("/api/v1/sales/daily", headers=_auth_header("analyst"))
        assert r.status_code == 200

    def test_admin_can_access(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_SALES_DF):
            r = client.get("/api/v1/sales/daily", headers=_auth_header("admin"))
        assert r.status_code == 200

    def test_response_structure(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_SALES_DF):
            r = client.get("/api/v1/sales/daily", headers=_auth_header("analyst"))
        body = r.json()
        assert "data" in body and "count" in body
        assert body["count"] == len(SAMPLE_SALES_DF)

    def test_each_record_has_required_fields(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_SALES_DF):
            r = client.get("/api/v1/sales/daily", headers=_auth_header("analyst"))
        for record in r.json()["data"]:
            assert "date" in record
            assert "product_name" in record
            assert "total_revenue" in record

    def test_total_revenue_is_float(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_SALES_DF):
            r = client.get("/api/v1/sales/daily", headers=_auth_header("analyst"))
        for record in r.json()["data"]:
            assert isinstance(record["total_revenue"], float)

    @pytest.mark.xfail(reason="BUG #1: None revenue raises TypeError before the nan-guard runs")
    def test_none_revenue_is_returned_as_zero(self):
        """
        Expose BUG #1: when total_revenue is None (e.g. a LEFT JOIN with no
        match), float(None) raises TypeError.  After the fix the API should
        return 0.0 instead of a 500.
        Fix: change the revenue line to:
            float(row["total_revenue"] or 0)
        """
        nan_df = pd.DataFrame([
            {"date": "2026-05-19", "product_name": "Widget", "total_revenue": None},
        ])
        with patch("main.pd.read_sql", return_value=nan_df):
            r = client.get("/api/v1/sales/daily", headers=_auth_header("analyst"))
        assert r.status_code == 200
        assert r.json()["data"][0]["total_revenue"] == 0.0

    def test_db_error_returns_503(self):
        with patch("main.pd.read_sql", side_effect=Exception("DB down")):
            r = client.get("/api/v1/sales/daily", headers=_auth_header("analyst"))
        assert r.status_code == 503

    def test_guest_role_returns_403(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_SALES_DF):
            r = client.get("/api/v1/sales/daily", headers=_auth_header("guest"))
        assert r.status_code == 403


class TestReviewsRaw:
    def test_no_token_returns_401(self):
        r = client.get("/api/v1/reviews/raw")
        assert r.status_code == 401

    def test_analyst_cannot_access(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_REVIEWS_DF):
            r = client.get("/api/v1/reviews/raw", headers=_auth_header("analyst"))
        assert r.status_code == 403

    def test_admin_can_access(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_REVIEWS_DF):
            r = client.get("/api/v1/reviews/raw", headers=_auth_header("admin"))
        assert r.status_code == 200

    def test_response_structure(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_REVIEWS_DF):
            r = client.get("/api/v1/reviews/raw", headers=_auth_header("admin"))
        body = r.json()
        assert "data" in body and "count" in body
        assert body["count"] == len(SAMPLE_REVIEWS_DF)

    def test_all_values_are_strings(self):
        with patch("main.pd.read_sql", return_value=SAMPLE_REVIEWS_DF):
            r = client.get("/api/v1/reviews/raw", headers=_auth_header("admin"))
        for record in r.json()["data"]:
            for v in record.values():
                assert isinstance(v, str)

    def test_null_values_become_empty_string(self):
        df_with_null = pd.DataFrame([
            {"review_id": 1, "product_id": 1, "rating": None, "review_text": "Good"},
        ])
        with patch("main.pd.read_sql", return_value=df_with_null):
            r = client.get("/api/v1/reviews/raw", headers=_auth_header("admin"))
        assert r.json()["data"][0]["rating"] == ""

    def test_db_error_returns_503(self):
        with patch("main.pd.read_sql", side_effect=Exception("DB down")):
            r = client.get("/api/v1/reviews/raw", headers=_auth_header("admin"))
        assert r.status_code == 503