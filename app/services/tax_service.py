"""
Tax Service - ระบบจัดการภาษีและใบกำกับภาษี
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Transaction, TaxInvoice, PaymentMethod
from app.config import VAT_RATE, WHT_RATE, TAX_ID, COMPANY_NAME
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TaxService:
    """Service for handling tax calculations and invoices"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_vat(self, amount: float) -> Dict[str, float]:
        """
        คำนวณภาษีมูลค่าเพิ่ม (VAT)
        """
        vat_amount = amount * VAT_RATE
        total_amount = amount + vat_amount
        
        return {
            "amount": amount,
            "vat_rate": VAT_RATE,
            "vat_amount": round(vat_amount, 2),
            "total_amount": round(total_amount, 2)
        }

    def calculate_wht(self, amount: float) -> Dict[str, float]:
        """
        คำนวณภาษีหัก ณ ที่จ่าย (Withholding Tax) 3%
        """
        wht_amount = amount * WHT_RATE
        net_amount = amount - wht_amount
        
        return {
            "gross_amount": amount,
            "wht_rate": WHT_RATE,
            "wht_amount": round(wht_amount, 2),
            "net_amount": round(net_amount, 2)
        }

    def create_tax_invoice(
        self,
        transaction_id: int,
        invoice_number: Optional[str] = None
    ) -> TaxInvoice:
        """
        สร้างใบกำกับภาษีอย่างย่อ (ภ.พ. 89)
        พร้อมระบุประเภทเงินที่รับมา
        """
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()

        if not transaction:
            raise ValueError("Transaction not found")

        # ตรวจสอบว่ามีใบกำกับภาษีแล้วหรือยัง
        existing_invoice = self.db.query(TaxInvoice).filter(
            TaxInvoice.transaction_id == transaction_id
        ).first()

        if existing_invoice:
            return existing_invoice

        # สร้างเลขที่ใบกำกับภาษี
        if not invoice_number:
            invoice_number = self._generate_invoice_number()

        # คำนวณ VAT
        tax_calc = self.calculate_vat(transaction.amount)

        # ดึง Payment Method จาก Transaction หรือ Food Court ID
        payment_method = transaction.payment_method.value if transaction.payment_method else None
        
        # ถ้ามี Food Court ID ให้ดึง Payment Method จาก Food Court ID
        if transaction.foodcourt_id:
            from app.models import FoodCourtID
            foodcourt_id = self.db.query(FoodCourtID).filter(
                FoodCourtID.foodcourt_id == transaction.foodcourt_id
            ).first()
            if foodcourt_id:
                payment_method = foodcourt_id.payment_method.value

        # สร้างใบกำกับภาษี
        tax_invoice = TaxInvoice(
            transaction_id=transaction_id,
            invoice_number=invoice_number,
            tax_id=TAX_ID,
            company_name=COMPANY_NAME,
            amount=tax_calc["amount"],
            vat_amount=tax_calc["vat_amount"],
            total_amount=tax_calc["total_amount"],
            payment_method=payment_method  # ระบุประเภทเงินที่รับมา
        )
        self.db.add(tax_invoice)
        self.db.commit()
        self.db.refresh(tax_invoice)

        return tax_invoice

    def _generate_invoice_number(self) -> str:
        """
        สร้างเลขที่ใบกำกับภาษี
        รูปแบบ: INV-YYYYMMDD-XXXXX
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        
        # นับจำนวนใบกำกับภาษีในวันนี้
        today_start = datetime.combine(now.date(), datetime.min.time())
        count = self.db.query(TaxInvoice).filter(
            TaxInvoice.issued_at >= today_start
        ).count()
        
        sequence = str(count + 1).zfill(5)
        return f"INV-{date_str}-{sequence}"

    def generate_sales_tax_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        สร้างรายงานภาษีขาย (Sales Tax Report)
        """
        transactions = self.db.query(Transaction).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == "confirmed"
        ).all()

        # แยกตามประเภทการชำระเงิน
        cash_total = 0.0
        promptpay_total = 0.0
        credit_total = 0.0
        crypto_total = 0.0  # Information only, not included in revenue

        cash_count = 0
        promptpay_count = 0
        credit_count = 0
        crypto_count = 0

        for transaction in transactions:
            if transaction.payment_method == PaymentMethod.CASH:
                cash_total += transaction.amount
                cash_count += 1
            elif transaction.payment_method == PaymentMethod.PROMPTPAY:
                promptpay_total += transaction.amount
                promptpay_count += 1
            elif transaction.payment_method == PaymentMethod.CREDIT:
                credit_total += transaction.amount
                credit_count += 1
            elif transaction.payment_method == PaymentMethod.CRYPTO:
                crypto_total += transaction.amount
                crypto_count += 1

        # Revenue (ไม่รวม Crypto)
        total_revenue = cash_total + promptpay_total + credit_total
        
        # คำนวณ VAT
        vat_calc = self.calculate_vat(total_revenue)

        # คำนวณ WHT (ถ้ามีการโอนเงินให้ร้านค้า)
        wht_calc = self.calculate_wht(total_revenue)

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_transactions": len(transactions),
                "total_revenue": round(total_revenue, 2),
                "vat_amount": vat_calc["vat_amount"],
                "total_with_vat": vat_calc["total_amount"],
                "wht_amount": wht_calc["wht_amount"],
                "net_after_wht": wht_calc["net_amount"]
            },
            "by_payment_method": {
                "cash": {
                    "count": cash_count,
                    "amount": round(cash_total, 2)
                },
                "promptpay": {
                    "count": promptpay_count,
                    "amount": round(promptpay_total, 2)
                },
                "credit": {
                    "count": credit_count,
                    "amount": round(credit_total, 2)
                },
                "crypto": {
                    "count": crypto_count,
                    "amount": round(crypto_total, 2),
                    "note": "Information only - not included in revenue"
                }
            },
            "transactions": [
                {
                    "id": t.id,
                    "receipt_number": t.receipt_number,
                    "amount": t.amount,
                    "payment_method": t.payment_method.value,
                    "created_at": t.created_at.isoformat()
                }
                for t in transactions
            ]
        }

    def send_e_tax_invoice(self, tax_invoice_id: int) -> bool:
        """
        ส่งใบกำกับภาษีไปยัง E-Tax Invoice Provider
        """
        tax_invoice = self.db.query(TaxInvoice).filter(
            TaxInvoice.id == tax_invoice_id
        ).first()

        if not tax_invoice:
            raise ValueError("Tax invoice not found")

        try:
            # TODO: Integrate with E-Tax Invoice Provider API
            # ตัวอย่าง: ส่งข้อมูลไปยัง RD Smart หรือ Provider อื่น
            
            # Simulate API call
            logger.info(f"Sending E-Tax Invoice {tax_invoice.invoice_number} to provider")
            
            tax_invoice.e_tax_sent = True
            tax_invoice.e_tax_sent_at = datetime.now()
            self.db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error sending E-Tax Invoice: {e}")
            return False

    def get_separation_of_funds_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        รายงานแยกยอดเงินสด/โอน (Revenue) ออกจากยอด Crypto Status (Information Only)
        """
        transactions = self.db.query(Transaction).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).all()

        revenue_transactions = []
        crypto_info = []

        for transaction in transactions:
            if transaction.payment_method == PaymentMethod.CRYPTO:
                # Crypto - Information only
                crypto_info.append({
                    "transaction_id": transaction.id,
                    "receipt_number": transaction.receipt_number,
                    "amount": transaction.amount,
                    "status": transaction.status.value,
                    "created_at": transaction.created_at.isoformat(),
                    "crypto_tx_hash": transaction.crypto_transaction.tx_hash if transaction.crypto_transaction else None
                })
            else:
                # Revenue transactions
                revenue_transactions.append({
                    "transaction_id": transaction.id,
                    "receipt_number": transaction.receipt_number,
                    "amount": transaction.amount,
                    "payment_method": transaction.payment_method.value,
                    "status": transaction.status.value,
                    "created_at": transaction.created_at.isoformat()
                })

        total_revenue = sum(t["amount"] for t in revenue_transactions)
        total_crypto_info = sum(t["amount"] for t in crypto_info)

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "revenue": {
                "total_amount": round(total_revenue, 2),
                "transaction_count": len(revenue_transactions),
                "transactions": revenue_transactions
            },
            "crypto_information": {
                "total_amount": round(total_crypto_info, 2),
                "transaction_count": len(crypto_info),
                "note": "Information only - not included in revenue",
                "transactions": crypto_info
            }
        }

