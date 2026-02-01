"""
Uvicorn Configuration for Production (Windows Compatible)
เหมาะสำหรับ Windows หรือ development
"""
import multiprocessing

# Server configuration
HOST = "0.0.0.0"
PORT = 8000

# Workers - สำหรับ Windows ใช้ 4 workers
# สำหรับ Linux/Unix สามารถใช้มากกว่านี้ได้
WORKERS = 4

# Log level
LOG_LEVEL = "info"

# Reload (development only)
RELOAD = False

# Access log
ACCESS_LOG = True

# Timeout
TIMEOUT_KEEP_ALIVE = 5
TIMEOUT_GRACEFUL_SHUTDOWN = 30

