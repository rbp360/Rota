import json
import base64

with open('rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json', 'r') as f:
    data = json.load(f)
    print(base64.b64encode(json.dumps(data).encode()).decode())
