from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("database_configs.id", ondelete="CASCADE"), nullable=False)
    sync_type = Column(String(50), nullable=True)  # 'manual', 'scheduled', 'webhook'
    status = Column(String(50), nullable=True)  # 'success', 'error', 'partial'
    rows_created = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    rows_deleted = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    config = relationship("DatabaseConfig", back_populates="sync_logs")
