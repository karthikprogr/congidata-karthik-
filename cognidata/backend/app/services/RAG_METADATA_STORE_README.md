# RAG Metadata Store Service

## Overview

The RAG Metadata Store Service is a critical component of the RAG Dataset Management feature. It provides persistent, thread-safe storage for tracking which datasets are indexed for RAG queries, maintaining metadata about chunk counts, indexing timestamps, and Qdrant vector ID ranges.

## Features

### Core Functionality
- **Persistent Metadata Storage**: Stores dataset metadata in JSON format at `.dataset_store/{user_id}/_rag_metadata.json`
- **Atomic File Writes**: Uses write-to-temp-then-rename pattern to prevent file corruption
- **In-Memory Caching**: Caches loaded metadata for performance with proper cache invalidation
- **Thread-Safe Operations**: Uses reentrant locks to handle concurrent access
- **Graceful Error Recovery**: Handles corrupted JSON files and missing metadata gracefully

### API Methods

#### `save(user_id, dataset_name, chunk_count, id_range)`
Records that a dataset has been indexed. Updates metadata with:
- Dataset name
- ISO 8601 timestamp with Z suffix
- Chunk count
- Source file path (.parquet or .csv)
- Qdrant ID range (start_id, end_id)

#### `load(user_id)`
Loads complete metadata structure for a user from disk, using cache when available.

#### `list_datasets(user_id)`
Returns list of all indexed datasets for a user with their metadata.

#### `delete(user_id, dataset_name)`
Removes a dataset from metadata. Returns True if found and deleted, False otherwise.

#### `get_next_id(user_id)`
Returns the next available Qdrant point ID for assigning to new vectors.

#### `get_id_range(user_id, dataset_name)`
Returns the (start_id, end_id) tuple for a specific dataset, used for targeted deletion.

#### `dataset_exists(user_id, dataset_name)`
Checks if a dataset is currently indexed.

#### `get_total_chunks(user_id)`
Returns sum of chunk counts across all indexed datasets for a user.

## Metadata File Structure

```json
{
  "datasets": {
    "dataset_name": {
      "name": "dataset_name",
      "indexed_at": "2024-01-15T10:30:00.123456Z",
      "chunk_count": 150,
      "source_path": "dataset_name.parquet",
      "qdrant_id_range": [0, 149]
    }
  },
  "next_id": 150
}
```

## Usage Example

```python
from pathlib import Path
from app.services.rag_metadata_store import RAGMetadataStore

# Initialize store
base_dir = Path(".dataset_store")
store = RAGMetadataStore(base_dir)

# Save dataset metadata
store.save(
    user_id="user@example.com",
    dataset_name="sales_data",
    chunk_count=200,
    id_range=(0, 199)
)

# List all indexed datasets for user
datasets = store.list_datasets("user@example.com")
for ds in datasets:
    print(f"{ds['name']}: {ds['chunk_count']} chunks")

# Get ID range for deletion
id_range = store.get_id_range("user@example.com", "sales_data")
# Use id_range to delete vectors from Qdrant

# Remove from metadata
store.delete("user@example.com", "sales_data")
```

## Thread Safety

The service uses `threading.RLock()` (reentrant lock) to ensure thread-safe operations:
- Multiple readers can access cached data simultaneously
- Writers acquire exclusive lock for file operations
- Nested operations within the same thread are supported

## Error Handling

### Corrupted JSON Recovery
If a metadata file is corrupted (invalid JSON syntax), the service:
1. Logs a warning with the error details
2. Returns an empty metadata structure
3. Allows the system to continue operating

### Missing Fields
If loaded metadata is missing required fields (`datasets` or `next_id`), they are automatically added with default values.

### File Write Failures
If file write operations fail:
1. Temporary files are cleaned up
2. A `RuntimeError` is raised with details
3. The original metadata file remains unchanged (atomic write protection)

## Testing

### Unit Tests (26 tests)
Located at: `app/services/test_rag_metadata_store.py`

Test coverage includes:
- Basic save/load/delete operations
- ID range management
- User isolation
- Re-indexing behavior
- Disk persistence
- Atomic writes
- Error recovery from corrupted JSON
- Cache invalidation
- Thread-safety with concurrent operations
- Timestamp formatting

Run tests:
```bash
cd cognidata/backend/app/services
python -m pytest test_rag_metadata_store.py -v
```

### Integration Tests (3 tests)
Located at: `tests/test_rag_metadata_integration.py`

Tests the service with actual backend paths and environment:
- Metadata storage with backend path structure
- User isolation in real environment
- Persistence across store instance restarts

Run tests:
```bash
cd cognidata/backend
python -m pytest tests/test_rag_metadata_integration.py -v
```

## Requirements Validated

This implementation satisfies the following requirements:

- **Requirement 2.1**: Persists metadata in `.dataset_store/{user_id}/` directory
- **Requirement 2.2**: Stores dataset name, timestamp, chunk count, and identifiers in JSON
- **Requirement 2.3**: Loads existing metadata on startup (via lazy loading)
- **Requirement 2.4**: Removes metadata when datasets are deleted
- **Requirement 2.5**: Maintains one `_rag_metadata.json` file per user
- **Requirement 8.6**: Organizes metadata by user_id for user isolation

## Design Patterns

### Atomic File Writes
```python
# Write to temporary file
temp_path = metadata_path.with_suffix('.json.tmp')
with open(temp_path, 'w') as f:
    json.dump(metadata, f)

# Atomic rename (overwrites destination)
temp_path.replace(metadata_path)
```

### Cache Invalidation
```python
# Invalidate cache on write operations
self._cache.pop(user_id, None)
```

### Graceful Error Recovery
```python
try:
    data = json.load(f)
    # Validate structure...
    return data
except (json.JSONDecodeError, ValueError) as e:
    print(f"Warning: Corrupted metadata: {e}")
    return {"datasets": {}, "next_id": 0}
```

## Future Enhancements

Potential improvements for future versions:
1. **Compression**: Compress metadata files for large numbers of datasets
2. **Versioning**: Track metadata schema version for migrations
3. **Backup**: Automatic backup of metadata before writes
4. **Metrics**: Track metadata file sizes and operation latencies
5. **Validation**: JSON schema validation for loaded metadata

## Dependencies

- **Python Standard Library**:
  - `json`: JSON serialization
  - `pathlib`: Cross-platform path handling
  - `threading`: Thread-safe operations
  - `datetime`: Timestamp generation

No external dependencies required.
