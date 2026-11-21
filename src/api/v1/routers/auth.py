"""Login endpoint that returns a JWT populated with the employee's primary role."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import create_access_token, authenticate_user
from database_priv.dependencies import get_privilege_session
from repositories_priv.employees import EmployeeRepository

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(..., example="username")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtain a JWT for an employee",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_privilege_session),
):
    employee = await authenticate_user(payload.username, db)
    if not employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    repo = EmployeeRepository(db)
    roles = await repo.get_active_roles(payload.username)
    if not roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no active role")

    primary_role = ",".join(roles)
    token = create_access_token(username=payload.username, role=primary_role)
    return LoginResponse(access_token=token)