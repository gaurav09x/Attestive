"""tutor conversations

Revision ID: 9f2c1a7b4e10
Revises: 38d689103031
Create Date: 2026-11-13 19:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9f2c1a7b4e10'
down_revision: Union[str, None] = '38d689103031'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('subject_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=160), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], name=op.f('fk_ai_conversations_subject_id_subjects'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_ai_conversations_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_conversations')),
    )
    op.create_index(op.f('ix_ai_conversations_subject_id'), 'ai_conversations', ['subject_id'], unique=False)
    op.create_index(op.f('ix_ai_conversations_user_id'), 'ai_conversations', ['user_id'], unique=False)
    op.create_index('ix_ai_conversations_user_updated', 'ai_conversations', ['user_id', 'updated_at'], unique=False)

    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('mode', sa.String(length=20), nullable=False),
        sa.Column('hint_level', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=60), nullable=False),
        sa.Column('sources', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], name=op.f('fk_conversation_messages_conversation_id_ai_conversations'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_conversation_messages')),
    )
    op.create_index(op.f('ix_conversation_messages_conversation_id'), 'conversation_messages', ['conversation_id'], unique=False)
    op.create_index('ix_conversation_messages_conversation_created', 'conversation_messages', ['conversation_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_conversation_messages_conversation_created', table_name='conversation_messages')
    op.drop_index(op.f('ix_conversation_messages_conversation_id'), table_name='conversation_messages')
    op.drop_table('conversation_messages')
    op.drop_index('ix_ai_conversations_user_updated', table_name='ai_conversations')
    op.drop_index(op.f('ix_ai_conversations_user_id'), table_name='ai_conversations')
    op.drop_index(op.f('ix_ai_conversations_subject_id'), table_name='ai_conversations')
    op.drop_table('ai_conversations')
