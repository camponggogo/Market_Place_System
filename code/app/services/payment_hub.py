"""
Payment Hub Service - ระบบจัดการการชำระเงินหลายรูปแบบ
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models import (
    PaymentMethod, FoodCourtID, CounterTransaction, StoreTransaction,
    Customer, CustomerBalance, Transaction, TransactionStatus
)
from datetime import datetime
import uuid
import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PaymentHub:
    """Payment Hub สำหรับจัดการการชำระเงินหลายรูปแบบ"""

    def __init__(self, db: Session):
        self.db = db

    def generate_foodcourt_id(self) -> str:
        """
        สร้าง Food Court ID
        รูปแบบ: FC-YYYYMMDD-XXXXX
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        
        # สุ่มตัวเลข 5 หลัก
        random_part = str(uuid.uuid4().int)[:5].zfill(5)
        
        return f"FC-{date_str}-{random_part}"

    def exchange_to_foodcourt_id(
        self,
        amount: float,
        payment_method: PaymentMethod,
        payment_details: Optional[Dict[str, Any]] = None,
        counter_id: Optional[int] = None,
        counter_user_id: Optional[int] = None,
        customer_id: Optional[int] = None
    ) -> FoodCourtID:
        """
        แลก Food Court ID ที่ Counter
        รองรับทั้งรูปแบบที่ 1 (เงินสดเท่านั้น) และรูปแบบที่ 2 (หลายรูปแบบ)
        """
        # สร้าง Food Court ID
        foodcourt_id_str = self.generate_foodcourt_id()
        
        # ตรวจสอบว่า ID ไม่ซ้ำ
        while self.db.query(FoodCourtID).filter(
            FoodCourtID.foodcourt_id == foodcourt_id_str
        ).first():
            foodcourt_id_str = self.generate_foodcourt_id()

        # สร้าง Food Court ID record
        foodcourt_id = FoodCourtID(
            foodcourt_id=foodcourt_id_str,
            customer_id=customer_id,
            initial_amount=amount,
            current_balance=amount,
            payment_method=payment_method,
            payment_details=json.dumps(payment_details) if payment_details else None,
            counter_id=counter_id,
            counter_user_id=counter_user_id,
            status="active"
        )
        self.db.add(foodcourt_id)
        self.db.commit()
        self.db.refresh(foodcourt_id)

        # บันทึก Counter Transaction
        counter_transaction = CounterTransaction(
            foodcourt_id=foodcourt_id_str,
            counter_id=counter_id or 0,
            counter_user_id=counter_user_id or 0,
            amount=amount,
            payment_method=payment_method,
            payment_details=json.dumps(payment_details) if payment_details else None,
            status="completed"
        )
        self.db.add(counter_transaction)
        self.db.commit()

        logger.info(f"Food Court ID created: {foodcourt_id_str}, Amount: {amount}, Method: {payment_method.value}")

        return foodcourt_id

    def use_foodcourt_id(
        self,
        foodcourt_id_str: str,
        store_id: int,
        amount: float
    ) -> Dict[str, Any]:
        """
        ใช้ Food Court ID ที่ร้านค้า (หักยอดเงิน)
        """
        foodcourt_id = self.db.query(FoodCourtID).filter(
            FoodCourtID.foodcourt_id == foodcourt_id_str,
            FoodCourtID.status == "active"
        ).first()

        if not foodcourt_id:
            raise ValueError("Food Court ID not found or inactive")

        if foodcourt_id.current_balance < amount:
            raise ValueError(f"Insufficient balance. Current balance: {foodcourt_id.current_balance}")

        # หักยอดเงิน
        foodcourt_id.current_balance -= amount
        foodcourt_id.updated_at = datetime.now()
        
        # ถ้ายอดเงินเหลือ 0 ให้เปลี่ยน status
        if foodcourt_id.current_balance <= 0:
            foodcourt_id.status = "used"

        self.db.commit()
        self.db.refresh(foodcourt_id)

        # บันทึก Store Transaction
        store_transaction = StoreTransaction(
            foodcourt_id=foodcourt_id_str,
            store_id=store_id,
            amount=amount,
            status="completed"
        )
        self.db.add(store_transaction)
        self.db.commit()

        # สร้าง Transaction record (ถ้ามี customer_id)
        transaction = None
        if foodcourt_id.customer_id:
            transaction = Transaction(
                customer_id=foodcourt_id.customer_id,
                store_id=store_id,
                amount=amount,
                payment_method=foodcourt_id.payment_method,
                status=TransactionStatus.CONFIRMED,
                receipt_number=self._generate_receipt_number(),
                foodcourt_id=foodcourt_id_str
            )
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)

        logger.info(f"Food Court ID used: {foodcourt_id_str}, Store: {store_id}, Amount: {amount}")

        return {
            "foodcourt_id": foodcourt_id_str,
            "remaining_balance": foodcourt_id.current_balance,
            "transaction_id": transaction.id if transaction else None
        }

    def refund_remaining_balance(
        self,
        foodcourt_id_str: str,
        counter_id: Optional[int] = None,
        counter_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        คืนเงินที่เหลือที่ Counter
        """
        foodcourt_id = self.db.query(FoodCourtID).filter(
            FoodCourtID.foodcourt_id == foodcourt_id_str
        ).first()

        if not foodcourt_id:
            raise ValueError("Food Court ID not found")

        if foodcourt_id.status == "refunded":
            raise ValueError("Food Court ID already refunded")

        if foodcourt_id.current_balance <= 0:
            raise ValueError("No balance to refund")

        refund_amount = foodcourt_id.current_balance

        # อัพเดท status
        foodcourt_id.status = "refunded"
        foodcourt_id.current_balance = 0
        foodcourt_id.updated_at = datetime.now()

        self.db.commit()

        logger.info(f"Refunded Food Court ID: {foodcourt_id_str}, Amount: {refund_amount}")

        return {
            "foodcourt_id": foodcourt_id_str,
            "refund_amount": refund_amount,
            "original_payment_method": foodcourt_id.payment_method.value
        }

    def get_foodcourt_id_balance(self, foodcourt_id_str: str) -> Optional[Dict[str, Any]]:
        """
        ตรวจสอบยอดเงินคงเหลือของ Food Court ID
        """
        try:
            logger.info(f"Getting balance for Food Court ID: {foodcourt_id_str}")
            foodcourt_id = self.db.query(FoodCourtID).filter(
                FoodCourtID.foodcourt_id == foodcourt_id_str
            ).first()

            if not foodcourt_id:
                logger.warning(f"Food Court ID not found: {foodcourt_id_str}")
                return None

            result = {
                "foodcourt_id": foodcourt_id.foodcourt_id,
                "initial_amount": float(foodcourt_id.initial_amount),
                "current_balance": float(foodcourt_id.current_balance),
                "status": foodcourt_id.status,
                "payment_method": foodcourt_id.payment_method.value,
                "created_at": foodcourt_id.created_at.isoformat() if foodcourt_id.created_at else None
            }
            
            logger.info(f"Balance info retrieved: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting balance for {foodcourt_id_str}: {str(e)}", exc_info=True)
            raise

    def _generate_receipt_number(self) -> str:
        """
        สร้างเลขที่ใบเสร็จ
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        
        # นับจำนวน transactions ในวันนี้
        today_start = datetime.combine(now.date(), datetime.min.time())
        count = self.db.query(Transaction).filter(
            Transaction.created_at >= today_start
        ).count()
        
        sequence = str(count + 1).zfill(5)
        return f"RCP-{date_str}-{sequence}"

    def get_payment_method_info(self, payment_method: PaymentMethod) -> Dict[str, Any]:
        """
        ดึงข้อมูล Payment Method
        """
        method_info = {
            # Cash
            PaymentMethod.CASH: {
                "name": "เงินสด",
                "name_en": "Cash",
                "type": "cash",
                "requires_gateway": False,
                "region": "global"
            },
            
            # Credit Cards
            PaymentMethod.CREDIT_CARD_VISA: {
                "name": "บัตรเครดิต Visa",
                "name_en": "Visa Credit Card",
                "type": "card",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CREDIT_CARD_MASTERCARD: {
                "name": "บัตรเครดิต Mastercard",
                "name_en": "Mastercard Credit Card",
                "type": "card",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CREDIT_CARD_AMEX: {
                "name": "บัตรเครดิต American Express",
                "name_en": "American Express",
                "type": "card",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CREDIT_CARD_JCB: {
                "name": "บัตรเครดิต JCB",
                "name_en": "JCB Credit Card",
                "type": "card",
                "requires_gateway": True,
                "region": "asia"
            },
            PaymentMethod.CREDIT_CARD_UNIONPAY: {
                "name": "บัตรเครดิต UnionPay",
                "name_en": "UnionPay Credit Card",
                "type": "card",
                "requires_gateway": True,
                "region": "asia"
            },
            
            # Digital Wallets - Thailand
            PaymentMethod.TRUE_WALLET: {
                "name": "True Wallet",
                "name_en": "True Wallet",
                "type": "wallet",
                "requires_gateway": True,
                "region": "thailand"
            },
            PaymentMethod.PROMPTPAY: {
                "name": "PromptPay",
                "name_en": "PromptPay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "thailand"
            },
            PaymentMethod.LINE_PAY: {
                "name": "LINE Pay",
                "name_en": "LINE Pay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "asia"
            },
            PaymentMethod.RABBIT_LINE_PAY: {
                "name": "Rabbit LINE Pay",
                "name_en": "Rabbit LINE Pay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "thailand"
            },
            PaymentMethod.SHOPEE_PAY: {
                "name": "ShopeePay",
                "name_en": "ShopeePay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "asia"
            },
            PaymentMethod.GRAB_PAY: {
                "name": "GrabPay",
                "name_en": "GrabPay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "asia"
            },
            
            # Digital Wallets - International
            PaymentMethod.APPLE_PAY: {
                "name": "Apple Pay",
                "name_en": "Apple Pay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.GOOGLE_PAY: {
                "name": "Google Pay",
                "name_en": "Google Pay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.SAMSUNG_PAY: {
                "name": "Samsung Pay",
                "name_en": "Samsung Pay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.ALIPAY: {
                "name": "Alipay",
                "name_en": "Alipay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "china"
            },
            PaymentMethod.WECHAT_PAY: {
                "name": "WeChat Pay",
                "name_en": "WeChat Pay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "china"
            },
            PaymentMethod.PAYPAL: {
                "name": "PayPal",
                "name_en": "PayPal",
                "type": "wallet",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.AMAZON_PAY: {
                "name": "Amazon Pay",
                "name_en": "Amazon Pay",
                "type": "wallet",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.VENMO: {
                "name": "Venmo",
                "name_en": "Venmo",
                "type": "wallet",
                "requires_gateway": True,
                "region": "usa"
            },
            PaymentMethod.ZELLE: {
                "name": "Zelle",
                "name_en": "Zelle",
                "type": "wallet",
                "requires_gateway": True,
                "region": "usa"
            },
            PaymentMethod.CASH_APP: {
                "name": "Cash App",
                "name_en": "Cash App",
                "type": "wallet",
                "requires_gateway": True,
                "region": "usa"
            },
            
            # Bank Transfers
            PaymentMethod.BANK_TRANSFER: {
                "name": "โอนเงินผ่านธนาคาร",
                "name_en": "Bank Transfer",
                "type": "bank_transfer",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.WIRE_TRANSFER: {
                "name": "Wire Transfer",
                "name_en": "Wire Transfer",
                "type": "bank_transfer",
                "requires_gateway": True,
                "region": "global"
            },
            
            # Cryptocurrency
            PaymentMethod.CRYPTO_BTC: {
                "name": "Bitcoin (BTC)",
                "name_en": "Bitcoin (BTC)",
                "type": "crypto",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CRYPTO_ETH: {
                "name": "Ethereum (ETH)",
                "name_en": "Ethereum (ETH)",
                "type": "crypto",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CRYPTO_XRP: {
                "name": "Ripple (XRP)",
                "name_en": "Ripple (XRP)",
                "type": "crypto",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CRYPTO_BITKUB: {
                "name": "Bitkub Token",
                "name_en": "Bitkub Token",
                "type": "crypto",
                "requires_gateway": True,
                "region": "thailand"
            },
            PaymentMethod.CRYPTO_BINANCE: {
                "name": "Binance Coin (BNB)",
                "name_en": "Binance Coin (BNB)",
                "type": "crypto",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CRYPTO_SOLANA: {
                "name": "Solana (SOL)",
                "name_en": "Solana (SOL)",
                "type": "crypto",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CRYPTO_USDT: {
                "name": "Tether (USDT)",
                "name_en": "Tether (USDT)",
                "type": "crypto",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CRYPTO_USDC: {
                "name": "USD Coin (USDC)",
                "name_en": "USD Coin (USDC)",
                "type": "crypto",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.CRYPTO_CUSTOM: {
                "name": "Custom Crypto Token",
                "name_en": "Custom Crypto Token",
                "type": "crypto",
                "requires_gateway": True,
                "region": "global"
            },
            
            # Points & Rewards
            PaymentMethod.POINTS_THE1: {
                "name": "The 1 Card Points",
                "name_en": "The 1 Card Points",
                "type": "points",
                "requires_gateway": True,
                "region": "thailand"
            },
            PaymentMethod.POINTS_BLUECARD: {
                "name": "BlueCard Points",
                "name_en": "BlueCard Points",
                "type": "points",
                "requires_gateway": True,
                "region": "thailand"
            },
            PaymentMethod.POINTS_CREDIT_CARD: {
                "name": "Credit Card Points",
                "name_en": "Credit Card Points",
                "type": "points",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.POINTS_AIRLINE: {
                "name": "Airline Miles",
                "name_en": "Airline Miles",
                "type": "points",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.POINTS_HOTEL: {
                "name": "Hotel Points",
                "name_en": "Hotel Points",
                "type": "points",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.POINTS_CUSTOM: {
                "name": "Custom Points",
                "name_en": "Custom Points",
                "type": "points",
                "requires_gateway": True,
                "region": "global"
            },
            
            # Vouchers & Coupons
            PaymentMethod.VOUCHER: {
                "name": "Voucher",
                "name_en": "Voucher",
                "type": "voucher",
                "requires_gateway": False,
                "region": "global"
            },
            PaymentMethod.GIFT_CARD: {
                "name": "Gift Card",
                "name_en": "Gift Card",
                "type": "voucher",
                "requires_gateway": False,
                "region": "global"
            },
            PaymentMethod.COUPON: {
                "name": "Coupon",
                "name_en": "Coupon",
                "type": "voucher",
                "requires_gateway": False,
                "region": "global"
            },
            
            # Buy Now Pay Later
            PaymentMethod.BNPL_ATOME: {
                "name": "Atome",
                "name_en": "Atome",
                "type": "bnpl",
                "requires_gateway": True,
                "region": "asia"
            },
            PaymentMethod.BNPL_SPLIT: {
                "name": "Split",
                "name_en": "Split",
                "type": "bnpl",
                "requires_gateway": True,
                "region": "thailand"
            },
            PaymentMethod.BNPL_GRAB_PAYLATER: {
                "name": "Grab PayLater",
                "name_en": "Grab PayLater",
                "type": "bnpl",
                "requires_gateway": True,
                "region": "asia"
            },
            PaymentMethod.BNPL_AFFIRM: {
                "name": "Affirm",
                "name_en": "Affirm",
                "type": "bnpl",
                "requires_gateway": True,
                "region": "usa"
            },
            PaymentMethod.BNPL_KLARNA: {
                "name": "Klarna",
                "name_en": "Klarna",
                "type": "bnpl",
                "requires_gateway": True,
                "region": "global"
            },
            PaymentMethod.BNPL_AFTERPAY: {
                "name": "Afterpay",
                "name_en": "Afterpay",
                "type": "bnpl",
                "requires_gateway": True,
                "region": "global"
            },
            
            # Custom
            PaymentMethod.CUSTOM: {
                "name": "Custom Payment",
                "name_en": "Custom Payment",
                "type": "custom",
                "requires_gateway": True,
                "region": "global"
            }
        }

        return method_info.get(payment_method, {
            "name": payment_method.value,
            "name_en": payment_method.value,
            "type": "unknown",
            "requires_gateway": False,
            "region": "global"
        })

