import uuid
from typing import Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings
from app.models.usuario import TipoUsuario
from app.repositories.usuario_repository import (
    PerfilEmpresaRepository,
    PerfilEstudianteRepository,
    UsuarioRepository,
)
from app.schemas.usuario import (
    PerfilEmpresaUpdate,
    PerfilEstudianteUpdate,
    RegistroEmpresaRequest,
    RegistroEstudianteRequest,
    UsuarioResponse,
)
from app.services.auth_service import hash_password

settings = get_settings()

CAMPOS_DOCUMENTO_ESTUDIANTE = {
    "cv": "url_cv",
    "documento_identidad": "url_documento_identidad",
    "certificados_academicos": "url_certificados_academicos",
    "foto_perfil": "url_foto_perfil",
    "diploma_titulo": "url_diploma_titulo",
}

CAMPOS_DOCUMENTO_EMPRESA = {
    "rut": "url_rut",
    "camara_comercio": "url_camara_comercio",
}


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


async def _subir_archivo_s3(file: UploadFile, key: str) -> str:
    s3 = _s3_client()
    try:
        contenido = await file.read()
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=contenido,
            ContentType=file.content_type or "application/octet-stream",
        )
        return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error al subir el archivo: {str(e)}",
        )


class UsuarioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.usuario_repo = UsuarioRepository(db)
        self.estudiante_repo = PerfilEstudianteRepository(db)
        self.empresa_repo = PerfilEmpresaRepository(db)

    async def registrar_estudiante(self, datos: RegistroEstudianteRequest) -> UsuarioResponse:
        existente = await self.usuario_repo.get_by_email(datos.email)
        if existente:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado")

        usuario = await self.usuario_repo.crear(
            email=datos.email,
            password_hash=hash_password(datos.password),
            tipo_usuario=TipoUsuario.estudiante,
        )
        await self.estudiante_repo.crear(
            usuario_id=usuario.id,
            nombres=datos.nombres,
            apellidos=datos.apellidos,
            universidad=datos.universidad,
            programa=datos.programa,
        )
        return await self._get_usuario_completo(usuario.id)

    async def registrar_empresa(self, datos: RegistroEmpresaRequest) -> UsuarioResponse:
        existente = await self.usuario_repo.get_by_email(datos.email)
        if existente:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado")

        usuario = await self.usuario_repo.crear(
            email=datos.email,
            password_hash=hash_password(datos.password),
            tipo_usuario=TipoUsuario.empresa,
        )
        await self.empresa_repo.crear(
            usuario_id=usuario.id,
            nombre_empresa=datos.nombre_empresa,
            nit=datos.nit,
            contacto_nombre=datos.contacto_nombre,
        )
        return await self._get_usuario_completo(usuario.id)

    async def get_perfil(self, usuario_id: uuid.UUID) -> UsuarioResponse:
        return await self._get_usuario_completo(usuario_id)

    async def actualizar_perfil_estudiante(
        self, usuario_id: uuid.UUID, datos: PerfilEstudianteUpdate
    ) -> UsuarioResponse:
        perfil = await self.estudiante_repo.get_by_usuario_id(usuario_id)
        if not perfil:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")
        await self.estudiante_repo.actualizar(perfil, datos.model_dump(exclude_none=True))
        return await self._get_usuario_completo(usuario_id)

    async def actualizar_perfil_empresa(
        self, usuario_id: uuid.UUID, datos: PerfilEmpresaUpdate
    ) -> UsuarioResponse:
        perfil = await self.empresa_repo.get_by_usuario_id(usuario_id)
        if not perfil:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")
        await self.empresa_repo.actualizar(perfil, datos.model_dump(exclude_none=True))
        return await self._get_usuario_completo(usuario_id)

    async def subir_documento_estudiante(
        self, usuario_id: uuid.UUID, tipo_documento: str, file: UploadFile
    ) -> str:
        campo = CAMPOS_DOCUMENTO_ESTUDIANTE.get(tipo_documento)
        if not campo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de documento inválido. Opciones: {list(CAMPOS_DOCUMENTO_ESTUDIANTE.keys())}",
            )
        key = f"estudiantes/{usuario_id}/{tipo_documento}/{file.filename}"
        url = await _subir_archivo_s3(file, key)
        await self.estudiante_repo.actualizar_url_documento(usuario_id, campo, url)
        return url

    async def subir_documento_empresa(
        self, usuario_id: uuid.UUID, tipo_documento: str, file: UploadFile
    ) -> str:
        campo = CAMPOS_DOCUMENTO_EMPRESA.get(tipo_documento)
        if not campo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de documento inválido. Opciones: {list(CAMPOS_DOCUMENTO_EMPRESA.keys())}",
            )
        key = f"empresas/{usuario_id}/{tipo_documento}/{file.filename}"
        url = await _subir_archivo_s3(file, key)
        await self.empresa_repo.actualizar_url_documento(usuario_id, campo, url)
        return url

    async def _get_usuario_completo(self, usuario_id: uuid.UUID) -> UsuarioResponse:
        usuario = await self.usuario_repo.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return UsuarioResponse.model_validate(usuario)
