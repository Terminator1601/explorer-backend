"""add cover_image and media_urls to events

Revision ID: 001_add_media_fields
Revises: 
Create Date: 2026-03-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001_add_media_fields'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cover_image', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('media_urls', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('media_urls')
        batch_op.drop_column('cover_image')
