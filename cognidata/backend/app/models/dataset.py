from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    schema_json = Column(JSON, nullable=False)  # PostgreSQL: JSONB, SQLite: JSON
    row_count = Column(Integer, nullable=True)
    file_size_mb = Column(DECIMAL(10, 2), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
