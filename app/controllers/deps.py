from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.usuario import Usuario, TipoUsuario
from app.services.auth_service import get_usuario_actual

bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Token JWT obtenido en /api/v1/auth/login",
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    return await get_usuario_actual(credentials.credentials, db)


async def require_estudiante(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.tipo_usuario != TipoUsuario.estudiante:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo estudiantes")
    return usuario


async def require_empresa(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.tipo_usuario != TipoUsuario.empresa:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo empresas")
    return usuario


async def require_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.tipo_usuario != TipoUsuario.administrador_institucional:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    return usuario
