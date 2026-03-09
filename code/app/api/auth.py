"""
Auth API - Store POS Login (ใช้ตาราง users + user_store)
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models import User, UserStore, Store

router = APIRouter(prefix="/api/auth", tags=["auth"])

try:
    import bcrypt
    def _hash_password(pwd: str) -> str:
        return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
    def _verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
except ImportError:
    from passlib.context import CryptContext
    _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def _hash_password(pwd: str) -> str:
        return _pwd.hash(pwd)
    def _verify_password(plain: str, hashed: str) -> bool:
        return _pwd.verify(plain, hashed)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user_id: int
    username: str
    name: Optional[str]
    store_ids: List[int]
    stores: List[dict]  # [{ id, name }]
    is_admin: bool = False


class MeResponse(BaseModel):
    user_id: int
    username: str
    name: Optional[str]
    store_ids: List[int]
    stores: List[dict]
    is_admin: bool = False


def _get_session_user(request: Request) -> Optional[dict]:
    """ดึงข้อมูล user จาก session"""
    session = getattr(request.state, "session", None) or getattr(request, "session", None)
    if not session:
        return None
    user_id = session.get("user_id")
    if not user_id:
        return None
    return {
        "user_id": user_id,
        "username": session.get("username", ""),
        "name": session.get("name"),
        "store_ids": session.get("store_ids", []),
        "is_admin": session.get("is_admin", False),
    }


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """ล็อกอิน: ตรวจสอบ username/password + ตรวจสอบสิทธิ์จาก user_store"""
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not _verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    # ตรวจสอบสิทธิ์จาก user_store (admin สามารถล็อกอินได้แม้ไม่มีร้าน — เพื่อเข้า Admin)
    user_stores = db.query(UserStore).filter(UserStore.user_id == user.id).all()
    store_ids = [us.store_id for us in user_stores]
    is_admin = getattr(user, "is_admin", False)

    if not store_ids and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="ไม่พบสิทธิ์เข้าถึงร้านค้า กรุณาติดต่อผู้ดูแลระบบ",
        )

    # โหลด store names
    stores = db.query(Store).filter(Store.id.in_(store_ids)).all() if store_ids else []
    stores_data = [{"id": s.id, "name": s.name} for s in stores]

    # บันทึก session
    session = request.session
    session["user_id"] = user.id
    session["username"] = user.username
    session["name"] = user.name
    session["store_ids"] = store_ids
    session["is_admin"] = getattr(user, "is_admin", False)

    return LoginResponse(
        success=True,
        user_id=user.id,
        username=user.username,
        name=user.name,
        store_ids=store_ids,
        stores=stores_data,
        is_admin=getattr(user, "is_admin", False),
    )


@router.get("/me", response_model=MeResponse)
async def me(request: Request, db: Session = Depends(get_db)):
    """ตรวจสอบสถานะล็อกอิน"""
    user_data = _get_session_user(request)
    if not user_data:
        raise HTTPException(status_code=401, detail="ไม่ได้ล็อกอิน")

    store_ids = user_data.get("store_ids", [])
    if store_ids:
        stores = db.query(Store).filter(Store.id.in_(store_ids)).all()
        stores_data = [{"id": s.id, "name": s.name} for s in stores]
    else:
        stores_data = []

    return MeResponse(
        user_id=user_data["user_id"],
        username=user_data["username"],
        name=user_data.get("name"),
        store_ids=store_ids,
        stores=stores_data,
        is_admin=user_data.get("is_admin", False),
    )


@router.post("/logout")
async def logout(request: Request):
    """ออกจากระบบ"""
    session = request.session
    session.clear()
    return JSONResponse(content={"success": True})


def get_current_session_user(request: Request) -> dict:
    """Dependency: ดึง user จาก session (ใช้กับ Store POS / Admin)"""
    user_data = _get_session_user(request)
    if not user_data:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบ")
    return user_data


def require_admin(request: Request) -> dict:
    """Dependency: ต้องล็อกอินและเป็น admin ขึ้นไป"""
    user_data = get_current_session_user(request)
    if not user_data.get("is_admin"):
        raise HTTPException(status_code=403, detail="ต้องเป็นผู้ดูแลระดับ admin ขึ้นไป")
    return user_data
