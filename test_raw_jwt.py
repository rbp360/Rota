import os
import json
import time
import base64
import hmac
import hashlib
import requests

JSON_PATH = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"

def test_raw_jwt():
    print("--- RAW JWT AUTH TEST ---")
    if not os.path.exists(JSON_PATH):
        print("Error: JSON file missing")
        return

    with open(JSON_PATH) as f:
        data = json.load(f)

    private_key = data['private_key']
    client_email = data['client_email']
    token_uri = data.get('token_uri', 'https://oauth2.googleapis.com/token')

    # JWT Header
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().replace("=", "")
    
    # JWT Payload
    now = int(time.time())
    payload = base64.urlsafe_b64encode(json.dumps({
        "iss": client_email,
        "scope": "https://www.googleapis.com/auth/cloud-platform",
        "aud": token_uri,
        "exp": now + 3600,
        "iat": now
    }).encode()).decode().replace("=", "")
    
    signing_input = f"{header}.{payload}"
    
    print(f"System Time (Seconds): {now}")
    print(f"Handshake Payload: {signing_input[:50]}...")

    # We can't easily sign RSA in raw python without a library, 
    # but we can try to use the google library's signer directly.
    from google.auth import crypt
    from google.auth import _helpers

    try:
        signer = crypt.RSASigner.from_string(private_key)
        signature = signer.sign(signing_input.encode())
        jwt = f"{signing_input}.{_helpers.decode_bytes(base64.urlsafe_b64encode(signature)).replace('=', '')}"
        
        print("JWT Created. Requesting token from Google...")
        resp = requests.post(token_uri, data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt
        })
        
        if resp.status_code == 200:
            print("✅ SUCCESS! Raw JWT was accepted. Token received.")
        else:
            print(f"❌ FAILED: {resp.status_code}")
            print(f"Response: {resp.text}")
            
    except Exception as e:
        print(f"❌ Error during signing: {e}")

if __name__ == "__main__":
    test_raw_jwt()
