from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class NotionPropertyInfo(BaseModel):
    name: str
    type: str
    config: Optional[Dict[str, Any]] = None


class NotionDatabaseInfo(BaseModel):
    id: str
    title: str
    properties: List[NotionPropertyInfo]
    url: str


class NotionPageInfo(BaseModel):
    id: str
    title: str
    url: str
