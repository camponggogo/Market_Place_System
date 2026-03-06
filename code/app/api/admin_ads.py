"""
Admin API - จัดการฟีดโฆษณา (Ad Feed) แสดงในแอปสมาชิก - เลือกทุกร้านหรือเฉพาะร้าน, ตั้งเวลาปล่อย, อัปโหลดไฟล์, stream/download
"""
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import AdFeed, AdImpression, StorePromotion, Store

router = APIRouter(prefix="/api/admin/ads", tags=["admin-ads"])

# โฟลเดอร์เก็บไฟล์โฆษณาที่อัปโหลด (ต้องตรงกับ main.py ที่ mount /ad-media)
AD_MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "ad_media"
AD_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_VIDEO_EXT = {".mp4", ".webm", ".ogg", ".mov"}


class AdFeedCreate(BaseModel):
    title: str
    body: Optional[str] = None
    media_type: str = "image"  # image | video
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    link_url: Optional[str] = None
    store_id: Optional[int] = None  # null = ทุกร้าน (broadcast)
    start_at: Optional[str] = None  # ISO datetime
    end_at: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    delivery_mode: str = "stream"  # stream | download (อนุญาตดาวน์โหลดเมื่อเน็ตขัดข้อง)


class AdFeedUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    media_type: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    link_url: Optional[str] = None
    store_id: Optional[int] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    delivery_mode: Optional[str] = None


class AdReorderItem(BaseModel):
    id: int
    sort_order: int


class AdReorderPayload(BaseModel):
    items: List[AdReorderItem]  # [{ id, sort_order }, ...]


def _parse_dt(s: Optional[str]):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


@router.get("/list")
def list_ads(db: Session = Depends(get_db)):
    rows = db.query(AdFeed).order_by(AdFeed.sort_order, AdFeed.id.desc()).all()
    return [
        {"id": r.id, "title": r.title, "body": r.body,
         "media_type": getattr(r, "media_type", None) or "image",
         "image_url": r.image_url, "video_url": getattr(r, "video_url", None), "link_url": r.link_url,
         "store_id": getattr(r, "store_id", None),
         "start_at": r.start_at.isoformat() if getattr(r, "start_at", None) else None,
         "end_at": r.end_at.isoformat() if getattr(r, "end_at", None) else None,
         "sort_order": r.sort_order, "is_active": r.is_active,
         "delivery_mode": getattr(r, "delivery_mode", None) or "stream",
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]


@router.post("/upload")
async def upload_ad_media(file: UploadFile = File(...)):
    """อัปโหลดไฟล์ภาพหรือวิดีโอสำหรับโฆษณา เก็บใน data/ad_media และให้บริการที่ /ad-media/"""
    ext = (Path(file.filename or "").suffix or "").lower()
    if ext in ALLOWED_IMAGE_EXT:
        media_type = "image"
    elif ext in ALLOWED_VIDEO_EXT:
        media_type = "video"
    else:
        raise HTTPException(
            status_code=400,
            detail="รองรับเฉพาะภาพ (jpg,png,gif,webp) และวิดีโอ (mp4,webm,ogg,mov)"
        )
    name = f"{uuid.uuid4().hex[:12]}{ext}"
    path = AD_MEDIA_DIR / name
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    url = f"/ad-media/{name}"
    return {"url": url, "media_type": media_type, "filename": name}


@router.post("/create")
def create_ad(data: AdFeedCreate, db: Session = Depends(get_db)):
    ad = AdFeed(
        title=data.title,
        body=data.body,
        media_type=(data.media_type or "image")[:20],
        image_url=data.image_url,
        video_url=getattr(data, "video_url", None),
        link_url=data.link_url,
        store_id=data.store_id,
        start_at=_parse_dt(data.start_at),
        end_at=_parse_dt(data.end_at),
        sort_order=data.sort_order,
        is_active=data.is_active,
        delivery_mode=(getattr(data, "delivery_mode", None) or "stream")[:20],
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return {"id": ad.id, "message": "สร้างโฆษณาเรียบร้อย"}


@router.put("/{ad_id}")
def update_ad(ad_id: int, data: AdFeedUpdate, db: Session = Depends(get_db)):
    ad = db.query(AdFeed).filter(AdFeed.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="ไม่พบโฆษณา")
    if data.title is not None:
        ad.title = data.title
    if data.body is not None:
        ad.body = data.body
    if data.media_type is not None:
        ad.media_type = data.media_type[:20] if data.media_type else "image"
    if data.image_url is not None:
        ad.image_url = data.image_url
    if data.video_url is not None:
        ad.video_url = data.video_url
    if data.link_url is not None:
        ad.link_url = data.link_url
    if data.store_id is not None:
        ad.store_id = data.store_id
    if data.start_at is not None:
        ad.start_at = _parse_dt(data.start_at)
    if data.end_at is not None:
        ad.end_at = _parse_dt(data.end_at)
    if data.sort_order is not None:
        ad.sort_order = data.sort_order
    if data.is_active is not None:
        ad.is_active = data.is_active
    if data.delivery_mode is not None:
        ad.delivery_mode = data.delivery_mode[:20] if data.delivery_mode else "stream"
    db.add(ad)
    db.commit()
    return {"message": "อัปเดตเรียบร้อย"}


@router.post("/reorder")
def reorder_ads(payload: AdReorderPayload, db: Session = Depends(get_db)):
    """จัดเรียงลำดับโฆษณา/สไลด์ (ส่งรายการ id กับ sort_order ใหม่)"""
    for item in payload.items:
        ad = db.query(AdFeed).filter(AdFeed.id == item.id).first()
        if ad:
            ad.sort_order = item.sort_order
            db.add(ad)
    db.commit()
    return {"message": "จัดเรียงเรียบร้อย"}


@router.delete("/{ad_id}")
def delete_ad(ad_id: int, db: Session = Depends(get_db)):
    ad = db.query(AdFeed).filter(AdFeed.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="ไม่พบโฆษณา")
    db.delete(ad)
    db.commit()
    return {"message": "ลบเรียบร้อย"}


@router.get("/summary")
def ads_summary(
    from_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """สรุปผลการตอบรับโฆษณา: จำนวน view และ click ต่อรายการ (มีตาราง ad_impressions)"""
    q = db.query(AdFeed).order_by(AdFeed.id)
    ads = q.all()
    start_dt = None
    end_dt = None
    if from_date:
        try:
            start_dt = datetime.strptime(from_date, "%Y-%m-%d")
        except ValueError:
            pass
    if to_date:
        try:
            end_dt = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            pass
    out = []
    for ad in ads:
        qr = db.query(
            AdImpression.event_type,
            func.count(AdImpression.id).label("cnt"),
        ).filter(AdImpression.ad_feed_id == ad.id)
        if start_dt:
            qr = qr.filter(AdImpression.created_at >= start_dt)
        if end_dt:
            qr = qr.filter(AdImpression.created_at < end_dt)
        rows = qr.group_by(AdImpression.event_type).all()
        views = clicks = 0
        for r in rows:
            if r.event_type == "view":
                views = r.cnt or 0
            elif r.event_type == "click":
                clicks = r.cnt or 0
        out.append({
            "ad_id": ad.id,
            "title": ad.title,
            "views": views,
            "clicks": clicks,
        })
    return {"items": out, "from": from_date, "to": to_date}


@router.get("/promotions")
def list_promotions(db: Session = Depends(get_db)):
    """รายการโปรโมชั่นร้าน (สำหรับปฏิทินและจัดการ)"""
    rows = db.query(StorePromotion).order_by(StorePromotion.id.desc()).all()
    return [
        {"id": r.id, "store_id": r.store_id, "title": r.title, "description": r.description,
         "valid_from": r.valid_from.isoformat() if r.valid_from else None,
         "valid_to": r.valid_to.isoformat() if r.valid_to else None, "is_active": r.is_active}
        for r in rows
    ]


class PromotionCreate(BaseModel):
    store_id: int
    title: str
    description: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    is_active: bool = True


class PromotionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/promotions")
def create_promotion(data: PromotionCreate, db: Session = Depends(get_db)):
    if not db.query(Store).filter(Store.id == data.store_id).first():
        raise HTTPException(status_code=404, detail="ไม่พบร้าน")
    p = StorePromotion(
        store_id=data.store_id,
        title=data.title,
        description=data.description,
        valid_from=_parse_dt(data.valid_from),
        valid_to=_parse_dt(data.valid_to),
        is_active=data.is_active,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "message": "สร้างโปรโมชั่นเรียบร้อย"}


@router.put("/promotions/{promo_id}")
def update_promotion(promo_id: int, data: PromotionUpdate, db: Session = Depends(get_db)):
    p = db.query(StorePromotion).filter(StorePromotion.id == promo_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="ไม่พบโปรโมชั่น")
    if data.title is not None:
        p.title = data.title
    if data.description is not None:
        p.description = data.description
    if data.valid_from is not None:
        p.valid_from = _parse_dt(data.valid_from)
    if data.valid_to is not None:
        p.valid_to = _parse_dt(data.valid_to)
    if data.is_active is not None:
        p.is_active = data.is_active
    db.commit()
    return {"message": "อัปเดตเรียบร้อย"}


@router.get("/calendar/events")
def calendar_events(
    start: Optional[str] = Query(None, description="ISO date หรือ YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="ISO date หรือ YYYY-MM-DD"),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """เหตุการณ์ปฏิทินจากโฆษณา (ad_feeds) และโปรโมชั่นร้าน (store_promotions) สำหรับแสดงแบบ Google Calendar"""
    start_dt = end_dt = None
    if start:
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        except Exception:
            try:
                start_dt = datetime.strptime(start[:10], "%Y-%m-%d")
            except Exception:
                pass
    if end:
        try:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        except Exception:
            try:
                end_dt = datetime.strptime(end[:10], "%Y-%m-%d") + timedelta(days=1)
            except Exception:
                pass
    if year and month and not start_dt:
        start_dt = datetime(year, month, 1)
        if month == 12:
            end_dt = datetime(year + 1, 1, 1)
        else:
            end_dt = datetime(year, month + 1, 1)
    if not end_dt and start_dt:
        end_dt = start_dt + timedelta(days=31)
    if not start_dt:
        start_dt = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(days=31)
    events = []
    # โฆษณา
    ad_rows = db.query(AdFeed).filter(AdFeed.is_active == True).all()
    for r in ad_rows:
        s = getattr(r, "start_at", None)
        e = getattr(r, "end_at", None)
        if not s:
            s = getattr(r, "created_at", None)
        if not s:
            continue
        if end_dt and s and s.replace(tzinfo=None) >= end_dt:
            continue
        if start_dt and e and e.replace(tzinfo=None) <= start_dt:
            continue
        events.append({
            "id": "ad-" + str(r.id),
            "title": r.title or "โฆษณา",
            "start": (s.isoformat() if s else None),
            "end": (e.isoformat() if e else s.isoformat() if s else None),
            "type": "ad",
            "store_id": getattr(r, "store_id", None),
        })
    # โปรโมชั่นร้าน
    promos = db.query(StorePromotion).filter(StorePromotion.is_active == True).all()
    for r in promos:
        s = getattr(r, "valid_from", None)
        e = getattr(r, "valid_to", None)
        if not s:
            continue
        if end_dt and s and s.replace(tzinfo=None) >= end_dt:
            continue
        if start_dt and e and e.replace(tzinfo=None) <= start_dt:
            continue
        events.append({
            "id": "promo-" + str(r.id),
            "title": r.title or "โปรโมชั่น",
            "start": (s.isoformat() if s else None),
            "end": (e.isoformat() if e else s.isoformat() if s else None),
            "type": "promotion",
            "store_id": r.store_id,
        })
    return {"events": events}
