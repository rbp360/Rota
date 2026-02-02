import requests

TARGET_URL = "https://rota-47dp.onrender.com"

test_data = [
    {
        "id": "test_id_123",
        "name": "Test Teacher",
        "role": "Teacher",
        "schedules": []
    }
]

print("Sending 1 test teacher...")
r = requests.post(f"{TARGET_URL}/api/import-staff", json=test_data)
print(f"Status: {r.status_code}")
print(f"Body: {r.text}")
