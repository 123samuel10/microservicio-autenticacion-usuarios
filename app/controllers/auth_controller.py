from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.controllers.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(datos: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(datos.email, datos.password)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(datos: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh(datos.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    datos: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    service = AuthService(db)
    await service.logout(datos.refresh_token)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    service = AuthService(db)
    await service.logout_all(usuario.id)
