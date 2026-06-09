"""create orders table

Revision ID: 546f8d1986b2
Revises: 9c7cff270b5a
Create Date: 2026-06-09 09:31:10.525126

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '546f8d1986b2'
down_revision: Union[str, Sequence[str], None] = '9c7cff270b5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. 创建枚举类型（使用 checkfirst=True）
    order_status_enum = postgresql.ENUM('PENDING', 'PAID', 'CANCELLED', 'EXPIRED', name='orderstatus')
    order_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. 创建订单表
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('status', 
                  postgresql.ENUM('PENDING', 'PAID', 'CANCELLED', 'EXPIRED', name='orderstatus', create_type=False),
                  nullable=False, server_default='PENDING'),
        sa.Column('trade_no', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_orders_user_id'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], name='fk_orders_plan_id'),
        sa.PrimaryKeyConstraint('id', name='pk_orders')
    )

    # 3. 创建索引
    op.create_index('ix_orders_id', 'orders', ['id'], unique=False)
    op.create_index('ix_orders_user_id', 'orders', ['user_id'], unique=False)
    op.create_index('ix_orders_trade_no', 'orders', ['trade_no'], unique=True)
    op.create_index('ix_orders_created_at', 'orders', ['created_at'], unique=False)

def downgrade() -> None:
    # 1. 删除索引
    op.drop_index('ix_orders_created_at', table_name='orders')
    op.drop_index('ix_orders_trade_no', table_name='orders')
    op.drop_index('ix_orders_user_id', table_name='orders')
    op.drop_index('ix_orders_id', table_name='orders')

    # 2. 删除订单表
    op.drop_table('orders')

    # 3. 删除枚举类型（使用 checkfirst=True）
    order_status_enum = postgresql.ENUM('PENDING', 'PAID', 'CANCELLED', 'EXPIRED', name='orderstatus')
    order_status_enum.drop(op.get_bind(), checkfirst=True)
