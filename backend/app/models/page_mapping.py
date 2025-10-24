from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PageMapping(Base):
    __tablename__ = "page_mappings"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("database_configs.id", ondelete="CASCADE"), nullable=False)
    source_page_id = Column(String(255), nullable=False)
    target_page_id = Column(String(255), nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    config = relationship("DatabaseConfig", back_populates="page_mappings")

    __table_args__ = (
        UniqueConstraint('config_id', 'source_page_id', name='unique_config_source_page'),
    )
