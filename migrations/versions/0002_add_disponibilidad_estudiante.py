"""Agrega disponibilidad al perfil de estudiante

Campo de disponibilidad laboral: tiempo_completo | medio_tiempo | fines_de_semana.

Revision ID: 0002_disponibilidad
Revises: 0001_initial
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_disponibilidad"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "perfiles_estudiante",
        sa.Column("disponibilidad", sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("perfiles_estudiante", "disponibilidad")
