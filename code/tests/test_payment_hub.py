"""
Tests for Payment Hub Service
"""
import pytest
from app.services.payment_hub import PaymentHub
from app.models import PaymentMethod, FoodCourtID, Customer, Store


def test_generate_foodcourt_id(db_session):
    """Test Food Court ID generation"""
    payment_hub = PaymentHub(db_session)
    foodcourt_id = payment_hub.generate_foodcourt_id()
    
    assert foodcourt_id.startswith("FC-")
    assert len(foodcourt_id) > 10


def test_exchange_to_foodcourt_id_cash(db_session):
    """Test exchanging cash to Food Court ID"""
    payment_hub = PaymentHub(db_session)
    
    foodcourt_id = payment_hub.exchange_to_foodcourt_id(
        amount=1000.00,
        payment_method=PaymentMethod.CASH,
        counter_id=1,
        counter_user_id=1
    )
    
    assert foodcourt_id.foodcourt_id.startswith("FC-")
    assert foodcourt_id.initial_amount == 1000.00
    assert foodcourt_id.current_balance == 1000.00
    assert foodcourt_id.payment_method == PaymentMethod.CASH
    assert foodcourt_id.status == "active"


def test_exchange_to_foodcourt_id_line_pay(db_session):
    """Test exchanging LINE Pay to Food Court ID"""
    payment_hub = PaymentHub(db_session)
    
    foodcourt_id = payment_hub.exchange_to_foodcourt_id(
        amount=500.00,
        payment_method=PaymentMethod.LINE_PAY,
        payment_details={"transaction_id": "LP123456"},
        counter_id=1,
        counter_user_id=1
    )
    
    assert foodcourt_id.payment_method == PaymentMethod.LINE_PAY
    assert foodcourt_id.initial_amount == 500.00


def test_use_foodcourt_id(db_session):
    """Test using Food Court ID at store"""
    payment_hub = PaymentHub(db_session)
    
    # Create Food Court ID
    foodcourt_id = payment_hub.exchange_to_foodcourt_id(
        amount=1000.00,
        payment_method=PaymentMethod.CASH,
        counter_id=1,
        counter_user_id=1
    )
    
    # Use at store
    result = payment_hub.use_foodcourt_id(
        foodcourt_id_str=foodcourt_id.foodcourt_id,
        store_id=1,
        amount=250.00
    )
    
    assert result["remaining_balance"] == 750.00
    
    # Check balance
    balance_info = payment_hub.get_foodcourt_id_balance(foodcourt_id.foodcourt_id)
    assert balance_info["current_balance"] == 750.00


def test_use_foodcourt_id_insufficient_balance(db_session):
    """Test using Food Court ID with insufficient balance"""
    payment_hub = PaymentHub(db_session)
    
    # Create Food Court ID with small amount
    foodcourt_id = payment_hub.exchange_to_foodcourt_id(
        amount=100.00,
        payment_method=PaymentMethod.CASH,
        counter_id=1,
        counter_user_id=1
    )
    
    # Try to use more than available
    with pytest.raises(ValueError, match="Insufficient balance"):
        payment_hub.use_foodcourt_id(
            foodcourt_id_str=foodcourt_id.foodcourt_id,
            store_id=1,
            amount=200.00
        )


def test_refund_remaining_balance(db_session):
    """Test refunding remaining balance"""
    payment_hub = PaymentHub(db_session)
    
    # Create Food Court ID
    foodcourt_id = payment_hub.exchange_to_foodcourt_id(
        amount=1000.00,
        payment_method=PaymentMethod.CASH,
        counter_id=1,
        counter_user_id=1
    )
    
    # Use some amount
    payment_hub.use_foodcourt_id(
        foodcourt_id_str=foodcourt_id.foodcourt_id,
        store_id=1,
        amount=250.00
    )
    
    # Refund remaining
    refund_info = payment_hub.refund_remaining_balance(
        foodcourt_id_str=foodcourt_id.foodcourt_id,
        counter_id=1,
        counter_user_id=1
    )
    
    assert refund_info["refund_amount"] == 750.00
    assert refund_info["original_payment_method"] == PaymentMethod.CASH.value
    
    # Check status
    balance_info = payment_hub.get_foodcourt_id_balance(foodcourt_id.foodcourt_id)
    assert balance_info["status"] == "refunded"


def test_get_payment_method_info(db_session):
    """Test getting payment method information"""
    payment_hub = PaymentHub(db_session)
    
    # Test cash
    cash_info = payment_hub.get_payment_method_info(PaymentMethod.CASH)
    assert cash_info["name"] == "เงินสด"
    assert cash_info["type"] == "cash"
    assert cash_info["requires_gateway"] == False
    
    # Test LINE Pay
    line_pay_info = payment_hub.get_payment_method_info(PaymentMethod.LINE_PAY)
    assert "LINE Pay" in line_pay_info["name"]
    assert line_pay_info["type"] == "wallet"
    assert line_pay_info["requires_gateway"] == True
    
    # Test Apple Pay
    apple_pay_info = payment_hub.get_payment_method_info(PaymentMethod.APPLE_PAY)
    assert apple_pay_info["name"] == "Apple Pay"
    assert apple_pay_info["region"] == "global"

