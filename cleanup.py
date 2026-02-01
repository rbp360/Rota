import os
import shutil

items = ["python", "runtime.txt", ".vercelignore", "requirements.txt"]
for item in items:
    path = os.path.join(os.getcwd(), item)
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Removed DIR: {item}")
        else:
            os.remove(path)
            print(f"Removed FILE: {item}")
    else:
        print(f"Not found: {item}")
