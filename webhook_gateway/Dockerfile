FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# โฟลเดอร์บันทึกไฟล์ (เมื่อ SAVE_TO_FILES=true)
RUN mkdir -p /app/data

ENV PORT=80
EXPOSE 80

CMD ["python", "webhook.py"]
