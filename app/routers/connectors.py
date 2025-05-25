from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID

from app.db.database import get_db
from app.api.mvp.auth import get_owner_user, get_current_user
from app.models.data_models.User import User
from app.models.data_models.Connector import Connector
from app.schemas.data_models.Connector import (
    ConnectorCreate,
    ConnectorRead,
    ConnectorUpdate,
    ConnectorSync,
    CSVUploadResponse,
    ConnectorTestResponse,
    OAuthInitRequest,
    OAuthInitResponse
)
from app.services.connector_service import ConnectorService

router = APIRouter(
    prefix="/connectors",
    tags=["connectors"]
)

@router.post("/", response_model=ConnectorRead, status_code=status.HTTP_201_CREATED)
async def create_connector(
    connector_data: ConnectorCreate,
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Create a new connector (OWNER role required)"""
    
    # Check if connector for this provider already exists for this user
    existing_connector = db.exec(
        select(Connector).where(
            Connector.provider == connector_data.provider,
            Connector.created_by == current_user.id
        )
    ).first()
    
    if existing_connector:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Connector for {connector_data.provider} already exists"
        )
    
    # Create new connector
    connector = Connector(
        provider=connector_data.provider,
        access_token=connector_data.config.get("access_token", ""),
        refresh_token=connector_data.config.get("refresh_token"),
        config=connector_data.config,
        created_by=current_user.id,
        status="PENDING"
    )
    
    db.add(connector)
    db.commit()
    db.refresh(connector)
    
    return connector

@router.get("/", response_model=List[ConnectorRead])
async def list_connectors(
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """List all connectors for the current owner"""
    connectors = db.exec(
        select(Connector).where(Connector.created_by == current_user.id)
    ).all()
    
    return connectors

@router.get("/{connector_id}", response_model=ConnectorRead)
async def get_connector(
    connector_id: UUID,
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Get a specific connector"""
    connector = db.exec(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.created_by == current_user.id
        )
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    return connector

@router.patch("/{connector_id}", response_model=ConnectorRead)
async def update_connector(
    connector_id: UUID,
    connector_update: ConnectorUpdate,
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Update a connector"""
    connector = db.exec(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.created_by == current_user.id
        )
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    # Update fields
    if connector_update.config is not None:
        connector.config = connector_update.config
        # Update access token if provided in config
        if "access_token" in connector_update.config:
            connector.access_token = connector_update.config["access_token"]
        if "refresh_token" in connector_update.config:
            connector.refresh_token = connector_update.config["refresh_token"]
    
    if connector_update.status is not None:
        connector.status = connector_update.status
    
    db.add(connector)
    db.commit()
    db.refresh(connector)
    
    return connector

@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: UUID,
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Delete a connector"""
    connector = db.exec(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.created_by == current_user.id
        )
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    db.delete(connector)
    db.commit()

@router.post("/{connector_id}/sync", response_model=ConnectorSync)
async def sync_connector(
    connector_id: UUID,
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Manually trigger a sync for a connector"""
    connector = db.exec(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.created_by == current_user.id
        )
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    service = ConnectorService(db)
    
    if connector.provider.value == "SHOPIFY":
        return await service.sync_shopify(connector_id)
    elif connector.provider.value == "SQUARE":
        return await service.sync_square(connector_id)
    elif connector.provider.value == "LIGHTSPEED":
        return await service.sync_lightspeed(connector_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sync not supported for this provider"
        )

@router.post("/{connector_id}/test", response_model=ConnectorTestResponse)
async def test_connector(
    connector_id: UUID,
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Test a connector connection"""
    connector = db.exec(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.created_by == current_user.id
        )
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    service = ConnectorService(db)
    return await service.test_connection(connector_id)

@router.post("/csv/upload", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    sku_column: str = Form(...),
    name_column: str = Form(...),
    on_hand_column: str = Form(...),
    cost_column: Optional[str] = Form(None),
    supplier_name_column: Optional[str] = Form(None),
    variant_column: Optional[str] = Form(None),
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Upload and import inventory from CSV file (OWNER role required)"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    service = ConnectorService(db)
    
    return await service.import_csv(
        file=file,
        sku_column=sku_column,
        name_column=name_column,
        on_hand_column=on_hand_column,
        cost_column=cost_column,
        supplier_name_column=supplier_name_column,
        variant_column=variant_column,
        user_id=current_user.id
    )

# Test endpoint to verify owner-only access
@router.get("/test/owner-only")
async def test_owner_only(current_user: User = Depends(get_owner_user)):
    """Test endpoint to verify owner-only access"""
    return {
        "message": "This endpoint is only accessible to users with OWNER role",
        "user_email": current_user.email,
        "user_role": current_user.role
    }

@router.post("/oauth/shopify", response_model=OAuthInitResponse, status_code=status.HTTP_201_CREATED)
async def initialize_shopify_oauth(
    oauth_data: OAuthInitRequest,
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Initialize Shopify connector via OAuth code exchange"""
    
    # Check if Shopify connector already exists for this user
    existing_connector = db.exec(
        select(Connector).where(
            Connector.provider == "SHOPIFY",
            Connector.created_by == current_user.id
        )
    ).first()
    
    if existing_connector:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Shopify connector already exists for this user"
        )
    
    if not oauth_data.shop_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop domain is required for Shopify OAuth"
        )
    
    service = ConnectorService(db)
    connector = await service.initialize_shopify_oauth(
        shop_domain=oauth_data.shop_domain,
        oauth_code=oauth_data.oauth_code,
        user_id=current_user.id
    )
    
    return OAuthInitResponse(
        connector_id=connector.id,
        provider=connector.provider,
        status=connector.status,
        message="Shopify connector initialized successfully" if connector.status == "ACTIVE" else "Shopify connector created but needs configuration"
    )

@router.post("/oauth/square", response_model=OAuthInitResponse, status_code=status.HTTP_201_CREATED)
async def initialize_square_oauth(
    oauth_data: OAuthInitRequest,
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Initialize Square connector via OAuth code exchange"""
    
    # Check if Square connector already exists for this user
    existing_connector = db.exec(
        select(Connector).where(
            Connector.provider == "SQUARE",
            Connector.created_by == current_user.id
        )
    ).first()
    
    if existing_connector:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Square connector already exists for this user"
        )
    
    service = ConnectorService(db)
    connector = await service.initialize_square_oauth(
        oauth_code=oauth_data.oauth_code,
        user_id=current_user.id
    )
    
    return OAuthInitResponse(
        connector_id=connector.id,
        provider=connector.provider,
        status=connector.status,
        message="Square connector initialized successfully" if connector.status == "ACTIVE" else "Square connector created but needs configuration"
    )

@router.post("/oauth/lightspeed", response_model=OAuthInitResponse, status_code=status.HTTP_201_CREATED)
async def initialize_lightspeed_oauth(
    oauth_data: OAuthInitRequest,
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Initialize Lightspeed connector via OAuth code exchange"""
    
    # Check if Lightspeed connector already exists for this user
    existing_connector = db.exec(
        select(Connector).where(
            Connector.provider == "LIGHTSPEED",
            Connector.created_by == current_user.id
        )
    ).first()
    
    if existing_connector:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lightspeed connector already exists for this user"
        )
    
    service = ConnectorService(db)
    connector = await service.initialize_lightspeed_oauth(
        oauth_code=oauth_data.oauth_code,
        user_id=current_user.id
    )
    
    return OAuthInitResponse(
        connector_id=connector.id,
        provider=connector.provider,
        status=connector.status,
        message="Lightspeed connector initialized successfully" if connector.status == "ACTIVE" else "Lightspeed connector created but needs configuration"
    )

@router.get("/oauth/urls", response_model=dict)
async def get_oauth_urls():
    """Get OAuth authorization URLs for each provider"""
    import os
    
    shopify_client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    square_client_id = os.environ.get("SQUARE_CLIENT_ID") 
    lightspeed_client_id = os.environ.get("LIGHTSPEED_CLIENT_ID")
    
    base_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    
    oauth_urls = {}
    
    if shopify_client_id:
        oauth_urls["shopify"] = {
            "auth_url": "https://{shop_domain}/admin/oauth/authorize",
            "client_id": shopify_client_id,
            "scopes": "read_products,read_inventory,read_locations",
            "redirect_uri": f"{base_url}/connectors/oauth/callback"
        }
    
    if square_client_id:
        oauth_urls["square"] = {
            "auth_url": "https://connect.squareup.com/oauth2/authorize",
            "client_id": square_client_id,
            "scopes": "INVENTORY_READ",
            "redirect_uri": f"{base_url}/connectors/oauth/callback"
        }
    
    if lightspeed_client_id:
        oauth_urls["lightspeed"] = {
            "auth_url": "https://cloud.lightspeedapp.com/oauth/authorize.php",
            "client_id": lightspeed_client_id,
            "scopes": "employee:all",
            "redirect_uri": f"{base_url}/connectors/oauth/callback"
        }
    
    return oauth_urls 