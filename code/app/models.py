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


class User(Base):
    """ผู้ใช้สำหรับ Store POS - ล็อกอินก่อนเข้าใช้งาน"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)  # ผู้ดูแลระดับ admin ขึ้นไป (ดูย้อนหลัง backup ได้)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_stores = relationship("UserStore", back_populates="user", cascade="all, delete-orphan")


class UserStore(Base):
    """สิทธิ์ผู้ใช้ต่อร้าน - user มีสิทธิ์เข้า store ใดบ้าง"""
    __tablename__ = "user_store"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_stores")
    store = relationship("Store", back_populates="user_stores")


class Customer(Base):
    """ลูกค้า/สมาชิก - รองรับทั้งลูกค้าเดิม (เฉพาะเบอร์) และสมาชิกออนไลน์ (username/email/รหัสผ่าน)"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    line_user_id = Column(String(100), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=True)
    promptpay_number = Column(String(20), nullable=True)
    # สมาชิกออนไลน์: ชื่อผู้ใช้ 4 ตัวขึ้นไป, อีเมล (ถ้ามี), รหัสผ่าน
    username = Column(String(64), unique=True, index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    total_points = Column(Float, default=0.0, nullable=False)  # แต้มสะสม
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    balances = relationship("CustomerBalance", back_populates="customer", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    refund_requests = relationship("RefundRequest", back_populates="customer", cascade="all, delete-orphan")
    points_ledger = relationship("MemberPointsLedger", back_populates="customer", cascade="all, delete-orphan")
    member_vouchers = relationship("MemberVoucher", back_populates="customer", cascade="all, delete-orphan")
    e_coupons = relationship("ECoupon", back_populates="customer", foreign_keys="ECoupon.customer_id")
    activities = relationship("MemberActivity", back_populates="customer", cascade="all, delete-orphan")


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
    name_i18n = Column(Text, nullable=True)  # JSON: {"th":"ร้านอาหาร","en":"Restaurant"}
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

    # SCB PromptPay App (ต่อร้าน – ใช้กับ Store-POS / Webhook)
    scb_app_name = Column(String(64), nullable=True)       # App Name จาก SCB Developer
    scb_api_key = Column(String(128), nullable=True)      # API Key
    scb_api_secret = Column(String(255), nullable=True)  # API Secret
    scb_callback_url = Column(String(512), nullable=True) # Callback URL ลงทะเบียนกับ SCB

    # K Bank (K API) QR Payment – ต่อร้าน (apiportal.kasikornbank.com)
    kbank_customer_id = Column(String(128), nullable=True)      # Customer ID จาก K API
    kbank_consumer_secret = Column(String(255), nullable=True)   # Consumer Secret
    
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
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")
    promptpay_back_transactions = relationship("PromptPayBackTransaction", back_populates="store")
    store_settlements = relationship("StoreSettlement", back_populates="store")
    user_stores = relationship("UserStore", back_populates="store", cascade="all, delete-orphan")


class Order(Base):
    """
    Order - เก็บคำสั่งซื้อของแต่ละร้าน (Store POS) สำหรับสืบค้นย้อนหลัง
    ref2 ใน PromptPay QR = order.id เพื่อจับคู่เมื่อเงินเข้า
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, paid, cancelled
    items = Column(Text, nullable=True)  # JSON: [{ menu_id, name, qty, unit_price }]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    store = relationship("Store", back_populates="orders")


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


# ---------- ลูกค้าสมาชิกออนไลน์: แต้ม, คูปอง, อีคูปอง, โฆษณา, ประวัติ ----------

class MemberPointsLedger(Base):
    """สมุดแต้มสะสมลูกค้า"""
    __tablename__ = "member_points_ledger"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    points_delta = Column(Float, nullable=False)  # บวกหรือลบ
    balance_after = Column(Float, nullable=False)
    reason = Column(String(100), nullable=True)  # purchase, promo, redeem, admin
    ref_id = Column(Integer, nullable=True)  # order_id หรือ voucher_id ฯลฯ
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="points_ledger")


class VoucherDefinition(Base):
    """คำจำกัดความคูปอง/วoucher ที่ Admin กำหนด"""
    __tablename__ = "voucher_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    voucher_type = Column(String(50), default="discount", nullable=False)  # discount, free_item, percent
    value = Column(Float, nullable=False)  # จำนวนบาท หรือเปอร์เซ็น
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    store = relationship("Store", backref="voucher_definitions")
    member_vouchers = relationship("MemberVoucher", back_populates="voucher_definition")


class MemberVoucher(Base):
    """คูปองที่ลูกค้าได้รับ/ใช้"""
    __tablename__ = "member_vouchers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    voucher_definition_id = Column(Integer, ForeignKey("voucher_definitions.id"), nullable=False, index=True)
    code = Column(String(64), nullable=True, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="member_vouchers")
    voucher_definition = relationship("VoucherDefinition", back_populates="member_vouchers")


class StorePromotion(Base):
    """โปรโมชั่นร้านที่ Admin กำหนด แสดงในแอปสมาชิก"""
    __tablename__ = "store_promotions"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    store = relationship("Store", backref="store_promotions")


class ECoupon(Base):
    """อีคูปอง - ลูกค้าแลกด้วยเงินสด/PromptPay/บัตร/E-wallet แล้วนำไปจ่ายที่ร้านแทน PromptPay จริง"""
    __tablename__ = "e_coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    status = Column(String(20), default="available", nullable=False)  # available, assigned, used
    payment_method = Column(String(50), nullable=True)  # cash, promptpay, card, omise, stripe, ...
    paid_at = Column(DateTime(timezone=True), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)
    redeemed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="e_coupons", foreign_keys=[customer_id])
    order = relationship("Order", backref="e_coupon_payments")
    store = relationship("Store", backref="e_coupons")


class AdFeed(Base):
    """ฟีดโฆษณาแสดงในแอปสมาชิก - เลือกทุกร้าน (store_id=null) หรือเฉพาะร้านได้ ตั้งเวลา start_at/end_at ได้"""
    __tablename__ = "ad_feeds"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    image_url = Column(String(512), nullable=True)
    link_url = Column(String(512), nullable=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)  # null = ทุกร้าน
    start_at = Column(DateTime(timezone=True), nullable=True)   # เริ่มแสดง
    end_at = Column(DateTime(timezone=True), nullable=True)      # สิ้นสุดแสดง
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AdImpression(Base):
    """บันทึกการดู/กดโฆษณา สำหรับสรุปผลการตอบรับ"""
    __tablename__ = "ad_impressions"

    id = Column(Integer, primary_key=True, index=True)
    ad_feed_id = Column(Integer, ForeignKey("ad_feeds.id"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False)  # view, click
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MemberActivity(Base):
    """ประวัติการใช้งาน: เติมเงิน, จ่ายเงิน, ใช้คูปอง ฯลฯ"""
    __tablename__ = "member_activities"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)  # topup, payment, redeem, earn_points, use_voucher
    amount = Column(Float, nullable=True)
    description = Column(String(255), nullable=True)
    ref_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="activities")


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
    """Log ทุกการดำเนินการในระบบ เพื่อใช้เป็นหลักฐานอ้างอิง"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    source = Column(String(50), nullable=True, index=True)  # admin, store_pos, member, system
    action = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=True)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmergencyBackupEntry(Base):
    """รายการกรอกข้อมูลสำรอง กรณีไฟดับ/ระบบใช้งานไม่ได้ (บังคับ login admin เพื่อดูย้อนหลัง)"""
    __tablename__ = "emergency_backup_entries"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(20), nullable=False)  # 'admin' | 'store_pos'
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)
    entry_type = Column(String(50), nullable=False)  # sale, exchange, topup, other
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    entered_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    store = relationship("Store", backref="emergency_backup_entries")
    entered_by = relationship("User", backref="emergency_backup_entries")


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
    name = Column(String(255), nullable=False)  # ชื่อสินค้า (default/fallback)
    name_i18n = Column(Text, nullable=True)  # JSON: {"th":"ต้มยำ","en":"Tom Yum","zh":"冬阴功"}
    description = Column(Text, nullable=True)  # คำอธิบาย (default/fallback)
    description_i18n = Column(Text, nullable=True)  # JSON: {"th":"...","en":"..."}
    unit_price = Column(Float, nullable=False)  # ราคาสินค้าต่อ Unit
    image_url = Column(String(512), nullable=True)  # URL รูปสินค้า (จาก server/ภายนอก)
    image_local = Column(String(255), nullable=True)  # path local เช่น menu_images/1_5.jpg
    image_base64 = Column(Text, nullable=True)  # base64 รูปขนาด 480x640; MySQL ใช้ MEDIUMTEXT (migrate_image_base64_mediumtext)
    barcode = Column(String(64), nullable=True, index=True)  # บาร์โค้ดสำหรับสแกนค้นหา
    addon_options = Column(Text, nullable=True)  # JSON: [{ "name": "ไข่ดาว", "price": 10 }, { "name": "พิเศษ", "price": 20 }]
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    store = relationship("Store", back_populates="menus")
    price_logs = relationship("MenuPriceLog", back_populates="menu", cascade="all, delete-orphan")


class MenuPriceLog(Base):
    """เก็บราคาเดิมของเมนู/add-on ณ วันที่แก้ไข เพื่ออ้างอิงในรายการย้อนหลัง"""
    __tablename__ = "menu_price_logs"

    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False, index=True)
    unit_price = Column(Float, nullable=False)
    addon_options_json = Column(Text, nullable=True)  # JSON ณ เวลาที่บันทึก
    effective_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by_user_id = Column(Integer, nullable=True)

    menu = relationship("Menu", back_populates="price_logs")


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


# ค่าที่ใช้ใน BankingProfile.provider_type
PROVIDER_K_API = "k_api"           # K API ธนาคารกสิกรไทย
PROVIDER_SCB_DEEPLINK = "scb_deeplink"  # SCB Deeplink ธนาคารไทยพาณิชย์
PROVIDER_OMISE = "omise"           # Omise QR PromptPay (https://docs.omise.co)
PROVIDER_MPAY = "mpay"             # MPay QR PromptPay (AIS – ติดต่อ mPAY-Followup@ais.co.th)
PROVIDER_STRIPE = "stripe"         # Stripe QR PromptPay (https://docs.stripe.com/payments/promptpay)
PROVIDER_APPLE_PAY = "apple_pay"   # Apple Pay ผ่าน Stripe (https://docs.stripe.com/payments/apple-pay)


class BankingProfile(Base):
    """
    ตั้งค่า Payment Gateway / Bank API ต่อ Group, Site หรือ Store
    provider_type: k_api | scb_deeplink | omise | mpay | stripe (null = legacy SCB+K Bank)
    ลำดับการ resolve: store_id > site_id > group_id
    """
    __tablename__ = "banking_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    scope_type = Column(String(20), nullable=False)  # "group" | "site" | "store"
    group_id = Column(Integer, nullable=True, index=True)
    site_id = Column(Integer, nullable=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)

    # เลือกผู้ให้บริการ (null = ใช้ทั้ง SCB + K Bank แบบเดิม)
    provider_type = Column(String(32), nullable=True, index=True)

    # K API (ธนาคารกสิกรไทย)
    kbank_customer_id = Column(String(128), nullable=True)
    kbank_consumer_secret = Column(String(255), nullable=True)
    kbank_webhook_secret = Column(String(255), nullable=True)

    # SCB Deeplink (ธนาคารไทยพาณิชย์)
    scb_app_name = Column(String(64), nullable=True)
    scb_api_key = Column(String(128), nullable=True)
    scb_api_secret = Column(String(255), nullable=True)
    scb_callback_url = Column(String(512), nullable=True)
    scb_webhook_secret = Column(String(255), nullable=True)

    # Omise QR PromptPay (https://docs.omise.co/promptpay)
    omise_public_key = Column(String(255), nullable=True)
    omise_secret_key = Column(String(255), nullable=True)
    omise_webhook_secret = Column(String(255), nullable=True)

    # Stripe QR PromptPay (https://docs.stripe.com/payments/promptpay)
    stripe_secret_key = Column(String(255), nullable=True)
    stripe_publishable_key = Column(String(255), nullable=True)
    stripe_webhook_secret = Column(String(255), nullable=True)

    # MPay QR PromptPay (AIS – ขอ API จาก mPAY-Followup@ais.co.th)
    mpay_merchant_id = Column(String(128), nullable=True)
    mpay_api_key = Column(String(255), nullable=True)
    mpay_webhook_secret = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    store = relationship("Store", backref="banking_profile_store")


class Locale(Base):
    """ภาษาที่รองรับ: ไทย, อังกฤษ, ลาว, พม่า, กัมพูชา, มาลายู, ไทใหญ่, จีน, รัสเซีย"""
    __tablename__ = "locales"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # th, en, lo, my, kh, ms, shn, zh, ru
    name = Column(String(64), nullable=False)  # ชื่อภาษาในภาษานั้น


class Currency(Base):
    """หน่วยเงินที่รองรับ พร้อมสัญลักษณ์"""
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # THB, USD, LAK, MMK, KHR, MYR, CNY, RUB
    symbol = Column(String(16), nullable=False)  # ฿, $, ₭, K, ៛, RM, ¥, ₽
    name = Column(String(64), nullable=False)  # Baht, Dollar, Kip, Kyat, Riel, Ringgit, Yuan, Ruble


class AppSetting(Base):
    """ตั้งค่าระบบ: ภาษา, หน่วยเงิน (key-value) - ใช้เป็น default เมื่อร้านไม่มีตั้งค่า"""
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    value = Column(String(255), nullable=True)


class StoreLocaleSetting(Base):
    """ตั้งค่าภาษา/หน่วยเงินต่อร้าน - จดจำตาม store_id"""
    __tablename__ = "store_locale_settings"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, unique=True, index=True)
    locale = Column(String(10), nullable=False, default="th")
    currency_code = Column(String(10), nullable=False, default="THB")
    currency_symbol = Column(String(16), nullable=False, default="฿")
    currency_name = Column(String(64), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    store = relationship("Store", backref="locale_setting")


class Translation(Base):
    """คำแปล UI ตามภาษา (legacy - ใช้ program_settings แทน)"""
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    locale = Column(String(10), nullable=False, index=True)
    key = Column(String(128), nullable=False, index=True)
    value = Column(Text, nullable=False)

    __table_args__ = ({"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},)


class ProgramSetting(Base):
    """
    Labels/ข้อความที่ใช้ใน Web Application - แต่ละ row คือ label key
    แต่ละ column คือภาษาต่างๆ (th, en, lo, my, kh, ms, shn, zh, ru)
    """
    __tablename__ = "program_settings"

    id = Column(Integer, primary_key=True, index=True)
    label_key = Column(String(128), unique=True, nullable=False, index=True)  # key เช่น barcode_placeholder, store_pos
    label_th = Column(Text, nullable=True)   # ไทย
    label_en = Column(Text, nullable=True)    # English
    label_lo = Column(Text, nullable=True)    # ລາວ
    label_my = Column(Text, nullable=True)    # မြန်မာ
    label_kh = Column(Text, nullable=True)   # ខ្មែរ
    label_ms = Column(Text, nullable=True)   # Melayu
    label_shn = Column(Text, nullable=True)  # တႆး
    label_zh = Column(Text, nullable=True)   # 中文
    label_ru = Column(Text, nullable=True)   # Русский

    __table_args__ = ({"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},)
