# code/

โฟลเดอร์เก็บ **source code** ของ Market_Place_System

- **app/** – FastAPI app (api, models, services, static, contracts, utils)
- **main.py** – จุดเข้าแอป (uvicorn main:app)
- **config.ini** – การตั้งค่า (override ได้ด้วย environment)
- **requirements.txt** – Dependencies
- **middleware/**, **tests/**, **hardware/**

## รันจาก root โปรเจกต์

```bash
# ตั้ง PYTHONPATH ให้ชี้ไปที่โฟลเดอร์ code/
PYTHONPATH=code uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

หรือใช้สคริปต์ใน **Run/** เช่น `Run/quick_start.ps1`
