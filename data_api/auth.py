import os
from datetime import datetime, timedelta
from typing import Dict

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

SECRET_KEY = os.getenv("JWT_SECRET") or "your-super-secret-jwt-key-change-this-in-production"
ALGORITHM  = "HS256" 
EXPIRE_MIN = 30

security = HTTPBearer()


def create_token(username: str, role: str) -> str:
    payload = {
        "sub":  username,
        "role": role,
        "exp":  datetime.utcnow() + timedelta(minutes=EXPIRE_MIN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(*roles):
    """Returns a FastAPI dependency that enforces role-based access."""
    def checker(token: Dict = Depends(verify_token)) -> Dict:
        if token.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Forbidden — insufficient role")
        return token
    return checker