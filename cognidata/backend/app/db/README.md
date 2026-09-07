# Database Module - Gemini Architecture Redesign

This module contains the database schema and initialization scripts for the Cognidata Gemini Architecture Redesign.

## Database Schema

### Tables

#### 1. users
Stores user account information with tier-based storage quotas.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| email | String(255) | Unique email address (indexed) |
| hashed_password | String(255) | Bcrypt hashed password |
| tier | String(20) | Subscription tier: 'free', 'basic', 'pro' |
| storage_quota_mb | Integer | Storage quota in MB (default: 100) |
| created_at | DateTime | Account creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Requirements**: 16.2

#### 2. datasets
Stores metadata for user-uploaded datasets.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users.id (CASCADE delete) |
| name | String(255) | Dataset name |
| file_path | String(500) | Path to dataset file in storage |
| schema_json | JSON/JSONB | Column definitions and statistics |
| row_count | Integer | Number of rows in dataset |
| file_size_mb | Decimal(10,2) | File size in MB |
| uploaded_at | DateTime | Upload timestamp (indexed) |
| updated_at | DateTime | Last update timestamp |

**Requirements**: 16.3

**Indexes**: user_id, uploaded_at

#### 3. api_usage
Tracks API usage for cost monitoring and quota enforcement.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users.id (CASCADE delete) |
| dataset_id | Integer | Foreign key to datasets.id (SET NULL) |
| operation | String(50) | Operation type: 'query', 'chart', 'insight' |
| model | String(50) | AI model: 'gemini-1.5-flash', 'gemini-1.5-pro' |
| input_tokens | Integer | Number of input tokens |
| output_tokens | Integer | Number of output tokens |
| cost | Decimal(10,6) | Calculated cost in USD |
| response_cached | Boolean | Whether response was from cache |
| timestamp | DateTime | Request timestamp (indexed) |

**Requirements**: 16.5

**Indexes**: user_id, timestamp, (user_id, DATE(timestamp)) composite

#### 4. admin_config
Stores admin configuration including encrypted API keys.

| Column | Type | Description |
|--------|------|-------------|
| key | String(100) | Primary key - config key name |
| value | Text | Configuration value |
| encrypted | Boolean | Whether value is encrypted |
| updated_at | DateTime | Last update timestamp |

**Requirements**: 16.5

## Foreign Key Constraints

- `datasets.user_id` → `users.id` (CASCADE on delete)
- `api_usage.user_id` → `users.id` (CASCADE on delete)
- `api_usage.dataset_id` → `datasets.id` (SET NULL on delete)

**Requirement**: 16.8, 16.9

## Connection Pooling

- **PostgreSQL**: pool_size=5 (minimum), max_overflow=15 (total max: 20)
- **SQLite**: Standard pooling configuration

**Requirement**: 16.10

## Usage

### Initialize Database (Direct)

```python
from app.db.init_db import init_db

init_db()
```

### Using Alembic Migrations

```bash
# Run migrations
cd cognidata/backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Downgrade one version
alembic downgrade -1
```

### Get Database Session

```python
from app.core.database import get_db

# In FastAPI route
@app.get("/api/endpoint")
async def endpoint(db: Session = Depends(get_db)):
    # Use db session
    pass
```

## Design References

See `design.md` Section: Database Schema for complete specifications.

## Testing

Run database tests:
```bash
pytest tests/unit/test_database.py
```
