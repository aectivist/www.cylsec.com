"""Add instance_name column to challenges

Revision ID: 386fc634d614
Revises: 0000000000_initial
Create Date: 2026-07-14 14:51:59.096168

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


revision = '386fc634d614'
down_revision = '0000000000_initial'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    cols = [c['name'] for c in Inspector.from_engine(bind).get_columns('challenges')]
    if 'instance_name' not in cols:
        with op.batch_alter_table('challenges', schema=None) as batch_op:
            batch_op.add_column(sa.Column('instance_name', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('challenges', schema=None) as batch_op:
        batch_op.drop_column('instance_name')
