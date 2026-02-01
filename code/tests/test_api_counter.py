"""
Tests for Counter API
"""
import pytest
from app.models import PaymentMethod


def test_exchange_foodcourt_id(client):
    """Test exchanging to Food Court ID via API"""
    response = client.post(
        "/api/counter/exchange",
        json={
            "amount": 1000.00,
            "payment_method": "cash",
            "counter_id": 1,
            "counter_user_id": 1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "foodcourt_id" in data
    assert data["amount"] == 1000.00
    assert data["payment_method"] == "cash"


def test_exchange_with_line_pay(client):
    """Test exchanging with LINE Pay"""
    response = client.post(
        "/api/counter/exchange",
        json={
            "amount": 500.00,
            "payment_method": "line_pay",
            "payment_details": {"transaction_id": "LP123456"},
            "counter_id": 1,
            "counter_user_id": 1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["payment_method"] == "line_pay"


def test_exchange_invalid_payment_method(client):
    """Test with invalid payment method"""
    response = client.post(
        "/api/counter/exchange",
        json={
            "amount": 1000.00,
            "payment_method": "invalid_method",
            "counter_id": 1,
            "counter_user_id": 1
        }
    )
    
    assert response.status_code == 400
    assert "Invalid payment method" in response.json()["detail"]


def test_get_balance(client):
    """Test getting Food Court ID balance"""
    # First create a Food Court ID
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
    
    # Get balance
    response = client.get(f"/api/counter/balance/{foodcourt_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["foodcourt_id"] == foodcourt_id
    assert data["current_balance"] == 1000.00


def test_get_balance_not_found(client):
    """Test getting balance for non-existent Food Court ID"""
    response = client.get("/api/counter/balance/FC-99999999-99999")
    
    assert response.status_code == 404


def test_refund_remaining_balance(client):
    """Test refunding remaining balance"""
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
    
    # Use some amount
    client.post(
        "/api/payment-hub/use",
        json={
            "foodcourt_id": foodcourt_id,
            "store_id": 1,
            "amount": 250.00
        }
    )
    
    # Refund
    response = client.post(
        "/api/counter/refund",
        json={
            "foodcourt_id": foodcourt_id,
            "counter_id": 1,
            "counter_user_id": 1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["refund_amount"] == 750.00


def test_get_payment_methods(client):
    """Test getting list of payment methods"""
    response = client.get("/api/counter/payment-methods")
    
    assert response.status_code == 200
    data = response.json()
    assert "payment_methods" in data
    assert len(data["payment_methods"]) > 0
    
    # Check for specific payment methods
    methods = {m["code"] for m in data["payment_methods"]}
    assert "cash" in methods
    assert "line_pay" in methods
    assert "apple_pay" in methods
    assert "samsung_pay" in methods

