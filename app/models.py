"""
Database models for Food Court System
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base


class RefundMethod(str, enum.Enum):
    CASH = "cash"
    PROMPTPAY = "promptpay"


class PaymentMethod(str, enum.Enum):
    # Cash
    CASH = "cash"
    
    # Credit Cards
    CREDIT_CARD_VISA = "credit_card_visa"
    CREDIT_CARD_MASTERCARD = "credit_card_mastercard"
    CREDIT_CARD_AMEX = "credit_card_amex"
    CREDIT_CARD_JCB = "credit_card_jcb"
    CREDIT_CARD_UNIONPAY = "credit_card_unionpay"
    
    # Digital Wallets - Thailand
    TRUE_WALLET = "true_wallet"
    PROMPTPAY = "promptpay"
    LINE_PAY = "line_pay"
    RABBIT_LINE_PAY = "rabbit_line_pay"
    SHOPEE_PAY = "shopee_pay"
    GRAB_PAY = "grab_pay"
    
    # Digital Wallets - International
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    SAMSUNG_PAY = "samsung_pay"
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    PAYPAL = "paypal"
    AMAZON_PAY = "amazon_pay"
    VENMO = "venmo"
    ZELLE = "zelle"
    CASH_APP = "cash_app"
    
    # Bank Transfers
    BANK_TRANSFER = "bank_transfer"
    WIRE_TRANSFER = "wire_transfer"
    
    # Cryptocurrency
    CRYPTO_BTC = "crypto_btc"
    CRYPTO_ETH = "crypto_eth"
    CRYPTO_XRP = "crypto_xrp"
    CRYPTO_BITKUB = "crypto_bitkub"
    CRYPTO_BINANCE = "crypto_binance"
    CRYPTO_SOLANA = "crypto_solana"
    CRYPTO_USDT = "crypto_usdt"
    CRYPTO_USDC = "crypto_usdc"
    CRYPTO_CUSTOM = "crypto_custom"
    
    # Points & Rewards
    POINTS_THE1 = "points_the1"
    POINTS_BLUECARD = "points_bluecard"
    POINTS_CREDIT_CARD = "points_credit_card"
    POINTS_AIRLINE = "points_airline"
    POINTS_HOTEL = "points_hotel"
    POINTS_CUSTOM = "points_custom"
    
    # Vouchers & Coupons
    VOUCHER = "voucher"
    GIFT_CARD = "gift_card"
    COUPON = "coupon"
    
    # Buy Now Pay Later
    BNPL_ATOME = "bnpl_atome"
    BNPL_SPLIT = "bnpl_split"
    BNPL_GRAB_PAYLATER = "bnpl_grab_paylater"
    BNPL_AFFIRM = "bnpl_affirm"
    BNPL_KLARNA = "bnpl_klarna"
    BNPL_AFTERPAY = "bnpl_afterpay"
    
    # Custom
    CUSTOM = "custom"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"


class CryptoTransactionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    line_user_id = Column(String(100), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=True)
    promptpay_number = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    balances = relationship("CustomerBalance", back_populates="customer", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    refund_requests = relationship("RefundRequest", back_populates="customer", cascade="all, delete-orphan")


class CustomerBalance(Base):
    __tablename__ = "customer_balances"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    last_reset_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="balances")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    receipt_number = Column(String(50), unique=True, index=True, nullable=False)
    qr_code = Column(Text, nullable=True)  # QR Code data for checking balance
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    foodcourt_id = Column(String(50), ForeignKey("foodcourt_ids.foodcourt_id"), nullable=True)  # Food Court ID ที่ใช้

    # PromptPay / Webhook (ref1=store token, ref2, ref3, เลขที่บัญชี)
    ref1 = Column(String(20), nullable=True, index=True)
    ref2 = Column(String(50), nullable=True)
    ref3 = Column(String(255), nullable=True)
    bank_account = Column(String(50), nullable=True)  # เลขที่บัญชี (จาก slip/callback)

    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    store = relationship("Store", back_populates="transactions")
    crypto_transaction = relationship("CryptoTransaction", back_populates="transaction", uselist=False)
    tax_invoice = relationship("TaxInvoice", back_populates="transaction", uselist=False)
    foodcourt_id_obj = relationship("FoodCourtID", foreign_keys=[foodcourt_id])


class CryptoTransaction(Base):
    __tablename__ = "crypto_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), unique=True, nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    tx_hash = Column(String(255), unique=True, index=True, nullable=False)
    blockchain_address = Column(String(255), nullable=False)
    amount_crypto = Column(Float, nullable=False)
    crypto_type = Column(String(50), default="BTC", nullable=False)
    status = Column(SQLEnum(CryptoTransactionStatus), default=CryptoTransactionStatus.PENDING)
    explorer_url = Column(Text, nullable=True)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transaction = relationship("Transaction", back_populates="crypto_transaction")
    store = relationship("Store", back_populates="crypto_transactions")


class Profile(Base):
    """
    Profile - สำหรับจัดการหลาย profile (เช่าล็อก, เช่าร้าน, จัดงาน event)
    """
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    profile_type = Column(String(50), nullable=False)  # "lock_rental", "store_rental", "event"
    is_active = Column(Boolean, default=True, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    stores = relationship("Store", back_populates="profile")
    events = relationship("Event", back_populates="profile")


class Event(Base):
    """
    Event - สำหรับจัดการงาน event
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="events")
    stores = relationship("Store", back_populates="event")


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(20), nullable=True)
    crypto_enabled = Column(Boolean, default=False, nullable=False)
    contract_accepted = Column(Boolean, default=False, nullable=False)
    contract_accepted_at = Column(DateTime(timezone=True), nullable=True)
    contract_version = Column(String(20), nullable=True)

    # Token ประจำร้าน 20 หลัก = group_id(3) + site_id(4) + store_id(6) + menu_id(7)
    group_id = Column(Integer, default=0, nullable=False)  # 3 digits
    site_id = Column(Integer, default=0, nullable=False)   # 4 digits
    token = Column(String(20), unique=True, index=True, nullable=True)  # 20-digit store token
    biller_id = Column(String(15), nullable=True)  # PromptPay Biller ID 15 หลัก (ใช้ใน QR Tag30)

    # Geo Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True)  # เช่น "ล็อก A1", "โซน 1"
    
    # Profile and Event
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="stores")
    event = relationship("Event", back_populates="stores")
    transactions = relationship("Transaction", back_populates="store")
    crypto_transactions = relationship("CryptoTransaction", back_populates="store")
    refund_requests = relationship("RefundRequest", back_populates="store")
    quick_amounts = relationship("StoreQuickAmount", back_populates="store", cascade="all, delete-orphan")
    menus = relationship("Menu", back_populates="store", cascade="all, delete-orphan")
    promptpay_back_transactions = relationship("PromptPayBackTransaction", back_populates="store")
    store_settlements = relationship("StoreSettlement", back_populates="store")


class RefundRequest(Base):
    __tablename__ = "refund_requests"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    amount = Column(Float, nullable=False)
    refund_method = Column(SQLEnum(RefundMethod), nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    promptpay_number = Column(String(20), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="refund_requests")
    store = relationship("Store", back_populates="refund_requests")


class RefundNotification(Base):
    __tablename__ = "refund_notifications"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    balance_amount = Column(Float, nullable=False)
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    refund_requested = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("Customer")


class TaxInvoice(Base):
    __tablename__ = "tax_invoices"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), unique=True, nullable=False)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    tax_id = Column(String(20), nullable=False)
    company_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    vat_amount = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=True)  # ระบุประเภทเงินที่รับมา
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    e_tax_sent = Column(Boolean, default=False, nullable=False)
    e_tax_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    transaction = relationship("Transaction", back_populates="tax_invoice")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=True)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FoodCourtID(Base):
    """
    Food Court ID - ระบบแลก Food Court ID ที่ Counter
    """
    __tablename__ = "foodcourt_ids"

    id = Column(Integer, primary_key=True, index=True)
    foodcourt_id = Column(String(50), unique=True, index=True, nullable=False)  # Food Court ID ที่ให้ลูกค้า
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # อาจจะยังไม่มี customer
    initial_amount = Column(Float, nullable=False)  # จำนวนเงินที่แลกมา
    current_balance = Column(Float, nullable=False)  # ยอดเงินคงเหลือ
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)  # วิธีชำระเงิน
    payment_details = Column(Text, nullable=True)  # JSON - รายละเอียดการชำระเงิน
    counter_id = Column(Integer, nullable=True)  # Counter ที่แลก
    counter_user_id = Column(Integer, nullable=True)  # User ที่แลกให้
    status = Column(String(50), default="active")  # active, used, refunded, expired
    expires_at = Column(DateTime(timezone=True), nullable=True)  # วันหมดอายุ (ถ้ามี)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    transactions = relationship("Transaction", back_populates="foodcourt_id_obj")


class PaymentGateway(Base):
    """
    Payment Gateway Configuration - สำหรับ Custom Payment Methods
    """
    __tablename__ = "payment_gateways"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # ชื่อ Payment Gateway
    payment_method = Column(String(50), nullable=False)  # Payment method code
    gateway_type = Column(String(50), nullable=False)  # cash, card, wallet, crypto, points, custom
    is_active = Column(Boolean, default=True, nullable=False)
    config = Column(Text, nullable=True)  # JSON - Configuration
    exchange_rate = Column(Float, default=1.0, nullable=False)  # อัตราแลกเปลี่ยน (ถ้ามี)
    points_per_baht = Column(Float, nullable=True)  # แต้มต่อบาท (สำหรับ points)
    created_by = Column(Integer, nullable=True)  # Admin user ที่สร้าง
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CounterTransaction(Base):
    """
    Counter Transaction - บันทึกการแลก Food Court ID ที่ Counter
    """
    __tablename__ = "counter_transactions"

    id = Column(Integer, primary_key=True, index=True)
    foodcourt_id = Column(String(50), ForeignKey("foodcourt_ids.foodcourt_id"), nullable=False)
    counter_id = Column(Integer, nullable=False)
    counter_user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    payment_details = Column(Text, nullable=True)  # JSON
    status = Column(String(50), default="completed")  # completed, failed, refunded
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    foodcourt_id_obj = relationship("FoodCourtID", foreign_keys=[foodcourt_id])


class StoreTransaction(Base):
    """
    Store Transaction - บันทึกการใช้งาน Food Court ID ที่ร้านค้า
    """
    __tablename__ = "store_transactions"

    id = Column(Integer, primary_key=True, index=True)
    foodcourt_id = Column(String(50), ForeignKey("foodcourt_ids.foodcourt_id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="completed")  # completed, failed, refunded
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    foodcourt_id_obj = relationship("FoodCourtID", foreign_keys=[foodcourt_id])
    store = relationship("Store")


class StoreQuickAmount(Base):
    """
    Store Quick Amount - ราคาด่วนสำหรับแต่ละร้านค้า
    """
    __tablename__ = "store_quick_amounts"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    label = Column(String(50), nullable=True)  # เช่น "50 บาท", "100 บาท" (optional)
    display_order = Column(Integer, default=0, nullable=False)  # สำหรับเรียงลำดับ
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    store = relationship("Store", back_populates="quick_amounts")


class Menu(Base):
    """
    Menu - รายการสินค้าของแต่ละร้านค้า
    """
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # ชื่อสินค้า
    description = Column(Text, nullable=True)  # คำอธิบายสินค้า
    unit_price = Column(Float, nullable=False)  # ราคาสินค้าต่อ Unit
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    store = relationship("Store", back_populates="menus")


class PromptPayBackTransaction(Base):
    """
    รับข้อมูล Back Transaction จากธนาคาร (Webhook/Callback ตาม SCB QR Payment)
    ใช้ ref1 (store token), ref2, ref3, ยอดเงิน, เวลา โอน เพื่อทำ Report และแจ้งร้าน
    อ้างอิง: https://developer.scb/ - QR Code Payment, Slip Verification
    """
    __tablename__ = "promptpay_back_transactions"

    id = Column(Integer, primary_key=True, index=True)
    ref1 = Column(String(20), nullable=False, index=True)   # store token (20 หลัก)
    ref2 = Column(String(50), nullable=True)                # menu id หรืออ้างอิง
    ref3 = Column(String(255), nullable=True)               # remark
    amount = Column(Float, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=False)  # เวลาที่โอน/ชำระ
    slip_reference = Column(String(100), nullable=True, index=True)  # เลขที่อ้างอิงจาก slip/bank
    bank_account = Column(String(50), nullable=True)  # เลขที่บัญชี (จาก slip/callback)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)  # ผูกจาก ref1
    status = Column(String(20), default="received")  # received, matched, settled, failed
    raw_payload = Column(Text, nullable=True)  # JSON จาก bank callback
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    store = relationship("Store", back_populates="promptpay_back_transactions")


class StoreSettlement(Base):
    """
    รายการเตรียมโอนเงินไปยังร้านค้า สิ้นวัน (ข้อกำหนดกฏหมาย: ถือฝากได้แค่ 1 วัน)
    ใช้ ref1/ref2/ref3 ยอดเงิน เวลาโอน แยกและแจ้งร้านว่าเงินเข้าเรียบร้อยแล้ว เพื่อพิมพ์ใบเสร็จรับเงิน
    """
    __tablename__ = "store_settlements"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    settlement_date = Column(DateTime(timezone=True), nullable=False)  # วันที่สรุป (สิ้นวัน)
    amount = Column(Float, nullable=False)  # ยอดคงเหลือที่ต้องโอน
    status = Column(String(20), default="pending")  # pending, transferred, notified
    transferred_at = Column(DateTime(timezone=True), nullable=True)  # เวลาที่โอนจริง
    notified_at = Column(DateTime(timezone=True), nullable=True)   # เวลาที่แจ้งร้าน (เงินเข้าเรียบร้อย)
    receipt_printed_at = Column(DateTime(timezone=True), nullable=True)  # ร้านพิมพ์ใบเสร็จรับเงินแล้ว (optional)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    store = relationship("Store", back_populates="store_settlements")
