
import requests
import json

try:
    res = requests.get("http://127.0.0.1:8000/staff")
    data = res.json()
    print(f"Count: {len(data)}")
    names = sorted([s['name'] for s in data])
    
    # Check for specific artifacts
    bad_list = ['gate', 'locked', '**', 'mr', 'calire', '?']
    found_bad = []
    for n in names:
        if any(b in n.lower() for b in bad_list):
            found_bad.append(n)
            
    print(f"BAD FOUND: {found_bad}")
    print("ALL NAMES:")
    print(names)
    
except Exception as e:
    print(e)
