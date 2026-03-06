import firebase_admin
from firebase_admin import credentials, firestore
import os

CREDS_PATH = "rotaai-49847-d923810f254e.json"

def test():
    print("Testing Firestore Access...")
    if not os.path.exists(CREDS_PATH):
        print("Missing JSON")
        return
    
    cred = credentials.Certificate(CREDS_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Connecting to 'staff' collection...")
    docs = db.collection("staff").limit(1).get()
    for doc in docs:
        print(f"Success! Found staff: {doc.to_dict().get('name')}")
    print("Done.")

if __name__ == "__main__":
    test()
