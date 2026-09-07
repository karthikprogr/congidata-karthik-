"""Initial schema for Gemini Architecture Redesign

Revision ID: 001
Revises: 
Create Date: 2024-01-15

Creates tables for Gemini architecture:
- users: User accounts with tier and storage quota
- datasets: User-uploaded datasets with metadata
- api_usage: API usage tracking for cost monitoring
- admin_config: Admin configuration with encrypted API keys

Requirements: 16.1, 16.2, 16.3, 16.5, 16.6, 16.7, 16.8, 16.9
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create all tables with indexes and foreign key constraints
    """
    # Determine if we're using PostgreSQL or SQLite
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'
    
    # JSON type: use JSONB for PostgreSQL, JSON for others
    json_type = postgresql.JSONB if is_postgresql else sa.JSON
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False, server_default='free'),
        sa.Column('storage_quota_mb', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        # Legacy fields for backward compatibility
        sa.Column('role', sa.String(length=50), server_default='user'),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('totp_secret', sa.String(length=64), nullable=True),
        sa.Column('totp_enabled', sa.Boolean(), server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('schema_json', json_type, nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('file_size_mb', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_datasets_id', 'datasets', ['id'], unique=False)
    op.create_index('ix_datasets_user_id', 'datasets', ['user_id'], unique=False)
    op.create_index('ix_datasets_uploaded_at', 'datasets', ['uploaded_at'], unique=False)
    
    # Create api_usage table
    op.create_table(
        'api_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('operation', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost', sa.DECIMAL(10, 6), nullable=False, server_default='0'),
        sa.Column('response_cached', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_usage_id', 'api_usage', ['id'], unique=False)
    op.create_index('ix_api_usage_user_id', 'api_usage', ['user_id'], unique=False)
    op.create_index('ix_api_usage_timestamp', 'api_usage', ['timestamp'], unique=False)
    
    # Create composite index for daily usage queries (PostgreSQL only)
    if is_postgresql:
        op.execute("""
            CREATE INDEX ix_api_usage_user_date 
            ON api_usage(user_id, DATE(timestamp))
        """)
    
    # Create admin_config table
    op.create_table(
        'admin_config',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('encrypted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )


def downgrade() -> None:
    """
    Drop all tables created in upgrade
    """
    # Drop in reverse order to respect foreign key constraints
    op.drop_table('admin_config')
    op.drop_table('api_usage')
    op.drop_table('datasets')
    op.drop_table('users')
