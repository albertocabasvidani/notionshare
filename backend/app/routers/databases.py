from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.services.notion import NotionService
from typing import List

router = APIRouter(prefix="/databases", tags=["databases"])


@router.get("/list")
async def list_databases(current_user: User = Depends(get_current_user)):
    """List all Notion databases accessible to the user"""
    if not current_user.notion_access_token:
        raise HTTPException(status_code=400, detail="Notion token not configured")

    notion = NotionService(current_user.notion_access_token)
    databases = await notion.get_databases()

    return {"databases": databases}


@router.get("/{db_id}/structure")
async def get_database_structure(
    db_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get database structure (schema)"""
    if not current_user.notion_access_token:
        raise HTTPException(status_code=400, detail="Notion token not configured")

    notion = NotionService(current_user.notion_access_token)
    schema = await notion.get_database_schema(db_id)

    return schema


@router.get("/pages/search")
async def search_pages(
    query: str = "",
    current_user: User = Depends(get_current_user)
):
    """Search for pages (for selecting target page)"""
    if not current_user.notion_access_token:
        raise HTTPException(status_code=400, detail="Notion token not configured")

    notion = NotionService(current_user.notion_access_token)
    pages = await notion.search_pages(query)

    return {"pages": pages}
