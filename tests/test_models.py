"""
Tests for Database Models
"""
import pytest
from app.models import (
    PaymentMethod, Customer, CustomerBalance, 
    FoodCourtID, Store, Transaction
)


def test_payment_method_enum():
    """Test PaymentMethod enum values"""
    assert PaymentMethod.CASH.value == "cash"
    assert PaymentMethod.LINE_PAY.value == "line_pay"
    assert PaymentMethod.APPLE_PAY.value == "apple_pay"
    assert PaymentMethod.SAMSUNG_PAY.value == "samsung_pay"


def test_create_customer(db_session):
    """Test creating a customer"""
    customer = Customer(
        phone="0812345678",
        name="Test Customer",
        promptpay_number="0812345678"
    )
    db_session.add(customer)
    db_session.commit()
    
    assert customer.id is not None
    assert customer.phone == "0812345678"
    assert customer.name == "Test Customer"


def test_create_store(db_session):
    """Test creating a store"""
    store = Store(
        name="Test Store",
        tax_id="1234567890123",
        crypto_enabled=False,
        contract_accepted=False
    )
    db_session.add(store)
    db_session.commit()
    
    assert store.id is not None
    assert store.name == "Test Store"


def test_create_foodcourt_id(db_session):
    """Test creating Food Court ID"""
    foodcourt_id = FoodCourtID(
        foodcourt_id="FC-20241201-12345",
        initial_amount=1000.00,
        current_balance=1000.00,
        payment_method=PaymentMethod.CASH,
        status="active"
    )
    db_session.add(foodcourt_id)
    db_session.commit()
    
    assert foodcourt_id.foodcourt_id == "FC-20241201-12345"
    assert foodcourt_id.initial_amount == 1000.00
    assert foodcourt_id.current_balance == 1000.00

