"""
Tax API - ระบบจัดการใบกำกับภาษี
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.tax_service import TaxService
from app.models import Transaction, TaxInvoice

router = APIRouter(prefix="/api/tax", tags=["tax"])


@router.post("/invoices/{transaction_id}")
async def create_tax_invoice(
    transaction_id: int,
    invoice_number: str = None,
    db: Session = Depends(get_db)
):
    """
    สร้างใบกำกับภาษีอย่างย่อ (ภ.พ. 89)
    """
    try:
        tax_service = TaxService(db)
        tax_invoice = tax_service.create_tax_invoice(transaction_id, invoice_number)
        
        return {
            "id": tax_invoice.id,
            "invoice_number": tax_invoice.invoice_number,
            "transaction_id": tax_invoice.transaction_id,
            "amount": tax_invoice.amount,
            "vat_amount": tax_invoice.vat_amount,
            "total_amount": tax_invoice.total_amount,
            "tax_id": tax_invoice.tax_id,
            "company_name": tax_invoice.company_name,
            "issued_at": tax_invoice.issued_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/{invoice_id}")
async def get_tax_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """
    ดึงข้อมูลใบกำกับภาษี
    """
    tax_invoice = db.query(TaxInvoice).filter(TaxInvoice.id == invoice_id).first()
    if not tax_invoice:
        raise HTTPException(status_code=404, detail="Tax invoice not found")
    
    return {
        "id": tax_invoice.id,
        "invoice_number": tax_invoice.invoice_number,
        "transaction_id": tax_invoice.transaction_id,
        "amount": tax_invoice.amount,
        "vat_amount": tax_invoice.vat_amount,
        "total_amount": tax_invoice.total_amount,
        "tax_id": tax_invoice.tax_id,
        "company_name": tax_invoice.company_name,
        "issued_at": tax_invoice.issued_at.isoformat(),
        "e_tax_sent": tax_invoice.e_tax_sent,
        "e_tax_sent_at": tax_invoice.e_tax_sent_at.isoformat() if tax_invoice.e_tax_sent_at else None
    }


@router.post("/invoices/{invoice_id}/send-e-tax")
async def send_e_tax_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """
    ส่งใบกำกับภาษีไปยัง E-Tax Invoice Provider
    """
    try:
        tax_service = TaxService(db)
        success = tax_service.send_e_tax_invoice(invoice_id)
        
        if success:
            return {
                "success": True,
                "message": "E-Tax Invoice sent successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send E-Tax Invoice")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices")
async def list_tax_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    ดึงรายการใบกำกับภาษี
    """
    tax_invoices = db.query(TaxInvoice).offset(skip).limit(limit).all()
    
    return [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "transaction_id": inv.transaction_id,
            "amount": inv.amount,
            "vat_amount": inv.vat_amount,
            "total_amount": inv.total_amount,
            "issued_at": inv.issued_at.isoformat(),
            "e_tax_sent": inv.e_tax_sent
        }
        for inv in tax_invoices
    ]

