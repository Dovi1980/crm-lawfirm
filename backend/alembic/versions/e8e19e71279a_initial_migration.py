"""initial_migration

Revision ID: e8e19e71279a
Revises: 
Create Date: 2026-05-26 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8e19e71279a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. CREATE users TABLE
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'LAWYER', 'ASSISTANT', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. CREATE clients TABLE
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('client_type', sa.Enum('NATURAL', 'LEGAL', name='clienttype'), nullable=False),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('province', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clients_email'), 'clients', ['email'], unique=False)
    op.create_index(op.f('ix_clients_id'), 'clients', ['id'], unique=False)
    op.create_index(op.f('ix_clients_is_active'), 'clients', ['is_active'], unique=False)
    op.create_index(op.f('ix_clients_tax_id'), 'clients', ['tax_id'], unique=True)

    # 3. CREATE cases TABLE
    op.create_table(
        'cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_number', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('case_type', sa.Enum('CIVIL', 'PENAL', 'LABORAL', 'COMERCIAL', 'FAMILIA', 'OTRO', name='casetype'), nullable=False),
        sa.Column('status', sa.Enum('NUEVO', 'EN_PROCESO', 'EN_ESPERA', 'CERRADO', 'ARCHIVADO', name='casestatus'), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('assigned_lawyer_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('estimated_close_date', sa.Date(), nullable=True),
        sa.Column('agreed_fees', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('internal_notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_lawyer_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cases_assigned_lawyer_id'), 'cases', ['assigned_lawyer_id'], unique=False)
    op.create_index(op.f('ix_cases_case_number'), 'cases', ['case_number'], unique=True)
    op.create_index(op.f('ix_cases_client_id'), 'cases', ['client_id'], unique=False)
    op.create_index(op.f('ix_cases_id'), 'cases', ['id'], unique=False)

    # 4. CREATE interactions TABLE
    op.create_table(
        'interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('interaction_type', sa.Enum('LLAMADA', 'EMAIL', 'REUNION', 'ESCRITO', 'AUDIENCIA', 'OTRO', name='interactiontype'), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('interaction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interactions_case_id'), 'interactions', ['case_id'], unique=False)
    op.create_index(op.f('ix_interactions_client_id'), 'interactions', ['client_id'], unique=False)
    op.create_index(op.f('ix_interactions_id'), 'interactions', ['id'], unique=False)
    op.create_index(op.f('ix_interactions_interaction_date'), 'interactions', ['interaction_date'], unique=False)
    op.create_index(op.f('ix_interactions_user_id'), 'interactions', ['user_id'], unique=False)

    # 5. CREATE tasks TABLE
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('priority', sa.Enum('BAJA', 'MEDIA', 'ALTA', 'URGENTE', name='taskpriority'), nullable=False),
        sa.Column('status', sa.Enum('PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'CANCELADA', name='taskstatus'), nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_assigned_to_id'), 'tasks', ['assigned_to_id'], unique=False)
    op.create_index(op.f('ix_tasks_case_id'), 'tasks', ['case_id'], unique=False)
    op.create_index(op.f('ix_tasks_client_id'), 'tasks', ['client_id'], unique=False)
    op.create_index(op.f('ix_tasks_due_date'), 'tasks', ['due_date'], unique=False)
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)

    # 6. CREATE refresh_tokens TABLE
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)

    # 7. CREATE password_reset_tokens TABLE
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_reset_tokens_id'), 'password_reset_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_password_reset_tokens_token_hash'), 'password_reset_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_password_reset_tokens_user_id'), 'password_reset_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('password_reset_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('tasks')
    op.drop_table('interactions')
    op.drop_table('cases')
    op.drop_table('clients')
    op.drop_table('users')
    
    # Drop custom enums
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='clienttype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='casetype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='casestatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='interactiontype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskpriority').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskstatus').drop(op.get_bind(), checkfirst=True)
