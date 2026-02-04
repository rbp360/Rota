import json
import os
from google.oauth2 import service_account
import google.auth.transport.requests

def test_auth():
    json_path = "rotaai-49847-d923810f254e.json"
    print(f"Checking {json_path}...")
    
    if not os.path.exists(json_path):
        print("File not found!")
        return

    try:
        # 1. Load credentials
        creds = service_account.Credentials.from_service_account_file(
            json_path, 
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        print(f"Project ID: {creds.project_id}")
        print(f"Service Account Email: {creds.service_account_email}")
        
        # 2. Try to refresh (get a token)
        print("Attempting to fetch OAuth2 token...")
        request = google.auth.transport.requests.Request()
        creds.refresh(request)
        
        print("✅ SUCCESS! Token fetched successfully.")
        print(f"Token (first 10 chars): {creds.token[:10]}...")
        
    except Exception as e:
        print("\n❌ AUTH REFRESH FAILED!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        if "invalid_grant" in str(e).lower():
            print("\nPossible Causes:")
            print("1. SYSTEM CLOCK: Your computer's time is wrong. Sync it now.")
            print("2. REVOKED KEY: This service account key might have been deleted in Google Console.")
            print("3. CORRUPT KEY: The private_key text in the JSON is mangled.")
            
        import datetime
        print(f"\nYour Local System Time: {datetime.datetime.now()}")

if __name__ == "__main__":
    test_auth()
