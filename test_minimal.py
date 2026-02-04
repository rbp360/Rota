import json
import os
from google.oauth2 import service_account
from google.cloud import firestore

JSON_PATH = "rotaai-49847-d923810f254e.json"

def test_minimal():
    print(f"--- MINIMAL AUTH TEST ---")
    if not os.path.exists(JSON_PATH):
        print("JSON Error: File not found")
        return

    try:
        # 1. Load the JSON manually
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
        
        print(f"Checking JSON Content:")
        print(f"  Project: {data.get('project_id')}")
        print(f"  Email: {data.get('client_email')}")
        
        # 2. Re-format the private key to be 100% sure it's valid PEM
        # Sometimes Windows/Pasting adds garbage
        pk = data.get("private_key", "")
        if "\\n" in pk:
            print("  HINT: Found literal \\n, converting to real newlines.")
            pk = pk.replace("\\n", "\n")
        
        # Ensure it has the headers
        if "-----BEGIN PRIVATE KEY-----" not in pk:
            print("  ERROR: Key is missing PEM headers!")
            return

        # 3. Connect using the REPAIRED key object
        creds = service_account.Credentials.from_service_account_info({
            **data,
            "private_key": pk
        })
        
        db = firestore.Client(project=data.get('project_id'), credentials=creds)
        
        print("Attempting to write test document...")
        test_ref = db.collection("test_connection").document("ping")
        test_ref.set({"status": "Success", "timestamp": str(os.times())})
        
        print("✅ SUCCESS! Authentication and Write both worked.")
        
    except Exception as e:
        print(f"❌ MINIMAL TEST FAILED!")
        print(f"Error: {e}")
        if "invalid_grant" in str(e):
            print("\nThis usually means the Private Key inside the JSON is mathematically incorrect")
            print("or it has been Revoked in the Google Cloud Console.")

if __name__ == "__main__":
    test_minimal()
