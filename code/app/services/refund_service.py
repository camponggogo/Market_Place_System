"""
Refund Service - ระบบจัดการการคืนเงิน (E-Money Guard)
"""
from datetime import datetime, time
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import (
    Customer, CustomerBalance, RefundRequest, RefundNotification,
    RefundMethod, TransactionStatus
)
from app.config import (
    HAS_E_MONEY_LICENSE, AUTO_REFUND_ENABLED, REFUND_NOTIFICATION_TIME,
    DAILY_BALANCE_RESET
)
import logging

logger = logging.getLogger(__name__)


class RefundService:
    """Service for handling refund logic with E-Money compliance"""

    def __init__(self, db: Session):
        self.db = db

    def check_and_send_refund_notification(self, customer_id: int) -> Optional[RefundNotification]:
        """
        ตรวจสอบและส่งการแจ้งเตือนคืนเงินให้ลูกค้า
        ทำงานตาม Configurable E-Money Guard
        """
        if HAS_E_MONEY_LICENSE:
            # ถ้ามีใบอนุญาต e-Money ไม่ต้องแจ้งเตือน
            return None

        if not AUTO_REFUND_ENABLED:
            return None

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None

        balance = self.db.query(CustomerBalance).filter(
            CustomerBalance.customer_id == customer_id
        ).first()

        if not balance or balance.balance <= 0:
            return None

        # ตรวจสอบว่ามีการแจ้งเตือนแล้วหรือยัง
        today = datetime.now().date()
        existing_notification = self.db.query(RefundNotification).filter(
            RefundNotification.customer_id == customer_id,
            RefundNotification.created_at >= datetime.combine(today, time.min)
        ).first()

        if existing_notification:
            return existing_notification

        # สร้างการแจ้งเตือนใหม่
        notification = RefundNotification(
            customer_id=customer_id,
            balance_amount=balance.balance,
            notification_sent=False
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        # ส่งการแจ้งเตือน (จะต้องเชื่อมต่อกับ LINE OA หรือ Push Notification)
        self._send_refund_notification(customer, balance.balance, notification.id)

        return notification

    def _send_refund_notification(self, customer: Customer, amount: float, notification_id: int):
        """
        ส่งการแจ้งเตือนให้ลูกค้า (LINE OA / Push Notification)
        """
        try:
            # TODO: Implement LINE OA notification
            # TODO: Implement Push Notification
            
            notification = self.db.query(RefundNotification).filter(
                RefundNotification.id == notification_id
            ).first()
            
            if notification:
                notification.notification_sent = True
                notification.notification_sent_at = datetime.now()
                self.db.commit()

            logger.info(f"Refund notification sent to customer {customer.id} for amount {amount}")
        except Exception as e:
            logger.error(f"Error sending refund notification: {e}")

    def create_refund_request(
        self,
        customer_id: int,
        amount: float,
        refund_method: RefundMethod,
        promptpay_number: Optional[str] = None
    ) -> RefundRequest:
        """
        สร้างคำขอคืนเงิน (Self-Service Refund)
        """
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError("Customer not found")

        balance = self.db.query(CustomerBalance).filter(
            CustomerBalance.customer_id == customer_id
        ).first()

        if not balance or balance.balance < amount:
            raise ValueError("Insufficient balance")

        # สร้างคำขอคืนเงิน
        refund_request = RefundRequest(
            customer_id=customer_id,
            amount=amount,
            refund_method=refund_method,
            promptpay_number=promptpay_number or customer.promptpay_number,
            status="pending"
        )
        self.db.add(refund_request)
        self.db.commit()
        self.db.refresh(refund_request)

        # อัพเดทสถานะการแจ้งเตือน
        notification = self.db.query(RefundNotification).filter(
            RefundNotification.customer_id == customer_id,
            RefundNotification.refund_requested == False
        ).order_by(RefundNotification.created_at.desc()).first()

        if notification:
            notification.refund_requested = True
            self.db.commit()

        return refund_request

    def process_refund(self, refund_request_id: int) -> RefundRequest:
        """
        ประมวลผลการคืนเงิน
        """
        refund_request = self.db.query(RefundRequest).filter(
            RefundRequest.id == refund_request_id
        ).first()

        if not refund_request:
            raise ValueError("Refund request not found")

        if refund_request.status != "pending":
            raise ValueError(f"Refund request already {refund_request.status}")

        customer = self.db.query(Customer).filter(
            Customer.id == refund_request.customer_id
        ).first()

        balance = self.db.query(CustomerBalance).filter(
            CustomerBalance.customer_id == refund_request.customer_id
        ).first()

        if not balance or balance.balance < refund_request.amount:
            refund_request.status = "failed"
            self.db.commit()
            raise ValueError("Insufficient balance")

        # ประมวลผลการคืนเงินตามวิธีที่เลือก
        if refund_request.refund_method == RefundMethod.PROMPTPAY:
            # TODO: Integrate with PromptPay API
            success = self._process_promptpay_refund(
                refund_request.promptpay_number,
                refund_request.amount
            )
        else:
            # Cash refund - ต้องไปรับที่เคาน์เตอร์
            success = True

        if success:
            # ลดยอดเงินในบัญชี
            balance.balance -= refund_request.amount
            refund_request.status = "completed"
            refund_request.processed_at = datetime.now()
            self.db.commit()
        else:
            refund_request.status = "failed"
            self.db.commit()

        return refund_request

    def _process_promptpay_refund(self, promptpay_number: str, amount: float) -> bool:
        """
        ประมวลผลการคืนเงินผ่าน PromptPay
        """
        # TODO: Integrate with PromptPay API
        try:
            # Simulate API call
            logger.info(f"Processing PromptPay refund: {promptpay_number}, Amount: {amount}")
            return True
        except Exception as e:
            logger.error(f"Error processing PromptPay refund: {e}")
            return False

    def daily_balance_reset(self):
        """
        รีเซ็ตยอดเงินทุกสิ้นวัน (เมื่อไม่มีใบอนุญาต e-Money)
        """
        if HAS_E_MONEY_LICENSE:
            return  # ไม่ต้องรีเซ็ตถ้ามีใบอนุญาต

        if not DAILY_BALANCE_RESET:
            return

        # หาลูกค้าทั้งหมดที่มียอดเงินคงเหลือ
        balances = self.db.query(CustomerBalance).filter(
            CustomerBalance.balance > 0
        ).all()

        reset_count = 0
        for balance in balances:
            # ส่งการแจ้งเตือนก่อนรีเซ็ต
            if balance.balance > 0:
                self.check_and_send_refund_notification(balance.customer_id)
            
            # รีเซ็ตยอดเป็น 0
            balance.balance = 0
            balance.last_reset_date = datetime.now()
            reset_count += 1

        self.db.commit()
        logger.info(f"Daily balance reset completed. Reset {reset_count} customer balances.")

    def get_customer_balance(self, customer_id: int) -> Optional[CustomerBalance]:
        """
        ดึงยอดเงินคงเหลือของลูกค้า
        """
        return self.db.query(CustomerBalance).filter(
            CustomerBalance.customer_id == customer_id
        ).first()

    def get_pending_refund_requests(self) -> List[RefundRequest]:
        """
        ดึงคำขอคืนเงินที่รอการประมวลผล
        """
        return self.db.query(RefundRequest).filter(
            RefundRequest.status == "pending"
        ).all()

