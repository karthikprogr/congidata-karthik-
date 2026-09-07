"""
Database initialization script for Gemini Architecture Redesign
Creates all tables with proper indexes and foreign key constraints
"""
from sqlalchemy import create_engine, text, Index
from app.core.database import Base, engine
from app.models import User, Dataset, APIUsage, AdminConfig


def init_db():
    """
    Initialize database by creating all tables with indexes and constraints.
    
    Tables created:
    - users: User accounts with tier and storage quota
    - datasets: User-uploaded datasets with metadata
    - api_usage: API usage tracking for cost monitoring
    - admin_config: Admin configuration including encrypted API keys
    
    Indexes created:
    - users.email (unique)
    - users.id (primary key, automatic)
    - datasets.user_id (foreign key)
    - datasets.uploaded_at (for temporal queries)
    - api_usage.user_id (foreign key)
    - api_usage.timestamp (for temporal queries)
    - Composite index on api_usage(user_id, DATE(timestamp)) for daily quota checks
    
    Foreign key constraints:
    - datasets.user_id -> users.id (CASCADE on delete)
    - api_usage.user_id -> users.id (CASCADE on delete)
    - api_usage.dataset_id -> datasets.id (SET NULL on delete)
    """
    print("Creating database tables...")
    
    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    
    # Create additional indexes for performance optimization
    # Composite index for daily usage queries (Requirement 12.2)
    with engine.connect() as conn:
        # Check database type to use appropriate syntax
        db_type = engine.dialect.name
        
        if db_type == "postgresql":
            # PostgreSQL-specific composite index on user_id and date
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_api_usage_user_date 
                    ON api_usage(user_id, DATE(timestamp))
                """))
                conn.commit()
                print("Created composite index: idx_api_usage_user_date")
            except Exception as e:
                print(f"Note: Could not create composite index (may already exist): {e}")
        
        elif db_type == "sqlite":
            # SQLite doesn't support DATE() in indexes, skip composite index
            print("Skipped composite index for SQLite (not supported)")
    
    print("Database initialization complete!")
    print("\nTables created:")
    print("  - users")
    print("  - datasets")
    print("  - api_usage")
    print("  - admin_config")
    print("\nIndexes created:")
    print("  - users(email) - unique")
    print("  - users(id) - primary key")
    print("  - datasets(user_id) - foreign key")
    print("  - datasets(uploaded_at) - temporal queries")
    print("  - api_usage(user_id) - foreign key")
    print("  - api_usage(timestamp) - temporal queries")
    if db_type == "postgresql":
        print("  - api_usage(user_id, DATE(timestamp)) - daily quota checks")


if __name__ == "__main__":
    init_db()
