"""
Crypto API - ระบบจัดการ Crypto Payment (P2P)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.services.crypto_service import CryptoService
from app.models import Store, CryptoTransaction

router = APIRouter(prefix="/api/crypto", tags=["crypto"])


class AcceptContractRequest(BaseModel):
    store_id: int
    contract_version: str


class CreateCryptoTransactionRequest(BaseModel):
    transaction_id: int
    store_id: int
    tx_hash: str
    blockchain_address: str
    amount_crypto: float
    crypto_type: str = "BTC"


class TransactionStatusResponse(BaseModel):
    status: str
    confirmations: Optional[int]
    tx_hash: str
    block_height: Optional[int]
    explorer_url: Optional[str]
    error: Optional[str]


@router.get("/stores/{store_id}/contract-status")
async def get_contract_status(store_id: int, db: Session = Depends(get_db)):
    """
    ตรวจสอบสถานะการยอมรับสัญญา P2P ของร้านค้า
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    return {
        "store_id": store.id,
        "store_name": store.name,
        "crypto_enabled": store.crypto_enabled,
        "contract_accepted": store.contract_accepted,
        "contract_accepted_at": store.contract_accepted_at.isoformat() if store.contract_accepted_at else None,
        "contract_version": store.contract_version
    }


@router.post("/stores/accept-contract")
async def accept_contract(request: AcceptContractRequest, db: Session = Depends(get_db)):
    """
    ร้านค้ายอมรับสัญญา P2P
    """
    try:
        crypto_service = CryptoService(db)
        store = crypto_service.accept_contract(request.store_id, request.contract_version)
        
        return {
            "success": True,
            "store_id": store.id,
            "contract_accepted": store.contract_accepted,
            "contract_accepted_at": store.contract_accepted_at.isoformat(),
            "contract_version": store.contract_version
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transactions")
async def create_crypto_transaction(
    request: CreateCryptoTransactionRequest,
    db: Session = Depends(get_db)
):
    """
    สร้าง Crypto Transaction Record
    """
    try:
        crypto_service = CryptoService(db)
        crypto_transaction = crypto_service.create_crypto_transaction(
            transaction_id=request.transaction_id,
            store_id=request.store_id,
            tx_hash=request.tx_hash,
            blockchain_address=request.blockchain_address,
            amount_crypto=request.amount_crypto,
            crypto_type=request.crypto_type
        )
        
        return {
            "id": crypto_transaction.id,
            "transaction_id": crypto_transaction.transaction_id,
            "tx_hash": crypto_transaction.tx_hash,
            "status": crypto_transaction.status.value,
            "created_at": crypto_transaction.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{tx_hash}/status", response_model=TransactionStatusResponse)
async def check_transaction_status(tx_hash: str, db: Session = Depends(get_db)):
    """
    ตรวจสอบสถานะ Transaction จาก Blockchain Explorer
    """
    try:
        crypto_service = CryptoService(db)
        status_data = await crypto_service.check_transaction_status(tx_hash)
        
        return TransactionStatusResponse(**status_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transactions/{crypto_transaction_id}/update-status")
async def update_transaction_status(
    crypto_transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    อัพเดทสถานะ Transaction จาก Blockchain Explorer
    """
    try:
        crypto_service = CryptoService(db)
        crypto_transaction = await crypto_service.update_transaction_status(crypto_transaction_id)
        
        return {
            "id": crypto_transaction.id,
            "tx_hash": crypto_transaction.tx_hash,
            "status": crypto_transaction.status.value,
            "last_checked": crypto_transaction.last_checked.isoformat() if crypto_transaction.last_checked else None,
            "explorer_url": crypto_transaction.explorer_url
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stores/{store_id}/transactions")
async def get_store_transactions(store_id: int, db: Session = Depends(get_db)):
    """
    ดึงรายการ Crypto Transactions ของร้านค้า
    """
    crypto_service = CryptoService(db)
    transactions = crypto_service.get_store_crypto_transactions(store_id)
    
    return [
        {
            "id": t.id,
            "transaction_id": t.transaction_id,
            "tx_hash": t.tx_hash,
            "blockchain_address": t.blockchain_address,
            "amount_crypto": t.amount_crypto,
            "crypto_type": t.crypto_type,
            "status": t.status.value,
            "explorer_url": t.explorer_url,
            "last_checked": t.last_checked.isoformat() if t.last_checked else None,
            "created_at": t.created_at.isoformat()
        }
        for t in transactions
    ]


@router.get("/fee/transaction")
async def get_transaction_fee(amount: float, db: Session = Depends(get_db)):
    """
    คำนวณ Transaction Fee
    """
    crypto_service = CryptoService(db)
    fee = crypto_service.calculate_transaction_fee(amount)
    
    return {
        "amount": amount,
        "transaction_fee": fee,
        "total": amount + fee
    }

