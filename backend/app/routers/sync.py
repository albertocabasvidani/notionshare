from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, DatabaseConfig, SyncLog
from app.schemas import SyncLogResponse, SyncTriggerResponse
from app.services.sync import NotionSyncEngine

router = APIRouter(prefix="/sync", tags=["synchronization"])


@router.post("/{config_id}/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(
    config_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger a manual sync for a configuration"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Run sync
    try:
        sync_engine = NotionSyncEngine(db)
        sync_log = await sync_engine.sync_database(config_id)

        return {
            "message": "Sync completed successfully",
            "sync_log_id": sync_log.id,
            "status": sync_log.status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/{config_id}/status")
def get_sync_status(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current sync status for a configuration"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Get latest sync log
    latest_sync = db.query(SyncLog).filter(
        SyncLog.config_id == config_id
    ).order_by(SyncLog.started_at.desc()).first()

    return {
        "config_id": config_id,
        "sync_enabled": config.sync_enabled,
        "last_sync_at": config.last_sync_at,
        "latest_sync_log": latest_sync if latest_sync else None
    }


@router.get("/{config_id}/logs", response_model=List[SyncLogResponse])
def get_sync_logs(
    config_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync logs for a configuration"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    logs = db.query(SyncLog).filter(
        SyncLog.config_id == config_id
    ).order_by(SyncLog.started_at.desc()).limit(limit).all()

    return logs


@router.put("/{config_id}/enable")
def toggle_sync(
    config_id: int,
    enabled: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable or disable automatic sync"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    config.sync_enabled = enabled
    db.commit()

    return {
        "message": f"Sync {'enabled' if enabled else 'disabled'} successfully",
        "config_id": config_id,
        "sync_enabled": enabled
    }
