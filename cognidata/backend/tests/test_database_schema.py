"""
Test suite for database schema validation
Tests all tables, indexes, and foreign key constraints per Task 1.1
Requirements: 16.1, 16.2, 16.3, 16.5, 16.6, 16.7, 16.8, 16.9
"""
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import User, Dataset, APIUsage, AdminConfig
from datetime import datetime
import os


@pytest.fixture(scope="module")
def test_engine():
    """Create a test database engine"""
    test_db_url = "sqlite:///./test_schema.db"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    
    # Enable foreign key constraints for SQLite
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()  # Close all connections before removing file
    if os.path.exists("test_schema.db"):
        try:
            os.remove("test_schema.db")
        except PermissionError:
            pass  # File still in use, will be cleaned up later


@pytest.fixture(scope="module")
def test_session(test_engine):
    """Create a test database session"""
    SessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    yield session
    session.close()


class TestUsersTable:
    """Test users table schema and constraints (Requirement 16.2)"""
    
    def test_users_table_exists(self, test_engine):
        """Verify users table exists"""
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "users" in tables, "users table should exist"
    
    def test_users_columns(self, test_engine):
        """Verify users table has all required columns"""
        inspector = inspect(test_engine)
        columns = {col['name']: col for col in inspector.get_columns('users')}
        
        # Required columns from specification
        required_columns = [
            'id', 'email', 'hashed_password', 'tier', 
            'storage_quota_mb', 'created_at', 'updated_at'
        ]
        
        for col_name in required_columns:
            assert col_name in columns, f"users table should have {col_name} column"
    
    def test_users_email_unique(self, test_engine):
        """Verify email column has unique constraint"""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes('users')
        
        email_unique = any(
            idx['unique'] and 'email' in idx['column_names'] 
            for idx in indexes
        )
        assert email_unique, "email column should have unique constraint"
    
    def test_users_primary_key(self, test_engine):
        """Verify id is primary key"""
        inspector = inspect(test_engine)
        pk = inspector.get_pk_constraint('users')
        assert 'id' in pk['constrained_columns'], "id should be primary key"
    
    def test_users_tier_default(self, test_session):
        """Verify tier has default value 'free'"""
        user = User(
            email="test@example.com",
            hashed_password="hashed123"
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        
        assert user.tier == 'free', "tier should default to 'free'"
        assert user.storage_quota_mb == 100, "storage_quota_mb should default to 100"
        assert user.created_at is not None, "created_at should be auto-populated"
        assert user.updated_at is not None, "updated_at should be auto-populated"
        
        # Cleanup
        test_session.delete(user)
        test_session.commit()


class TestDatasetsTable:
    """Test datasets table schema and constraints (Requirement 16.3)"""
    
    def test_datasets_table_exists(self, test_engine):
        """Verify datasets table exists"""
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "datasets" in tables, "datasets table should exist"
    
    def test_datasets_columns(self, test_engine):
        """Verify datasets table has all required columns"""
        inspector = inspect(test_engine)
        columns = {col['name']: col for col in inspector.get_columns('datasets')}
        
        required_columns = [
            'id', 'user_id', 'name', 'file_path', 'schema_json',
            'row_count', 'file_size_mb', 'uploaded_at', 'updated_at'
        ]
        
        for col_name in required_columns:
            assert col_name in columns, f"datasets table should have {col_name} column"
    
    def test_datasets_foreign_key(self, test_engine):
        """Verify datasets.user_id foreign key to users.id (Requirement 16.8)"""
        inspector = inspect(test_engine)
        fks = inspector.get_foreign_keys('datasets')
        
        user_fk = any(
            fk['referred_table'] == 'users' and 
            'user_id' in fk['constrained_columns']
            for fk in fks
        )
        assert user_fk, "datasets should have foreign key to users"
    
    def test_datasets_cascade_delete(self, test_session):
        """Verify CASCADE deletion when user is deleted (Requirement 16.9)"""
        # Create user
        user = User(email="cascade_test@example.com", hashed_password="hash123")
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        
        # Create dataset for user
        dataset = Dataset(
            user_id=user.id,
            name="Test Dataset",
            file_path="/test/path.parquet",
            schema_json={"columns": [{"name": "col1", "type": "int"}]},
            row_count=100,
            file_size_mb=1.5
        )
        test_session.add(dataset)
        test_session.commit()
        dataset_id = dataset.id
        
        # Delete user
        test_session.delete(user)
        test_session.commit()
        
        # Verify dataset was cascade deleted
        deleted_dataset = test_session.query(Dataset).filter_by(id=dataset_id).first()
        assert deleted_dataset is None, "Dataset should be cascade deleted when user is deleted"
    
    def test_datasets_indexes(self, test_engine):
        """Verify required indexes exist (Requirement 16.6, 16.7)"""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes('datasets')
        
        # Check user_id index
        user_id_indexed = any(
            'user_id' in idx['column_names'] 
            for idx in indexes
        )
        assert user_id_indexed, "user_id should be indexed"
        
        # Check uploaded_at index
        uploaded_at_indexed = any(
            'uploaded_at' in idx['column_names'] 
            for idx in indexes
        )
        assert uploaded_at_indexed, "uploaded_at should be indexed"


class TestAPIUsageTable:
    """Test api_usage table schema and constraints (Requirement 16.5)"""
    
    def test_api_usage_table_exists(self, test_engine):
        """Verify api_usage table exists"""
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "api_usage" in tables, "api_usage table should exist"
    
    def test_api_usage_columns(self, test_engine):
        """Verify api_usage table has all required columns"""
        inspector = inspect(test_engine)
        columns = {col['name']: col for col in inspector.get_columns('api_usage')}
        
        required_columns = [
            'id', 'user_id', 'dataset_id', 'operation', 'model',
            'input_tokens', 'output_tokens', 'cost', 'response_cached', 'timestamp'
        ]
        
        for col_name in required_columns:
            assert col_name in columns, f"api_usage table should have {col_name} column"
    
    def test_api_usage_foreign_keys(self, test_engine):
        """Verify foreign key constraints (Requirement 16.8)"""
        inspector = inspect(test_engine)
        fks = inspector.get_foreign_keys('api_usage')
        
        # Check user_id foreign key
        user_fk = any(
            fk['referred_table'] == 'users' and 
            'user_id' in fk['constrained_columns']
            for fk in fks
        )
        assert user_fk, "api_usage should have foreign key to users"
        
        # Check dataset_id foreign key
        dataset_fk = any(
            fk['referred_table'] == 'datasets' and 
            'dataset_id' in fk['constrained_columns']
            for fk in fks
        )
        assert dataset_fk, "api_usage should have foreign key to datasets"
    
    def test_api_usage_cascade_delete_user(self, test_session):
        """Verify CASCADE deletion when user is deleted (Requirement 16.9)"""
        # Create user
        user = User(email="api_cascade@example.com", hashed_password="hash123")
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        
        # Create api_usage record
        api_usage = APIUsage(
            user_id=user.id,
            operation="query",
            model="gemini-1.5-flash",
            input_tokens=100,
            output_tokens=200,
            cost=0.003
        )
        test_session.add(api_usage)
        test_session.commit()
        usage_id = api_usage.id
        
        # Delete user
        test_session.delete(user)
        test_session.commit()
        
        # Verify api_usage was cascade deleted
        deleted_usage = test_session.query(APIUsage).filter_by(id=usage_id).first()
        assert deleted_usage is None, "APIUsage should be cascade deleted when user is deleted"
    
    def test_api_usage_set_null_dataset(self, test_session):
        """Verify SET NULL when dataset is deleted"""
        # Create user and dataset
        user = User(email="setnull_test@example.com", hashed_password="hash123")
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        
        dataset = Dataset(
            user_id=user.id,
            name="Test Dataset",
            file_path="/test/path.parquet",
            schema_json={"columns": []}
        )
        test_session.add(dataset)
        test_session.commit()
        test_session.refresh(dataset)
        
        # Create api_usage record
        api_usage = APIUsage(
            user_id=user.id,
            dataset_id=dataset.id,
            operation="query",
            model="gemini-1.5-flash"
        )
        test_session.add(api_usage)
        test_session.commit()
        usage_id = api_usage.id
        
        # Delete dataset
        test_session.delete(dataset)
        test_session.commit()
        
        # Verify api_usage.dataset_id is set to NULL
        usage = test_session.query(APIUsage).filter_by(id=usage_id).first()
        assert usage is not None, "APIUsage should still exist"
        assert usage.dataset_id is None, "dataset_id should be NULL after dataset deletion"
        
        # Cleanup
        test_session.delete(usage)
        test_session.delete(user)
        test_session.commit()
    
    def test_api_usage_indexes(self, test_engine):
        """Verify required indexes exist (Requirement 16.6, 16.7)"""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes('api_usage')
        
        # Check user_id index
        user_id_indexed = any(
            'user_id' in idx['column_names'] 
            for idx in indexes
        )
        assert user_id_indexed, "user_id should be indexed"
        
        # Check timestamp index
        timestamp_indexed = any(
            'timestamp' in idx['column_names'] 
            for idx in indexes
        )
        assert timestamp_indexed, "timestamp should be indexed"
    
    def test_api_usage_defaults(self, test_session):
        """Verify default values for columns"""
        user = User(email="defaults_test@example.com", hashed_password="hash123")
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        
        usage = APIUsage(
            user_id=user.id,
            operation="query"
        )
        test_session.add(usage)
        test_session.commit()
        test_session.refresh(usage)
        
        assert usage.input_tokens == 0, "input_tokens should default to 0"
        assert usage.output_tokens == 0, "output_tokens should default to 0"
        assert usage.cost == 0, "cost should default to 0"
        assert usage.response_cached == False, "response_cached should default to False"
        assert usage.timestamp is not None, "timestamp should be auto-populated"
        
        # Cleanup
        test_session.delete(usage)
        test_session.delete(user)
        test_session.commit()


class TestAdminConfigTable:
    """Test admin_config table schema (Requirement 16.1)"""
    
    def test_admin_config_table_exists(self, test_engine):
        """Verify admin_config table exists"""
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "admin_config" in tables, "admin_config table should exist"
    
    def test_admin_config_columns(self, test_engine):
        """Verify admin_config table has all required columns"""
        inspector = inspect(test_engine)
        columns = {col['name']: col for col in inspector.get_columns('admin_config')}
        
        required_columns = ['key', 'value', 'encrypted', 'updated_at']
        
        for col_name in required_columns:
            assert col_name in columns, f"admin_config table should have {col_name} column"
    
    def test_admin_config_primary_key(self, test_engine):
        """Verify key is primary key"""
        inspector = inspect(test_engine)
        pk = inspector.get_pk_constraint('admin_config')
        assert 'key' in pk['constrained_columns'], "key should be primary key"
    
    def test_admin_config_crud(self, test_session):
        """Test CRUD operations on admin_config"""
        # Create
        config = AdminConfig(
            key="test_key",
            value="test_value",
            encrypted=False
        )
        test_session.add(config)
        test_session.commit()
        test_session.refresh(config)
        
        assert config.key == "test_key"
        assert config.value == "test_value"
        assert config.encrypted == False
        assert config.updated_at is not None
        
        # Read
        fetched = test_session.query(AdminConfig).filter_by(key="test_key").first()
        assert fetched is not None
        assert fetched.value == "test_value"
        
        # Update
        fetched.value = "updated_value"
        test_session.commit()
        test_session.refresh(fetched)
        assert fetched.value == "updated_value"
        
        # Delete
        test_session.delete(fetched)
        test_session.commit()
        deleted = test_session.query(AdminConfig).filter_by(key="test_key").first()
        assert deleted is None


class TestDatabaseConnectionPooling:
    """Test connection pooling configuration (Requirement 16.10)"""
    
    def test_connection_pool_settings(self):
        """Verify connection pooling is configured correctly"""
        from app.core.database import engine
        
        # Check pool size settings
        if "postgresql" in str(engine.url):
            assert engine.pool.size() >= 5, "PostgreSQL pool should have minimum 5 connections"
            # max_overflow is 15, so total max is pool_size + max_overflow = 20
        
        # Verify pool_pre_ping is enabled
        assert engine.pool._pre_ping == True, "pool_pre_ping should be enabled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
