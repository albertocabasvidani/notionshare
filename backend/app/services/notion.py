from notion_client import AsyncClient
from typing import Dict, Any, List, Optional
from app.utils.notion_helpers import extract_title_from_database, extract_title_from_page
import asyncio


class NotionService:
    """Service for interacting with Notion API"""

    def __init__(self, access_token: str):
        self.client = AsyncClient(auth=access_token)

    async def get_databases(self) -> List[Dict[str, Any]]:
        """List all databases the integration has access to"""
        try:
            response = await self.client.search(filter={"property": "object", "value": "database"})
            databases = []
            for db in response.get("results", []):
                databases.append({
                    "id": db["id"],
                    "title": extract_title_from_database(db),
                    "url": db.get("url", ""),
                })
            return databases
        except Exception as e:
            raise Exception(f"Failed to fetch databases: {str(e)}")

    async def get_database_schema(self, db_id: str) -> Dict[str, Any]:
        """Get database schema (properties)"""
        try:
            database = await self.client.databases.retrieve(database_id=db_id)
            properties = database.get("properties", {})

            schema = {
                "id": database["id"],
                "title": extract_title_from_database(database),
                "url": database.get("url", ""),
                "properties": []
            }

            for prop_name, prop_config in properties.items():
                schema["properties"].append({
                    "name": prop_name,
                    "type": prop_config.get("type"),
                    "config": prop_config
                })

            return schema
        except Exception as e:
            raise Exception(f"Failed to fetch database schema: {str(e)}")

    async def query_database(
        self,
        db_id: str,
        filter_obj: Optional[Dict[str, Any]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Query database with optional filters"""
        try:
            all_results = []
            has_more = True
            start_cursor = None

            while has_more:
                query_params = {"page_size": page_size}
                if filter_obj:
                    query_params["filter"] = filter_obj
                if start_cursor:
                    query_params["start_cursor"] = start_cursor

                response = await self.client.databases.query(
                    database_id=db_id,
                    **query_params
                )

                all_results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

                # Rate limiting
                if has_more:
                    await asyncio.sleep(0.35)  # ~3 req/sec

            return all_results
        except Exception as e:
            raise Exception(f"Failed to query database: {str(e)}")

    async def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new database"""
        try:
            database = await self.client.databases.create(
                parent={"type": "page_id", "page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": title}}],
                properties=properties
            )
            return database
        except Exception as e:
            raise Exception(f"Failed to create database: {str(e)}")

    async def create_page(self, db_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a page (row) in a database"""
        try:
            page = await self.client.pages.create(
                parent={"database_id": db_id},
                properties=properties
            )
            return page
        except Exception as e:
            raise Exception(f"Failed to create page: {str(e)}")

    async def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update a page (row)"""
        try:
            page = await self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            return page
        except Exception as e:
            raise Exception(f"Failed to update page: {str(e)}")

    async def archive_page(self, page_id: str) -> Dict[str, Any]:
        """Archive (soft delete) a page"""
        try:
            page = await self.client.pages.update(
                page_id=page_id,
                archived=True
            )
            return page
        except Exception as e:
            raise Exception(f"Failed to archive page: {str(e)}")

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get a page by ID"""
        try:
            page = await self.client.pages.retrieve(page_id=page_id)
            return page
        except Exception as e:
            raise Exception(f"Failed to get page: {str(e)}")

    async def search_pages(self, query: str = "") -> List[Dict[str, Any]]:
        """Search for pages"""
        try:
            response = await self.client.search(
                query=query,
                filter={"property": "object", "value": "page"}
            )
            pages = []
            for page in response.get("results", []):
                pages.append({
                    "id": page["id"],
                    "title": extract_title_from_page(page),
                    "url": page.get("url", ""),
                })
            return pages
        except Exception as e:
            raise Exception(f"Failed to search pages: {str(e)}")
