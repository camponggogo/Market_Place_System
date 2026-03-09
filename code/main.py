
"""
Marketplace Management System - Main Application
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.database import engine, Base
from app.api import customer, crypto, reports, tax, refund, stores, counter, payment_hub, reports_payment, admin, admin_config, profiles, geo, store_quick_amounts, menus, payment_callback, signage, pos_settings, locale_settings, program_settings, auth, member, member_scan, admin_ecoupon, admin_ads, admin_backup_audit
from app.config import BACKEND_URL, SECRET_KEY
import os

# Paths relative to main.py (code/) so server works from project root or code/
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.join(_BASE_DIR, "app", "static")
_CONTRACTS_DIR = os.path.join(_BASE_DIR, "app", "contracts")

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Marketplace Management System",
    description="ระบบบริหารจัดการ Marketplace ที่รองรับการชำระเงินหลากหลายรูปแบบ",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "false").lower() == "true" else None,  # ซ่อน docs ใน production
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "false").lower() == "true" else None
)

# Security Middleware (สำหรับ public internet)
try:
    from middleware.security import SecurityMiddleware
    app.add_middleware(
        SecurityMiddleware,
        rate_limit_per_minute=300  # 300 ต่อนาทีต่อ IP (path ที่ poll บ่อยเช่น /admin, /api/signage ไม่นับ)
    )
except ImportError:
    # ถ้าไม่มี middleware ก็ข้ามไป
    pass

# Session middleware - สำหรับ Store POS Login
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS middleware - ระบุ allowed origins ใน production
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests
)

# Include routers
app.include_router(customer.router)
app.include_router(crypto.router)
app.include_router(reports.router)
app.include_router(tax.router)
app.include_router(refund.router)
app.include_router(stores.router)
app.include_router(counter.router)
app.include_router(payment_hub.router)
app.include_router(reports_payment.router)
app.include_router(admin.router)
app.include_router(admin_config.router)
app.include_router(profiles.router)
app.include_router(geo.router)
app.include_router(store_quick_amounts.router)
app.include_router(menus.router)
app.include_router(payment_callback.router)
app.include_router(signage.router)
app.include_router(pos_settings.router)
app.include_router(locale_settings.router)
app.include_router(program_settings.router)
app.include_router(auth.router)
app.include_router(member.router)
app.include_router(member_scan.router)
app.include_router(admin_ecoupon.router)
app.include_router(admin_ads.router)
app.include_router(admin_backup_audit.router)

# Mount static files (must be before specific routes to avoid conflicts)
if os.path.exists(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
if os.path.exists(_CONTRACTS_DIR):
    app.mount("/contracts", StaticFiles(directory=_CONTRACTS_DIR), name="contracts")

# Mount images directory
_imgs_dir = os.path.join(_BASE_DIR, "app", "imgs")
if os.path.exists(_imgs_dir):
    app.mount("/static/imgs", StaticFiles(directory=_imgs_dir), name="imgs")

# Mount menu images (local cached 480x640)
_menu_images_dir = os.path.join(_BASE_DIR, "data", "menu_images")
os.makedirs(_menu_images_dir, exist_ok=True)
app.mount("/menu-images", StaticFiles(directory=_menu_images_dir), name="menu_images")

# Mount videos (Smartparking.mp4 etc. สำหรับ signage)
_videos_dir = os.path.join(os.path.dirname(_BASE_DIR), "videos")
if os.path.exists(_videos_dir):
    app.mount("/videos", StaticFiles(directory=_videos_dir), name="videos")

# โฟลเดอร์สื่อโฆษณา (upload จาก Admin) - ใช้ path บน server หรืออัปโหลด
_ad_media_dir = os.path.join(_BASE_DIR, "data", "ad_media")
os.makedirs(_ad_media_dir, exist_ok=True)
app.mount("/ad-media", StaticFiles(directory=_ad_media_dir), name="ad_media")

# Favicon - ลด 404 ในคอนโซลเมื่อเบราว์เซอร์ขอ favicon.ico
@app.get("/favicon.ico")
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)


# Redirect root to admin dashboard (ต้องล็อกอินและเป็น admin ก่อน)
@app.get("/admin")
async def admin_dashboard(request: Request):
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    file_path = os.path.join(_BASE_DIR, "app", "static", "admin_dashboard.html")
    return FileResponse(file_path)

@app.get("/store-pos-login")
async def store_pos_login_page():
    """หน้า Login ก่อนเข้า Store POS"""
    from fastapi.responses import FileResponse
    file_path = os.path.join(_BASE_DIR, "app", "static", "store_pos_login.html")
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file_path)


def _get_session(request: Request):
    """อ่าน session แบบเดียวกับ auth (รองรับทั้ง request.session และ request.state)"""
    return getattr(request.state, "session", None) or getattr(request, "session", None)


def _require_admin_redirect(request: Request):
    """ใช้เฉพาะกับเส้นทาง Admin เท่านั้น: ถ้าไม่ได้ล็อกอินหรือไม่ใช่ admin ให้ redirect ไป store-pos-login (หน้า store-pos ไม่เรียกฟังก์ชันนี้)"""
    from fastapi.responses import RedirectResponse
    session = _get_session(request)
    if not session or not session.get("user_id"):
        return RedirectResponse(url="/store-pos-login?next=" + (request.url.path or "/admin"), status_code=302)
    if not session.get("is_admin"):
        return RedirectResponse(url="/store-pos-login?next=" + (request.url.path or "/admin") + "&error=admin_required", status_code=302)
    return None


@app.get("/store-pos")
async def store_pos(request: Request):
    """Store POS - ต้องล็อกอินก่อน (มี user_id + สิทธิ์ร้าน) ไม่บังคับสิทธิ์ admin เฉพาะส่วน /admin ขึ้นไปที่ต้องเป็น admin"""
    from fastapi.responses import FileResponse, RedirectResponse

    session = _get_session(request)
    if not session or not session.get("user_id"):
        next_url = "/store-pos"
        return RedirectResponse(url=f"/store-pos-login?next={next_url}", status_code=302)

    file_path = os.path.join(_BASE_DIR, "app", "static", "store_pos.html")
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file_path)


@app.get("/store-menus")
async def store_menus_page(request: Request):
    """หน้าจัดการเมนู - ต้องล็อกอินก่อน"""
    from fastapi.responses import FileResponse, RedirectResponse
    session = _get_session(request)
    if not session or not session.get("user_id"):
        return RedirectResponse(url="/store-pos-login?next=/store-menus", status_code=302)
    file_path = os.path.join(_BASE_DIR, "app", "static", "store_menus.html")
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/store-pos-settings")
async def store_pos_settings_page(request: Request):
    """หน้า Web Setting สำหรับตั้งค่า Store POS - ต้องล็อกอินก่อน"""
    from fastapi.responses import FileResponse, RedirectResponse
    session = _get_session(request)
    if not session or not session.get("user_id"):
        return RedirectResponse(url="/store-pos-login?next=/store-pos-settings", status_code=302)
    file_path = os.path.join(_BASE_DIR, "app", "static", "store_pos_settings.html")
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/links-qr")
async def links_qr_page():
    """หน้าแสดง QR Code ลิงก์ Store-POS/Member, Signage, Admin"""
    from fastapi.responses import FileResponse
    file_path = os.path.join(_BASE_DIR, "app", "static", "links_qr.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/signage")
async def signage_page():
    from fastapi.responses import FileResponse
    file_path = os.path.join(_BASE_DIR, "app", "static", "signage.html")
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file_path)


@app.get("/launch")
async def launch_pos_and_signage():
    """เปิด store-pos และ signage ใน 2 หน้าต่าง (สำหรับเครื่อง POS 2 จอ)"""
    from fastapi.responses import FileResponse, HTMLResponse
    file_path = os.path.join(_BASE_DIR, "app", "static", "launch.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(content="<p>launch.html not found</p>")

@app.get("/customer-qr")
async def customer_qr():
    from fastapi.responses import FileResponse
    file_path = os.path.join(_BASE_DIR, "app", "static", "customer_qr.html")
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file_path)

@app.get("/customer")
async def customer():
    from fastapi.responses import FileResponse
    file_path = os.path.join(_BASE_DIR, "app", "static", "customer.html")
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file_path)


# ---------- ลูกค้าสมาชิกออนไลน์ (Member App) - รองรับ Mobile + Line OA ----------
@app.get("/member")
async def member_login_page():
    """หน้าแรกสมาชิก: Login (ชื่อผู้ใช้ หรือ เบอร์ หรือ อีเมล + รหัสผ่าน)"""
    from fastapi.responses import FileResponse
    path = os.path.join(_BASE_DIR, "app", "static", "member_login.html")
    if not os.path.exists(path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)

@app.get("/member/register")
async def member_register_page():
    """หน้าลงทะเบียนสมาชิก"""
    from fastapi.responses import FileResponse
    path = os.path.join(_BASE_DIR, "app", "static", "member_register.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/member/dashboard")
async def member_dashboard_page():
    """หน้าแดชบอร์ดสมาชิก (ยอดเงิน, แต้ม, คูปอง, โปรโมชั่น) + เมนูล่าง"""
    from fastapi.responses import FileResponse
    path = os.path.join(_BASE_DIR, "app", "static", "member_dashboard.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/member/scan")
async def member_scan_page():
    """หน้าสแกน QR PromptPay เพื่อจ่ายด้วย e-coupon"""
    from fastapi.responses import FileResponse
    path = os.path.join(_BASE_DIR, "app", "static", "member_scan.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/emergency-backup")
async def emergency_backup_page(request: Request):
    """หน้ากรอกข้อมูลรายการสำรอง (กรณีไฟดับ/ระบบล่ม) - ต้องล็อกอิน; ดูย้อนหลังได้เฉพาะ admin"""
    from fastapi.responses import FileResponse, RedirectResponse
    session = _get_session(request)
    if not session or not session.get("user_id"):
        return RedirectResponse(url="/store-pos-login?next=/emergency-backup", status_code=302)
    path = os.path.join(_BASE_DIR, "app", "static", "emergency_backup.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/audit-logs")
async def audit_logs_page(request: Request):
    """หน้า Audit Logs - เฉพาะ admin (ต้องล็อกอิน admin ก่อน)"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "audit_logs.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/admin/config")
async def admin_config_page(request: Request):
    """หน้าจัดการ config.ini (เฉพาะ admin)"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "admin_config.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/admin/transfer-report")
async def admin_transfer_report_page(request: Request):
    """หน้ารายงานยอดโอนให้ร้านค้า (เฉพาะ admin)"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "admin_transfer_report.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/admin/gp-settings")
async def admin_gp_settings_page(request: Request):
    """หน้าตั้งค่า % GP (อัตราหัก Gross Profit) (เฉพาะ admin)"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "admin_gp_settings.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/admin/coupon")
async def admin_coupon_page(request: Request):
    """หน้าจัดการคูปอง / E-Coupon"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "admin_coupon.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/admin/payment-settings")
async def admin_payment_settings_page(request: Request):
    """หน้าตั้งค่าการรับเงิน (Payment Gateway)"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "admin_payment_settings.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/admin/calendar")
async def admin_calendar_page(request: Request):
    """ปฏิทินโฆษณา / โปรโมชั่น (Campaign) แบบ Google Calendar"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "admin_calendar.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/admin/ads-summary")
async def admin_ads_summary_page(request: Request):
    """หน้าสรุปผลการตอบรับโฆษณา (Views / Clicks)"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "admin_ads_summary.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/admin/ads-manage")
async def admin_ads_manage_page(request: Request):
    """จัดการโฆษณา / ตั้งเวลาปล่อย (start_at, end_at, store)"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "admin_ads_manage.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/report-qr-payments")
async def report_qr_payments_page(request: Request):
    """รายงานการชำระ QR / Stripe (Back Transactions) - สำหรับ Admin (ทุกร้าน)"""
    from fastapi.responses import FileResponse
    redirect = _require_admin_redirect(request)
    if redirect:
        return redirect
    path = os.path.join(_BASE_DIR, "app", "static", "report_qr_payments.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/store-report-qr-payments")
async def store_report_qr_payments_page(request: Request):
    """รายงาน QR/Stripe เฉพาะร้าน – ต้องล็อกอิน Store POS; แสดงเฉพาะร้านที่ user มีสิทธิ์"""
    from fastapi.responses import FileResponse, RedirectResponse
    session = _get_session(request)
    if not session or not session.get("user_id"):
        return RedirectResponse(url="/store-pos-login?next=/store-report-qr-payments", status_code=302)
    path = os.path.join(_BASE_DIR, "app", "static", "store_report_qr_payments.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin")


@app.get("/health")
async def health_check():
    """Health check - รวมการตรวจสอบ DB"""
    from app.database import check_db_connection
    db_ok, db_msg = check_db_connection()
    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "database": "ok" if db_ok else db_msg,
    }

