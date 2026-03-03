#!/usr/bin/env python3
"""
Simple Self-Test: ตรวจสอบระบบแบบเร็ว (ไม่ต้องเปิดเซิร์ฟเวอร์)
ใช้: python scripts/simple_self_test.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def ok(name):
    print("[PASS]", name)

def fail(name, e):
    print("[FAIL]", name, "-", e)
    return False

def main():
    n_ok, n_fail = 0, 0

    # 1. DB
    try:
        from app.database import check_db_connection
        ok_db, _ = check_db_connection()
        if ok_db:
            ok("Database connection")
            n_ok += 1
        else:
            n_fail += 1
            fail("Database connection", "check_db_connection returned False")
    except Exception as e:
        n_fail += 1
        fail("Database connection", e)

    # 2. App import
    try:
        from main import app
        ok("App import (main:app)")
        n_ok += 1
    except Exception as e:
        n_fail += 1
        fail("App import", e)
        return 1

    # 3. API tests (TestClient)
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
    except Exception as e:
        n_fail += 1
        fail("TestClient", e)
        return 1

    # Health
    try:
        r = client.get("/health")
        assert r.status_code == 200 and "status" in (r.json() or {}), r.status_code
        ok("GET /health")
        n_ok += 1
    except Exception as e:
        n_fail += 1
        fail("GET /health", e)

    # Member register
    try:
        import time
        uid = str(int(time.time()))[-6:]
        r = client.post("/api/member/register", json={
            "username": "t" + uid,
            "phone": "089" + uid,
            "password": "pass1234",
        })
        assert r.status_code == 200, (r.status_code, r.text)
        ok("POST /api/member/register")
        n_ok += 1
    except Exception as e:
        n_fail += 1
        fail("POST /api/member/register", e)

    # Member login
    try:
        r = client.post("/api/member/login", json={"login_id": "t" + uid, "password": "pass1234"})
        assert r.status_code == 200, r.status_code
        token = (r.json() or {}).get("token")
        assert token, "no token"
        ok("POST /api/member/login")
        n_ok += 1
    except Exception as e:
        n_fail += 1
        fail("POST /api/member/login", e)

    # Member me
    try:
        r = client.get("/api/member/me", headers={"Authorization": "Bearer " + token})
        assert r.status_code == 200 and "balance" in (r.json() or {}), r.status_code
        ok("GET /api/member/me")
        n_ok += 1
    except Exception as e:
        n_fail += 1
        fail("GET /api/member/me", e)

    # Member ads
    try:
        r = client.get("/api/member/ads")
        assert r.status_code == 200, r.status_code
        ok("GET /api/member/ads")
        n_ok += 1
    except Exception as e:
        n_fail += 1
        fail("GET /api/member/ads", e)

    # Admin ecoupon list
    try:
        r = client.get("/api/admin/ecoupon/list")
        assert r.status_code == 200, r.status_code
        ok("GET /api/admin/ecoupon/list")
        n_ok += 1
    except Exception as e:
        n_fail += 1
        fail("GET /api/admin/ecoupon/list", e)

    # Pages
    for path in ["/member", "/member/register", "/member/dashboard", "/member/scan", "/store-pos-login", "/admin"]:
        try:
            r = client.get(path)
            assert r.status_code in (200, 302), (path, r.status_code)
            ok("GET " + path)
            n_ok += 1
        except Exception as e:
            n_fail += 1
            fail("GET " + path, e)

    # Store POS redirect when not logged in
    try:
        r = client.get("/store-pos", follow_redirects=False)
        assert r.status_code == 302, r.status_code
        ok("GET /store-pos -> 302 redirect")
        n_ok += 1
    except Exception as e:
        n_fail += 1
        fail("GET /store-pos redirect", e)

    # Summary
    print("")
    print("---")
    print("Result: %d passed, %d failed" % (n_ok, n_fail))
    if n_fail > 0:
        sys.exit(1)
    print("Simple self-test OK.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
