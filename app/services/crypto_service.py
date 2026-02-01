"""
Crypto Service - ระบบจัดการ Crypto Payment (P2P Contract Model)
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import (
    Store, CryptoTransaction, Transaction, CryptoTransactionStatus
)
from app.config import (
    BLOCKCHAIN_EXPLORER_API, TRANSACTION_FEE, CRYPTO_ENABLED
)
import aiohttp
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CryptoService:
    """Service for handling crypto transactions with P2P model"""

    def __init__(self, db: Session):
        self.db = db

    def check_store_contract(self, store_id: int) -> bool:
        """
        ตรวจสอบว่าร้านค้ายอมรับสัญญา P2P หรือยัง
        """
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            return False
        
        return store.contract_accepted and store.crypto_enabled

    def accept_contract(self, store_id: int, contract_version: str) -> Store:
        """
        ร้านค้ายอมรับสัญญา P2P
        """
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            raise ValueError("Store not found")

        store.contract_accepted = True
        store.contract_accepted_at = datetime.now()
        store.contract_version = contract_version
        store.crypto_enabled = True
        self.db.commit()
        self.db.refresh(store)

        return store

    def create_crypto_transaction(
        self,
        transaction_id: int,
        store_id: int,
        tx_hash: str,
        blockchain_address: str,
        amount_crypto: float,
        crypto_type: str = "BTC"
    ) -> CryptoTransaction:
        """
        สร้าง Crypto Transaction Record
        """
        # ตรวจสอบว่าร้านค้ายอมรับสัญญาหรือยัง
        if not self.check_store_contract(store_id):
            raise ValueError("Store has not accepted P2P contract")

        crypto_transaction = CryptoTransaction(
            transaction_id=transaction_id,
            store_id=store_id,
            tx_hash=tx_hash,
            blockchain_address=blockchain_address,
            amount_crypto=amount_crypto,
            crypto_type=crypto_type,
            status=CryptoTransactionStatus.PENDING
        )
        self.db.add(crypto_transaction)
        self.db.commit()
        self.db.refresh(crypto_transaction)

        return crypto_transaction

    async def check_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        ตรวจสอบสถานะ Transaction จาก Blockchain Explorer
        """
        if not CRYPTO_ENABLED:
            return {"error": "Crypto is not enabled"}

        try:
            async with aiohttp.ClientSession() as session:
                # ตัวอย่างการเรียก API จาก Blockchain Explorer
                # ปรับตาม API ที่ใช้จริง
                url = f"{BLOCKCHAIN_EXPLORER_API}/tx/{tx_hash}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # ตรวจสอบสถานะ transaction
                        confirmations = data.get("confirmations", 0)
                        status = "confirmed" if confirmations >= 1 else "pending"
                        
                        return {
                            "status": status,
                            "confirmations": confirmations,
                            "tx_hash": tx_hash,
                            "block_height": data.get("block_height"),
                            "explorer_url": f"{BLOCKCHAIN_EXPLORER_API}/tx/{tx_hash}"
                        }
                    else:
                        return {
                            "status": "failed",
                            "error": f"API returned status {response.status}"
                        }
        except Exception as e:
            logger.error(f"Error checking transaction status: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def update_transaction_status(self, crypto_transaction_id: int) -> CryptoTransaction:
        """
        อัพเดทสถานะ Transaction จาก Blockchain Explorer
        """
        crypto_transaction = self.db.query(CryptoTransaction).filter(
            CryptoTransaction.id == crypto_transaction_id
        ).first()

        if not crypto_transaction:
            raise ValueError("Crypto transaction not found")

        # ตรวจสอบสถานะจาก Blockchain Explorer
        status_data = await self.check_transaction_status(crypto_transaction.tx_hash)

        if status_data.get("status") == "confirmed":
            crypto_transaction.status = CryptoTransactionStatus.CONFIRMED
            crypto_transaction.explorer_url = status_data.get("explorer_url")
            
            # อัพเดท Transaction Status
            transaction = self.db.query(Transaction).filter(
                Transaction.id == crypto_transaction.transaction_id
            ).first()
            if transaction:
                from app.models import TransactionStatus
                transaction.status = TransactionStatus.CONFIRMED
        elif status_data.get("status") == "failed":
            crypto_transaction.status = CryptoTransactionStatus.FAILED
            
            transaction = self.db.query(Transaction).filter(
                Transaction.id == crypto_transaction.transaction_id
            ).first()
            if transaction:
                from app.models import TransactionStatus
                transaction.status = TransactionStatus.FAILED

        crypto_transaction.last_checked = datetime.now()
        self.db.commit()
        self.db.refresh(crypto_transaction)

        return crypto_transaction

    def get_store_crypto_transactions(self, store_id: int) -> list:
        """
        ดึงรายการ Crypto Transactions ของร้านค้า
        """
        return self.db.query(CryptoTransaction).filter(
            CryptoTransaction.store_id == store_id
        ).order_by(CryptoTransaction.created_at.desc()).all()

    def calculate_transaction_fee(self, amount: float) -> float:
        """
        คำนวณ Transaction Fee
        """
        return TRANSACTION_FEE

