import binascii
import os

# CONFIG
JSON_PATH = "rotaai-49847-d923810f254e.json"

def create_safe_hex():
    print("--- IRONCLAD HEX KEY GENERATOR ---")
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} not found in this folder.")
        return

    try:
        with open(JSON_PATH, 'rb') as f:
            raw_data = f.read()
        
        # Convert the entire file to a safe Hex blob
        hex_blob = binascii.hexlify(raw_data).decode('utf-8')
        
        output_file = "RENDER_SAFE_KEY.txt"
        with open(output_file, 'w') as f:
            f.write("### RENDER SECURE HEX KEY ###\n")
            f.write("Variable Name: FIREBASE_KEY_HEX\n")
            f.write("Value:\n")
            f.write(hex_blob)
            f.write("\n\n### INSTRUCTIONS ###\n")
            f.write("1. Copy the long 'Value' string above.\n")
            f.write("2. Go to Render Dashboard -> Settings -> Environment.\n")
            f.write("3. ADD A NEW VARIABLE called: FIREBASE_KEY_HEX\n")
            f.write("4. Paste the long string. It contains no special characters, so it cannot break.\n")
        
        print(f"\n✅ SUCCESS! Safe key generated in: {output_file}")
        print("\nNext Step: Run 'git add/commit/push' to deploy the new Hex decoder (v5.5.40).")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_safe_hex()
