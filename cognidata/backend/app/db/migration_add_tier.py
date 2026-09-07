"""
Database migration script to add tier and storage_quota_mb to users table.
Run this script once to update existing database schema.
"""
import sqlite3
from pathlib import Path

def migrate_database():
    """Add tier and storage_quota_mb columns to users table."""
    
    # Get database path from environment or use default
    db_path = Path("./cognidata.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "tier" not in columns:
            print("Adding 'tier' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN tier VARCHAR(20) DEFAULT 'free' NOT NULL")
            print("✓ Added 'tier' column")
        else:
            print("'tier' column already exists")
        
        if "storage_quota_mb" not in columns:
            print("Adding 'storage_quota_mb' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN storage_quota_mb INTEGER DEFAULT 100 NOT NULL")
            print("✓ Added 'storage_quota_mb' column")
        else:
            print("'storage_quota_mb' column already exists")
        
        if "created_at" not in columns:
            print("Adding 'created_at' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL")
            print("✓ Added 'created_at' column")
        else:
            print("'created_at' column already exists")
        
        if "updated_at" not in columns:
            print("Adding 'updated_at' column to users table...")
            # SQLite doesn't support CURRENT_TIMESTAMP in ALTER TABLE ADD COLUMN
            # So we add it without a default, then update existing rows
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME")
            cursor.execute("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
            print("✓ Added 'updated_at' column")
        else:
            print("'updated_at' column already exists")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()


if __name__ == "__main__":
    print("Starting database migration...")
    migrate_database()
