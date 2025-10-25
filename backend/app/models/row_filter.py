from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RowFilter(Base):
    __tablename__ = "row_filters"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("database_configs.id", ondelete="CASCADE"), nullable=False)
    filter_type = Column(String(50), nullable=False)  # 'property_match', 'formula', 'manual_select'
    property_name = Column(String(255), nullable=True)
    operator = Column(String(50), nullable=True)  # 'equals', 'contains', 'is_empty', etc.
    value = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    config = relationship("DatabaseConfig", back_populates="row_filters")
    user_permissions = relationship("UserPermission", secondary="user_permission_row_filters", back_populates="row_filters")
