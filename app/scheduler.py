"""
Scheduler - ระบบทำงานตามเวลาที่กำหนด (Cron Jobs)
"""
import schedule
import time
from datetime import datetime
from app.database import SessionLocal
from app.services.refund_service import RefundService
from app.services.crypto_service import CryptoService
from app.config import REFUND_NOTIFICATION_TIME
import logging

logger = logging.getLogger(__name__)


def daily_balance_reset():
    """
    รีเซ็ตยอดเงินทุกสิ้นวัน (เมื่อไม่มีใบอนุญาต e-Money)
    """
    db = SessionLocal()
    try:
        refund_service = RefundService(db)
        refund_service.daily_balance_reset()
        logger.info(f"Daily balance reset completed at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error in daily balance reset: {e}")
    finally:
        db.close()


def send_refund_notifications():
    """
    ส่งการแจ้งเตือนคืนเงินให้ลูกค้าที่มียอดเงินคงเหลือ
    """
    db = SessionLocal()
    try:
        from app.models import CustomerBalance
        
        balances = db.query(CustomerBalance).filter(
            CustomerBalance.balance > 0
        ).all()
        
        refund_service = RefundService(db)
        for balance in balances:
            refund_service.check_and_send_refund_notification(balance.customer_id)
        
        logger.info(f"Refund notifications sent at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error sending refund notifications: {e}")
    finally:
        db.close()


def update_crypto_transactions():
    """
    อัพเดทสถานะ Crypto Transactions จาก Blockchain Explorer
    """
    db = SessionLocal()
    try:
        from app.models import CryptoTransaction, CryptoTransactionStatus
        
        # ดึง transactions ที่ยัง pending
        pending_transactions = db.query(CryptoTransaction).filter(
            CryptoTransaction.status == CryptoTransactionStatus.PENDING
        ).all()
        
        crypto_service = CryptoService(db)
        for tx in pending_transactions:
            try:
                # Use asyncio to run async function
                import asyncio
                asyncio.run(crypto_service.update_transaction_status(tx.id))
            except Exception as e:
                logger.error(f"Error updating transaction {tx.id}: {e}")
        
        logger.info(f"Crypto transactions updated at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error updating crypto transactions: {e}")
    finally:
        db.close()


def daily_settlement_schedule():
    """
    สร้างรายการเตรียมโอนเงินไปยังร้านค้า สิ้นวัน
    ข้อกำหนดกฏหมาย: ถือฝากได้แค่ 1 วัน (เกิน = payment gateway ต้องขอใบอนุญาต)
    ใช้ ref1/ref2/ref3 ยอดเงิน เวลาโอน แยกและแจ้งร้านว่าเงินเข้าเรียบร้อยแล้ว เพื่อพิมพ์ใบเสร็จรับเงิน
    """
    db = SessionLocal()
    try:
        from app.services.settlement_service import create_daily_settlements
        from datetime import date

        created = create_daily_settlements(db, settlement_date=date.today())
        logger.info(f"Daily settlement schedule: created {len(created)} items at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error creating daily settlements: {e}")
    finally:
        db.close()


def setup_scheduler():
    """
    ตั้งค่า Scheduled Tasks
    """
    # Daily balance reset at midnight
    schedule.every().day.at("00:00").do(daily_balance_reset)
    
    # Send refund notifications at configured time
    schedule.every().day.at(REFUND_NOTIFICATION_TIME).do(send_refund_notifications)
    
    # Update crypto transactions every 5 minutes
    schedule.every(5).minutes.do(update_crypto_transactions)

    # สิ้นวัน: สร้างรายการเตรียมโอนเงินไปยังร้านค้า (ข้อกำหนดกฏหมาย ถือฝากได้ 1 วัน)
    schedule.every().day.at("23:00").do(daily_settlement_schedule)
    
    logger.info("Scheduler setup completed")


def run_scheduler():
    """
    รัน Scheduler (เรียกใช้ใน background thread)
    """
    setup_scheduler()
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    # For testing
    setup_scheduler()
    run_scheduler()

