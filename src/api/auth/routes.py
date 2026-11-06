from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.limiter import limiter
from src.core.security import require_user, verify_api_key
from src.schemas import dtos
from . import service

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    # Toda la API exige la API Key del BFF (a nivel de router: ninguna ruta
    # nueva puede quedarse sin proteger por descuido). Fuera quedan solo
    # /health y /docs, que son infraestructura, no API.
    dependencies=[Depends(verify_api_key)],
)


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, data: dtos.UserLogin, db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.login(data)


@router.post("/register", response_model=dtos.Token)
@limiter.limit("10/minute")
async def register(request: Request, data: dtos.UserRegister, db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.register(data)


@router.post("/refresh", response_model=dtos.Token)
@limiter.limit("30/minute")
async def refresh(request: Request, data: dtos.RefreshRequest, db: AsyncSession = Depends(get_db)):
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
@limiter.limit("10/minute")
async def google(request: Request, data: dtos.AuthGoogleRequest, db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    return await svc.google_login(data.googleToken)

