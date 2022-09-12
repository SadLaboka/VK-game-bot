"""Add models

Revision ID: d402ced049d2
Revises: eb59eef0af20
Create Date: 2022-09-11 13:51:03.374886

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd402ced049d2'
down_revision = 'eb59eef0af20'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('difficulties',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('right_answers_to_win', sa.Integer(), nullable=False),
    sa.Column('wrong_answers_to_lose', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_difficulties_id'), 'difficulties', ['id'], unique=False)
    op.create_table('players',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('vk_id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=False),
    sa.Column('games_count', sa.Integer(), nullable=False),
    sa.Column('wins_count', sa.Integer(), nullable=False),
    sa.Column('loses_count', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('vk_id')
    )
    op.create_index(op.f('ix_players_id'), 'players', ['id'], unique=False)
    op.create_table('sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('started_by_vk_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('winner_id', sa.Integer(), nullable=True),
    sa.Column('response_time', sa.Integer(), nullable=False),
    sa.Column('session_duration', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['winner_id'], ['players.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)
    op.create_table('players_status',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('difficulty_id', sa.Integer(), nullable=False),
    sa.Column('right_answers', sa.Integer(), nullable=False),
    sa.Column('wrong_answers', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['difficulty_id'], ['difficulties.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('player_id')
    )
    op.create_index(op.f('ix_players_status_id'), 'players_status', ['id'], unique=False)
    op.add_column('questions', sa.Column('difficulty_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'questions', 'difficulties', ['difficulty_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'questions', type_='foreignkey')
    op.drop_column('questions', 'difficulty_id')
    op.drop_index(op.f('ix_players_status_id'), table_name='players_status')
    op.drop_table('players_status')
    op.drop_index(op.f('ix_sessions_id'), table_name='sessions')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_players_id'), table_name='players')
    op.drop_table('players')
    op.drop_index(op.f('ix_difficulties_id'), table_name='difficulties')
    op.drop_table('difficulties')
    # ### end Alembic commands ###
