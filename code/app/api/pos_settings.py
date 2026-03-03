"""
POS Settings API – ตั้งค่า Store POS (เครื่องพิมพ์ Thermal, เครื่องอ่าน QR, EDC)
ค่าจาก config.ini + override จาก pos_settings.json (บันทึกจากหน้า Web Setting)
"""
import json
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import config as app_config

router = APIRouter(prefix="/api/pos-settings", tags=["pos-settings"])

# เก็บ override ที่บันทึกจากหน้า Web (ไม่เขียน config.ini)
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SETTINGS_FILE = _DATA_DIR / "pos_settings.json"


def _default_settings() -> dict:
    return {
        "thermal_printer_driver": getattr(app_config, "POS_THERMAL_PRINTER_DRIVER", "ESC/POS"),
        "thermal_printer_name": getattr(app_config, "POS_THERMAL_PRINTER_NAME", "") or "",
        "thermal_printer_port": getattr(app_config, "POS_THERMAL_PRINTER_PORT", "") or "",
        "qr_reader_port": getattr(app_config, "POS_QR_READER_PORT", "") or "",
        "edc_reader_port": getattr(app_config, "POS_EDC_READER_PORT", "") or "",
        "thermal_paper_width_mm": getattr(app_config, "POS_THERMAL_PAPER_WIDTH_MM", 80) or 80,
        "menu_image_priority": "local,server,base64",
        "menu_columns": 6,
        "payment_promptpay_enabled": getattr(app_config, "POS_PAYMENT_PROMPTPAY_ENABLED", True),
        "payment_credit_debit_enabled": getattr(app_config, "POS_PAYMENT_CREDIT_DEBIT_ENABLED", True),
        "payment_cash_enabled": getattr(app_config, "POS_PAYMENT_CASH_ENABLED", True),
    }


def _load_overrides() -> dict:
    if not _SETTINGS_FILE.exists():
        return {}
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_overrides(data: dict) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class PosSettingsBody(BaseModel):
    thermal_printer_driver: Optional[str] = None
    thermal_printer_name: Optional[str] = None
    thermal_printer_port: Optional[str] = None
    qr_reader_port: Optional[str] = None
    edc_reader_port: Optional[str] = None
    thermal_paper_width_mm: Optional[int] = None
    menu_image_priority: Optional[str] = None
    menu_columns: Optional[int] = None
    payment_promptpay_enabled: Optional[bool] = None
    payment_credit_debit_enabled: Optional[bool] = None
    payment_cash_enabled: Optional[bool] = None


@router.get("")
def get_pos_settings() -> dict:
    """ดึงการตั้งค่า POS (config + override จากไฟล์)"""
    base = _default_settings()
    overrides = _load_overrides()
    for k, v in overrides.items():
        if k in base and v is not None:
            base[k] = v
    return base


@router.put("")
def save_pos_settings(body: PosSettingsBody) -> dict:
    """บันทึกการตั้งค่า POS (เขียนลง pos_settings.json)"""
    overrides = _load_overrides()
    if body.thermal_printer_driver is not None:
        overrides["thermal_printer_driver"] = body.thermal_printer_driver
    if body.thermal_printer_name is not None:
        overrides["thermal_printer_name"] = body.thermal_printer_name
    if body.thermal_printer_port is not None:
        overrides["thermal_printer_port"] = body.thermal_printer_port
    if body.qr_reader_port is not None:
        overrides["qr_reader_port"] = body.qr_reader_port
    if body.edc_reader_port is not None:
        overrides["edc_reader_port"] = body.edc_reader_port
    if body.thermal_paper_width_mm is not None:
        overrides["thermal_paper_width_mm"] = max(58, min(80, body.thermal_paper_width_mm))
    if body.menu_image_priority is not None:
        overrides["menu_image_priority"] = body.menu_image_priority.strip()
    if body.menu_columns is not None:
        cols = max(2, min(8, int(body.menu_columns)))
        overrides["menu_columns"] = cols
    if body.payment_promptpay_enabled is not None:
        overrides["payment_promptpay_enabled"] = body.payment_promptpay_enabled
    if body.payment_credit_debit_enabled is not None:
        overrides["payment_credit_debit_enabled"] = body.payment_credit_debit_enabled
    if body.payment_cash_enabled is not None:
        overrides["payment_cash_enabled"] = body.payment_cash_enabled
    _save_overrides(overrides)
    return get_pos_settings()


@router.post("/test-printer")
def test_printer() -> dict:
    """
    ทดสอบการเชื่อมต่อ/ส่งคำสั่งไปเครื่องพิมพ์ Thermal
    หมายเหตุ: การพิมพ์จริงทำที่ฝั่ง Browser (window.print) หรือผ่าน local agent
    """
    return {
        "ok": True,
        "message": "ส่งคำสั่งทดสอบแล้ว (ให้ใช้ปุ่ม 'พิมพ์หน้าทดสอบ' บนหน้า Setting เพื่อพิมพ์จาก Browser)",
    }


@router.post("/test-qr-reader")
def test_qr_reader() -> dict:
    """
    ทดสอบเครื่องอ่าน QR – ฝั่ง Server ไม่มี direct access กับอุปกรณ์
    ให้ใช้ช่องสแกนบาร์โค้ดบน Store POS และสแกนทดสอบ
    """
    return {
        "ok": True,
        "message": "ให้ไปที่หน้า Store POS แล้วสแกน QR/บาร์โค้ดที่ช่อง 'พิมพ์หรือสแกนบาร์โค้ด'",
    }


@router.post("/test-edc")
def test_edc() -> dict:
    """
    ทดสอบเครื่อง EDC รูดบัตร – ต้องใช้โปรแกรม/driver ฝั่งเครื่อง POS
    API นี้แจ้งสถานะว่าค่าตั้งค่า EDC ถูกบันทึกแล้ว
    """
    return {
        "ok": True,
        "message": "ตั้งค่า EDC บันทึกแล้ว – ให้ลองรูดบัตรทดสอบที่เครื่อง EDC (ต้องมี driver ติดตั้งที่เครื่อง POS)",
    }
