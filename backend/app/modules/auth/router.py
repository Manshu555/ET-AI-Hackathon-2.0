from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from motor.motor_asyncio import AsyncIOMotorDatabase
from jose import jwt, JWTError
from app.db.base import get_db
from app.modules.auth import schemas
from app.modules.auth.dependencies import get_current_user
from app.core import security
from app.core.config import settings
from typing import Optional
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: schemas.UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db.users.find_one({"email": user_in.email})
    if user:
        raise HTTPException(
            status_code=409,
            detail="The user with this email already exists in the system",
        )
        
    new_user = {
        "_id": str(uuid.uuid4()),
        "name": user_in.name,
        "email": user_in.email,
        "password_hash": security.get_password_hash(user_in.password),
        "role": user_in.role,
        "auth_provider": "local",
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(new_user)
    new_user["id"] = new_user.pop("_id")
    return new_user


@router.post("/login")
async def login(response: Response, user_in: schemas.UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db.users.find_one({"email": user_in.email})
    
    if not user or not user.get("password_hash") or not security.verify_password(user_in.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = security.create_access_token(subject=user["_id"], role=user.get("role", "engineer"))
    refresh_token = security.create_refresh_token(subject=user["_id"])

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
    )
    return {
        "access_token": access_token,
        "user": schemas.UserResponse(id=user["_id"], name=user["name"], email=user["email"], role=user.get("role", "engineer")),
    }


@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Use the httpOnly refresh token cookie to get a new access token."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    try:
        payload = jwt.decode(refresh_token, settings.JWT_REFRESH_SECRET, algorithms=[security.ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Issue new tokens
    new_access = security.create_access_token(subject=user["_id"], role=user.get("role", "engineer"))
    new_refresh = security.create_refresh_token(subject=user["_id"])

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return {
        "access_token": new_access,
        "user": schemas.UserResponse(id=user["_id"], name=user["name"], email=user["email"], role=user.get("role", "engineer")),
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=schemas.UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get the currently authenticated user."""
    return current_user
