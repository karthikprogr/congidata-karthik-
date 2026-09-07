#!/usr/bin/env python3
"""
Comprehensive startup verification script
Checks all critical components before running the application
"""
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verify Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False


def check_dependencies():
    """Check if critical dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required = [
        "fastapi",
        "uvicorn",
        "pandas",
        "numpy",
        "sqlalchemy",
        "pydantic",
        "jose",
        "passlib",
        "slowapi",
        "cachetools",
        "openpyxl",
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"   ✅ {pkg}")
        except ImportError:
            print(f"   ❌ {pkg} - MISSING")
            missing.append(pkg)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def check_pyarrow():
    """Check if pyarrow is installed for parquet support"""
    print("\n🏹 Checking pyarrow (parquet support)...")
    try:
        import pyarrow
        print(f"   ✅ pyarrow installed")
        return True
    except ImportError:
        print(f"   ⚠️  pyarrow not installed - parquet will fallback to CSV")
        print("   Run: pip install pyarrow")
        return False


def check_env_file():
    """Check if .env file exists"""
    print("\n⚙️  Checking configuration...")
    
    env_path = Path("cognidata/backend/.env")
    if env_path.exists():
        print(f"   ✅ .env file found")
        
        # Check critical env vars
        with open(env_path) as f:
            content = f.read()
            
        checks = {
            "OPENAI_API_KEY": "OPENAI_API_KEY" in content and "sk-" in content,
            "SECRET_KEY": "SECRET_KEY" in content and len(content) > 50,
            "DATABASE_URL": "DATABASE_URL" in content,
        }
        
        for key, exists in checks.items():
            if exists:
                print(f"   ✅ {key} configured")
            else:
                print(f"   ⚠️  {key} missing or invalid")
        
        return all(checks.values())
    else:
        print(f"   ❌ .env file not found at {env_path}")
        return False


def check_directory_structure():
    """Verify required directories exist"""
    print("\n📁 Checking directory structure...")
    
    required_dirs = [
        "cognidata/backend/app",
        "cognidata/backend/app/api",
        "cognidata/backend/app/services",
        "cognidata/backend/app/models",
        "cognidata/frontend/src",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_dataset_store():
    """Check if dataset store directory exists"""
    print("\n💾 Checking dataset store...")
    
    store_path = Path("cognidata/backend/.dataset_store")
    if store_path.exists():
        print(f"   ✅ Dataset store exists")
        
        # Count existing datasets
        user_dirs = list(store_path.glob("*"))
        if user_dirs:
            total_files = sum(1 for d in user_dirs if d.is_dir() for f in d.glob("*.parquet"))
            print(f"   📊 {len(user_dirs)} user directories, {total_files} datasets")
    else:
        print(f"   ℹ️  Dataset store will be created on first upload")
    
    return True


def check_database():
    """Check if database file exists (SQLite)"""
    print("\n🗄️  Checking database...")
    
    db_path = Path("cognidata/backend/cognidata.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ Database exists ({size_mb:.2f} MB)")
    else:
        print(f"   ℹ️  Database will be created on first run")
    
    return True


def check_frontend_deps():
    """Check if frontend dependencies are installed"""
    print("\n🎨 Checking frontend...")
    
    node_modules = Path("cognidata/frontend/node_modules")
    if node_modules.exists():
        print(f"   ✅ node_modules exists")
        return True
    else:
        print(f"   ⚠️  node_modules not found")
        print("   Run: cd cognidata/frontend && npm install")
        return False


def check_ports():
    """Check if required ports are available"""
    print("\n🔌 Checking ports...")
    
    import socket
    
    ports = {
        8000: "Backend API",
        5173: "Frontend Dev Server"
    }
    
    available = True
    for port, service in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"   ⚠️  Port {port} ({service}) is already in use")
            available = False
        else:
            print(f"   ✅ Port {port} ({service}) available")
    
    return available


def main():
    print("=" * 70)
    print("🔍 COGNIDATA - Startup Verification")
    print("=" * 70)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Dependencies", check_dependencies()),
        ("PyArrow", check_pyarrow()),
        ("Configuration", check_env_file()),
        ("Directory Structure", check_directory_structure()),
        ("Dataset Store", check_dataset_store()),
        ("Database", check_database()),
        ("Frontend Dependencies", check_frontend_deps()),
        ("Ports", check_ports()),
    ]
    
    print("\n" + "=" * 70)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 70)
    
    for name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    print(f"\n🎯 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ All checks passed! Ready to start.")
        print("\nTo start the application:")
        print("   cd cognidata")
        print("   powershell -ExecutionPolicy Bypass -File run.ps1")
    elif passed >= total - 2:
        print("\n⚠️  Minor issues detected, but application should work.")
        print("   Some features may be limited.")
    else:
        print("\n❌ Critical issues detected. Please fix errors before starting.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
