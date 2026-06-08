import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.config import get_settings
from app.models.usuario import Usuario, TipoUsuario
from app.repositories.usuario_repository import RefreshTokenRepository, UsuarioRepository
from app.schemas.usuario import TokenResponse

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(usuario_id: uuid.UUID, tipo_usuario: TipoUsuario) -> str:
    return _create_token(
        {"sub": str(usuario_id), "tipo": tipo_usuario.value},
        timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(usuario_id: uuid.UUID) -> str:
    return _create_token(
        {"sub": str(usuario_id), "tipo": "refresh"},
        timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.usuario_repo = UsuarioRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)

    async def login(self, email: str, password: str) -> TokenResponse:
        usuario = await self.usuario_repo.get_by_email(email)
        if not usuario or not verify_password(password, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
            )
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario desactivado",
            )

        access_token = create_access_token(usuario.id, usuario.tipo_usuario)
        refresh_token_str = create_refresh_token(usuario.id)

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self.refresh_repo.crear(usuario.id, refresh_token_str, expires_at)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("tipo") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

        rt = await self.refresh_repo.get_by_token(refresh_token)
        if not rt or rt.revocado:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado o no encontrado")

        now = datetime.now(timezone.utc)
        expires = rt.expires_at if rt.expires_at.tzinfo else rt.expires_at.replace(tzinfo=timezone.utc)
        if now > expires:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expirado")

        await self.refresh_repo.revocar(refresh_token)

        usuario = rt.usuario
        new_access = create_access_token(usuario.id, usuario.tipo_usuario)
        new_refresh = create_refresh_token(usuario.id)
        new_expires = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self.refresh_repo.crear(usuario.id, new_refresh, new_expires)

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, refresh_token: str) -> None:
        await self.refresh_repo.revocar(refresh_token)

    async def logout_all(self, usuario_id: uuid.UUID) -> None:
        await self.refresh_repo.revocar_todos_usuario(usuario_id)


async def get_usuario_actual(token: str, db: AsyncSession) -> Usuario:
    payload = decode_token(token)
    usuario_id_str: Optional[str] = payload.get("sub")
    if not usuario_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    repo = UsuarioRepository(db)
    usuario = await repo.get_by_id(uuid.UUID(usuario_id_str))
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o desactivado")
    return usuario
