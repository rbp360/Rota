import json
import binascii

with open('rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json', 'r') as f:
    data = json.load(f)
    hex_str = binascii.hexlify(json.dumps(data).encode()).decode()
    with open('hex_key_final.txt', 'w') as out:
        out.write(hex_str)
    print(f"DONE. Length: {len(hex_str)}")
