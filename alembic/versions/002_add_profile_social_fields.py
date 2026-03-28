"""add bio, interests, social_links to users

Revision ID: 002_add_profile_social
Revises: 001_add_media_fields
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002_add_profile_social'
down_revision: Union[str, None] = '001_add_media_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bio', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('interests', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('social_links', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('social_links')
        batch_op.drop_column('interests')
        batch_op.drop_column('bio')
