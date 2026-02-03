import json
import os

f = 'rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json'
if not os.path.exists(f):
    print("File not found")
else:
    with open(f, 'r') as file:
        try:
            d = json.load(file)
            pk = d.get('private_key', '')
            print(f"Project ID: {d.get('project_id')}")
            print(f"Key Length: {len(pk)}")
            print(f"Contains headers: {'BEGIN' in pk and 'END' in pk}")
            print(f"Newline Count: {pk.count('\\n')} literal, {pk.count('\n')} real")
            # Check for potential bad characters
            import re
            cleaned = pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").replace("\n", "").replace(" ", "").replace("\\n", "")
            bad = re.findall(r'[^A-Za-z0-9+/=]', cleaned)
            if bad:
                print(f"Found non-base64 characters in body: {list(set(bad))}")
            else:
                print("Body contains only valid Base64 characters")
        except Exception as e:
            print(f"JSON Error: {e}")
