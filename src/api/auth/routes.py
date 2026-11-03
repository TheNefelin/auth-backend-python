from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_current_user
from src.schemas import dtos
from . import service

from src.core.dependencies import get_db
from src.core.dependencies import get_current_user
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


@router.post("/refresh")
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.refresh_token(refresh_token)


@router.post("/logout")
async def logout(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.logout(user["id"])


@router.get("/me", response_model=dtos.UserProfile)
async def me(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.get_profile(user["id"])
@router.post("/google")
async def google(data: dict, db: AsyncSession = Depends(get_db)):
    google_token = data.get("googleToken") or data.get("id_token", "")
    if not google_token:
        raise CredentialsException("Token de Google no proporcionado")
    svc = service.AuthService(db)
    return await svc.google_login(google_token)

