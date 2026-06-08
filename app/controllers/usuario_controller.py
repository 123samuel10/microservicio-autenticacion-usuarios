from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    DocumentoUploadResponse,
    PerfilEmpresaUpdate,
    PerfilEstudianteUpdate,
    RegistroEmpresaRequest,
    RegistroEstudianteRequest,
    UsuarioResponse,
)
from app.services.usuario_service import UsuarioService
from app.controllers.deps import get_current_user, require_empresa, require_estudiante

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post(
    "/registro/estudiante",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_estudiante(datos: RegistroEstudianteRequest, db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.registrar_estudiante(datos)


@router.post(
    "/registro/empresa",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_empresa(datos: RegistroEmpresaRequest, db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.registrar_empresa(datos)


@router.get("/me", response_model=UsuarioResponse)
async def get_perfil(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    service = UsuarioService(db)
    return await service.get_perfil(usuario.id)


@router.put("/me/perfil/estudiante", response_model=UsuarioResponse)
async def actualizar_perfil_estudiante(
    datos: PerfilEstudianteUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_estudiante),
):
    service = UsuarioService(db)
    return await service.actualizar_perfil_estudiante(usuario.id, datos)


@router.put("/me/perfil/empresa", response_model=UsuarioResponse)
async def actualizar_perfil_empresa(
    datos: PerfilEmpresaUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_empresa),
):
    service = UsuarioService(db)
    return await service.actualizar_perfil_empresa(usuario.id, datos)


@router.post(
    "/me/documentos/estudiante/{tipo_documento}",
    response_model=DocumentoUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def subir_documento_estudiante(
    tipo_documento: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_estudiante),
):
    service = UsuarioService(db)
    url = await service.subir_documento_estudiante(usuario.id, tipo_documento, file)
    return DocumentoUploadResponse(
        campo=tipo_documento,
        url=url,
        mensaje="Documento subido correctamente",
    )


@router.post(
    "/me/documentos/empresa/{tipo_documento}",
    response_model=DocumentoUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def subir_documento_empresa(
    tipo_documento: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_empresa),
):
    service = UsuarioService(db)
    url = await service.subir_documento_empresa(usuario.id, tipo_documento, file)
    return DocumentoUploadResponse(
        campo=tipo_documento,
        url=url,
        mensaje="Documento subido correctamente",
    )
