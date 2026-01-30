import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from backend.normalize_legacy import normalize_legacy_absences
    normalize_legacy_absences()
    print("Success")
except Exception as e:
    print(f"Error: {e}")
