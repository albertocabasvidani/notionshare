from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.notion import NotionService
from app.models import DatabaseConfig, PageMapping, SyncLog
from app.utils.notion_helpers import build_notion_filter, filter_properties, is_property_writable
import asyncio


class NotionSyncEngine:
    """Engine for synchronizing Notion databases"""

    def __init__(self, db: Session):
        self.db = db

    async def sync_database(self, config_id: int) -> SyncLog:
        """Main sync function - orchestrates bidirectional sync"""
        # Load configuration
        config = self.db.query(DatabaseConfig).filter(DatabaseConfig.id == config_id).first()
        if not config:
            raise ValueError(f"Configuration {config_id} not found")

        if not config.owner.notion_access_token:
            raise ValueError("User has no Notion access token")

        # Create sync log
        sync_log = SyncLog(
            config_id=config_id,
            sync_type="manual",
            status="running"
        )
        self.db.add(sync_log)
        self.db.commit()

        try:
            notion = NotionService(config.owner.notion_access_token)

            # If target database doesn't exist, create it
            if not config.target_database_id:
                await self._create_mirror_database(config, notion)
                self.db.commit()

            # Sync source -> target
            rows_created, rows_updated = await self._sync_source_to_target(config, notion)

            # Sync target -> source (only writable properties)
            rows_updated_reverse = await self._sync_target_to_source(config, notion)

            # Update sync log
            sync_log.status = "success"
            sync_log.rows_created = rows_created
            sync_log.rows_updated = rows_updated + rows_updated_reverse
            sync_log.completed_at = datetime.utcnow()

            # Update config last sync
            config.last_sync_at = datetime.utcnow()

            self.db.commit()

            return sync_log

        except Exception as e:
            sync_log.status = "error"
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    async def _create_mirror_database(self, config: DatabaseConfig, notion: NotionService):
        """Create the mirror database in target page"""
        # Get source database schema
        source_schema = await notion.get_database_schema(config.source_database_id)

        # Build properties schema for target (only visible properties)
        visible_props = {pm.property_name for pm in config.property_mappings if pm.is_visible}

        target_properties = {}
        for prop in source_schema["properties"]:
            if not visible_props or prop["name"] in visible_props:
                # Copy property config
                prop_config = prop["config"].copy()
                # Remove id field if present
                prop_config.pop("id", None)
                target_properties[prop["name"]] = prop_config

        # Create database
        target_db = await notion.create_database(
            parent_page_id=config.target_page_id,
            title=f"{source_schema['title']} (Mirror)",
            properties=target_properties
        )

        config.target_database_id = target_db["id"]

    async def _sync_source_to_target(
        self,
        config: DatabaseConfig,
        notion: NotionService
    ) -> tuple[int, int]:
        """Sync changes from source to target"""
        rows_created = 0
        rows_updated = 0

        # Build filter from config
        notion_filter = build_notion_filter(config.row_filters)

        # Fetch source rows (with filters)
        source_pages = await notion.query_database(
            config.source_database_id,
            filter_obj=notion_filter
        )

        # Get existing page mappings
        existing_mappings = {
            pm.source_page_id: pm.target_page_id
            for pm in config.page_mappings
        }

        source_page_ids = {page["id"] for page in source_pages}

        for source_page in source_pages:
            source_id = source_page["id"]

            # Filter properties based on config
            filtered_props = filter_properties(
                source_page["properties"],
                config.property_mappings
            )

            if source_id in existing_mappings:
                # Update existing target page
                target_id = existing_mappings[source_id]
                try:
                    await notion.update_page(target_id, filtered_props)
                    rows_updated += 1

                    # Update page mapping timestamp
                    mapping = self.db.query(PageMapping).filter(
                        PageMapping.config_id == config.id,
                        PageMapping.source_page_id == source_id
                    ).first()
                    if mapping:
                        mapping.last_synced_at = datetime.utcnow()

                except Exception as e:
                    print(f"Failed to update page {target_id}: {e}")

                # Rate limiting
                await asyncio.sleep(0.35)

            else:
                # Create new target page
                try:
                    new_page = await notion.create_page(
                        config.target_database_id,
                        filtered_props
                    )
                    rows_created += 1

                    # Create page mapping
                    mapping = PageMapping(
                        config_id=config.id,
                        source_page_id=source_id,
                        target_page_id=new_page["id"],
                        last_synced_at=datetime.utcnow()
                    )
                    self.db.add(mapping)

                except Exception as e:
                    print(f"Failed to create page: {e}")

                # Rate limiting
                await asyncio.sleep(0.35)

        # Archive pages that no longer match filters
        for source_id, target_id in existing_mappings.items():
            if source_id not in source_page_ids:
                try:
                    await notion.archive_page(target_id)
                    # Remove mapping
                    self.db.query(PageMapping).filter(
                        PageMapping.config_id == config.id,
                        PageMapping.source_page_id == source_id
                    ).delete()
                except Exception as e:
                    print(f"Failed to archive page {target_id}: {e}")

                await asyncio.sleep(0.35)

        return rows_created, rows_updated

    async def _sync_target_to_source(
        self,
        config: DatabaseConfig,
        notion: NotionService
    ) -> int:
        """Sync changes from target back to source (only writable properties)"""
        rows_updated = 0

        # Get writable properties
        writable_props = {
            pm.property_name for pm in config.property_mappings
            if pm.is_writable
        }

        if not writable_props:
            return 0

        # Fetch target pages
        target_pages = await notion.query_database(config.target_database_id)

        # Get page mappings (target -> source)
        target_to_source = {
            pm.target_page_id: pm.source_page_id
            for pm in config.page_mappings
        }

        for target_page in target_pages:
            target_id = target_page["id"]

            if target_id not in target_to_source:
                continue

            source_id = target_to_source[target_id]

            # Get source page current state
            try:
                source_page = await notion.get_page(source_id)
            except Exception as e:
                print(f"Failed to get source page {source_id}: {e}")
                continue

            # Build update with only writable properties that changed
            updates = {}
            for prop_name in writable_props:
                if prop_name in target_page["properties"]:
                    target_value = target_page["properties"][prop_name]
                    source_value = source_page["properties"].get(prop_name)

                    # Simple comparison (can be enhanced)
                    if target_value != source_value:
                        updates[prop_name] = target_value

            if updates:
                try:
                    await notion.update_page(source_id, updates)
                    rows_updated += 1
                except Exception as e:
                    print(f"Failed to update source page {source_id}: {e}")

                await asyncio.sleep(0.35)

        return rows_updated
