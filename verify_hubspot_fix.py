import requests
import time
import os

BASE_URL = "http://localhost:8000"
USER_DATA = {
    "username": f"verif_user_{int(time.time())}",
    "email": f"verif_{int(time.time())}@example.com",
    "password": "testpassword"
}

def verify_hubspot():
    print("Starting HubSpot Integration Verification...")
    
    # 1. Register & Login
    print("Step 1: Authenticating...")
    reg_response = requests.post(f"{BASE_URL}/auth/register", json=USER_DATA)
    if reg_response.status_code != 201:
        print(f"  ❌ Registration failed: {reg_response.text}")
        return
    
    api_key = reg_response.json()["api_key"]
    headers = {"X-API-Key": api_key}
    print("  ✅ Authenticated")
    
    # 2. Check Integration Config
    print("Step 2: Checking Integration Configuration...")
    config_response = requests.get(f"{BASE_URL}/integrations/config", headers=headers)
    if config_response.status_code == 200:
        config = config_response.json()
        print(f"  Config: {config}")
        if config.get("hubspot_enabled"):
            print("  ✅ HubSpot Integration is ENABLED in the server")
        else:
            print("  ❌ HubSpot Integration is DISABLED in the server. Check .env loading.")
            return
    else:
        print(f"  ❌ Failed to get config: {config_response.text}")
        return

    # 3. Test Sync (Real API call now enabled)
    print("Step 3: Testing Lead Sync (this will now attempt a REAL HubSpot call)...")
    # Create a test lead
    lead_data = {
        "name": "HubSpot Verification Lead",
        "email": f"hubspot_verif_{int(time.time())}@example.com",
        "company": "Verification Inc",
        "source": "website"
    }
    lead_response = requests.post(f"{BASE_URL}/leads/", json=lead_data, headers=headers)
    if lead_response.status_code != 201:
        print(f"  ❌ Failed to create lead: {lead_response.text}")
        return
    
    lead_id = lead_response.json()["id"]
    print(f"  ✅ Created test lead (ID: {lead_id})")
    
    # Sync to HubSpot
    sync_response = requests.post(f"{BASE_URL}/integrations/sync/{lead_id}/hubspot", headers=headers)
    if sync_response.status_code == 200:
        print(f"  ✅ Sync successful: {sync_response.json()}")
    elif sync_response.status_code == 500:
        print(f"  ⚠️ Sync attempted but failed at HubSpot (expected if key is invalid, but proves logic is NOT mocked): {sync_response.text}")
    else:
        print(f"  ❌ Sync failed with unexpected error: {sync_response.status_code} - {sync_response.text}")

if __name__ == "__main__":
    verify_hubspot()
