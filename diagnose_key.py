import json
import os
import re
from cryptography.hazmat.primitives import serialization

def diagnose_key():
    json_path = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"
    if not os.path.exists(json_path):
        print("File not found")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)
    
    pk = data.get('private_key', '')
    print(f"Original Length: {len(pk)}")
    
    # Check for non-standard characters
    non_base64 = re.findall(r'[^A-Za-z0-9+/=\s-]', pk)
    if non_base64:
        print(f"Found suspicious characters: {set(non_base64)}")
    
    # Try to load with Cryptography
    try:
        serialization.load_pem_private_key(pk.encode(), password=None)
        print("✅ Cryptography library successfully loaded the PEM key.")
    except Exception as e:
        print(f"❌ Cryptography failed to load key: {e}")
        
        # Try cleaning and loading
        meat = pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").strip()
        meat = "".join(meat.split())
        clean_pk = f"-----BEGIN PRIVATE KEY-----\n{meat}\n-----END PRIVATE KEY-----\n"
        try:
            serialization.load_pem_private_key(clean_pk.encode(), password=None)
            print("✅ Key loaded successfully AFTER cleaning.")
            print("Action: We need to use the cleaned version in the script.")
        except Exception as e2:
            print(f"❌ Key still failed after cleaning: {e2}")

if __name__ == "__main__":
    diagnose_key()
