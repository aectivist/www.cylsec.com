"""add shutdown_votes table

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'shutdown_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('voted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['docker_instances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('instance_id', 'user_id', name='uq_shutdown_vote'),
    )


def downgrade():
    op.drop_table('shutdown_votes')
