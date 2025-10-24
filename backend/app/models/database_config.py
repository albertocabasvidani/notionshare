from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class DatabaseConfig(Base):
    __tablename__ = "database_configs"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_database_id = Column(String(255), nullable=False)
    target_page_id = Column(String(255), nullable=True)
    target_database_id = Column(String(255), nullable=True)
    config_name = Column(String(255), nullable=False)
    sync_enabled = Column(Boolean, default=True)
    sync_interval_minutes = Column(Integer, default=15)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="database_configs")
    row_filters = relationship("RowFilter", back_populates="config", cascade="all, delete-orphan")
    property_mappings = relationship("PropertyMapping", back_populates="config", cascade="all, delete-orphan")
    user_permissions = relationship("UserPermission", back_populates="config", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="config", cascade="all, delete-orphan")
    page_mappings = relationship("PageMapping", back_populates="config", cascade="all, delete-orphan")
