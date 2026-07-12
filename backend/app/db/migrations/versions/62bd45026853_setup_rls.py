"""setup RLS

Revision ID: 62bd45026853
Revises: 4a06f57ea8e1
Create Date: 2026-07-12 17:26:46.552174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62bd45026853'
down_revision: Union[str, Sequence[str], None] = '4a06f57ea8e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('''
        CREATE OR REPLACE FUNCTION current_project_id()
        RETURNS text AS $$
        BEGIN
            RETURN current_setting('app.current_project_id', true);
        END;
        $$ LANGUAGE plpgsql;
    ''')


def downgrade() -> None:
    op.execute('DROP FUNCTION IF EXISTS current_project_id();')
