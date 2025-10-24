from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models import DatabaseConfig
from app.services.sync import NotionSyncEngine
import asyncio


@celery_app.task(name="app.tasks.sync_tasks.sync_database")
def sync_database(config_id: int):
    """Sync a specific database configuration"""
    db = SessionLocal()
    try:
        engine = NotionSyncEngine(db)
        asyncio.run(engine.sync_database(config_id))
    except Exception as e:
        print(f"Error syncing config {config_id}: {e}")
    finally:
        db.close()


@celery_app.task(name="app.tasks.sync_tasks.sync_all_enabled")
def sync_all_enabled():
    """Sync all enabled configurations"""
    db = SessionLocal()
    try:
        configs = db.query(DatabaseConfig).filter(
            DatabaseConfig.sync_enabled == True
        ).all()

        for config in configs:
            # Queue individual sync tasks
            sync_database.delay(config.id)

        print(f"Queued {len(configs)} sync tasks")

    except Exception as e:
        print(f"Error queuing sync tasks: {e}")
    finally:
        db.close()
