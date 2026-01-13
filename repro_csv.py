import requests
import json
import time

BASE_URL = "http://localhost:8000"

def repro():
    # 1. Register/Login to get headers
    username = f"repro_user_{int(time.time())}"
    reg_data = {"username": username, "email": f"{username}@example.com", "password": "password"}
    requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    login_response = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": "password"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test with valid lowercase columns
    print("Testing with lowercase columns (name, email)...")
    csv_content = "name,email\nTest1,t1@example.com"
    files = {'file': ('test_lower.csv', csv_content, 'text/csv')}
    response = requests.post(f"{BASE_URL}/leads/upload/csv", files=files, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

    # 3. Test with uppercase columns
    print("\nTesting with uppercase columns (Name, Email)...")
    csv_content = "Name,Email\nTest2,t2@example.com"
    files = {'file': ('test_upper.csv', csv_content, 'text/csv')}
    response = requests.post(f"{BASE_URL}/leads/upload/csv", files=files, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

    # 4. Test with mixed case columns
    print("\nTesting with mixed case columns (NAME, email)...")
    csv_content = "NAME,email\nTest3,t3@example.com"
    files = {'file': ('test_mixed.csv', csv_content, 'text/csv')}
    response = requests.post(f"{BASE_URL}/leads/upload/csv", files=files, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

if __name__ == "__main__":
    repro()
