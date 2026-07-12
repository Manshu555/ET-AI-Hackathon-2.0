from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.base import get_db
from app.modules.auth import schemas, models
from app.core import security

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=409,
            detail="The user with this email already exists in the system",
        )
    user = models.User(
        name=user_in.name,
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login")
async def login(response: Response, user_in: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == user_in.email))
    user = result.scalars().first()
    if not user or not security.verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = security.create_access_token(subject=user.id, role=user.role)
    refresh_token = security.create_refresh_token(subject=user.id)
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True, # Note: HTTPS required in production
        samesite="lax"
    )
    return {"access_token": access_token, "user": schemas.UserResponse(id=user.id, name=user.name, email=user.email, role=user.role)}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
