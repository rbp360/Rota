import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

def test_claire_availability():
    # Thursday, Jan 29, 2026 (based on the .ics content)
    test_date = "2026-01-29"
    # P1 (08:40-09:20) from .ics is "Primary Assembly" - should be busy
    params = {
        "periods": "1",
        "day": "Thursday",
        "date": test_date
    }
    
    try:
        response = requests.get(f"{API_URL}/availability", params=params)
        data = response.json()
        
        claire = next((s for s in data if s['name'] == 'Claire'), None)
        if claire:
            print(f"Claire Availability for Date {test_date}, P1:")
            print(f"  Free: {claire['is_free']}")
            print(f"  Activity/Reason: {claire['activity']}")
        else:
            print("Claire not found in availability list.")
            
    except Exception as e:
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    test_claire_availability()
