#!/usr/bin/env python3
"""
Automated test script for NotionShare application.
Tests backend API endpoints via Windows PowerShell.
"""
import subprocess
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": f"test_{int(time.time())}@example.com",
    "password": "testpass123"
}

def run_powershell_request(method, endpoint, data=None, token=None):
    """Execute HTTP request via curl from WSL."""
    url = f"{BASE_URL}{endpoint}"

    cmd = ["curl.exe", "-s", "-X", method, url, "-H", "Content-Type: application/json"]

    if token:
        cmd.extend(["-H", f"Authorization: Bearer {token}"])

    if data:
        cmd.extend(["-d", json.dumps(data)])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return None

    try:
        return json.loads(result.stdout)
    except:
        return result.stdout

def test_health():
    """Test health endpoint."""
    print("Testing /docs (API documentation)...")
    result = run_powershell_request("GET", "/docs")
    if result:
        print("✓ API docs accessible")
        return True
    print("❌ API docs failed")
    return False

def test_register():
    """Test user registration."""
    print(f"\nTesting registration for {TEST_USER['email']}...")
    result = run_powershell_request("POST", "/auth/register", TEST_USER)
    if result and "email" in result:
        print(f"✓ Registration successful: {result['email']}")
        return True
    print("❌ Registration failed")
    return False

def test_login():
    """Test user login."""
    print(f"\nTesting login...")
    result = run_powershell_request("POST", "/auth/login", TEST_USER)
    if result and "access_token" in result:
        print("✓ Login successful")
        return result["access_token"]
    print("❌ Login failed")
    return None

def test_get_user(token):
    """Test get current user."""
    print("\nTesting /auth/me...")
    result = run_powershell_request("GET", "/auth/me", token=token)
    if result and "email" in result:
        print(f"✓ Get user successful: {result['email']}")
        return True
    print("❌ Get user failed")
    return False

def test_list_configs(token):
    """Test list configurations."""
    print("\nTesting /configs/...")
    result = run_powershell_request("GET", "/configs/", token=token)
    if isinstance(result, list):
        print(f"✓ List configs successful: {len(result)} configs")
        return True
    print("❌ List configs failed")
    return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("NotionShare Automated Tests")
    print("=" * 60)

    # Give server time to start
    print("\nWaiting for server to start...")
    time.sleep(3)

    tests = [
        ("Health Check", test_health),
        ("User Registration", test_register),
        ("User Login", test_login),
    ]

    results = []
    token = None

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result is not None and result != False))
            if test_name == "User Login" and result:
                token = result
        except Exception as e:
            print(f"❌ {test_name} exception: {e}")
            results.append((test_name, False))

    # Tests requiring auth
    if token:
        auth_tests = [
            ("Get Current User", lambda: test_get_user(token)),
            ("List Configurations", lambda: test_list_configs(token)),
        ]

        for test_name, test_func in auth_tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} exception: {e}")
                results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nPassed: {passed}/{total}")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
