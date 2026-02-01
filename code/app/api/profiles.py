"""
Profiles API - ระบบจัดการ Profiles (เช่าล็อก, เช่าร้าน, จัดงาน event)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models import Profile, Event, Store

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


class ProfileCreate(BaseModel):
    name: str
    description: Optional[str] = None
    profile_type: str  # "lock_rental", "store_rental", "event"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProfileResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    profile_type: str
    is_active: bool
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    profile_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    location: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    profile_id: Optional[int]
    name: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    location: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=ProfileResponse)
async def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    """สร้าง Profile ใหม่"""
    db_profile = Profile(**profile.dict())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


@router.get("/", response_model=List[ProfileResponse])
async def list_profiles(
    profile_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """ดึงรายการ Profiles"""
    query = db.query(Profile)
    
    if profile_type:
        query = query.filter(Profile.profile_type == profile_type)
    if is_active is not None:
        query = query.filter(Profile.is_active == is_active)
    
    return query.order_by(Profile.created_at.desc()).all()


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """ดึง Profile ตาม ID"""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/events/", response_model=EventResponse)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """สร้าง Event ใหม่"""
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.get("/events/", response_model=List[EventResponse])
async def list_events(
    profile_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """ดึงรายการ Events"""
    query = db.query(Event)
    
    if profile_id:
        query = query.filter(Event.profile_id == profile_id)
    if is_active is not None:
        query = query.filter(Event.is_active == is_active)
    
    return query.order_by(Event.start_date.desc()).all()


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """ดึง Event ตาม ID"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

