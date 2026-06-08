import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.usuario import Usuario, PerfilEstudiante, PerfilEmpresa, RefreshToken, TipoUsuario


class UsuarioRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, usuario_id: uuid.UUID) -> Optional[Usuario]:
        result = await self.db.execute(
            select(Usuario)
            .options(
                selectinload(Usuario.perfil_estudiante),
                selectinload(Usuario.perfil_empresa),
            )
            .where(Usuario.id == usuario_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        result = await self.db.execute(
            select(Usuario)
            .options(
                selectinload(Usuario.perfil_estudiante),
                selectinload(Usuario.perfil_empresa),
            )
            .where(Usuario.email == email)
        )
        return result.scalar_one_or_none()

    async def crear(self, email: str, password_hash: str, tipo_usuario: TipoUsuario) -> Usuario:
        usuario = Usuario(email=email, password_hash=password_hash, tipo_usuario=tipo_usuario)
        self.db.add(usuario)
        await self.db.flush()
        await self.db.refresh(usuario)
        return usuario

    async def actualizar_activo(self, usuario_id: uuid.UUID, activo: bool) -> None:
        usuario = await self.get_by_id(usuario_id)
        if usuario:
            usuario.activo = activo
            await self.db.flush()


class PerfilEstudianteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_usuario_id(self, usuario_id: uuid.UUID) -> Optional[PerfilEstudiante]:
        result = await self.db.execute(
            select(PerfilEstudiante).where(PerfilEstudiante.usuario_id == usuario_id)
        )
        return result.scalar_one_or_none()

    async def crear(self, usuario_id: uuid.UUID, nombres: str, apellidos: str, **kwargs) -> PerfilEstudiante:
        perfil = PerfilEstudiante(usuario_id=usuario_id, nombres=nombres, apellidos=apellidos, **kwargs)
        self.db.add(perfil)
        await self.db.flush()
        await self.db.refresh(perfil)
        return perfil

    async def actualizar(self, perfil: PerfilEstudiante, datos: dict) -> PerfilEstudiante:
        for campo, valor in datos.items():
            if valor is not None:
                setattr(perfil, campo, valor)
        await self.db.flush()
        await self.db.refresh(perfil)
        return perfil

    async def actualizar_url_documento(self, usuario_id: uuid.UUID, campo: str, url: str) -> Optional[PerfilEstudiante]:
        perfil = await self.get_by_usuario_id(usuario_id)
        if perfil:
            setattr(perfil, campo, url)
            await self.db.flush()
            await self.db.refresh(perfil)
        return perfil


class PerfilEmpresaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_usuario_id(self, usuario_id: uuid.UUID) -> Optional[PerfilEmpresa]:
        result = await self.db.execute(
            select(PerfilEmpresa).where(PerfilEmpresa.usuario_id == usuario_id)
        )
        return result.scalar_one_or_none()

    async def crear(self, usuario_id: uuid.UUID, nombre_empresa: str, **kwargs) -> PerfilEmpresa:
        perfil = PerfilEmpresa(usuario_id=usuario_id, nombre_empresa=nombre_empresa, **kwargs)
        self.db.add(perfil)
        await self.db.flush()
        await self.db.refresh(perfil)
        return perfil

    async def actualizar(self, perfil: PerfilEmpresa, datos: dict) -> PerfilEmpresa:
        for campo, valor in datos.items():
            if valor is not None:
                setattr(perfil, campo, valor)
        await self.db.flush()
        await self.db.refresh(perfil)
        return perfil

    async def actualizar_url_documento(self, usuario_id: uuid.UUID, campo: str, url: str) -> Optional[PerfilEmpresa]:
        perfil = await self.get_by_usuario_id(usuario_id)
        if perfil:
            setattr(perfil, campo, url)
            await self.db.flush()
            await self.db.refresh(perfil)
        return perfil


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear(self, usuario_id: uuid.UUID, token: str, expires_at) -> RefreshToken:
        rt = RefreshToken(usuario_id=usuario_id, token=token, expires_at=expires_at)
        self.db.add(rt)
        await self.db.flush()
        return rt

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken)
            .options(selectinload(RefreshToken.usuario))
            .where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def revocar(self, token: str) -> None:
        rt = await self.get_by_token(token)
        if rt:
            rt.revocado = True
            await self.db.flush()

    async def revocar_todos_usuario(self, usuario_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.usuario_id == usuario_id,
                RefreshToken.revocado == False,
            )
        )
        tokens = result.scalars().all()
        for t in tokens:
            t.revocado = True
        await self.db.flush()
