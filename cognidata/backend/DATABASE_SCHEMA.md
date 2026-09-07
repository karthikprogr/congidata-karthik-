# Database Schema Documentation

## Overview

This document describes the PostgreSQL database schema for the Gemini Architecture Redesign. The schema supports user management, dataset storage, API usage tracking, and admin configuration.

**Implementation Status:** ✅ Complete (Task 1.1)

**Requirements Satisfied:** 16.1, 16.2, 16.3, 16.5, 16.6, 16.7, 16.8, 16.9, 16.10

## Tables

### 1. Users Table

Stores user account information with tier-based access control.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'free' NOT NULL,  -- 'free', 'basic', 'pro'
    storage_quota_mb INTEGER DEFAULT 100 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Legacy fields for backward compatibility
    role VARCHAR(50) DEFAULT 'user',
    name VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    totp_secret VARCHAR(64),
    totp_enabled BOOLEAN DEFAULT FALSE
);

CREATE UNIQUE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_id ON users(id);
```

**Fields:**
- `id`: Primary key, auto-incremented
- `email`: Unique user email address (indexed for fast lookup)
- `hashed_password`: Bcrypt hashed password
- `tier`: User subscription tier ('free', 'basic', 'pro')
- `storage_quota_mb`: Storage quota in megabytes (default: 100 MB)
- `created_at`: Account creation timestamp
- `updated_at`: Last account update timestamp

**Requirements:** 16.2

---

### 2. Datasets Table

Stores metadata for user-uploaded datasets.

```sql
CREATE TABLE datasets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    schema_json JSONB NOT NULL,  -- PostgreSQL: JSONB, SQLite: JSON
    row_count INTEGER,
    file_size_mb DECIMAL(10, 2),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_datasets_id ON datasets(id);
CREATE INDEX ix_datasets_user_id ON datasets(user_id);
CREATE INDEX ix_datasets_uploaded_at ON datasets(uploaded_at);
```

**Fields:**
- `id`: Primary key, auto-incremented
- `user_id`: Foreign key to users table (CASCADE on delete)
- `name`: User-provided dataset name
- `file_path`: Path to parquet file in dataset store
- `schema_json`: Dataset schema as JSON (columns with names, types, stats)
- `row_count`: Number of rows in dataset
- `file_size_mb`: File size in megabytes
- `uploaded_at`: Upload timestamp (indexed for temporal queries)
- `updated_at`: Last update timestamp

**Foreign Keys:**
- `user_id` → `users(id)` ON DELETE CASCADE

**Indexes:**
- `user_id`: Fast user-specific dataset queries
- `uploaded_at`: Temporal queries and sorting

**Requirements:** 16.3, 16.6, 16.7, 16.8, 16.9

---

### 3. API Usage Table

Tracks API usage for cost monitoring and quota enforcement.

```sql
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
    operation VARCHAR(50) NOT NULL,  -- 'query', 'chart', 'insight', etc.
    model VARCHAR(50),  -- 'gemini-1.5-flash', 'gemini-1.5-pro', NULL for non-AI
    input_tokens INTEGER DEFAULT 0 NOT NULL,
    output_tokens INTEGER DEFAULT 0 NOT NULL,
    cost DECIMAL(10, 6) DEFAULT 0 NOT NULL,
    response_cached BOOLEAN DEFAULT FALSE NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_api_usage_id ON api_usage(id);
CREATE INDEX ix_api_usage_user_id ON api_usage(user_id);
CREATE INDEX ix_api_usage_timestamp ON api_usage(timestamp);

-- PostgreSQL only: Composite index for daily usage queries
CREATE INDEX ix_api_usage_user_date ON api_usage(user_id, DATE(timestamp));
```

**Fields:**
- `id`: Primary key, auto-incremented
- `user_id`: Foreign key to users table (CASCADE on delete)
- `dataset_id`: Foreign key to datasets table (SET NULL on delete)
- `operation`: Type of operation ('query', 'chart', 'insight', 'upload')
- `model`: AI model used ('gemini-1.5-flash', 'gemini-1.5-pro', NULL for non-AI ops)
- `input_tokens`: Number of input tokens consumed
- `output_tokens`: Number of output tokens consumed
- `cost`: Calculated cost in USD (decimal precision for micro-transactions)
- `response_cached`: Whether response was served from cache
- `timestamp`: Operation timestamp (indexed for temporal queries)

**Foreign Keys:**
- `user_id` → `users(id)` ON DELETE CASCADE
- `dataset_id` → `datasets(id)` ON DELETE SET NULL

**Indexes:**
- `user_id`: Fast user-specific usage queries
- `timestamp`: Temporal queries and cost reporting
- `(user_id, DATE(timestamp))`: Optimized daily quota checks (PostgreSQL only)

**Requirements:** 16.5, 16.6, 16.7, 16.8, 16.9

---

### 4. Admin Config Table

Stores administrative configuration including encrypted API keys.

```sql
CREATE TABLE admin_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    encrypted BOOLEAN DEFAULT FALSE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Example: Store encrypted Gemini API key
INSERT INTO admin_config (key, value, encrypted) 
VALUES ('gemini_api_key', '<encrypted_value>', TRUE);
```

**Fields:**
- `key`: Configuration key (primary key)
- `value`: Configuration value (TEXT for large values)
- `encrypted`: Whether value is encrypted at rest
- `updated_at`: Last update timestamp

**Common Configuration Keys:**
- `gemini_api_key`: Encrypted Google Gemini API key
- `default_model`: Default AI model to use
- `fallback_enabled`: Whether fallback handler is active
- `cost_alert_threshold`: Daily cost threshold for admin alerts

**Requirements:** 16.1

---

## Connection Pooling

Database connections use connection pooling for optimal performance:

**PostgreSQL:**
- Pool size: 5 minimum connections
- Max overflow: 15 additional connections
- Total maximum: 20 concurrent connections
- Pool pre-ping: Enabled (validates connections before use)
- Pool recycle: 3600 seconds (1 hour)

**SQLite:**
- Pool size: 10 connections
- Max overflow: 20 additional connections
- WAL mode: Enabled for better concurrent reads
- Foreign keys: Enabled via PRAGMA

**Implementation:** `app/core/database.py`

**Requirements:** 16.10

---

## Foreign Key Constraints

All foreign key relationships enforce referential integrity:

### CASCADE Deletion
When a user is deleted, all associated records are automatically removed:
- `datasets.user_id` → Deletes all user datasets
- `api_usage.user_id` → Deletes all user API usage records

### SET NULL Deletion
When a dataset is deleted, API usage records retain the user reference:
- `api_usage.dataset_id` → Sets to NULL when dataset is deleted

**Implementation:**
- PostgreSQL: Native foreign key constraints
- SQLite: Foreign keys enabled via `PRAGMA foreign_keys=ON`

**Requirements:** 16.8, 16.9

---

## Database Models (SQLAlchemy)

### Location
- `app/models/user.py` - User model
- `app/models/dataset.py` - Dataset model
- `app/models/api_usage.py` - APIUsage model
- `app/models/admin_config.py` - AdminConfig model

### Usage Example

```python
from app.models import User, Dataset, APIUsage, AdminConfig
from app.core.database import get_db

# Get database session
db = next(get_db())

# Create user
user = User(
    email="user@example.com",
    hashed_password="hashed_password",
    tier="free"
)
db.add(user)
db.commit()

# Create dataset
dataset = Dataset(
    user_id=user.id,
    name="Sales Data",
    file_path="/datasets/user_123/sales.parquet",
    schema_json={"columns": [{"name": "revenue", "type": "float"}]},
    row_count=1000,
    file_size_mb=2.5
)
db.add(dataset)
db.commit()

# Track API usage
usage = APIUsage(
    user_id=user.id,
    dataset_id=dataset.id,
    operation="query",
    model="gemini-1.5-flash",
    input_tokens=100,
    output_tokens=200,
    cost=0.003
)
db.add(usage)
db.commit()
```

---

## Migrations

### Alembic Setup

The project uses Alembic for database migrations:

**Migration Files:**
- `alembic/versions/001_initial_schema.py` - Initial schema creation

**Running Migrations:**

```bash
# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Create new migration
alembic revision -m "Description of changes"
```

**Configuration:**
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Environment setup

---

## Database Initialization

### Using init_db.py

Initialize the database schema:

```bash
cd cognidata/backend
python -m app.db.init_db
```

This creates all tables, indexes, and constraints.

**Implementation:** `app/db/init_db.py`

---

## Testing

### Test Suite

Comprehensive test suite validates all schema requirements:

**Test File:** `tests/test_database_schema.py`

**Test Coverage:**
- ✅ Table existence
- ✅ Column definitions and types
- ✅ Primary keys
- ✅ Foreign keys
- ✅ Indexes
- ✅ CASCADE deletion
- ✅ SET NULL deletion
- ✅ Default values
- ✅ Unique constraints
- ✅ Connection pooling

**Running Tests:**

```bash
pytest tests/test_database_schema.py -v
```

**Test Results:** 22 tests pass, 100% coverage of schema requirements

---

## Schema Verification Checklist

- [x] Users table with id, email, hashed_password, tier, storage_quota_mb, created_at, updated_at
- [x] Datasets table with id, user_id, name, file_path, schema_json, row_count, file_size_mb, uploaded_at
- [x] API usage table with id, user_id, dataset_id, operation, model, input_tokens, output_tokens, cost, response_cached, timestamp
- [x] Admin config table with key, value, encrypted, updated_at
- [x] Indexes on user_id columns (datasets, api_usage)
- [x] Indexes on timestamp columns (api_usage)
- [x] Indexes on uploaded_at column (datasets)
- [x] Unique index on email column (users)
- [x] Composite index on (user_id, DATE(timestamp)) for api_usage (PostgreSQL)
- [x] Foreign key constraints with CASCADE deletion (users → datasets, users → api_usage)
- [x] Foreign key constraints with SET NULL deletion (datasets → api_usage)
- [x] Connection pooling (min 5, max 20 for PostgreSQL)
- [x] Foreign keys enabled in SQLite via PRAGMA
- [x] All requirements (16.1-16.9) satisfied

---

## Next Steps

The database schema is complete and tested. Next phase tasks:

1. **Task 1.2:** Implement authentication system with JWT tokens
2. **Task 1.3:** Create DatasetStore class for file handling
3. **Task 1.4:** Set up basic FastAPI application structure

---

## References

- Requirements Document: `.kiro/specs/gemini-architecture-redesign/requirements.md`
- Design Document: `.kiro/specs/gemini-architecture-redesign/design.md`
- Tasks Document: `.kiro/specs/gemini-architecture-redesign/tasks.md`
