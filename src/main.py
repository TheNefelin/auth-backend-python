from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_problem.handler import add_exception_handler, new_exception_handler
from rfc9457 import ServerProblem, UnprocessableProblem

from src.core.config import settings
from src.core.startup import assert_roles_consistent
from src.api.auth.routes import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Valida al arrancar que los roles del enum existan en la BD (falla temprano).
    await assert_roles_consistent()
    yield


app = FastAPI(
  title=settings.APP_NAME,
  description="Sistema de autenticación transversal que soporta email + contraseña y Google como proveedor externo",
  version=settings.APP_VERSION,
  docs_url="/docs",
  redoc_url="/redoc",
  lifespan=lifespan,
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
  CORSMiddleware,
  allow_origins=settings.CORS_ORIGINS,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


# PROBLEM HANDLERS (respuestas RFC 9457 / Problem Details) --------------
class RequestValidationProblem(UnprocessableProblem):
  type_ = "request-validation-failed"
  title = "Request validation error."

  def __init__(self, errors=None, **kwargs):
    super().__init__(errors=errors, **kwargs)
    self.detail = "; ".join(str(e.get("msg", "")) for e in errors) if errors else self.title


class InternalServerErrorProblem(ServerProblem):
  type_ = "internal-server-error"
  title = "Internal server error."

  def __init__(self, detail=None, **kwargs):
    super().__init__(detail="Internal server error", **kwargs)


# Handler global: convierte AppError/excepciones semánticas, HTTPException y
# errores de validación a un único formato {type, title, status, detail}.
eh = new_exception_handler(
  unhandled_wrappers={
    "422": RequestValidationProblem,
    "500": InternalServerErrorProblem,
  },
)
add_exception_handler(app, eh)


@app.get("/health")
async def health_check():
  return {"status": "ok", "service": "auth-unificado-backend"}

app.include_router(auth_router)
