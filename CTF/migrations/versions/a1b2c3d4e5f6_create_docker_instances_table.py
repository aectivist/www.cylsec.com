"""Create docker_instances table

Revision ID: a1b2c3d4e5f6
Revises: 386fc634d614
Create Date: 2026-07-14 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '386fc634d614'
branch_labels = None
depends_on = None


def upgrade():
    # Guard: skip creation if the table already exists (e.g. created by db.create_all)
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    if 'docker_instances' in inspector.get_table_names():
        return

    op.create_table(
        'docker_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('container_id', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_extended_at', sa.DateTime(), nullable=True),
        sa.Column('extensions_used', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('url', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['challenge_id'], ['challenges.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('container_id'),
    )


def downgrade():
    op.drop_table('docker_instances')
