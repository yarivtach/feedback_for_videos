import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_credentials():
    try:
        # For production (Render)
        if os.getenv('GOOGLE_CLOUD_CREDENTIALS'):
            return json.loads(os.getenv('GOOGLE_CLOUD_CREDENTIALS'))
            
        # For local development
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            with open(credentials_path, 'r') as f:
                return json.load(f)
                
        raise FileNotFoundError("No credentials found")
        
    except Exception as e:
        print(f"Error loading credentials: {str(e)}")
        return None

# Read the JSON file
credentials = get_credentials()

# Convert to single line and save to a file
with open('credentials_single_line.txt', 'w') as f:
    f.write(json.dumps(credentials))

# Also print to console
print("Your credentials in single line format:")
print(json.dumps(credentials))
