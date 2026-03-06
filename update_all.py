import subprocess
import os
import sys

def run_step(name, cmd):
    print(f"\n>>> Running: {name} ...")
    try:
        # Use sys.executable to ensure we use the same python environment
        result = subprocess.run([sys.executable] + cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"DONE: {name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {name}")
        print(f"Error: {e.stderr}")
        return False

def update_all():
    # 0. Copy Source
    import shutil
    source = "GV cover and staff absence.xlsx"
    target = "temp_rota.xlsx"
    print(f"\n>>> Copying {source} to {target}...")
    try:
        shutil.copy(source, target)
        print("Copy successful.")
    except Exception as e:
        print(f"FAILED to copy: {e}")
        return

    # 1. Normalize
    if not run_step("Normalize Data (Excel -> SQLite)", ["backend/normalize.py"]):
        return
    
    # 2. Sync to Cloud
    if not run_step("Sync to Cloud (SQLite -> Firestore)", ["push_all_data.py"]):
        return

    print("\n✅ ALL STEPS COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    update_all()
