"""production readiness

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-11-14 11:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False),
    )
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        'email_tokens',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('purpose', sa.String(length=24), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_email_tokens_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_email_tokens')),
    )
    op.create_index(op.f('ix_email_tokens_user_id'), 'email_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_tokens_token_hash'), 'email_tokens', ['token_hash'], unique=True)
    op.create_index('ix_email_tokens_user_purpose', 'email_tokens', ['user_id', 'purpose'], unique=False)

    # Index review: dashboard and analytics filter completed attempts per user and
    # read the XP ledger newest-first.
    op.create_index(
        'ix_assessment_attempts_user_status_completed',
        'assessment_attempts',
        ['user_id', 'status', 'completed_at'],
        unique=False,
    )
    op.create_index(
        'ix_xp_transactions_user_created',
        'xp_transactions',
        ['user_id', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_xp_transactions_user_created', table_name='xp_transactions')
    op.drop_index('ix_assessment_attempts_user_status_completed', table_name='assessment_attempts')

    op.drop_index('ix_email_tokens_user_purpose', table_name='email_tokens')
    op.drop_index(op.f('ix_email_tokens_token_hash'), table_name='email_tokens')
    op.drop_index(op.f('ix_email_tokens_user_id'), table_name='email_tokens')
    op.drop_table('email_tokens')

    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
