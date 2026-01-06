"""ingest_runs_raw_records

Revision ID: a2c4e6f8b1d3
Revises: 78b15fee4f9b
Create Date: 2026-01-06 12:00:00.000000

"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a2c4e6f8b1d3'
down_revision: str | Sequence[str] | None = '78b15fee4f9b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - create data_sources and ingested_records tables."""
    # Create data_sources table
    op.create_table(
        'data_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_sources_id'), 'data_sources', ['id'], unique=False)
    op.create_index(op.f('ix_data_sources_name'), 'data_sources', ['name'], unique=True)
    
    # Create ingested_records table
    op.create_table(
        'ingested_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('processed_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('ingested_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ingested_records_id'), 'ingested_records', ['id'], unique=False)
    op.create_index(op.f('ix_ingested_records_source_id'), 'ingested_records', ['source_id'], unique=False)
    op.create_index(op.f('ix_ingested_records_status'), 'ingested_records', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema - drop ingestion tables."""
    op.drop_index(op.f('ix_ingested_records_status'), table_name='ingested_records')
    op.drop_index(op.f('ix_ingested_records_source_id'), table_name='ingested_records')
    op.drop_index(op.f('ix_ingested_records_id'), table_name='ingested_records')
    op.drop_table('ingested_records')
    
    op.drop_index(op.f('ix_data_sources_name'), table_name='data_sources')
    op.drop_index(op.f('ix_data_sources_id'), table_name='data_sources')
    op.drop_table('data_sources')
