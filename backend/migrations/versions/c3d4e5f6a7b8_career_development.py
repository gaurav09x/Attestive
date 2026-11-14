"""career development

Revision ID: c3d4e5f6a7b8
Revises: 9f2c1a7b4e10
Create Date: 2026-11-14 10:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = '9f2c1a7b4e10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'career_roles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('slug', sa.String(length=60), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('skills', sa.JSON(), nullable=False),
        sa.Column('portfolio_briefs', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_career_roles')),
    )
    op.create_index(op.f('ix_career_roles_slug'), 'career_roles', ['slug'], unique=True)

    op.create_table(
        'interview_questions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('skill_id', sa.Uuid(), nullable=True),
        sa.Column('kind', sa.String(length=24), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('rubric', sa.JSON(), nullable=False),
        sa.Column('model_answer', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['career_roles.id'], name=op.f('fk_interview_questions_role_id_career_roles'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('fk_interview_questions_skill_id_skills'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_questions')),
    )
    op.create_index(op.f('ix_interview_questions_role_id'), 'interview_questions', ['role_id'], unique=False)
    op.create_index(op.f('ix_interview_questions_skill_id'), 'interview_questions', ['skill_id'], unique=False)
    op.create_index('ix_interview_questions_role_position', 'interview_questions', ['role_id', 'position'], unique=False)

    op.create_table(
        'mock_interviews',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('readiness', sa.String(length=24), nullable=True),
        sa.Column('feedback', sa.JSON(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['career_roles.id'], name=op.f('fk_mock_interviews_role_id_career_roles'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_mock_interviews_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_mock_interviews')),
    )
    op.create_index(op.f('ix_mock_interviews_user_id'), 'mock_interviews', ['user_id'], unique=False)
    op.create_index(op.f('ix_mock_interviews_role_id'), 'mock_interviews', ['role_id'], unique=False)
    op.create_index('ix_mock_interviews_user_started', 'mock_interviews', ['user_id', 'started_at'], unique=False)

    op.create_table(
        'interview_responses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('interview_id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('matched_points', sa.JSON(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['mock_interviews.id'], name=op.f('fk_interview_responses_interview_id_mock_interviews'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['interview_questions.id'], name=op.f('fk_interview_responses_question_id_interview_questions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_responses')),
        sa.UniqueConstraint('interview_id', 'question_id', name='interview_question_once'),
    )
    op.create_index(op.f('ix_interview_responses_interview_id'), 'interview_responses', ['interview_id'], unique=False)
    op.create_index(op.f('ix_interview_responses_question_id'), 'interview_responses', ['question_id'], unique=False)

    op.create_table(
        'resume_skills',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('skill_id', sa.Uuid(), nullable=True),
        sa.Column('label', sa.String(length=120), nullable=False),
        sa.Column('claimed_level', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('fk_resume_skills_skill_id_skills'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_resume_skills_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_resume_skills')),
        sa.UniqueConstraint('user_id', 'label', name='user_resume_label'),
    )
    op.create_index(op.f('ix_resume_skills_user_id'), 'resume_skills', ['user_id'], unique=False)
    op.create_index(op.f('ix_resume_skills_skill_id'), 'resume_skills', ['skill_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_skills_skill_id'), table_name='resume_skills')
    op.drop_index(op.f('ix_resume_skills_user_id'), table_name='resume_skills')
    op.drop_table('resume_skills')

    op.drop_index(op.f('ix_interview_responses_question_id'), table_name='interview_responses')
    op.drop_index(op.f('ix_interview_responses_interview_id'), table_name='interview_responses')
    op.drop_table('interview_responses')

    op.drop_index('ix_mock_interviews_user_started', table_name='mock_interviews')
    op.drop_index(op.f('ix_mock_interviews_role_id'), table_name='mock_interviews')
    op.drop_index(op.f('ix_mock_interviews_user_id'), table_name='mock_interviews')
    op.drop_table('mock_interviews')

    op.drop_index('ix_interview_questions_role_position', table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_skill_id'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_role_id'), table_name='interview_questions')
    op.drop_table('interview_questions')

    op.drop_index(op.f('ix_career_roles_slug'), table_name='career_roles')
    op.drop_table('career_roles')
