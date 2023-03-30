"""Added ChatModel

Revision ID: 86224176ed81
Revises: f41cf7b5e372
Create Date: 2023-03-29 12:20:49.933365

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86224176ed81'
down_revision = 'f41cf7b5e372'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chats',
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('game_is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('chat_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('chats')
    # ### end Alembic commands ###
