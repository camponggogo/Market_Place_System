"""
Hypercorn Configuration
Hypercorn เป็น ASGI server ที่เร็วและรองรับ HTTP/2, HTTP/3
"""
from hypercorn.config import Config

config = Config()
config.bind = ["0.0.0.0:8000"]
config.workers = 4  # จำนวน workers
config.keep_alive_timeout = 65
config.graceful_timeout = 30
config.accesslog = "-"  # stdout
config.errorlog = "-"  # stderr
config.loglevel = "info"

# HTTP/2 Support (ถ้า browser รองรับ)
config.h2 = True

# SSL (ถ้าต้องการ)
# config.certfile = "/path/to/certfile"
# config.keyfile = "/path/to/keyfile"

