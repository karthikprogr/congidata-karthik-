"""
Integration tests for RAG Metadata Store

Tests the metadata store in the actual backend environment with
the correct .dataset_store path structure.
"""

import pytest
import pathlib
from app.services.rag_metadata_store import RAGMetadataStore


@pytest.fixture
def metadata_store():
    """Create a RAGMetadataStore with the actual backend path."""
    base_dir = pathlib.Path(__file__).resolve().parents[1] / ".dataset_store"
    return RAGMetadataStore(base_dir)


def test_metadata_store_with_backend_path(metadata_store):
    """Test that metadata store works with actual backend path structure."""
    user_id = "integration_test@example.com"
    dataset_name = "test_dataset_integration"
    
    try:
        # Save dataset
        metadata_store.save(user_id, dataset_name, 50, (0, 49))
        
        # Verify it was saved
        datasets = metadata_store.list_datasets(user_id)
        assert len(datasets) == 1
        assert datasets[0]["name"] == dataset_name
        assert datasets[0]["chunk_count"] == 50
        
        # Verify ID range
        id_range = metadata_store.get_id_range(user_id, dataset_name)
        assert id_range == (0, 49)
        
        # Verify next_id
        next_id = metadata_store.get_next_id(user_id)
        assert next_id == 50
        
    finally:
        # Clean up
        metadata_store.delete(user_id, dataset_name)


def test_metadata_store_user_isolation(metadata_store):
    """Test that different users have isolated metadata."""
    user1 = "user1_integration@example.com"
    user2 = "user2_integration@example.com"
    
    try:
        # Save datasets for both users
        metadata_store.save(user1, "dataset_1", 100, (0, 99))
        metadata_store.save(user2, "dataset_1", 200, (0, 199))
        
        # Verify isolation
        user1_datasets = metadata_store.list_datasets(user1)
        user2_datasets = metadata_store.list_datasets(user2)
        
        assert len(user1_datasets) == 1
        assert len(user2_datasets) == 1
        assert user1_datasets[0]["chunk_count"] == 100
        assert user2_datasets[0]["chunk_count"] == 200
        
    finally:
        # Clean up
        metadata_store.delete(user1, "dataset_1")
        metadata_store.delete(user2, "dataset_1")


def test_metadata_persistence_across_restarts(metadata_store):
    """Test that metadata persists when creating new store instances."""
    user_id = "persistence_test@example.com"
    dataset_name = "persistent_dataset"
    base_dir = pathlib.Path(__file__).resolve().parents[1] / ".dataset_store"
    
    try:
        # Save with first instance
        metadata_store.save(user_id, dataset_name, 75, (0, 74))
        
        # Create new instance (simulates restart)
        new_store = RAGMetadataStore(base_dir)
        
        # Verify data persisted
        datasets = new_store.list_datasets(user_id)
        assert len(datasets) == 1
        assert datasets[0]["name"] == dataset_name
        assert datasets[0]["chunk_count"] == 75
        
    finally:
        # Clean up
        metadata_store.delete(user_id, dataset_name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
