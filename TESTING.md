# Testing Guide - Food Court Management System

## การติดตั้ง Dependencies สำหรับ Testing

```bash
pip install -r requirements-test.txt
```

หรือติดตั้งพร้อมกับ requirements หลัก:

```bash
pip install -r requirements.txt -r requirements-test.txt
```

## โครงสร้าง Tests

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_models.py          # Tests for database models
├── test_payment_hub.py     # Tests for Payment Hub Service
├── test_api_counter.py     # Tests for Counter API
└── test_api_payment_hub.py # Tests for Payment Hub API
```

## วิธีรัน Tests

### รัน Tests ทั้งหมด

```bash
pytest
```

### รัน Tests พร้อม Coverage Report

```bash
pytest --cov=app --cov-report=html
```

Coverage report จะถูกสร้างในโฟลเดอร์ `htmlcov/`

### รัน Tests เฉพาะไฟล์

```bash
pytest tests/test_payment_hub.py
```

### รัน Tests เฉพาะฟังก์ชัน

```bash
pytest tests/test_payment_hub.py::test_exchange_to_foodcourt_id_cash
```

### รัน Tests แบบ Verbose

```bash
pytest -v
```

### รัน Tests แบบแสดง Output

```bash
pytest -s
```

## Test Fixtures

### `db_session`
- สร้าง test database session (SQLite in-memory)
- ใช้สำหรับทดสอบ database operations
- Auto cleanup หลัง test เสร็จ

### `client`
- สร้าง FastAPI test client
- ใช้สำหรับทดสอบ API endpoints
- Auto override database dependency

## ตัวอย่าง Tests

### Test Payment Hub Service

```python
def test_exchange_to_foodcourt_id_cash(db_session):
    """Test exchanging cash to Food Court ID"""
    payment_hub = PaymentHub(db_session)
    
    foodcourt_id = payment_hub.exchange_to_foodcourt_id(
        amount=1000.00,
        payment_method=PaymentMethod.CASH,
        counter_id=1,
        counter_user_id=1
    )
    
    assert foodcourt_id.initial_amount == 1000.00
    assert foodcourt_id.status == "active"
```

### Test API Endpoint

```python
def test_exchange_foodcourt_id(client):
    """Test exchanging to Food Court ID via API"""
    response = client.post(
        "/api/counter/exchange",
        json={
            "amount": 1000.00,
            "payment_method": "cash",
            "counter_id": 1,
            "counter_user_id": 1
        }
    )
    
    assert response.status_code == 200
    assert response.json()["success"] == True
```

## Coverage Goals

- **Target Coverage**: 80%+
- **Critical Paths**: 100% (Payment Hub, Counter API, Payment Hub API)
- **Models**: 90%+

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices

1. **Test Isolation**: แต่ละ test ควรเป็นอิสระจากกัน
2. **Use Fixtures**: ใช้ fixtures สำหรับ setup/teardown
3. **Clear Names**: ตั้งชื่อ test ให้ชัดเจนว่า test อะไร
4. **AAA Pattern**: Arrange, Act, Assert
5. **Test Edge Cases**: ทดสอบกรณีผิดปกติด้วย

## Debugging Tests

### รัน Tests พร้อม Debugger

```bash
pytest --pdb
```

### Print Debug Information

```python
def test_something(db_session):
    result = some_function()
    print(f"Debug: {result}")  # ใช้ pytest -s เพื่อดู output
    assert result == expected
```

## Performance Testing

สำหรับ performance tests ใช้ `pytest-benchmark`:

```bash
pip install pytest-benchmark
```

```python
def test_performance(benchmark):
    result = benchmark(some_function)
    assert result is not None
```

## หมายเหตุ

- Tests ใช้ SQLite in-memory database เพื่อความเร็ว
- ไม่ต้องมี MariaDB running สำหรับรัน tests
- Tests จะ cleanup ข้อมูลอัตโนมัติหลังเสร็จ

