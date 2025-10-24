from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PropertyMapping(Base):
    __tablename__ = "property_mappings"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("database_configs.id", ondelete="CASCADE"), nullable=False)
    property_name = Column(String(255), nullable=False)
    property_type = Column(String(50), nullable=True)  # 'title', 'text', 'number', 'select', etc.
    is_visible = Column(Boolean, default=True)
    is_writable = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    config = relationship("DatabaseConfig", back_populates="property_mappings")
