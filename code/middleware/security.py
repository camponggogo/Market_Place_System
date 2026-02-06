"""
Security Middleware for Public Internet Access
เพิ่มความปลอดภัยสำหรับ public web
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, HTMLResponse
import time
import os
from collections import defaultdict
from typing import Dict, List

# Rate limiting storage (ใน production ควรใช้ Redis)
rate_limit_store: Dict[str, list] = defaultdict(list)

# Paths ที่ไม่นับ rate limit (polling / หน้าเว็บที่โหลดบ่อย)
RATE_LIMIT_SKIP_PREFIXES: List[str] = [
    "/admin",
    "/api/signage",
    "/api/payment-callback/stores/",
    "/store-pos",
    "/signage",
    "/customer",
    "/launch",
    "/static",
    "/favicon",
]


def _should_skip_rate_limit(path: str) -> bool:
    for prefix in RATE_LIMIT_SKIP_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware สำหรับ public internet
    - Rate limiting (ยกเว้น path ที่ poll บ่อย เช่น signage, admin)
    - CORS headers
    - Security headers
    """
    
    def __init__(self, app, rate_limit_per_minute: int = 300):
        super().__init__(app)
        self.rate_limit_per_minute = rate_limit_per_minute
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path or ""

        # ไม่นับ rate limit สำหรับ path ที่โหลด/ poll บ่อย
        if not _should_skip_rate_limit(path):
            if not self._check_rate_limit(client_ip):
                accept = (request.headers.get("accept") or "").lower()
                if "text/html" in accept or path in ("/admin", "/"):
                    return HTMLResponse(
                        status_code=429,
                        content="""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Too Many Requests</title></head><body>
                        <h1>429 Too Many Requests</h1>
                        <p>คำขอมากเกินไป กรุณารอสักครู่แล้วลองใหม่</p>
                        <p><a href="/admin">กลับหน้า Admin</a></p>
                        </body></html>""",
                        media_type="text/html; charset=utf-8",
                    )
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                )
        
        # Security headers
        response = await call_next(request)
        
        # เพิ่ม security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # CORS headers (ถ้ายังไม่มี)
        if "Access-Control-Allow-Origin" not in response.headers:
            # ควรระบุ domain ที่อนุญาตแทน "*"
            allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
            origin = request.headers.get("origin")
            if origin in allowed_origins or "*" in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin or "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """ตรวจสอบ rate limit"""
        now = time.time()
        minute_ago = now - 60
        
        # ลบ requests เก่า
        rate_limit_store[client_ip] = [
            req_time for req_time in rate_limit_store[client_ip]
            if req_time > minute_ago
        ]
        
        # ตรวจสอบจำนวน requests
        if len(rate_limit_store[client_ip]) >= self.rate_limit_per_minute:
            return False
        
        # เพิ่ม request ใหม่
        rate_limit_store[client_ip].append(now)
        return True

