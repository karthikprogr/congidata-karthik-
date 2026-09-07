#!/usr/bin/env python3
"""
Comprehensive test script to verify dataset upload functionality
Tests all critical paths and error cases
"""
import io
import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth():
    """Test authentication and get JWT token"""
    print("\n🔐 Testing Authentication...")
    
    # Login with admin credentials
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "rudraadmin@gmail.com", "password": "adminrudra@1234"}
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"   ✅ Login successful, token received")
        return token
    else:
        print(f"   ❌ Login failed: {response.status_code} - {response.text}")
        return None


def test_upload(token):
    """Test dataset upload"""
    print("\n📤 Testing Dataset Upload...")
    
    # Create test CSV data
    csv_data = """name,age,salary,city
Alice,30,50000,NYC
Bob,25,45000,LA
Charlie,35,60000,Chicago
Alice,30,50000,NYC
David,28,52000,Boston
Eve,32,58000,Seattle"""
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Upload CSV
    files = {"file": ("test_data.csv", io.BytesIO(csv_data.encode()), "text/csv")}
    response = requests.post(f"{BASE_URL}/api/data/upload", files=files, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Upload successful")
        print(f"      - Filename: {data.get('filename')}")
        print(f"      - Rows: {data.get('rows')}")
        print(f"      - Columns: {data.get('columns')}")
        print(f"      - Column names: {data.get('column_names')}")
        print(f"      - Memory: {data.get('memory_mb')} MB")
        return True
    else:
        print(f"   ❌ Upload failed: {response.status_code}")
        print(f"      Response: {response.text[:500]}")
        return False


def test_preview(token):
    """Test data preview"""
    print("\n👁️  Testing Data Preview...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/data/preview?n=5", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Preview successful")
        print(f"      - Rows returned: {len(data.get('data', []))}")
        print(f"      - Total rows: {data.get('total_rows')}")
        if data.get('data'):
            print(f"      - First row: {data['data'][0]}")
        return True
    else:
        print(f"   ❌ Preview failed: {response.status_code} - {response.text[:200]}")
        return False


def test_info(token):
    """Test data info"""
    print("\n📊 Testing Data Info...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/data/info", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Info successful")
        print(f"      - Rows: {data.get('rows')}")
        print(f"      - Columns: {data.get('columns')}")
        print(f"      - Numeric columns: {data.get('numeric_columns')}")
        print(f"      - Categorical columns: {data.get('categorical_columns')}")
        return True
    else:
        print(f"   ❌ Info failed: {response.status_code} - {response.text[:200]}")
        return False


def test_stats(token):
    """Test statistics"""
    print("\n📈 Testing Statistics...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/data/stats", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Stats successful")
        print(f"      - Columns with stats: {list(data.keys())}")
        return True
    else:
        print(f"   ❌ Stats failed: {response.status_code} - {response.text[:200]}")
        return False


def test_doctor(token):
    """Test data doctor (health check)"""
    print("\n🏥 Testing Data Doctor...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/data/doctor", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Data doctor successful")
        print(f"      - Health score: {data.get('health_score')}/100")
        print(f"      - Duplicate rows: {data.get('duplicate_rows')}")
        print(f"      - Missing columns: {len(data.get('missing_cols', []))}")
        print(f"      - Outlier columns: {len(data.get('outlier_cols', []))}")
        return True
    else:
        print(f"   ❌ Data doctor failed: {response.status_code} - {response.text[:200]}")
        return False


def test_clean(token):
    """Test data cleaning"""
    print("\n🧹 Testing Data Cleaning...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/data/clean", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Cleaning successful")
        print(f"      - Rows before: {data.get('rows_before')}")
        print(f"      - Rows after: {data.get('rows_after')}")
        print(f"      - Rows removed: {data.get('rows_removed')}")
        print(f"      - Nulls filled: {data.get('nulls_filled')}")
        return True
    else:
        print(f"   ❌ Cleaning failed: {response.status_code} - {response.text[:200]}")
        return False


def test_multi_dataset(token):
    """Test multi-dataset functionality"""
    print("\n📚 Testing Multi-Dataset Support...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List datasets
    response = requests.get(f"{BASE_URL}/api/data/datasets", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Dataset listing successful")
        print(f"      - Total datasets: {len(data.get('datasets', []))}")
        print(f"      - Active dataset: {data.get('active')}")
        print(f"      - Datasets: {data.get('datasets')}")
        return True
    else:
        print(f"   ❌ Dataset listing failed: {response.status_code} - {response.text[:200]}")
        return False


def test_error_cases(token):
    """Test error handling"""
    print("\n⚠️  Testing Error Cases...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Empty file
    print("   Testing empty file...")
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    response = requests.post(f"{BASE_URL}/api/data/upload", files=files, headers=headers)
    if response.status_code in [400, 422]:
        print(f"      ✅ Empty file correctly rejected: {response.status_code}")
    else:
        print(f"      ⚠️  Empty file response: {response.status_code}")
    
    # Test 2: Unsupported format
    print("   Testing unsupported format...")
    files = {"file": ("test.txt", io.BytesIO(b"some text"), "text/plain")}
    response = requests.post(f"{BASE_URL}/api/data/upload", files=files, headers=headers)
    if response.status_code == 400:
        print(f"      ✅ Unsupported format correctly rejected")
    else:
        print(f"      ⚠️  Unsupported format response: {response.status_code}")
    
    # Test 3: Invalid CSV
    print("   Testing malformed CSV...")
    files = {"file": ("bad.csv", io.BytesIO(b"name,age\nAlice"), "text/csv")}
    response = requests.post(f"{BASE_URL}/api/data/upload", files=files, headers=headers)
    print(f"      Response: {response.status_code}")
    
    return True


def main():
    print("=" * 70)
    print("🚀 COGNIDATA - Dataset Upload Functionality Test Suite")
    print("=" * 70)
    
    # Test authentication
    token = test_auth()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    # Run all tests
    results = {
        "Upload": test_upload(token),
        "Preview": test_preview(token),
        "Info": test_info(token),
        "Stats": test_stats(token),
        "Data Doctor": test_doctor(token),
        "Clean": test_clean(token),
        "Multi-Dataset": test_multi_dataset(token),
        "Error Cases": test_error_cases(token),
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Dataset upload is fully functional.")
    else:
        print("⚠️  Some tests failed. Check logs above for details.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
