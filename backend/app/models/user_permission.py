from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("database_configs.id", ondelete="CASCADE"), nullable=False)
    user_email = Column(String(255), nullable=False)
    access_level = Column(String(50), default="read")  # 'read', 'write'
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    config = relationship("DatabaseConfig", back_populates="user_permissions")

    __table_args__ = (
        UniqueConstraint('config_id', 'user_email', name='unique_config_user'),
    )
