from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, DatabaseConfig, PropertyMapping, RowFilter, UserPermission
from app.schemas import (
    DatabaseConfigCreate,
    DatabaseConfigUpdate,
    DatabaseConfigResponse,
    PropertyMappingCreate,
    PropertyMappingResponse,
    RowFilterCreate,
    RowFilterResponse,
    UserPermissionCreate,
    UserPermissionResponse,
)

router = APIRouter(prefix="/configs", tags=["configurations"])


@router.get("/", response_model=List[DatabaseConfigResponse])
def list_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all configurations for current user"""
    configs = db.query(DatabaseConfig).filter(
        DatabaseConfig.owner_user_id == current_user.id
    ).all()

    return configs


@router.post("/", response_model=DatabaseConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config(
    config_data: DatabaseConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new database configuration"""
    # Create config
    new_config = DatabaseConfig(
        owner_user_id=current_user.id,
        source_database_id=config_data.source_database_id,
        target_page_id=config_data.target_page_id,
        config_name=config_data.config_name,
        sync_enabled=config_data.sync_enabled,
        sync_interval_minutes=config_data.sync_interval_minutes
    )

    db.add(new_config)
    db.flush()  # Get ID without committing

    # Add property mappings
    for pm_data in config_data.property_mappings:
        pm = PropertyMapping(
            config_id=new_config.id,
            **pm_data.model_dump()
        )
        db.add(pm)

    # Add row filters
    for rf_data in config_data.row_filters:
        rf = RowFilter(
            config_id=new_config.id,
            **rf_data.model_dump()
        )
        db.add(rf)

    # Add user permissions
    for up_data in config_data.user_permissions:
        up = UserPermission(
            config_id=new_config.id,
            **up_data.model_dump()
        )
        db.add(up)

    db.commit()
    db.refresh(new_config)

    return new_config


@router.get("/{config_id}", response_model=DatabaseConfigResponse)
def get_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific configuration"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return config


@router.put("/{config_id}", response_model=DatabaseConfigResponse)
def update_config(
    config_id: int,
    config_data: DatabaseConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a configuration"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Update fields
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a configuration"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    db.delete(config)
    db.commit()

    return None


@router.post("/{config_id}/properties", response_model=PropertyMappingResponse)
def add_property_mapping(
    config_id: int,
    property_data: PropertyMappingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a property mapping to a configuration"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    new_mapping = PropertyMapping(
        config_id=config_id,
        **property_data.model_dump()
    )

    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    return new_mapping


@router.post("/{config_id}/filters", response_model=RowFilterResponse)
def add_row_filter(
    config_id: int,
    filter_data: RowFilterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a row filter to a configuration"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    new_filter = RowFilter(
        config_id=config_id,
        **filter_data.model_dump()
    )

    db.add(new_filter)
    db.commit()
    db.refresh(new_filter)

    return new_filter


@router.post("/{config_id}/users", response_model=UserPermissionResponse)
def add_user_permission(
    config_id: int,
    user_data: UserPermissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add user permission to a configuration"""
    config = db.query(DatabaseConfig).filter(
        DatabaseConfig.id == config_id,
        DatabaseConfig.owner_user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    new_permission = UserPermission(
        config_id=config_id,
        **user_data.model_dump()
    )

    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)

    return new_permission
