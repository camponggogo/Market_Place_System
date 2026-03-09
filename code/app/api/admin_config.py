"""
Admin Config API - จัดการ config.ini ผ่านหน้า Admin
- GET: แสดงค่าทั้งหมด (ค่าลับเป็น ****)
- GET /reveal: แสดงค่าจริงของ key ที่ระบุ (กดไอคอนดวงตา)
- PUT: อัปเดตค่า (เฉพาะ admin)
"""
import configparser
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.auth import require_admin
from app.config import CONFIG_FILE

router = APIRouter(prefix="/api/admin/config", tags=["admin-config"])

# คีย์ที่ถือว่าลับ — แสดงเป็น **** และต้องใช้ /reveal เพื่อดูค่า
SENSITIVE_SUBSTRINGS = (
    "password", "secret", "_key", "token", "api_key", "webhook_secret",
    "consumer_secret", "access_token", "channel_secret", "channel_access",
)


def _is_sensitive(key: str) -> bool:
    k = (key or "").lower()
    return any(s in k for s in SENSITIVE_SUBSTRINGS)


def _load_config() -> configparser.ConfigParser:
    """โหลด config จากไฟล์ (ใช้ค่าล่าสุดจาก disk)"""
    cfg = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        cfg.read(CONFIG_FILE, encoding="utf-8")
    return cfg


@router.get("")
async def get_config_masked(user: dict = Depends(require_admin)):
    """
    ดึง config ทั้งหมด สำหรับค่าลับส่งเป็น ****
    ใช้ร่วมกับ /reveal เมื่อต้องการดูค่าจริง
    """
    cfg = _load_config()
    out = {}
    for section in cfg.sections():
        out[section] = []
        for key in cfg[section]:
            raw = cfg[section][key]
            masked = _is_sensitive(key)
            out[section].append({
                "key": key,
                "value": "********" if masked and raw else (raw or ""),
                "masked": masked,
            })
    return {"sections": out}


@router.get("/reveal")
async def reveal_config_value(
    section: str = Query(..., description="Section ใน config.ini"),
    key: str = Query(..., description="Key ที่ต้องการดูค่า"),
    user: dict = Depends(require_admin),
):
    """
    แสดงค่าจริงของ key ที่ระบุ (สำหรับกดไอคอนดวงตา)
    ใช้เฉพาะเมื่อจำเป็น เพื่อลดความเสี่ยงจากการถ่ายภาพหรือ screen capture
    """
    cfg = _load_config()
    if not cfg.has_section(section):
        raise HTTPException(status_code=404, detail="ไม่พบ section")
    if not cfg.has_option(section, key):
        raise HTTPException(status_code=404, detail="ไม่พบ key")
    value = cfg.get(section, key)
    return {"section": section, "key": key, "value": value}


class ConfigUpdateBody(BaseModel):
    section: str
    key: str
    value: str


GP_SECTION = "PAYMENT"
GP_KEY = "SETTLEMENT_GP_PERCENT"


@router.get("/gp")
async def get_gp_percent(user: dict = Depends(require_admin)):
    """ดึงอัตราหัก GP % ปัจจุบัน (จาก config.ini หรือ env)"""
    cfg = _load_config()
    value = None
    if cfg.has_section(GP_SECTION) and cfg.has_option(GP_SECTION, GP_KEY):
        value = cfg.get(GP_SECTION, GP_KEY)
    if value is None or value.strip() == "":
        value = os.environ.get("SETTLEMENT_GP_PERCENT", "0")
    try:
        gp = float((value or "0").strip())
    except (ValueError, TypeError):
        gp = 0.0
    return {"gp_percent": round(gp, 2)}


class GPUpdateBody(BaseModel):
    gp_percent: float


@router.put("/gp")
async def update_gp_percent(
    body: GPUpdateBody,
    user: dict = Depends(require_admin),
):
    """ตั้งค่าอัตราหัก GP % (เขียนลง config.ini)"""
    if body.gp_percent < 0 or body.gp_percent > 100:
        raise HTTPException(status_code=400, detail="อัตราหัก GP ต้องอยู่ระหว่าง 0 ถึง 100")
    cfg = _load_config()
    if not cfg.has_section(GP_SECTION):
        cfg.add_section(GP_SECTION)
    cfg.set(GP_SECTION, GP_KEY, str(round(body.gp_percent, 2)))
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            cfg.write(f)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"เขียนไฟล์ config ไม่ได้: {e}")
    return {"success": True, "gp_percent": round(body.gp_percent, 2), "message": "บันทึกอัตราหัก GP แล้ว"}


@router.put("")
async def update_config(
    body: ConfigUpdateBody,
    user: dict = Depends(require_admin),
):
    """อัปเดตค่าใน config.ini (เขียนทับไฟล์)"""
    if not body.section.strip() or not body.key.strip():
        raise HTTPException(status_code=400, detail="section และ key ต้องไม่ว่าง")
    cfg = _load_config()
    if not cfg.has_section(body.section):
        cfg.add_section(body.section)
    cfg.set(body.section, body.key, body.value)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            cfg.write(f)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"เขียนไฟล์ config ไม่ได้: {e}")
    # โหลด config ใหม่ใน process (app.config ยังใช้ของเก่าจนกว่าจะ restart)
    return {"success": True, "message": "บันทึกแล้ว (บางค่าอาจมีผลหลัง restart server)"}
