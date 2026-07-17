"""Initial schema — create all base tables

Revision ID: 0000000000_initial
Revises:
Create Date: 2026-07-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


revision = '0000000000_initial'
down_revision = None
branch_labels = None
depends_on = None


def _tables(bind):
    return Inspector.from_engine(bind).get_table_names()


def upgrade():
    bind = op.get_bind()
    existing = _tables(bind)

    if 'users' not in existing:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=80), nullable=False),
            sa.Column('email', sa.String(length=120), nullable=False),
            sa.Column('password_hash', sa.String(length=128), nullable=False),
            sa.Column('xp', sa.Integer(), nullable=True),
            sa.Column('role', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('confirmed', sa.Boolean(), nullable=True),
            sa.Column('confirmed_at', sa.DateTime(), nullable=True),
            sa.Column('custom_rank', sa.String(length=50), nullable=True),
            sa.Column('rank_color', sa.String(length=7), nullable=True),
            sa.Column('two_factor_enabled', sa.Boolean(), nullable=True),
            sa.Column('totp_secret', sa.String(length=32), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('username'),
        )

    if 'categories' not in existing:
        op.create_table(
            'categories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('icon', sa.String(length=100), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
        )

    if 'challenges' not in existing:
        op.create_table(
            'challenges',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('difficulty', sa.String(length=20), nullable=True),
            sa.Column('points', sa.Integer(), nullable=True),
            sa.Column('flag', sa.String(length=100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('type', sa.String(length=20), nullable=True),
            sa.Column('file_url', sa.String(length=200), nullable=True),
            sa.Column('challenge_url', sa.String(length=200), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'solves' not in existing:
        op.create_table(
            'solves',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('challenge_id', sa.Integer(), nullable=False),
            sa.Column('solved_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['challenge_id'], ['challenges.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'admin_logs' not in existing:
        op.create_table(
            'admin_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('admin_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.String(length=200), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['admin_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'settings' not in existing:
        op.create_table(
            'settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('key', sa.String(length=50), nullable=False),
            sa.Column('value', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('key'),
        )


def downgrade():
    op.drop_table('settings')
    op.drop_table('admin_logs')
    op.drop_table('solves')
    op.drop_table('challenges')
    op.drop_table('categories')
    op.drop_table('users')
