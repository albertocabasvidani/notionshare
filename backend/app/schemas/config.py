from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# PropertyMapping schemas
class PropertyMappingCreate(BaseModel):
    property_name: str
    property_type: Optional[str] = None
    is_visible: bool = True
    is_writable: bool = False


class PropertyMappingResponse(BaseModel):
    id: int
    config_id: int
    property_name: str
    property_type: Optional[str]
    is_visible: bool
    is_writable: bool
    created_at: datetime

    class Config:
        from_attributes = True


# RowFilter schemas
class RowFilterCreate(BaseModel):
    filter_type: str  # 'property_match', 'formula', 'manual_select'
    property_name: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None
    formula: Optional[str] = None


class RowFilterResponse(BaseModel):
    id: int
    config_id: int
    filter_type: str
    property_name: Optional[str]
    operator: Optional[str]
    value: Optional[str]
    formula: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# UserPermission schemas
class UserPermissionCreate(BaseModel):
    user_email: str
    access_level: str = "read"  # 'read', 'write'
    row_filter_ids: List[int] = []  # IDs of RowFilters specific to this user


class UserPermissionResponse(BaseModel):
    id: int
    config_id: int
    user_email: str
    access_level: str
    user_page_id: Optional[str]
    target_database_id: Optional[str]
    notified: bool
    created_at: datetime
    row_filters: List[RowFilterResponse] = []

    class Config:
        from_attributes = True


# DatabaseConfig schemas
class DatabaseConfigCreate(BaseModel):
    source_database_id: str
    parent_page_id: str
    config_name: str
    sync_enabled: bool = True
    sync_interval_minutes: int = 15
    property_mappings: List[PropertyMappingCreate] = []
    row_filters: List[RowFilterCreate] = []
    user_permissions: List[UserPermissionCreate] = []


class DatabaseConfigUpdate(BaseModel):
    config_name: Optional[str] = None
    sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = None
    parent_page_id: Optional[str] = None


class DatabaseConfigResponse(BaseModel):
    id: int
    owner_user_id: int
    source_database_id: str
    parent_page_id: Optional[str]
    config_name: str
    sync_enabled: bool
    sync_interval_minutes: int
    last_sync_at: Optional[datetime]
    created_at: datetime
    property_mappings: List[PropertyMappingResponse] = []
    row_filters: List[RowFilterResponse] = []
    user_permissions: List[UserPermissionResponse] = []

    class Config:
        from_attributes = True
