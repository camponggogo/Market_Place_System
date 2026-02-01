"""
Script สำหรับติดตั้ง dependencies ที่ขาด
"""
import sys
import subprocess
from pathlib import Path

def install_requirements():
    """ติดตั้ง dependencies จาก requirements.txt (ใน code/)"""
    root_dir = Path(__file__).parent.parent / "code"
    requirements_file = root_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    print("=" * 60)
    print("Installing Dependencies from requirements.txt")
    print("=" * 60)
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("\n✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error installing dependencies: {e}")
        return False

def install_test_requirements():
    """ติดตั้ง test dependencies (ใน code/)"""
    root_dir = Path(__file__).parent.parent / "code"
    test_requirements_file = root_dir / "requirements-test.txt"
    
    if not test_requirements_file.exists():
        print("⚠️  requirements-test.txt not found (optional)")
        return True
    
    print("\n" + "=" * 60)
    print("Installing Test Dependencies")
    print("=" * 60)
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(test_requirements_file)
        ])
        print("\n✅ Test dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n⚠️  Error installing test dependencies: {e}")
        return False

def upgrade_pip():
    """อัพเกรด pip"""
    print("=" * 60)
    print("Upgrading pip...")
    print("=" * 60)
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ])
        print("✅ pip upgraded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error upgrading pip: {e}")
        return False

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("Food Court Management System - Dependency Installer")
    print("=" * 60 + "\n")
    
    # Upgrade pip first
    upgrade_pip()
    
    # Install main dependencies
    success = install_requirements()
    
    # Install test dependencies (optional)
    install_test_requirements()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Installation completed!")
        print("\nNext steps:")
        print("  1. Run: python scripts/check_setup.py")
        print("  2. Run: python scripts/create_database.py")
        print("  3. Run: python scripts/init_db.py")
    else:
        print("⚠️  Installation had errors. Please check the output above.")
    print("=" * 60 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

