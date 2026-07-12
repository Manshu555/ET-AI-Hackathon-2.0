"""add compliance and rfi models

Revision ID: 2e9fd6c8acd3
Revises: 8e2a358df54d
Create Date: 2026-07-12 21:20:01.974053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e9fd6c8acd3'
down_revision: Union[str, Sequence[str], None] = '8e2a358df54d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'vendors',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'specifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('spec_code', sa.String(), nullable=False),
        sa.Column('section', sa.String(), nullable=True),
        sa.Column('requirement_text', sa.String(), nullable=False),
        sa.Column('numeric_requirement', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'submittals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('vendor_id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'rfis',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('rfi_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['rfi_id'], ['rfis.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'deviations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('submittal_id', sa.String(), nullable=False),
        sa.Column('spec_id', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('detected_by', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('resolution_note', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['spec_id'], ['specifications.id'], ),
        sa.ForeignKeyConstraint(['submittal_id'], ['submittals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_table('deviations')
    op.drop_table('chat_sessions')
    op.drop_table('rfis')
    op.drop_table('submittals')
    op.drop_table('specifications')
    op.drop_table('vendors')
