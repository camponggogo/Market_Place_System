"""
Tests for Payment Hub API
"""
import pytest


def test_use_foodcourt_id(client):
    """Test using Food Court ID at store"""
    # Create Food Court ID
    exchange_response = client.post(
        "/api/counter/exchange",
        json={
            "amount": 1000.00,
            "payment_method": "cash",
            "counter_id": 1,
            "counter_user_id": 1
        }
    )
    foodcourt_id = exchange_response.json()["foodcourt_id"]
    
    # Use at store
    response = client.post(
        "/api/payment-hub/use",
        json={
            "foodcourt_id": foodcourt_id,
            "store_id": 1,
            "amount": 250.00
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["remaining_balance"] == 750.00


def test_use_foodcourt_id_insufficient_balance(client):
    """Test using Food Court ID with insufficient balance"""
    # Create Food Court ID with small amount
    exchange_response = client.post(
        "/api/counter/exchange",
        json={
            "amount": 100.00,
            "payment_method": "cash",
            "counter_id": 1,
            "counter_user_id": 1
        }
    )
    foodcourt_id = exchange_response.json()["foodcourt_id"]
    
    # Try to use more than available
    response = client.post(
        "/api/payment-hub/use",
        json={
            "foodcourt_id": foodcourt_id,
            "store_id": 1,
            "amount": 200.00
        }
    )
    
    assert response.status_code == 400
    assert "Insufficient balance" in response.json()["detail"]


def test_use_foodcourt_id_not_found(client):
    """Test using non-existent Food Court ID"""
    response = client.post(
        "/api/payment-hub/use",
        json={
            "foodcourt_id": "FC-99999999-99999",
            "store_id": 1,
            "amount": 100.00
        }
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()

