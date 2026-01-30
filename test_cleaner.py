
import sys
import os

# Mock the function from normalize.py to test strictly logic
import re

def clean_staff_name(name):
    if not name: return ""
    n = str(name).strip()
    
    IGNORED = [
        "TBC", "External", "Coach", "Room", "Music Room", "Hall",
        "Gym", "Pitch", "Court", "Pool", "Library", "PRE NURSERY", "PRE NUSERY", "Outside Prov.",
        "**", "gate", "locked", "at", "8.30", "Mr", "1", "Calire", "?"
    ]
    if any(i.lower() in n.lower() for i in IGNORED):
        return None

    n = re.sub(r'^(k\.|kun\s|k\s)', '', n, flags=re.IGNORECASE).strip()
    n = n.split('(')[0].strip()
    
    nl = n.lower()
    
    if "jactina" in nl: return "Jacinta"
    if "nokkaew" in nl: return "Nokkeaw"
    if "nick" in nl and ("c" in nl or nl == "nick"): return "Nick.C"
    
    if nl == "darryl": return "Daryl"
    if nl == "ginny": return "Jinny"
    if nl == "jinny": return "Jinny" 
    if nl == "janel": return "Janel"
    
    return n

test_cases = [
    "Jactina", "Jactina ", "Jacinta",
    "Nick C", "Nick. C", "Nick", "Nick.C",
    "Nokkaew", "Nokkeaw",
    "Pre nursery", "PRE NUSERY", "Outside Prov."
]

print("--- Testing Name Cleaning Logic ---")
for t in test_cases:
    res = clean_staff_name(t)
    print(f"'{t}' -> '{res}'")
