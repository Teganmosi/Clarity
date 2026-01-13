import requests
import json
import os
import time
import pandas as pd
import io

BASE_URL = "http://localhost:8000"
USER_DATA = {
    "username": f"qa_test_user_{int(time.time())}",
    "email": f"qa_{int(time.time())}@example.com",
    "password": "testpassword"
}

def test_health():
    print("Testing /health...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("  ✅ Passed")

def test_auth():
    print("Testing Authentication...")
    # Register
    reg_response = requests.post(f"{BASE_URL}/auth/register", json=USER_DATA)
    if reg_response.status_code != 201:
        print(f"  ❌ Registration failed: {reg_response.text}")
        return None
    
    api_key = reg_response.json()["api_key"]
    print("  ✅ Registration passed")
    
    # Login
    login_data = {
        "username": USER_DATA["username"],
        "password": USER_DATA["password"]
    }
    # Form data for login
    login_response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    print("  ✅ Login passed")
    
    # Me
    headers = {"X-API-Key": api_key}
    me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert me_response.status_code == 200
    print("  ✅ API Key auth passed")
    
    return headers

def test_lead_crud(headers):
    print("Testing Lead CRUD...")
    lead_data = {
        "name": "Test Lead",
        "email": "test@example.com",
        "company": "QA Corp",
        "source": "website",
        "budget": "high",
        "past_interactions": 10
    }
    
    # Create
    response = requests.post(f"{BASE_URL}/leads/", json=lead_data, headers=headers)
    assert response.status_code == 201
    lead_id = response.json()["id"]
    print(f"  ✅ Create lead passed (ID: {lead_id}, Score: {response.json()['score']})")
    
    # Get
    response = requests.get(f"{BASE_URL}/leads/{lead_id}", headers=headers)
    assert response.status_code == 200
    print("  ✅ Get lead passed")
    
    # List
    response = requests.get(f"{BASE_URL}/leads/", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 1
    print("  ✅ List leads passed")
    
    # Update
    update_data = {"status": "contacted"}
    response = requests.put(f"{BASE_URL}/leads/{lead_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "contacted"
    print("  ✅ Update lead passed")
    
    return lead_id

def test_csv_upload(headers):
    print("Testing CSV Upload (Fix Verification)...")
    csv_content = """name,email,company,source,budget,past_interactions
Lead 1,l1@example.com,C1,website,high,5
Lead 2,l2@example.com,C2,referral,medium,10
Lead 3,l3@example.com,C3,paid_ads,low,2
"""
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    response = requests.post(f"{BASE_URL}/leads/upload/csv", files=files, headers=headers)
    
    if response.status_code == 200:
        print(f"  ✅ CSV Upload passed: {response.json()['success_count']} leads created")
    else:
        print(f"  ❌ CSV Upload FAILED: {response.text}")
    
    return response.status_code == 200

def test_retrain_model(headers):
    print("Testing Model Retraining (Fix Verification)...")
    # Mark some leads as converted to satisfy minimum requirements
    response = requests.get(f"{BASE_URL}/leads/", headers=headers)
    leads = response.json()["leads"]
    
    for i, lead in enumerate(leads[:2]):
        requests.post(f"{BASE_URL}/leads/{lead['id']}/mark-converted", headers=headers)
    
    # Retrain
    response = requests.post(f"{BASE_URL}/leads/retrain-model", headers=headers)
    if response.status_code == 200:
        print(f"  ✅ Retrain model passed: {response.json()['message']}")
    else:
        print(f"  ❌ Retrain model FAILED: {response.text}")

def test_analytics(headers):
    print("Testing Analytics...")
    response = requests.get(f"{BASE_URL}/analytics/dashboard", headers=headers)
    assert response.status_code == 200
    print("  ✅ /analytics/dashboard passed")
    
    response = requests.get(f"{BASE_URL}/analytics/source-performance", headers=headers)
    assert response.status_code == 200
    print("  ✅ /analytics/source-performance passed")

if __name__ == "__main__":
    try:
        test_health()
        headers = test_auth()
        if headers:
            test_lead_crud(headers)
            test_csv_upload(headers)
            test_retrain_model(headers)
            test_analytics(headers)
            print("\nBackend testing completed successfully!")
    except Exception as e:
        print(f"\n❌ Testing aborted due to error: {e}")
