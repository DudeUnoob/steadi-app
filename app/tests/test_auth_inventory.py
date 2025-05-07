import pytest
from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4
import os

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """Create a fixture to generate auth headers with test user token"""
    # First, create a test user if it doesn't exist
    signup_data = {
        "email": "test-owner@steadi.app",
        "password": "Test1234!",
        "role": "OWNER"
    }
    
    # Try to sign up (will fail if user already exists)
    signup_response = client.post("/auth/signup", json=signup_data)
    
    # Login and get token
    login_data = {
        "username": signup_data["email"],
        "password": signup_data["password"]
    }
    login_response = client.post("/auth/login", data=login_data)
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Return auth headers
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_user2():
    """Create a fixture for a second owner user to test data isolation"""
    # Create a second test user
    signup_data = {
        "email": "test-owner2@steadi.app",
        "password": "Test1234!",
        "role": "OWNER"
    }
    
    # Try to sign up
    signup_response = client.post("/auth/signup", json=signup_data)
    
    # Login and get token
    login_data = {
        "username": signup_data["email"],
        "password": signup_data["password"]
    }
    login_response = client.post("/auth/login", data=login_data)
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Return auth headers
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def staff_auth_headers():
    """Create a fixture to generate auth headers with staff role (lower privileges)"""
    # Create a test staff user
    signup_data = {
        "email": "test-staff@steadi.app",
        "password": "Test1234!",
        "role": "STAFF"
    }
    
    # Try to sign up
    signup_response = client.post("/auth/signup", json=signup_data)
    
    # Login and get token
    login_data = {
        "username": signup_data["email"],
        "password": signup_data["password"]
    }
    login_response = client.post("/auth/login", data=login_data)
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Return auth headers
    return {"Authorization": f"Bearer {token}"}

def test_inventory_endpoints_without_auth():
    """Test that inventory endpoints return 401 without authentication"""
    # Test GET /api/inventory
    response = client.get("/api/inventory")
    assert response.status_code == 401
    
    # Test GET /api/inventory/{sku}
    response = client.get("/api/inventory/TEST-SKU")
    assert response.status_code == 401
    
    # Test POST /api/inventory
    test_product = {
        "sku": f"TEST-{uuid4()}",
        "name": "Test Product",
        "supplier_id": str(uuid4()),
        "cost": 10.0,
        "on_hand": 5,
        "reorder_point": 2
    }
    response = client.post("/api/inventory", json=test_product)
    assert response.status_code == 401
    
    # Test PATCH /api/inventory/{sku}
    update_data = {"reorder_point": 10}
    response = client.patch("/api/inventory/TEST-SKU", json=update_data)
    assert response.status_code == 401
    
    # Test POST /api/inventory/{sku}/adjust
    adjust_data = {"quantity_delta": 5}
    response = client.post("/api/inventory/TEST-SKU/adjust", params=adjust_data)
    assert response.status_code == 401
    
    # Test GET /api/inventory/ledger/{product_id}
    response = client.get(f"/api/inventory/ledger/{uuid4()}")
    assert response.status_code == 401

def test_inventory_endpoints_with_auth(auth_headers):
    """Test that inventory endpoints work with proper authentication"""
    # Test GET /api/inventory
    response = client.get("/api/inventory", headers=auth_headers)
    assert response.status_code == 200
    assert "items" in response.json()
    
    # Other tests would follow similar pattern, but would need valid IDs
    # For a complete test suite, you would need to create test data first

def test_inventory_role_based_access(staff_auth_headers, auth_headers):
    """Test that inventory endpoints respect role-based access control"""
    # Staff should be able to view inventory
    response = client.get("/api/inventory", headers=staff_auth_headers)
    assert response.status_code == 200
    
    # Staff should NOT be able to create products
    test_product = {
        "sku": f"TEST-{uuid4()}",
        "name": "Test Product",
        "supplier_id": str(uuid4()),
        "cost": 10.0,
        "on_hand": 5,
        "reorder_point": 2
    }
    response = client.post("/api/inventory", json=test_product, headers=staff_auth_headers)
    assert response.status_code == 403  # Forbidden
    
    # Owner should be able to create products
    response = client.post("/api/inventory", json=test_product, headers=auth_headers)
    # This might fail with 400 if supplier_id doesn't exist, which is fine for this test
    assert response.status_code != 401 and response.status_code != 403

def test_data_isolation_between_users(auth_headers, auth_headers_user2):
    """Test that users can only access their own data"""
    # Create a supplier for testing
    supplier_data = {
        "name": "Test Supplier",
        "contact_email": "supplier@test.com",
        "lead_time_days": 7
    }
    
    # First, create a supplier (this might fail if already exists)
    try:
        supplier_response = client.post("/api/suppliers", json=supplier_data, headers=auth_headers)
        supplier_id = supplier_response.json().get("id")
    except:
        # If failed, get existing supplier
        suppliers_response = client.get("/api/suppliers", headers=auth_headers)
        if suppliers_response.status_code == 200 and len(suppliers_response.json().get("items", [])) > 0:
            supplier_id = suppliers_response.json()["items"][0]["id"]
        else:
            pytest.skip("Test requires a supplier to be available")
    
    # User 1 creates a product
    product_sku = f"TEST-ISOLATION-{uuid4()}"
    product_data = {
        "sku": product_sku,
        "name": "Test Isolation Product",
        "supplier_id": supplier_id,
        "cost": 15.0,
        "on_hand": 10,
        "reorder_point": 3
    }
    
    # User 1 creates product
    create_response = client.post("/api/inventory", json=product_data, headers=auth_headers)
    
    # Should succeed with 200 or 201
    assert create_response.status_code in [200, 201]
    
    # User 1 should be able to see this product
    get_response = client.get(f"/api/inventory/{product_sku}", headers=auth_headers)
    assert get_response.status_code == 200
    
    # User 2 should NOT be able to see User 1's product
    get_response2 = client.get(f"/api/inventory/{product_sku}", headers=auth_headers_user2)
    assert get_response2.status_code == 404
    
    # Verify that inventory list only shows user's own products
    list_response1 = client.get("/api/inventory", headers=auth_headers)
    list_response2 = client.get("/api/inventory", headers=auth_headers_user2)
    
    # Both should succeed
    assert list_response1.status_code == 200
    assert list_response2.status_code == 200
    
    # User 1's product list should include the test product
    product_found = False
    for product in list_response1.json()["items"]:
        if product["sku"] == product_sku:
            product_found = True
            break
    assert product_found
    
    # User 2's product list should NOT include User 1's product
    product_found = False
    for product in list_response2.json()["items"]:
        if product["sku"] == product_sku:
            product_found = True
            break
    assert not product_found 