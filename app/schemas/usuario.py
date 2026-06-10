import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.usuario import TipoUsuario


# --- Auth ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    tipo: str
    exp: int


# --- Registro ---

class RegistroEstudianteRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    nombres: str = Field(min_length=1, max_length=100)
    apellidos: str = Field(min_length=1, max_length=100)
    universidad: Optional[str] = None
    programa: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("La contraseña debe tener al menos una mayúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe tener al menos un número")
        return v


class RegistroEmpresaRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    nombre_empresa: str = Field(min_length=1, max_length=200)
    nit: Optional[str] = None
    contacto_nombre: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("La contraseña debe tener al menos una mayúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe tener al menos un número")
        return v


# --- Perfil Estudiante ---

class PerfilEstudianteBase(BaseModel):
    nombres: str = Field(max_length=100)
    apellidos: str = Field(max_length=100)
    documento_identidad: Optional[str] = None
    telefono: Optional[str] = None
    universidad: Optional[str] = None
    programa: Optional[str] = None
    semestre: Optional[int] = Field(None, ge=1, le=12)
    disponibilidad: Optional[str] = Field(
        None, description="tiempo_completo | medio_tiempo | fines_de_semana"
    )
    # Optional[...] = None para que un update parcial no borre las habilidades
    # existentes; en las respuestas se lee la lista real del ORM (server_default '{}').
    habilidades: Optional[List[str]] = None


class PerfilEstudianteUpdate(PerfilEstudianteBase):
    pass


class PerfilEstudianteResponse(PerfilEstudianteBase):
    id: uuid.UUID
    usuario_id: uuid.UUID
    url_cv: Optional[str] = None
    url_documento_identidad: Optional[str] = None
    url_certificados_academicos: Optional[str] = None
    url_foto_perfil: Optional[str] = None
    url_diploma_titulo: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Perfil Empresa ---

class PerfilEmpresaBase(BaseModel):
    nombre_empresa: str = Field(max_length=200)
    nit: Optional[str] = None
    sector: Optional[str] = None
    descripcion: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_email: Optional[EmailStr] = None


class PerfilEmpresaUpdate(PerfilEmpresaBase):
    pass


class PerfilEmpresaResponse(PerfilEmpresaBase):
    id: uuid.UUID
    usuario_id: uuid.UUID
    url_rut: Optional[str] = None
    url_camara_comercio: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Usuario ---

class UsuarioResponse(BaseModel):
    id: uuid.UUID
    email: str
    tipo_usuario: TipoUsuario
    activo: bool
    email_verificado: bool
    created_at: datetime
    perfil_estudiante: Optional[PerfilEstudianteResponse] = None
    perfil_empresa: Optional[PerfilEmpresaResponse] = None

    model_config = {"from_attributes": True}


class UsuarioResumenResponse(BaseModel):
    id: uuid.UUID
    email: str
    tipo_usuario: TipoUsuario
    activo: bool

    model_config = {"from_attributes": True}


class PerfilPublicoResponse(BaseModel):
    """Datos públicos de un usuario, consultables por su id sin autenticación.

    Pensado para que otros servicios/el frontend resuelvan el nombre visible
    de una empresa o estudiante a partir de su `usuario_id` (p. ej. mostrar el
    nombre de la empresa dueña de una vacante). NO expone email ni datos de
    contacto sensibles.
    """
    id: uuid.UUID
    tipo_usuario: TipoUsuario
    nombre: str
    sector: Optional[str] = None
    ciudad: Optional[str] = None
    programa: Optional[str] = None
    universidad: Optional[str] = None


# --- Documentos ---

class DocumentoUploadResponse(BaseModel):
    campo: str
    url: str
    mensaje: str
