"""
Gunicorn Configuration for Production
เหมาะสำหรับ: ~1000 users/day, ~200 stores/day
Public Internet Access

⚠️  หมายเหตุ: Gunicorn ไม่รองรับ Windows
   สำหรับ Windows ใช้ Uvicorn หรือ Hypercorn แทน
   ดู README_SERVERS.md สำหรับรายละเอียด
"""
import multiprocessing
import os
import sys

# ตรวจสอบ OS
if sys.platform == "win32":
    raise RuntimeError(
        "Gunicorn ไม่รองรับ Windows!\n"
        "สำหรับ Windows ใช้:\n"
        "  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4\n"
        "หรือ:\n"
        "  hypercorn main:app --bind 0.0.0.0:8000 --workers 4\n"
        "ดู README_SERVERS.md สำหรับรายละเอียด"
    )

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes - ปรับให้เหมาะสมกับ scale เล็ก-กลาง
# สำหรับ 1000 users/day = ~0.7 requests/second (เฉลี่ย)
# ใช้ 4-8 workers ก็เพียงพอ
cpu_count = multiprocessing.cpu_count()
workers = min(cpu_count * 2, 8)  # สูงสุด 8 workers
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 60  # เพิ่ม timeout สำหรับ public internet
keepalive = 5  # เพิ่ม keepalive

# Logging
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "foodcourt-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (ถ้าต้องการ)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

