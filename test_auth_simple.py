import json
import os
import datetime
from google.oauth2 import service_account
import google.auth.transport.requests

def test_auth():
    json_path = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"
    results = []
    
    results.append(f"Checking {json_path}...")
    
    if not os.path.exists(json_path):
        results.append("File not found!")
    else:
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            results.append(f"Project ID: {data.get('project_id')}")
            results.append(f"Email: {data.get('client_email')}")
            
            # Load credentials
            creds = service_account.Credentials.from_service_account_info(data, scopes=["https://www.googleapis.com/auth/cloud-platform"])
            
            # Try to refresh (get a token)
            results.append("Attempting to fetch OAuth2 token...")
            request = google.auth.transport.requests.Request()
            creds.refresh(request)
            
            results.append("✅ SUCCESS! Token fetched successfully.")
            results.append(f"Token Length: {len(creds.token)}")
            
        except Exception as e:
            results.append("\n❌ AUTH REFRESH FAILED!")
            results.append(f"Error Type: {type(e).__name__}")
            results.append(f"Error Message: {str(e)}")
            
            if "invalid_grant" in str(e).lower():
                results.append("\nHINT: JWT Signature is invalid.")
    
    # Save to file
    with open("auth_status.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    print("Results written to auth_status.txt")

if __name__ == "__main__":
    test_auth()
