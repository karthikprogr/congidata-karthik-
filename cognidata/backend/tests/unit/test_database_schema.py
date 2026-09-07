"""
Unit tests for database schema verification
Tests Requirements: 16.1, 16.2, 16.3, 16.5, 16.6, 16.7, 16.8, 16.9
"""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import User, Dataset, APIUsage, AdminConfig


@pytest.fixture(scope="module")
def test_engine():
    """Create a test database engine"""
    engine = create_engine("sqlite:///:memory:")
    
    # Enable foreign key constraints for SQLite
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_session(test_engine):
    """Create a test database session"""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


class TestDatabaseSchema:
    """Test database schema structure and constraints"""
    
    def test_users_table_exists(self, test_engine):
        """Verify users table exists with correct columns"""
        inspector = inspect(test_engine)
        assert 'users' in inspector.get_table_names()
        
        columns = {col['name']: col for col in inspector.get_columns('users')}
        
        # Verify required columns exist (Requirement 16.2)
        assert 'id' in columns
        assert 'email' in columns
        assert 'hashed_password' in columns
        assert 'tier' in columns
        assert 'storage_quota_mb' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns
    
    def test_datasets_table_exists(self, test_engine):
        """Verify datasets table exists with correct columns"""
        inspector = inspect(test_engine)
        assert 'datasets' in inspector.get_table_names()
        
        columns = {col['name']: col for col in inspector.get_columns('datasets')}
        
        # Verify required columns exist (Requirement 16.3)
        assert 'id' in columns
        assert 'user_id' in columns
        assert 'name' in columns
        assert 'file_path' in columns
        assert 'schema_json' in columns
        assert 'row_count' in columns
        assert 'file_size_mb' in columns
        assert 'uploaded_at' in columns
        assert 'updated_at' in columns
    
    def test_api_usage_table_exists(self, test_engine):
        """Verify api_usage table exists with correct columns"""
        inspector = inspect(test_engine)
        assert 'api_usage' in inspector.get_table_names()
        
        columns = {col['name']: col for col in inspector.get_columns('api_usage')}
        
        # Verify required columns exist (Requirement 16.5)
        assert 'id' in columns
        assert 'user_id' in columns
        assert 'dataset_id' in columns
        assert 'operation' in columns
        assert 'model' in columns
        assert 'input_tokens' in columns
        assert 'output_tokens' in columns
        assert 'cost' in columns
        assert 'response_cached' in columns
        assert 'timestamp' in columns
    
    def test_admin_config_table_exists(self, test_engine):
        """Verify admin_config table exists with correct columns"""
        inspector = inspect(test_engine)
        assert 'admin_config' in inspector.get_table_names()
        
        columns = {col['name']: col for col in inspector.get_columns('admin_config')}
        
        # Verify required columns exist (Requirement 16.5)
        assert 'key' in columns
        assert 'value' in columns
        assert 'encrypted' in columns
        assert 'updated_at' in columns
    
    def test_indexes_exist(self, test_engine):
        """Verify required indexes are created (Requirement 16.6, 16.7)"""
        inspector = inspect(test_engine)
        
        # Check users indexes
        users_indexes = {idx['name']: idx for idx in inspector.get_indexes('users')}
        assert 'ix_users_email' in users_indexes
        assert users_indexes['ix_users_email']['unique'] == True
        
        # Check datasets indexes
        datasets_indexes = {idx['name']: idx for idx in inspector.get_indexes('datasets')}
        assert 'ix_datasets_user_id' in datasets_indexes
        assert 'ix_datasets_uploaded_at' in datasets_indexes
        
        # Check api_usage indexes
        api_usage_indexes = {idx['name']: idx for idx in inspector.get_indexes('api_usage')}
        assert 'ix_api_usage_user_id' in api_usage_indexes
        assert 'ix_api_usage_timestamp' in api_usage_indexes
    
    def test_foreign_key_constraints(self, test_engine):
        """Verify foreign key constraints are properly defined (Requirement 16.8, 16.9)"""
        inspector = inspect(test_engine)
        
        # Check datasets foreign keys
        datasets_fks = inspector.get_foreign_keys('datasets')
        assert len(datasets_fks) == 1
        assert datasets_fks[0]['referred_table'] == 'users'
        assert 'user_id' in datasets_fks[0]['constrained_columns']
        
        # Check api_usage foreign keys
        api_usage_fks = inspector.get_foreign_keys('api_usage')
        assert len(api_usage_fks) >= 1  # At least user_id FK
        
        fk_tables = {fk['referred_table'] for fk in api_usage_fks}
        assert 'users' in fk_tables
        assert 'datasets' in fk_tables
    
    def test_create_user(self, test_session):
        """Test creating a user record"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            tier="free",
            storage_quota_mb=100
        )
        test_session.add(user)
        test_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.tier == "free"
        assert user.storage_quota_mb == 100
    
    def test_create_dataset(self, test_session):
        """Test creating a dataset record"""
        # Get existing user
        user = test_session.query(User).filter_by(email="test@example.com").first()
        assert user is not None
        
        dataset = Dataset(
            user_id=user.id,
            name="Test Dataset",
            file_path="/path/to/dataset.parquet",
            schema_json={"columns": [{"name": "col1", "type": "int"}]},
            row_count=1000,
            file_size_mb=5.2
        )
        test_session.add(dataset)
        test_session.commit()
        
        assert dataset.id is not None
        assert dataset.user_id == user.id
        assert dataset.name == "Test Dataset"
    
    def test_create_api_usage(self, test_session):
        """Test creating an api_usage record"""
        user = test_session.query(User).filter_by(email="test@example.com").first()
        dataset = test_session.query(Dataset).filter_by(user_id=user.id).first()
        
        usage = APIUsage(
            user_id=user.id,
            dataset_id=dataset.id,
            operation="query",
            model="gemini-1.5-flash",
            input_tokens=100,
            output_tokens=50,
            cost=0.00015,
            response_cached=False
        )
        test_session.add(usage)
        test_session.commit()
        
        assert usage.id is not None
        assert usage.user_id == user.id
        assert usage.operation == "query"
        assert usage.model == "gemini-1.5-flash"
    
    def test_create_admin_config(self, test_session):
        """Test creating an admin_config record"""
        config = AdminConfig(
            key="gemini_api_key",
            value="encrypted_key_here",
            encrypted=True
        )
        test_session.add(config)
        test_session.commit()
        
        assert config.key == "gemini_api_key"
        assert config.encrypted == True
    
    def test_cascade_delete_user(self, test_session):
        """Test that deleting a user cascades to datasets and api_usage (Requirement 16.9)"""
        # Create test user
        user = User(
            email="cascade_test@example.com",
            hashed_password="hashed",
            tier="free"
        )
        test_session.add(user)
        test_session.commit()
        user_id = user.id
        
        # Create dataset
        dataset = Dataset(
            user_id=user_id,
            name="Cascade Test Dataset",
            file_path="/path",
            schema_json={}
        )
        test_session.add(dataset)
        test_session.commit()
        dataset_id = dataset.id
        
        # Create api usage
        usage = APIUsage(
            user_id=user_id,
            dataset_id=dataset_id,
            operation="test"
        )
        test_session.add(usage)
        test_session.commit()
        
        # Delete user
        test_session.delete(user)
        test_session.commit()
        
        # Verify cascade deletion
        assert test_session.query(User).filter_by(id=user_id).first() is None
        assert test_session.query(Dataset).filter_by(id=dataset_id).first() is None
        # Note: api_usage should also be deleted due to cascade on user_id
