
"""
Food Court Management System - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.api import customer, crypto, reports, tax, refund, stores, counter, payment_hub, reports_payment, admin, profiles, geo, store_quick_amounts, menus, payment_callback, signage
from app.config import BACKEND_URL
import os

# Paths relative to main.py (code/) so server works from project root or code/
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.join(_BASE_DIR, "app", "static")
_CONTRACTS_DIR = os.path.join(_BASE_DIR, "app", "contracts")

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Food Court Management System",
    description="ระบบบริหารจัดการ Food Court ที่รองรับการชำระเงินหลากหลายรูปแบบ",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "false").lower() == "true" else None,  # ซ่อน docs ใน production
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "false").lower() == "true" else None
)

# Security Middleware (สำหรับ public internet)
try:
    from middleware.security import SecurityMiddleware
    app.add_middleware(
        SecurityMiddleware,
        rate_limit_per_minute=60  # 60 requests ต่อนาทีต่อ IP
    )
except ImportError:
    # ถ้าไม่มี middleware ก็ข้ามไป
    pass

# CORS middleware - ระบุ allowed origins ใน production
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
app.include_router(profiles.router)
app.include_router(geo.router)
app.include_router(store_quick_amounts.router)
app.include_router(menus.router)
app.include_router(payment_callback.router)
app.include_router(signage.router)

# Mount static files (must be before specific routes to avoid conflicts)
if os.path.exists(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
if os.path.exists(_CONTRACTS_DIR):
    app.mount("/contracts", StaticFiles(directory=_CONTRACTS_DIR), name="contracts")

# Mount images directory
_imgs_dir = os.path.join(_BASE_DIR, "app", "imgs")
if os.path.exists(_imgs_dir):
    app.mount("/static/imgs", StaticFiles(directory=_imgs_dir), name="imgs")

# Redirect root to admin dashboard
@app.get("/admin")
async def admin_dashboard():
    from fastapi.responses import FileResponse
    file_path = os.path.join(_BASE_DIR, "app", "static", "admin_dashboard.html")
    return FileResponse(file_path)

@app.get("/store-pos")
async def store_pos():
    from fastapi.responses import FileResponse
    file_path = os.path.join(_BASE_DIR, "app", "static", "store_pos.html")
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
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


@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

