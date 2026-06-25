"""add_custom_templates_table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-24 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'custom_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('instruction', sa.Text(), nullable=False),
        # Postgres maps SQLAlchemy JSON to JSONB
        sa.Column('variables', sa.JSON(), nullable=False),
        sa.Column('default_title', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_custom_templates_id'), 'custom_templates', ['id'], unique=False)
    op.create_index(op.f('ix_custom_templates_key'), 'custom_templates', ['key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_custom_templates_key'), table_name='custom_templates')
    op.drop_index(op.f('ix_custom_templates_id'), table_name='custom_templates')
    op.drop_table('custom_templates')
