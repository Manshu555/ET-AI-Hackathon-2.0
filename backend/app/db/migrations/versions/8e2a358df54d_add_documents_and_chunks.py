"""add documents and chunks

Revision ID: 8e2a358df54d
Revises: 62bd45026853
Create Date: 2026-07-12 21:18:19.657044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '8e2a358df54d'
down_revision: Union[str, Sequence[str], None] = '62bd45026853'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('doc_type', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('storage_url', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.Column('ingestion_status', sa.String(), nullable=True, default='queued'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('chunk_text', sa.String(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_heading', sa.String(), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('document_chunks')
    op.drop_table('documents')
