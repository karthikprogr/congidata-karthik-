"""
RAG Metadata Store Service

Manages persistent metadata about indexed datasets for RAG (Retrieval-Augmented Generation).
Each user has their own metadata file tracking which datasets are indexed, chunk counts,
indexing timestamps, and Qdrant vector ID ranges.

Metadata Structure:
{
  "datasets": {
    "dataset_name": {
      "name": "dataset_name",
      "indexed_at": "2024-01-15T10:30:00Z",
      "chunk_count": 150,
      "source_path": "dataset_name.parquet",
      "qdrant_id_range": [0, 149]
    }
  },
  "next_id": 150
}
"""

import json
import pathlib
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any


class RAGMetadataStore:
    """
    Manages RAG indexing metadata with disk persistence and in-memory caching.
    
    Features:
    - Atomic file writes (write to temp, then rename) for data safety
    - In-memory caching with cache invalidation on writes
    - Thread-safe file operations with locking
    - Graceful handling of corrupted JSON files
    - Cross-platform path handling via pathlib
    """
    
    def __init__(self, base_dir: pathlib.Path):
        """
        Initialize the metadata store.
        
        Args:
            base_dir: Base directory for dataset storage (e.g., .dataset_store)
        """
        self._base_dir = pathlib.Path(base_dir)
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested operations
        
        # Ensure base directory exists
        self._base_dir.mkdir(exist_ok=True)
    
    def _get_user_dir(self, user_id: str) -> pathlib.Path:
        """
        Get the directory path for a user's data.
        
        Args:
            user_id: User identifier (e.g., email)
            
        Returns:
            Path object for user's directory
        """
        # Sanitize user_id for filesystem (same pattern as data_store.py)
        sanitized = user_id.replace("@", "_at_").replace(".", "_")
        user_dir = self._base_dir / sanitized
        user_dir.mkdir(exist_ok=True)
        return user_dir
    
    def _get_metadata_path(self, user_id: str) -> pathlib.Path:
        """
        Get the metadata file path for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Path object for metadata JSON file
        """
        return self._get_user_dir(user_id) / "_rag_metadata.json"
    
    def _read_metadata_file(self, user_id: str) -> Dict[str, Any]:
        """
        Read metadata from disk with error recovery.
        
        Args:
            user_id: User identifier
            
        Returns:
            Parsed metadata dictionary or empty structure on error
        """
        metadata_path = self._get_metadata_path(user_id)
        
        if not metadata_path.exists():
            # Return empty structure for new users
            return {
                "datasets": {},
                "next_id": 0
            }
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("Metadata root must be a dictionary")
            
            if "datasets" not in data:
                data["datasets"] = {}
            
            if "next_id" not in data:
                data["next_id"] = 0
            
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return empty structure
            print(f"Warning: Corrupted metadata file for user {user_id}: {e}")
            print(f"Initializing with empty metadata structure")
            return {
                "datasets": {},
                "next_id": 0
            }
        except Exception as e:
            # Log unexpected errors
            print(f"Error reading metadata for user {user_id}: {e}")
            return {
                "datasets": {},
                "next_id": 0
            }
    
    def _write_metadata_file(self, user_id: str, metadata: Dict[str, Any]) -> None:
        """
        Write metadata to disk atomically.
        
        Uses atomic file write pattern: write to temp file, then rename.
        This ensures the file is never left in a partially written state.
        
        Args:
            user_id: User identifier
            metadata: Metadata dictionary to write
        """
        metadata_path = self._get_metadata_path(user_id)
        temp_path = metadata_path.with_suffix('.json.tmp')
        
        try:
            # Write to temporary file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Atomic rename (overwrites destination on most platforms)
            temp_path.replace(metadata_path)
            
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise RuntimeError(f"Failed to write metadata for user {user_id}: {e}")
    
    def save(self, user_id: str, dataset_name: str, 
             chunk_count: int, id_range: Tuple[int, int]) -> None:
        """
        Record that a dataset has been indexed.
        
        Args:
            user_id: User identifier
            dataset_name: Name of the indexed dataset
            chunk_count: Number of chunks/vectors indexed
            id_range: Tuple of (start_id, end_id) for Qdrant point IDs
        """
        with self._lock:
            # Load existing metadata
            metadata = self._read_metadata_file(user_id)
            
            # Determine source path (check for .parquet or .csv)
            user_dir = self._get_user_dir(user_id)
            source_path = None
            for ext in ['.parquet', '.csv']:
                candidate = user_dir / f"{dataset_name}{ext}"
                if candidate.exists():
                    source_path = f"{dataset_name}{ext}"
                    break
            
            if source_path is None:
                # Default to .parquet if file doesn't exist yet
                source_path = f"{dataset_name}.parquet"
            
            # Create/update dataset entry
            metadata["datasets"][dataset_name] = {
                "name": dataset_name,
                "indexed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "chunk_count": chunk_count,
                "source_path": source_path,
                "qdrant_id_range": list(id_range)  # Convert tuple to list for JSON
            }
            
            # Update next_id counter if needed
            if id_range[1] >= metadata["next_id"]:
                metadata["next_id"] = id_range[1] + 1
            
            # Write to disk
            self._write_metadata_file(user_id, metadata)
            
            # Invalidate cache
            self._cache.pop(user_id, None)
    
    def load(self, user_id: str) -> Dict[str, Any]:
        """
        Load all metadata for a user from disk.
        
        Uses in-memory cache for performance.
        
        Args:
            user_id: User identifier
            
        Returns:
            Complete metadata dictionary with "datasets" and "next_id" keys
        """
        with self._lock:
            # Check cache first
            if user_id in self._cache:
                return self._cache[user_id].copy()
            
            # Load from disk
            metadata = self._read_metadata_file(user_id)
            
            # Cache it
            self._cache[user_id] = metadata.copy()
            
            return metadata.copy()
    
    def list_datasets(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get list of indexed datasets for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of dataset metadata dictionaries, each containing:
            - name: Dataset name
            - chunk_count: Number of indexed chunks
            - indexed_at: ISO 8601 timestamp
            - source_path: Original dataset file path
            - qdrant_id_range: [start_id, end_id] range
        """
        metadata = self.load(user_id)
        datasets = metadata.get("datasets", {})
        
        # Return list of dataset metadata
        return list(datasets.values())
    
    def delete(self, user_id: str, dataset_name: str) -> bool:
        """
        Remove a dataset from metadata.
        
        Args:
            user_id: User identifier
            dataset_name: Name of dataset to remove
            
        Returns:
            True if dataset was found and deleted, False if not found
        """
        with self._lock:
            # Load metadata
            metadata = self._read_metadata_file(user_id)
            datasets = metadata.get("datasets", {})
            
            # Check if dataset exists
            if dataset_name not in datasets:
                return False
            
            # Remove dataset entry
            del datasets[dataset_name]
            
            # Write updated metadata
            self._write_metadata_file(user_id, metadata)
            
            # Invalidate cache
            self._cache.pop(user_id, None)
            
            return True
    
    def get_next_id(self, user_id: str) -> int:
        """
        Get next available Qdrant point ID for user.
        
        This method returns the current next_id value but does NOT increment it.
        The increment happens in save() when a dataset is successfully indexed.
        
        Args:
            user_id: User identifier
            
        Returns:
            Next available integer ID for Qdrant points
        """
        metadata = self.load(user_id)
        return metadata.get("next_id", 0)
    
    def get_id_range(self, user_id: str, dataset_name: str) -> Optional[Tuple[int, int]]:
        """
        Get Qdrant ID range for a specific dataset.
        
        Used for targeted deletion of dataset vectors.
        
        Args:
            user_id: User identifier
            dataset_name: Name of dataset
            
        Returns:
            Tuple of (start_id, end_id) or None if dataset not found
        """
        metadata = self.load(user_id)
        datasets = metadata.get("datasets", {})
        
        if dataset_name not in datasets:
            return None
        
        id_range = datasets[dataset_name].get("qdrant_id_range")
        
        if id_range and len(id_range) == 2:
            return tuple(id_range)
        
        return None
    
    def dataset_exists(self, user_id: str, dataset_name: str) -> bool:
        """
        Check if a dataset is indexed.
        
        Args:
            user_id: User identifier
            dataset_name: Name of dataset
            
        Returns:
            True if dataset is indexed, False otherwise
        """
        metadata = self.load(user_id)
        datasets = metadata.get("datasets", {})
        return dataset_name in datasets
    
    def get_total_chunks(self, user_id: str) -> int:
        """
        Get total number of indexed chunks across all datasets for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Sum of chunk counts across all indexed datasets
        """
        datasets = self.list_datasets(user_id)
        return sum(d.get("chunk_count", 0) for d in datasets)
