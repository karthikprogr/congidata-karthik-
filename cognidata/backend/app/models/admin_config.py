from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class AdminConfig(Base):
    __tablename__ = "admin_config"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    encrypted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
