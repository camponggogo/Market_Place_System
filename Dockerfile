# Food Court Management System - Docker
# ใช้ PyMySQL (ไม่ต้องติดตั้ง mysqlclient/libmysql)
FROM python:3.12-slim

WORKDIR /app

# รันแบบ non-root (optional แต่แนะนำสำหรับ production)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Application
COPY . .

RUN mkdir -p /app/logs /app/data

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Gunicorn + Uvicorn workers
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "120", \
     "--access-logfile", "-", "--error-logfile", "-"]
