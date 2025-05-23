import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from app.main import app
from app.db.database import get_db
from app.models.data_models.User import User
from app.models.data_models.Connector import Connector
from app.models.enums.UserRole import UserRole
from app.models.enums.ConnectorProvider import ConnectorProvider
from app.api.mvp.auth import create_access_token
import tempfile
import os

# Create test database
engine = create_engine("sqlite:///test_connectors.db", echo=False)

def get_test_db():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_db] = get_test_db

client = TestClient(app=app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create tables for testing"""
    SQLModel.metadata.create_all(engine)
    yield
    # Cleanup
    if os.path.exists("test_connectors.db"):
        os.remove("test_connectors.db")

@pytest.fixture
def owner_user():
    """Create an owner user for testing"""
    with Session(engine) as session:
        user = User(
            email="owner@test.com",
            password_hash="hashed_password",
            role=UserRole.OWNER
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

@pytest.fixture
def staff_user():
    """Create a staff user for testing"""
    with Session(engine) as session:
        user = User(
            email="staff@test.com", 
            password_hash="hashed_password",
            role=UserRole.STAFF
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

@pytest.fixture
def owner_token(owner_user):
    """Create access token for owner user"""
    return create_access_token(data={"sub": str(owner_user.id), "role": owner_user.role})

@pytest.fixture
def staff_token(staff_user):
    """Create access token for staff user"""
    return create_access_token(data={"sub": str(staff_user.id), "role": staff_user.role})

def test_create_connector_owner_success(owner_token):
    """Test that owner can create a connector"""
    response = client.post(
        "/connectors/",
        json={
            "provider": "SHOPIFY",
            "config": {"access_token": "test_token"}
        },
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "SHOPIFY"
    assert data["status"] == "PENDING"

def test_create_connector_staff_forbidden(staff_token):
    """Test that staff cannot create a connector"""
    response = client.post(
        "/connectors/",
        json={
            "provider": "SHOPIFY", 
            "config": {"access_token": "test_token"}
        },
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert response.status_code == 403

def test_list_connectors_owner(owner_token):
    """Test that owner can list their connectors"""
    response = client.get(
        "/connectors/",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_csv_upload_owner_success(owner_token):
    """Test CSV upload functionality for owner"""
    # Create a test CSV file
    csv_content = "sku,name,quantity\nTEST001,Test Product,10\nTEST002,Another Product,5"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        f.flush()
        
        with open(f.name, 'rb') as csv_file:
            response = client.post(
                "/connectors/csv/upload",
                files={"file": ("test.csv", csv_file, "text/csv")},
                data={
                    "sku_column": "sku",
                    "name_column": "name", 
                    "on_hand_column": "quantity"
                },
                headers={"Authorization": f"Bearer {owner_token}"}
            )
    
    # Cleanup
    os.unlink(f.name)
    
    assert response.status_code == 200
    data = response.json()
    assert "imported_items" in data
    assert "updated_items" in data

def test_csv_upload_staff_forbidden(staff_token):
    """Test that staff cannot upload CSV"""
    csv_content = "sku,name,quantity\nTEST001,Test Product,10"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        f.flush()
 