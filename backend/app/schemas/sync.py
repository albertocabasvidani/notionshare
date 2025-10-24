from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SyncLogResponse(BaseModel):
    id: int
    config_id: int
    sync_type: Optional[str]
    status: Optional[str]
    rows_created: int
    rows_updated: int
    rows_deleted: int
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SyncTriggerResponse(BaseModel):
    message: str
    sync_log_id: Optional[int] = None
    status: str
