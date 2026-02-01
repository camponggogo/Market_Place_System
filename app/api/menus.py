"""
Menu API - ระบบจัดการรายการสินค้า
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models import Menu, Store

router = APIRouter(prefix="/api/menus", tags=["menus"])


class MenuCreate(BaseModel):
    store_id: int
    name: str
    description: Optional[str] = None
    unit_price: float
    is_active: bool = True


class MenuUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[float] = None
    is_active: Optional[bool] = None


class MenuResponse(BaseModel):
    id: int
    store_id: int
    name: str
    description: Optional[str] = None
    unit_price: float
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/", response_model=MenuResponse)
async def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    """
    สร้างรายการสินค้าใหม่
    """
    # ตรวจสอบว่า store มีอยู่จริง
    store = db.query(Store).filter(Store.id == menu.store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    new_menu = Menu(
        store_id=menu.store_id,
        name=menu.name,
        description=menu.description,
        unit_price=menu.unit_price,
        is_active=menu.is_active
    )
    db.add(new_menu)
    db.commit()
    db.refresh(new_menu)
    
    return MenuResponse(
        id=new_menu.id,
        store_id=new_menu.store_id,
        name=new_menu.name,
        description=new_menu.description,
        unit_price=new_menu.unit_price,
        is_active=new_menu.is_active,
        created_at=new_menu.created_at.isoformat() if new_menu.created_at else "",
        updated_at=new_menu.updated_at.isoformat() if new_menu.updated_at else None
    )


@router.get("/store/{store_id}", response_model=List[MenuResponse])
async def get_menus_by_store(
    store_id: int,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    ดึงรายการสินค้าตาม store_id
    """
    # ตรวจสอบว่า store มีอยู่จริง
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    query = db.query(Menu).filter(Menu.store_id == store_id)
    
    if is_active is not None:
        query = query.filter(Menu.is_active == is_active)
    
    menus = query.order_by(Menu.created_at.desc()).all()
    
    return [
        MenuResponse(
            id=menu.id,
            store_id=menu.store_id,
            name=menu.name,
            description=menu.description,
            unit_price=menu.unit_price,
            is_active=menu.is_active,
            created_at=menu.created_at.isoformat() if menu.created_at else "",
            updated_at=menu.updated_at.isoformat() if menu.updated_at else None
        )
        for menu in menus
    ]


@router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu(menu_id: int, db: Session = Depends(get_db)):
    """
    ดึงข้อมูลรายการสินค้า
    """
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    return MenuResponse(
        id=menu.id,
        store_id=menu.store_id,
        name=menu.name,
        description=menu.description,
        unit_price=menu.unit_price,
        is_active=menu.is_active,
        created_at=menu.created_at.isoformat() if menu.created_at else "",
        updated_at=menu.updated_at.isoformat() if menu.updated_at else None
    )


@router.put("/{menu_id}", response_model=MenuResponse)
async def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    db: Session = Depends(get_db)
):
    """
    อัปเดตรายการสินค้า
    """
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    if menu_update.name is not None:
        menu.name = menu_update.name
    if menu_update.description is not None:
        menu.description = menu_update.description
    if menu_update.unit_price is not None:
        menu.unit_price = menu_update.unit_price
    if menu_update.is_active is not None:
        menu.is_active = menu_update.is_active
    
    db.commit()
    db.refresh(menu)
    
    return MenuResponse(
        id=menu.id,
        store_id=menu.store_id,
        name=menu.name,
        description=menu.description,
        unit_price=menu.unit_price,
        is_active=menu.is_active,
        created_at=menu.created_at.isoformat() if menu.created_at else "",
        updated_at=menu.updated_at.isoformat() if menu.updated_at else None
    )


@router.delete("/{menu_id}")
async def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    """
    ลบรายการสินค้า
    """
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    db.delete(menu)
    db.commit()
    
    return {"message": "Menu deleted successfully"}

