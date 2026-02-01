import os
import firebase_admin
from firebase_admin import credentials, firestore

p = 'rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json'
print(f"Checking {p}...")
if os.path.exists(p):
    print("File exists. Connecting...")
    try:
        cred = credentials.Certificate(p)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        docs = list(db.collection('staff').limit(3).stream())
        print(f"Connection successful. Found {len(docs)} staff.")
        for d in docs:
            print(f" - {d.to_dict().get('name')}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("File DOES NOT exist!")
