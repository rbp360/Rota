import firebase_admin
from firebase_admin import credentials, firestore
import os

SERVICE_ACCOUNT_PATH = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"

try:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("SUCCESS: Firebase initialized.")
    # Test read
    collections = db.collections()
    print("Collections found:", [c.id for c in collections])
except Exception as e:
    print("ERROR:", str(e))
