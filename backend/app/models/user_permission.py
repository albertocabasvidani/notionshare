from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


# Association table for UserPermission and RowFilter (many-to-many)
user_permission_row_filters = Table(
    'user_permission_row_filters',
    Base.metadata,
    Column('user_permission_id', Integer, ForeignKey('user_permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('row_filter_id', Integer, ForeignKey('row_filters.id', ondelete='CASCADE'), primary_key=True)
)


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("database_configs.id", ondelete="CASCADE"), nullable=False)
    user_email = Column(String(255), nullable=False)
    access_level = Column(String(50), default="read")  # 'read', 'write'

    # Notion page and database for this user
    user_page_id = Column(String(255), nullable=True)  # Dedicated subpage for this user
    target_database_id = Column(String(255), nullable=True)  # Mirror database in user's page

    notified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    config = relationship("DatabaseConfig", back_populates="user_permissions")
    row_filters = relationship("RowFilter", secondary=user_permission_row_filters, back_populates="user_permissions")

    __table_args__ = (
        UniqueConstraint('config_id', 'user_email', name='unique_config_user'),
    )
