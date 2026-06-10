from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import get_settings
from app.controllers.auth_controller import router as auth_router
from app.controllers.usuario_controller import router as usuario_router

settings = get_settings()

DESCRIPTION = """
## Microservicio de Autenticación y Usuarios

Gestiona el registro, inicio de sesión y perfiles de los usuarios de la plataforma **Emplea Humboldt**.

### Flujo de autenticación
1. Registra un usuario en `/api/v1/usuarios/registro/estudiante` o `/api/v1/usuarios/registro/empresa`.
2. Obtén un token en `/api/v1/auth/login`.
3. Usa el token en el header `Authorization: Bearer <token>` para los endpoints protegidos.
4. Renueva el token con `/api/v1/auth/refresh` antes de que expire.

### Tipos de usuario
- **Estudiante** — puede postularse a vacantes y hacer seguimiento de sus prácticas.
- **Empresa** — puede publicar vacantes y gestionar postulaciones.
"""

TAGS_METADATA = [
    {
        "name": "Autenticación",
        "description": "Login, logout, renovación de tokens JWT y gestión de sesiones.",
    },
    {
        "name": "Usuarios",
        "description": "Registro de estudiantes y empresas, consulta y actualización de perfil, subida de documentos a S3.",
    },
    {
        "name": "Health",
        "description": "Verificación del estado del servicio.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # El esquema de la BD lo gestiona Alembic ("alembic upgrade head",
    # ejecutado por entrypoint.sh antes de arrancar uvicorn), no create_all.
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=DESCRIPTION,
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(usuario_router, prefix="/api/v1")


@app.get("/health", tags=["Health"], summary="Estado del servicio")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        tags=TAGS_METADATA,
        routes=app.routes,
    )
    schema.setdefault("components", {})["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Token JWT obtenido en /api/v1/auth/login",
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
