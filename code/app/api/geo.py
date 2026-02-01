"""
Geo API - ระบบจัดการตำแหน่งร้านค้าและแผนที่
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models import Store, Profile, Event

router = APIRouter(prefix="/api/geo", tags=["geo"])


class StoreLocationUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    profile_id: Optional[int] = None
    event_id: Optional[int] = None


class StoreLocationResponse(BaseModel):
    id: int
    name: str
    latitude: Optional[float]
    longitude: Optional[float]
    location_name: Optional[str]
    profile_id: Optional[int]
    event_id: Optional[int]
    profile_name: Optional[str] = None
    event_name: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/stores", response_model=List[StoreLocationResponse])
async def get_stores_with_locations(
    profile_id: Optional[int] = Query(None),
    event_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """ดึงรายการร้านค้าพร้อมตำแหน่ง"""
    query = db.query(Store)
    
    if profile_id:
        query = query.filter(Store.profile_id == profile_id)
    if event_id:
        query = query.filter(Store.event_id == event_id)
    
    stores = query.all()
    
    result = []
    for store in stores:
        profile_name = None
        event_name = None
        
        if store.profile_id:
            profile = db.query(Profile).filter(Profile.id == store.profile_id).first()
            profile_name = profile.name if profile else None
        
        if store.event_id:
            event = db.query(Event).filter(Event.id == store.event_id).first()
            event_name = event.name if event else None
        
        result.append({
            "id": store.id,
            "name": store.name,
            "latitude": store.latitude,
            "longitude": store.longitude,
            "location_name": store.location_name,
            "profile_id": store.profile_id,
            "event_id": store.event_id,
            "profile_name": profile_name,
            "event_name": event_name
        })
    
    return result


@router.put("/stores/{store_id}/location")
async def update_store_location(
    store_id: int,
    location: StoreLocationUpdate,
    db: Session = Depends(get_db)
):
    """อัปเดตตำแหน่งร้านค้า"""
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    if location.latitude is not None:
        store.latitude = location.latitude
    if location.longitude is not None:
        store.longitude = location.longitude
    if location.location_name is not None:
        store.location_name = location.location_name
    if location.profile_id is not None:
        store.profile_id = location.profile_id
    if location.event_id is not None:
        store.event_id = location.event_id
    
    db.commit()
    db.refresh(store)
    
    return {
        "success": True,
        "store_id": store.id,
        "latitude": store.latitude,
        "longitude": store.longitude,
        "location_name": store.location_name
    }

