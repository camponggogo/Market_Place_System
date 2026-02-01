"""
Report Service - ระบบรายงานสรุปยอด
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app.models import (
    FoodCourtID, CounterTransaction, StoreTransaction,
    Transaction, PaymentMethod, Store
)
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating reports"""

    def __init__(self, db: Session):
        self.db = db

    def get_store_summary(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        profile_id: Optional[int] = None,
        event_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        สรุปยอดรายร้านค้า
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # ดึงข้อมูล Store
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            return {
                "store_id": store_id,
                "error": "Store not found"
            }
        
        # ตรวจสอบ profile_id และ event_id
        if profile_id and store.profile_id != profile_id:
            return {
                "store_id": store_id,
                "error": "Store does not belong to the specified profile"
            }
        
        if event_id and store.event_id != event_id:
            return {
                "store_id": store_id,
                "error": "Store does not belong to the specified event"
            }

        # ดึงข้อมูล Store Transactions
        store_transactions = self.db.query(StoreTransaction).filter(
            StoreTransaction.store_id == store_id,
            StoreTransaction.created_at >= start_date,
            StoreTransaction.created_at <= end_date,
            StoreTransaction.status == "completed"
        ).all()

        total_amount = sum(t.amount for t in store_transactions)
        transaction_count = len(store_transactions)

        # แยกตาม Payment Method
        payment_method_summary = {}
        for transaction in store_transactions:
            foodcourt_id = self.db.query(FoodCourtID).filter(
                FoodCourtID.foodcourt_id == transaction.foodcourt_id
            ).first()
            
            if foodcourt_id:
                method = foodcourt_id.payment_method.value
                if method not in payment_method_summary:
                    payment_method_summary[method] = {"count": 0, "amount": 0.0}
                payment_method_summary[method]["count"] += 1
                payment_method_summary[method]["amount"] += transaction.amount

        return {
            "store_id": store_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_transactions": transaction_count,
                "total_amount": round(total_amount, 2)
            },
            "by_payment_method": payment_method_summary,
            "transactions": [
                {
                    "id": t.id,
                    "foodcourt_id": t.foodcourt_id,
                    "amount": t.amount,
                    "created_at": t.created_at.isoformat()
                }
                for t in store_transactions
            ]
        }

    def get_daily_summary(
        self,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        สรุปยอดรายวัน
        """
        if not date:
            date = datetime.now()

        start_date = datetime.combine(date.date(), datetime.min.time())
        end_date = datetime.combine(date.date(), datetime.max.time())

        # ดึงข้อมูล Counter Transactions (การแลก Food Court ID)
        counter_transactions = self.db.query(CounterTransaction).filter(
            CounterTransaction.created_at >= start_date,
            CounterTransaction.created_at <= end_date,
            CounterTransaction.status == "completed"
        ).all()

        # ดึงข้อมูล Store Transactions (การใช้งาน)
        store_transactions = self.db.query(StoreTransaction).filter(
            StoreTransaction.created_at >= start_date,
            StoreTransaction.created_at <= end_date,
            StoreTransaction.status == "completed"
        ).all()

        # สรุปการแลก
        exchange_total = sum(t.amount for t in counter_transactions)
        exchange_count = len(counter_transactions)

        # สรุปการใช้งาน
        usage_total = sum(t.amount for t in store_transactions)
        usage_count = len(store_transactions)

        # แยกตาม Payment Method
        payment_method_summary = {}
        for transaction in counter_transactions:
            method = transaction.payment_method.value
            if method not in payment_method_summary:
                payment_method_summary[method] = {"count": 0, "amount": 0.0}
            payment_method_summary[method]["count"] += 1
            payment_method_summary[method]["amount"] += transaction.amount

        # สรุปรายร้านค้า
        store_summary = {}
        for transaction in store_transactions:
            store_id = transaction.store_id
            if store_id not in store_summary:
                store = self.db.query(Store).filter(Store.id == store_id).first()
                store_summary[store_id] = {
                    "store_id": store_id,
                    "store_name": store.name if store else "Unknown",
                    "count": 0,
                    "amount": 0.0
                }
            store_summary[store_id]["count"] += 1
            store_summary[store_id]["amount"] += transaction.amount

        return {
            "date": date.date().isoformat(),
            "exchange": {
                "total_amount": round(exchange_total, 2),
                "transaction_count": exchange_count
            },
            "usage": {
                "total_amount": round(usage_total, 2),
                "transaction_count": usage_count
            },
            "by_payment_method": payment_method_summary,
            "by_store": list(store_summary.values())
        }

    def get_monthly_summary(
        self,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        สรุปยอดรายเดือน
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        end_date = datetime.combine(end_date.date(), datetime.max.time())

        # ดึงข้อมูล Counter Transactions
        counter_transactions = self.db.query(CounterTransaction).filter(
            CounterTransaction.created_at >= start_date,
            CounterTransaction.created_at <= end_date,
            CounterTransaction.status == "completed"
        ).all()

        # ดึงข้อมูล Store Transactions
        store_transactions = self.db.query(StoreTransaction).filter(
            StoreTransaction.created_at >= start_date,
            StoreTransaction.created_at <= end_date,
            StoreTransaction.status == "completed"
        ).all()

        exchange_total = sum(t.amount for t in counter_transactions)
        usage_total = sum(t.amount for t in store_transactions)

        # สรุปรายวัน
        daily_summaries = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            daily_summary = self.get_daily_summary(datetime.combine(current_date, datetime.min.time()))
            daily_summaries.append(daily_summary)
            current_date += timedelta(days=1)

        # สรุปรายร้านค้า
        store_summary = {}
        for transaction in store_transactions:
            store_id = transaction.store_id
            if store_id not in store_summary:
                store = self.db.query(Store).filter(Store.id == store_id).first()
                store_summary[store_id] = {
                    "store_id": store_id,
                    "store_name": store.name if store else "Unknown",
                    "count": 0,
                    "amount": 0.0
                }
            store_summary[store_id]["count"] += 1
            store_summary[store_id]["amount"] += transaction.amount

        return {
            "year": year,
            "month": month,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "exchange": {
                "total_amount": round(exchange_total, 2),
                "transaction_count": len(counter_transactions)
            },
            "usage": {
                "total_amount": round(usage_total, 2),
                "transaction_count": len(store_transactions)
            },
            "daily_summaries": daily_summaries,
            "by_store": list(store_summary.values())
        }

    def get_yearly_summary(
        self,
        year: int
    ) -> Dict[str, Any]:
        """
        สรุปยอดรายปี
        """
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        # ดึงข้อมูล Counter Transactions
        counter_transactions = self.db.query(CounterTransaction).filter(
            CounterTransaction.created_at >= start_date,
            CounterTransaction.created_at <= end_date,
            CounterTransaction.status == "completed"
        ).all()

        # ดึงข้อมูล Store Transactions
        store_transactions = self.db.query(StoreTransaction).filter(
            StoreTransaction.created_at >= start_date,
            StoreTransaction.created_at <= end_date,
            StoreTransaction.status == "completed"
        ).all()

        exchange_total = sum(t.amount for t in counter_transactions)
        usage_total = sum(t.amount for t in store_transactions)

        # สรุปรายเดือน
        monthly_summaries = []
        for month in range(1, 13):
            monthly_summary = self.get_monthly_summary(year, month)
            monthly_summaries.append(monthly_summary)

        # สรุปรายร้านค้า
        store_summary = {}
        for transaction in store_transactions:
            store_id = transaction.store_id
            if store_id not in store_summary:
                store = self.db.query(Store).filter(Store.id == store_id).first()
                store_summary[store_id] = {
                    "store_id": store_id,
                    "store_name": store.name if store else "Unknown",
                    "count": 0,
                    "amount": 0.0
                }
            store_summary[store_id]["count"] += 1
            store_summary[store_id]["amount"] += transaction.amount

        return {
            "year": year,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "exchange": {
                "total_amount": round(exchange_total, 2),
                "transaction_count": len(counter_transactions)
            },
            "usage": {
                "total_amount": round(usage_total, 2),
                "transaction_count": len(store_transactions)
            },
            "monthly_summaries": monthly_summaries,
            "by_store": list(store_summary.values())
        }

