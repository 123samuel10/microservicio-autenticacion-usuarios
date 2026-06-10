"""Esquema inicial: usuarios, perfiles y refresh tokens

Refleja el esquema que hasta ahora se creaba con Base.metadata.create_all.
En una BD ya existente con estas tablas, marca esta revisión sin recrearlas con:
    alembic stamp 0001_initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tipo ENUM de Postgres para el tipo de usuario.
tipo_usuario_enum = postgresql.ENUM(
    "estudiante",
    "empresa",
    "administrador_institucional",
    name="tipo_usuario_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    # Crear el tipo ENUM explícitamente (checkfirst evita error si ya existe).
    tipo_usuario_enum.create(bind, checkfirst=True)

    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("tipo_usuario", tipo_usuario_enum, nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("email_verificado", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usuarios_email"), "usuarios", ["email"], unique=True)

    op.create_table(
        "perfiles_estudiante",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombres", sa.String(length=100), nullable=False),
        sa.Column("apellidos", sa.String(length=100), nullable=False),
        sa.Column("documento_identidad", sa.String(length=20), nullable=True),
        sa.Column("telefono", sa.String(length=20), nullable=True),
        sa.Column("universidad", sa.String(length=200), nullable=True),
        sa.Column("programa", sa.String(length=200), nullable=True),
        sa.Column("semestre", sa.Integer(), nullable=True),
        sa.Column("url_cv", sa.Text(), nullable=True),
        sa.Column("url_documento_identidad", sa.Text(), nullable=True),
        sa.Column("url_certificados_academicos", sa.Text(), nullable=True),
        sa.Column("url_foto_perfil", sa.Text(), nullable=True),
        sa.Column("url_diploma_titulo", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id"),
    )

    op.create_table(
        "perfiles_empresa",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre_empresa", sa.String(length=200), nullable=False),
        sa.Column("nit", sa.String(length=20), nullable=True),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("telefono", sa.String(length=20), nullable=True),
        sa.Column("direccion", sa.String(length=300), nullable=True),
        sa.Column("ciudad", sa.String(length=100), nullable=True),
        sa.Column("contacto_nombre", sa.String(length=200), nullable=True),
        sa.Column("contacto_email", sa.String(length=255), nullable=True),
        sa.Column("url_rut", sa.Text(), nullable=True),
        sa.Column("url_camara_comercio", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocado", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_refresh_tokens_token"), "refresh_tokens", ["token"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_tokens_token"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("perfiles_empresa")
    op.drop_table("perfiles_estudiante")
    op.drop_index(op.f("ix_usuarios_email"), table_name="usuarios")
    op.drop_table("usuarios")
    tipo_usuario_enum.drop(op.get_bind(), checkfirst=True)
