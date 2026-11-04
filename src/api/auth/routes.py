from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, require_user
from src.schemas import dtos
from . import service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(data: dtos.UserLogin, db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.login(data)


@router.post("/register")
async def register(data: dtos.UserRegister, db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.register(data)


@router.post("/refresh", response_model=dtos.Token)
async def refresh(data: dtos.RefreshRequest, db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.refresh_token(data.refresh_token)


@router.post("/logout")
async def logout(user=Depends(require_user), db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.logout(user["id"])


@router.get("/me", response_model=dtos.UserProfile)
async def me(user=Depends(require_user), db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.get_profile(user["id"])


@router.post("/google", response_model=dtos.Token)
async def google(data: dtos.AuthGoogleRequest, db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.google_login(data.googleToken)

