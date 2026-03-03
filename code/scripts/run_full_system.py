#!/usr/bin/env python3
"""
Run เต็มระบบ: รัน migration (ถ้ายังไม่รัน), ทำ simple self-test แล้ว start เซิร์ฟเวอร์
ใช้: python scripts/run_full_system.py
     python scripts/run_full_system.py --no-serve   (เทสอย่างเดียว ไม่เปิดเซิร์ฟเวอร์)
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def run(cmd, cwd=None):
    cwd = cwd or str(ROOT)
    p = subprocess.run(cmd, shell=True, cwd=cwd)
    return p.returncode == 0

def main():
    serve = "--no-serve" not in sys.argv
    print("=== Run full system ===\n")

    # 1. Migrations (optional - อาจรันแล้ว)
    print("1. Migration (member_online)...")
    if run("python scripts/migrate_member_online.py"):
        print("   OK\n")
    else:
        print("   (skip or check DB)\n")
    print("   Migration (audit_menu, ad_impressions)...")
    if run("python scripts/migrate_audit_menu.py"):
        print("   OK\n")
    else:
        print("   (skip or check DB)\n")

    # 2. Simple self-test
    print("2. Simple self-test...")
    if not run("python scripts/simple_self_test.py"):
        print("\nSelf-test failed. Fix errors before starting server.")
        return 1
    print("")

    if not serve:
        print("Done (--no-serve: server not started).")
        return 0

    # 3. Start server
    print("3. Starting server (uvicorn main:app --host 0.0.0.0 --port 8000)...")
    print("   Press Ctrl+C to stop.\n")
    return subprocess.call([
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
    ], cwd=str(ROOT))

if __name__ == "__main__":
    sys.exit(main())
