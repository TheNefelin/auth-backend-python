from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.auth.routes import router as auth_router

app = FastAPI(
  title=settings.APP_NAME,
  description="Sistema de autenticación transversal que soporta email + contraseña y Google como proveedor externo",
  version=settings.APP_VERSION,
  docs_url="/docs",
  redoc_url="/redoc",
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
  CORSMiddleware,
  allow_origins=settings.BACKEND_CORS_ORIGINS,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/health")
async def health_check():
  return {"status": "ok", "service": "auth-unificado-backend"}

app.include_router(auth_router)