from __future__ import annotations

import uuid
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Enum, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class TipoUsuario(str, enum.Enum):
    estudiante = "estudiante"
    empresa = "empresa"
    administrador_institucional = "administrador_institucional"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_usuario: Mapped[TipoUsuario] = mapped_column(
        Enum(TipoUsuario, name="tipo_usuario_enum"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verificado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    perfil_estudiante: Mapped[Optional[PerfilEstudiante]] = relationship(
        back_populates="usuario", uselist=False, cascade="all, delete-orphan"
    )
    perfil_empresa: Mapped[Optional[PerfilEmpresa]] = relationship(
        back_populates="usuario", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List[RefreshToken]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class PerfilEstudiante(Base):
    __tablename__ = "perfiles_estudiante"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    documento_identidad: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    universidad: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    programa: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    semestre: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    url_cv: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_documento_identidad: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_certificados_academicos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_foto_perfil: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_diploma_titulo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    usuario: Mapped[Usuario] = relationship(back_populates="perfil_estudiante")


class PerfilEmpresa(Base):
    __tablename__ = "perfiles_empresa"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    nombre_empresa: Mapped[str] = mapped_column(String(200), nullable=False)
    nit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    ciudad: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contacto_nombre: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contacto_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url_rut: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_camara_comercio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    usuario: Mapped[Usuario] = relationship(back_populates="perfil_empresa")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revocado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    usuario: Mapped[Usuario] = relationship(back_populates="refresh_tokens")
