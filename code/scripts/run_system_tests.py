"""
รันทดสอบระบบทั้งหมด: migration, import app, API member/admin, หน้าเว็บ
ใช้: python scripts/run_system_tests.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_imports():
    from app.api import member, member_scan, admin_ecoupon, admin_ads
    from main import app
    return True

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200, r.status_code
    assert r.json().get("status") in ("healthy", "degraded"), r.json()
    return True

def test_member_register_login_me(client):
    import time
    uid = str(int(time.time()))[-8:]
    r = client.post("/api/member/register", json={
        "username": "syscheck" + uid,
        "phone": "081" + uid,
        "password": "pass1234",
    })
    assert r.status_code == 200, (r.status_code, r.text)
    r = client.post("/api/member/login", json={"login_id": "syscheck" + uid, "password": "pass1234"})
    assert r.status_code == 200, (r.status_code, r.text)
    token = r.json().get("token")
    assert token, r.json()
    r = client.get("/api/member/me", headers={"Authorization": "Bearer " + token})
    assert r.status_code == 200, (r.status_code, r.text)
    assert "balance" in r.json(), r.json()
    return True

def test_member_ads(client):
    r = client.get("/api/member/ads")
    assert r.status_code == 200, r.status_code
    return True

def test_admin_ecoupon_ads(client):
    r = client.post("/api/admin/ecoupon/issue", json={"amount": 50, "payment_method": "cash"})
    assert r.status_code == 200, (r.status_code, r.text)
    r = client.get("/api/admin/ecoupon/list")
    assert r.status_code == 200, r.status_code
    r = client.get("/api/admin/ads/list")
    assert r.status_code == 200, r.status_code
    return True

def test_pages(client):
    for path in ["/member", "/member/register", "/member/dashboard", "/member/scan", "/store-pos-login", "/admin"]:
        r = client.get(path)
        assert r.status_code in (200, 302), (path, r.status_code)
    r = client.get("/store-pos", follow_redirects=False)
    assert r.status_code == 302, r.status_code
    return True

def main():
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    tests = [
        ("imports", lambda: test_imports()),
        ("health", lambda: test_health(client)),
        ("member register/login/me", lambda: test_member_register_login_me(client)),
        ("member ads", lambda: test_member_ads(client)),
        ("admin ecoupon & ads", lambda: test_admin_ecoupon_ads(client)),
        ("pages", lambda: test_pages(client)),
    ]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print("[OK]", name)
        except Exception as e:
            print("[FAIL]", name, ":", e)
            failed.append(name)
    if failed:
        print("Failed:", failed)
        sys.exit(1)
    print("All system tests passed.")


if __name__ == "__main__":
    main()
