import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data_api"))

from auth import (
    ALGORITHM,
    SECRET_KEY,
    create_token,
    require_role,
    verify_token,
)


class TestCreateToken:
    def test_returns_string(self):
        token = create_token("alice", "analyst")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_payload_contains_sub(self):
        token = create_token("alice", "analyst")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "alice"

    def test_payload_contains_role(self):
        token = create_token("bob", "admin")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["role"] == "admin"

    def test_payload_contains_exp(self):
        token = create_token("alice", "analyst")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_token_expires_in_future(self):
        token = create_token("alice", "analyst")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["exp"] > datetime.utcnow().timestamp()

    def test_different_users_different_tokens(self):
        t1 = create_token("alice", "analyst")
        t2 = create_token("bob", "admin")
        assert t1 != t2

def _make_creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestVerifyToken:
    def test_valid_token_returns_payload(self):
        token = create_token("alice", "analyst")
        payload = verify_token(_make_creds(token))
        assert payload["sub"] == "alice"
        assert payload["role"] == "analyst"

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            verify_token(_make_creds("not.a.valid.token"))
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        payload = {
            "sub": "alice",
            "role": "analyst",
            "exp": datetime.utcnow() - timedelta(seconds=1),
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            verify_token(_make_creds(expired_token))
        assert exc_info.value.status_code == 401

    def test_token_signed_with_wrong_key_raises_401(self):
        wrong_key_token = jwt.encode(
            {"sub": "alice", "role": "analyst", "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong-secret",
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(_make_creds(wrong_key_token))
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises_401(self):
        token = create_token("alice", "analyst")

        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(HTTPException) as exc_info:
            verify_token(_make_creds(tampered))
        assert exc_info.value.status_code == 401
class TestRequireRole:
    def _run_checker(self, roles, token_role):
        """Helper: build a checker and call it with a real token."""
        checker = require_role(*roles)
        token = create_token("user", token_role)
        return checker(verify_token(_make_creds(token)))

    def test_matching_role_passes(self):
        result = self._run_checker(("analyst",), "analyst")
        assert result["role"] == "analyst"

    def test_admin_role_passes_when_admin_required(self):
        result = self._run_checker(("admin",), "admin")
        assert result["role"] == "admin"

    def test_multi_role_allows_first(self):
        result = self._run_checker(("analyst", "admin"), "analyst")
        assert result["role"] == "analyst"

    def test_multi_role_allows_second(self):
        result = self._run_checker(("analyst", "admin"), "admin")
        assert result["role"] == "admin"

    def test_wrong_role_raises_403(self):
        checker = require_role("admin")
        analyst_token = create_token("user", "analyst")
        with pytest.raises(HTTPException) as exc_info:
            checker(verify_token(_make_creds(analyst_token)))
        assert exc_info.value.status_code == 403

    def test_unknown_role_raises_403(self):
        checker = require_role("admin", "analyst")
        guest_token = create_token("user", "guest")
        with pytest.raises(HTTPException) as exc_info:
            checker(verify_token(_make_creds(guest_token)))
        assert exc_info.value.status_code == 403