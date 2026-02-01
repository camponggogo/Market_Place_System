"""
Universal Server Startup Script
ตรวจสอบ OS และเลือก server ที่เหมาะสม
"""
import sys
import platform
import subprocess

def detect_os():
    """ตรวจสอบ OS"""
    os_name = platform.system().lower()
    return os_name

def start_server():
    """เริ่ม server ตาม OS"""
    os_name = detect_os()
    
    print("=" * 50)
    print("Food Court Management System - Server Startup")
    print("=" * 50)
    print(f"Detected OS: {platform.system()} {platform.release()}")
    print()
    
    if os_name == "windows":
        print("⚠️  Windows detected!")
        print("Gunicorn ไม่รองรับ Windows (ใช้ fcntl module ที่เป็น Unix-only)")
        print()
        print("ตัวเลือกสำหรับ Windows:")
        print("1. Uvicorn (แนะนำ) - รองรับ Windows, เร็ว, เสถียร")
        print("2. Hypercorn - เร็วกว่า, รองรับ HTTP/2")
        print()
        
        choice = input("เลือกตัวเลือก (1=Uvicorn, 2=Hypercorn, Enter=Uvicorn): ").strip()
        
        if choice == "2":
            print("\n🚀 Starting Hypercorn...")
            print("Command: hypercorn main:app --bind 0.0.0.0:8000 --workers 4")
            print()
            try:
                subprocess.run([
                    sys.executable, "-m", "hypercorn",
                    "main:app",
                    "--bind", "0.0.0.0:8000",
                    "--workers", "4"
                ])
            except KeyboardInterrupt:
                print("\n\nServer stopped.")
        else:
            print("\n🚀 Starting Uvicorn with 4 workers...")
            print("Command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4")
            print()
            try:
                subprocess.run([
                    sys.executable, "-m", "uvicorn",
                    "main:app",
                    "--host", "0.0.0.0",
                    "--port", "8000",
                    "--workers", "4"
                ])
            except KeyboardInterrupt:
                print("\n\nServer stopped.")
    
    else:
        # Linux/Unix/Mac
        print("✅ Unix-like OS detected!")
        print("สามารถใช้ Gunicorn ได้")
        print()
        print("ตัวเลือก:")
        print("1. Gunicorn + Uvicorn Workers (แนะนำสำหรับ production)")
        print("2. Hypercorn (เร็วกว่า, รองรับ HTTP/2)")
        print("3. Uvicorn (ง่ายที่สุด)")
        print()
        
        choice = input("เลือกตัวเลือก (1=Gunicorn, 2=Hypercorn, 3=Uvicorn, Enter=Gunicorn): ").strip()
        
        if choice == "2":
            print("\n🚀 Starting Hypercorn...")
            print("Command: hypercorn main:app --config hypercorn_config.py")
            print()
            try:
                subprocess.run([
                    sys.executable, "-m", "hypercorn",
                    "main:app",
                    "--config", "hypercorn_config.py"
                ])
            except KeyboardInterrupt:
                print("\n\nServer stopped.")
        elif choice == "3":
            print("\n🚀 Starting Uvicorn with 4 workers...")
            print("Command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4")
            print()
            try:
                subprocess.run([
                    sys.executable, "-m", "uvicorn",
                    "main:app",
                    "--host", "0.0.0.0",
                    "--port", "8000",
                    "--workers", "4"
                ])
            except KeyboardInterrupt:
                print("\n\nServer stopped.")
        else:
            print("\n🚀 Starting Gunicorn + Uvicorn Workers...")
            print("Command: gunicorn main:app -c gunicorn_config.py")
            print()
            try:
                subprocess.run([
                    sys.executable, "-m", "gunicorn",
                    "main:app",
                    "-c", "gunicorn_config.py"
                ])
            except KeyboardInterrupt:
                print("\n\nServer stopped.")

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
        sys.exit(0)

