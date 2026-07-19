"""add is_approved / approved_at to users

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-19 06:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7c8d9e0f1a2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # server_default=true grandfathers in all existing accounts as approved;
    # new registrations explicitly pass is_approved=False at the ORM layer.
    op.add_column('users', sa.Column('is_approved', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('users', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.execute('UPDATE users SET approved_at = confirmed_at WHERE is_approved = 1')


def downgrade():
    op.drop_column('users', 'approved_at')
    op.drop_column('users', 'is_approved')
