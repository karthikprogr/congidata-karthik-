"""
Unit tests for RAG Metadata Store Service

Tests cover:
- Basic save/load/delete operations
- Atomic file writes and error recovery
- Cache invalidation
- Concurrent access handling
- JSON corruption recovery
- ID range management
"""

import json
import pytest
import tempfile
import pathlib
import threading
from datetime import datetime
from typing import List

from rag_metadata_store import RAGMetadataStore


@pytest.fixture
def temp_store_dir():
    """Create a temporary directory for test metadata storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)


@pytest.fixture
def metadata_store(temp_store_dir):
    """Create a RAGMetadataStore instance for testing."""
    return RAGMetadataStore(temp_store_dir)


class TestBasicOperations:
    """Test basic save, load, list, delete operations."""
    
    def test_save_and_load_single_dataset(self, metadata_store):
        """Test saving and loading a single dataset."""
        user_id = "test@example.com"
        dataset_name = "dataset_1"
        chunk_count = 100
        id_range = (0, 99)
        
        # Save dataset
        metadata_store.save(user_id, dataset_name, chunk_count, id_range)
        
        # Load and verify
        metadata = metadata_store.load(user_id)
        assert "datasets" in metadata
        assert dataset_name in metadata["datasets"]
        
        dataset_info = metadata["datasets"][dataset_name]
        assert dataset_info["name"] == dataset_name
        assert dataset_info["chunk_count"] == chunk_count
        assert dataset_info["qdrant_id_range"] == [0, 99]
        assert "indexed_at" in dataset_info
        assert "source_path" in dataset_info
    
    def test_save_multiple_datasets(self, metadata_store):
        """Test saving multiple datasets for the same user."""
        user_id = "test@example.com"
        
        # Save first dataset
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        
        # Save second dataset
        metadata_store.save(user_id, "dataset_2", 50, (100, 149))
        
        # Verify both exist
        datasets = metadata_store.list_datasets(user_id)
        assert len(datasets) == 2
        
        dataset_names = [d["name"] for d in datasets]
        assert "dataset_1" in dataset_names
        assert "dataset_2" in dataset_names
    
    def test_list_datasets_empty(self, metadata_store):
        """Test listing datasets when none are indexed."""
        user_id = "test@example.com"
        datasets = metadata_store.list_datasets(user_id)
        assert datasets == []
    
    def test_delete_dataset(self, metadata_store):
        """Test deleting a dataset."""
        user_id = "test@example.com"
        
        # Save two datasets
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        metadata_store.save(user_id, "dataset_2", 50, (100, 149))
        
        # Delete first dataset
        result = metadata_store.delete(user_id, "dataset_1")
        assert result is True
        
        # Verify only second dataset remains
        datasets = metadata_store.list_datasets(user_id)
        assert len(datasets) == 1
        assert datasets[0]["name"] == "dataset_2"
    
    def test_delete_nonexistent_dataset(self, metadata_store):
        """Test deleting a dataset that doesn't exist."""
        user_id = "test@example.com"
        result = metadata_store.delete(user_id, "nonexistent")
        assert result is False
    
    def test_dataset_exists(self, metadata_store):
        """Test checking if a dataset exists."""
        user_id = "test@example.com"
        
        # Initially doesn't exist
        assert metadata_store.dataset_exists(user_id, "dataset_1") is False
        
        # Save dataset
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        
        # Now exists
        assert metadata_store.dataset_exists(user_id, "dataset_1") is True
        
        # Delete dataset
        metadata_store.delete(user_id, "dataset_1")
        
        # No longer exists
        assert metadata_store.dataset_exists(user_id, "dataset_1") is False


class TestIDManagement:
    """Test ID range allocation and retrieval."""
    
    def test_get_next_id_initial(self, metadata_store):
        """Test getting next ID for new user."""
        user_id = "test@example.com"
        next_id = metadata_store.get_next_id(user_id)
        assert next_id == 0
    
    def test_get_next_id_after_save(self, metadata_store):
        """Test that next_id is updated after saving."""
        user_id = "test@example.com"
        
        # Save first dataset (IDs 0-99)
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        next_id = metadata_store.get_next_id(user_id)
        assert next_id == 100
        
        # Save second dataset (IDs 100-149)
        metadata_store.save(user_id, "dataset_2", 50, (100, 149))
        next_id = metadata_store.get_next_id(user_id)
        assert next_id == 150
    
    def test_get_id_range(self, metadata_store):
        """Test retrieving ID range for a dataset."""
        user_id = "test@example.com"
        
        # Save dataset
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        
        # Get ID range
        id_range = metadata_store.get_id_range(user_id, "dataset_1")
        assert id_range == (0, 99)
    
    def test_get_id_range_nonexistent(self, metadata_store):
        """Test getting ID range for nonexistent dataset."""
        user_id = "test@example.com"
        id_range = metadata_store.get_id_range(user_id, "nonexistent")
        assert id_range is None
    
    def test_get_total_chunks(self, metadata_store):
        """Test calculating total chunks across all datasets."""
        user_id = "test@example.com"
        
        # Initially zero
        assert metadata_store.get_total_chunks(user_id) == 0
        
        # Add datasets
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        assert metadata_store.get_total_chunks(user_id) == 100
        
        metadata_store.save(user_id, "dataset_2", 50, (100, 149))
        assert metadata_store.get_total_chunks(user_id) == 150
        
        # Delete one dataset
        metadata_store.delete(user_id, "dataset_1")
        assert metadata_store.get_total_chunks(user_id) == 50


class TestUserIsolation:
    """Test that users' metadata is isolated."""
    
    def test_different_users_separate_metadata(self, metadata_store):
        """Test that different users have separate metadata."""
        user1 = "user1@example.com"
        user2 = "user2@example.com"
        
        # Save dataset for user1
        metadata_store.save(user1, "dataset_1", 100, (0, 99))
        
        # Save dataset for user2
        metadata_store.save(user2, "dataset_1", 50, (0, 49))
        
        # Verify isolation
        user1_datasets = metadata_store.list_datasets(user1)
        user2_datasets = metadata_store.list_datasets(user2)
        
        assert len(user1_datasets) == 1
        assert len(user2_datasets) == 1
        assert user1_datasets[0]["chunk_count"] == 100
        assert user2_datasets[0]["chunk_count"] == 50
    
    def test_user_id_sanitization(self, metadata_store, temp_store_dir):
        """Test that user IDs are properly sanitized for filesystem."""
        user_id = "test@example.com"
        
        # Save dataset
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        
        # Check that directory uses sanitized name
        expected_dir = temp_store_dir / "test_at_example_com"
        assert expected_dir.exists()
        
        metadata_file = expected_dir / "_rag_metadata.json"
        assert metadata_file.exists()


class TestReindexing:
    """Test re-indexing (updating) existing datasets."""
    
    def test_reindex_updates_metadata(self, metadata_store):
        """Test that re-indexing updates timestamp and chunk count."""
        user_id = "test@example.com"
        dataset_name = "dataset_1"
        
        # Initial index
        metadata_store.save(user_id, dataset_name, 100, (0, 99))
        first_metadata = metadata_store.load(user_id)
        first_time = first_metadata["datasets"][dataset_name]["indexed_at"]
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        # Re-index with different chunk count
        metadata_store.save(user_id, dataset_name, 150, (0, 149))
        second_metadata = metadata_store.load(user_id)
        
        # Verify updates
        dataset_info = second_metadata["datasets"][dataset_name]
        assert dataset_info["chunk_count"] == 150
        assert dataset_info["qdrant_id_range"] == [0, 149]
        assert dataset_info["indexed_at"] != first_time  # Timestamp updated
    
    def test_reindex_preserves_other_datasets(self, metadata_store):
        """Test that re-indexing one dataset doesn't affect others."""
        user_id = "test@example.com"
        
        # Save two datasets
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        metadata_store.save(user_id, "dataset_2", 50, (100, 149))
        
        # Re-index first dataset
        metadata_store.save(user_id, "dataset_1", 200, (0, 199))
        
        # Verify second dataset unchanged
        datasets = metadata_store.list_datasets(user_id)
        dataset_2 = next(d for d in datasets if d["name"] == "dataset_2")
        assert dataset_2["chunk_count"] == 50
        assert dataset_2["qdrant_id_range"] == [100, 149]


class TestPersistence:
    """Test disk persistence and atomic writes."""
    
    def test_metadata_persists_across_instances(self, temp_store_dir):
        """Test that metadata persists when creating new store instance."""
        user_id = "test@example.com"
        
        # Create first instance and save data
        store1 = RAGMetadataStore(temp_store_dir)
        store1.save(user_id, "dataset_1", 100, (0, 99))
        
        # Create second instance and verify data exists
        store2 = RAGMetadataStore(temp_store_dir)
        datasets = store2.list_datasets(user_id)
        
        assert len(datasets) == 1
        assert datasets[0]["name"] == "dataset_1"
        assert datasets[0]["chunk_count"] == 100
    
    def test_atomic_write_no_partial_files(self, metadata_store, temp_store_dir):
        """Test that atomic writes don't leave partial files."""
        user_id = "test@example.com"
        
        # Save dataset
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        
        # Check no .tmp files remain
        user_dir = temp_store_dir / "test_at_example_com"
        tmp_files = list(user_dir.glob("*.tmp"))
        assert len(tmp_files) == 0


class TestErrorHandling:
    """Test error handling and recovery."""
    
    def test_corrupted_json_recovery(self, temp_store_dir):
        """Test that corrupted JSON is handled gracefully."""
        user_id = "test@example.com"
        
        # Create metadata store
        store = RAGMetadataStore(temp_store_dir)
        
        # Manually write corrupted JSON
        user_dir = temp_store_dir / "test_at_example_com"
        user_dir.mkdir(exist_ok=True)
        metadata_file = user_dir / "_rag_metadata.json"
        metadata_file.write_text("{ corrupted json }", encoding="utf-8")
        
        # Should recover gracefully and return empty structure
        metadata = store.load(user_id)
        assert metadata["datasets"] == {}
        assert metadata["next_id"] == 0
    
    def test_invalid_metadata_structure_recovery(self, temp_store_dir):
        """Test recovery from invalid metadata structure."""
        user_id = "test@example.com"
        
        # Create metadata store
        store = RAGMetadataStore(temp_store_dir)
        
        # Manually write invalid structure (array instead of object)
        user_dir = temp_store_dir / "test_at_example_com"
        user_dir.mkdir(exist_ok=True)
        metadata_file = user_dir / "_rag_metadata.json"
        metadata_file.write_text("[1, 2, 3]", encoding="utf-8")
        
        # Should recover gracefully
        metadata = store.load(user_id)
        assert isinstance(metadata, dict)
        assert "datasets" in metadata
        assert "next_id" in metadata
    
    def test_missing_fields_recovery(self, temp_store_dir):
        """Test recovery when metadata is missing required fields."""
        user_id = "test@example.com"
        
        # Create metadata store
        store = RAGMetadataStore(temp_store_dir)
        
        # Manually write incomplete metadata
        user_dir = temp_store_dir / "test_at_example_com"
        user_dir.mkdir(exist_ok=True)
        metadata_file = user_dir / "_rag_metadata.json"
        metadata_file.write_text('{"some_field": "value"}', encoding="utf-8")
        
        # Should add missing fields
        metadata = store.load(user_id)
        assert "datasets" in metadata
        assert "next_id" in metadata


class TestCaching:
    """Test in-memory caching behavior."""
    
    def test_cache_populated_on_load(self, metadata_store):
        """Test that cache is populated after load."""
        user_id = "test@example.com"
        
        # Save dataset
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        
        # First load populates cache
        metadata1 = metadata_store.load(user_id)
        
        # Second load should use cache (same instance)
        metadata2 = metadata_store.load(user_id)
        
        assert metadata1 == metadata2
    
    def test_cache_invalidated_on_save(self, metadata_store):
        """Test that cache is invalidated when saving."""
        user_id = "test@example.com"
        
        # Load to populate cache
        metadata_store.load(user_id)
        
        # Save should invalidate cache
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        
        # Next load should reflect new data
        datasets = metadata_store.list_datasets(user_id)
        assert len(datasets) == 1
    
    def test_cache_invalidated_on_delete(self, metadata_store):
        """Test that cache is invalidated when deleting."""
        user_id = "test@example.com"
        
        # Save and load to populate cache
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        metadata_store.load(user_id)
        
        # Delete should invalidate cache
        metadata_store.delete(user_id, "dataset_1")
        
        # Next load should reflect deletion
        datasets = metadata_store.list_datasets(user_id)
        assert len(datasets) == 0


class TestConcurrency:
    """Test thread-safety of concurrent operations."""
    
    def test_concurrent_saves(self, metadata_store):
        """Test that concurrent saves don't corrupt data."""
        user_id = "test@example.com"
        num_threads = 10
        errors: List[Exception] = []
        
        def save_dataset(index: int):
            try:
                metadata_store.save(
                    user_id, 
                    f"dataset_{index}", 
                    100 * index, 
                    (index * 100, (index + 1) * 100 - 1)
                )
            except Exception as e:
                errors.append(e)
        
        # Create and start threads
        threads = [
            threading.Thread(target=save_dataset, args=(i,))
            for i in range(num_threads)
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Check no errors occurred
        assert len(errors) == 0
        
        # Verify all datasets were saved
        datasets = metadata_store.list_datasets(user_id)
        assert len(datasets) == num_threads
    
    def test_concurrent_read_write(self, metadata_store):
        """Test concurrent reads and writes."""
        user_id = "test@example.com"
        num_readers = 5
        num_writers = 5
        errors: List[Exception] = []
        
        def read_datasets():
            try:
                for _ in range(10):
                    metadata_store.list_datasets(user_id)
            except Exception as e:
                errors.append(e)
        
        def write_dataset(index: int):
            try:
                for i in range(10):
                    metadata_store.save(
                        user_id,
                        f"dataset_{index}",
                        100 + i,
                        (index * 100, index * 100 + 99 + i)
                    )
            except Exception as e:
                errors.append(e)
        
        # Create threads
        readers = [threading.Thread(target=read_datasets) for _ in range(num_readers)]
        writers = [threading.Thread(target=write_dataset, args=(i,)) for i in range(num_writers)]
        
        # Start all threads
        all_threads = readers + writers
        for t in all_threads:
            t.start()
        
        # Wait for completion
        for t in all_threads:
            t.join()
        
        # Check no errors
        assert len(errors) == 0


class TestTimestamps:
    """Test timestamp handling."""
    
    def test_timestamp_format(self, metadata_store):
        """Test that timestamps use ISO 8601 format with Z suffix."""
        user_id = "test@example.com"
        
        # Save dataset
        metadata_store.save(user_id, "dataset_1", 100, (0, 99))
        
        # Get timestamp
        datasets = metadata_store.list_datasets(user_id)
        timestamp = datasets[0]["indexed_at"]
        
        # Verify format (ends with Z)
        assert timestamp.endswith("Z")
        
        # Verify parseable as ISO 8601
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
