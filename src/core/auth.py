"""
JWT utilities and FastAPI dependencies that read the employee/role
information from the *access‑control* database.
"""
from __future__ import annotations

import jwt
import structlog
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from configs.config import settings
from database_priv.dependencies import get_privilege_session
from repositories_priv.employees import EmployeeRepository
from models_priv import Employees

security = HTTPBearer()

class TokenData(BaseModel):
    sub: str
    role: str
    exp: int

def create_access_token(*, username: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": username, "role": role}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=2))
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, settings.JWT_SECRET.get_secret_value(), algorithm="HS256")

def decode_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET.get_secret_value(), algorithms=["HS256"])
        return TokenData(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

def get_token_data(
    request: Request,
    auth: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    token = auth.credentials
    token_data = decode_access_token(token)
    
    structlog.contextvars.bind_contextvars(username=token_data.sub)
    request.state.user = token_data.sub
    
    return token_data

def require_permissions(required_permissions: List[str]) -> Callable:
    """Dependency factory to check if user has all required permissions."""
    async def _permission_dependency(
        token: TokenData = Depends(get_token_data),
        db: AsyncSession = Depends(get_privilege_session),
    ):
        repo = EmployeeRepository(db)
        user_perms = await repo.get_permissions(token.role)
        
        for perm in required_permissions:
            if perm not in user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail=f"Permission '{perm}' required"
                )
        return token
    return _permission_dependency

def require_viewer(token: TokenData = Depends(get_token_data)):
    if token.role not in {"VIEWER", "EDITOR", "ADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewer privilege required")
    return token

def require_editor(token: TokenData = Depends(get_token_data)):
    if token.role not in {"EDITOR", "ADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Editor privilege required")
    return token

async def authenticate_user(
    username: str,
    db: AsyncSession,
) -> Employees | None:
    """
    For a real‑world system you would store a hashed password column
    (e.g. `hashed_password`) in `employees`.  The dump does not contain it,
    so this demo simply verifies that the username exists and returns the
    employee record.
    """
    repo = EmployeeRepository(db)
    employee = await repo.get_by_username(username)
    if not employee:
        return None
    return employee