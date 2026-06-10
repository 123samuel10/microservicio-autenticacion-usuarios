"""Agrega habilidades al perfil de estudiante

Lista de skills del estudiante (ARRAY de strings), por defecto vacía.

Revision ID: 0003_habilidades
Revises: 0002_disponibilidad
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_habilidades"
down_revision: Union[str, None] = "0002_disponibilidad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "perfiles_estudiante",
        sa.Column(
            "habilidades",
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
    )


def downgrade() -> None:
    op.drop_column("perfiles_estudiante", "habilidades")
