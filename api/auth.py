"""Authentication router for HeartGuard API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.deps import CurrentUser, create_access_token, get_current_user
from src.auth.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool = True


class RegisterResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserResponse | None = None
    id: int
    name: str
    email: str
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    try:
        user = AuthService.register_user(
            name=body.name,
            email=body.email,
            password=body.password,
            confirm_password=body.confirm_password or body.password,
        )
        role_normalized = user["role"].lower() if isinstance(user.get("role"), str) else "patient"
        token = create_access_token(data={
            "user_id": user["id"],
            "role": user["role"],
            "name": user["name"],
            "email": user["email"],
        })
        user_resp = UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            role=role_normalized,
            is_active=True,
        )
        return RegisterResponse(
            access_token=token,
            token_type="bearer",
            user=user_resp,
            id=user["id"],
            name=user["name"],
            email=user["email"],
            role=role_normalized,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    user = AuthService.authenticate_user(email=body.email, password=body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    role_normalized = user["role"].lower() if isinstance(user.get("role"), str) else "patient"
    token = create_access_token(data={
        "user_id": user["id"],
        "role": user["role"],
        "name": user["name"],
        "email": user["email"],
    })
    user_resp = UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        role=role_normalized,
        is_active=True,
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user_resp,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    role_normalized = current_user.role.lower() if isinstance(current_user.role, str) else "patient"
    return UserResponse(
        id=current_user.user_id,
        name=current_user.name,
        email=current_user.email,
        role=role_normalized,
        is_active=True,
    )
