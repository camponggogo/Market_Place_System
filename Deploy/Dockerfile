# Market_Place_System - Docker
# Build context = โปรเจกต์ root, โค้ดอยู่ที่ code/
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencies จาก code/
COPY code/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Application จาก code/
COPY code/ .

RUN mkdir -p /app/logs /app/data

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=639

EXPOSE 639

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:639/health || exit 1

CMD ["sh", "-c", "gunicorn main:app --bind 0.0.0.0:${PORT} --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120 --access-logfile - --error-logfile -"]
