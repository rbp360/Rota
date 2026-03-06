import os
import shutil

root = r"c:\Users\rob_b\Rota"
to_delete = [
    "vercel.json", 
    ".vercelignore", 
    ".vercelignore.bak", 
    "vercel_fix.env", 
    "vercel_import.env", 
    "cleanup.py",
    "api"
]

for item in to_delete:
    path = os.path.join(root, item)
    if os.path.exists(path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"Deleted DIR: {item}")
            else:
                os.remove(path)
                print(f"Deleted FILE: {item}")
        except Exception as e:
            print(f"Error deleting {item}: {e}")
    else:
        print(f"Already gone/Doesn't exist: {item}")
