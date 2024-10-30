import os
import json
from dotenv import load_dotenv
from google.cloud import storage



def verify_google_credentials():
    try:
        print("\n=== Verifying Google Cloud Credentials ===")
        
        # Get credentials path
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            print("❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            return False
            
        print(f"📂 Checking credentials file: {creds_path}")
        
        # Check if file exists
        if not os.path.exists(creds_path):
            print("❌ ERROR: Credentials file not found")
            return False
            
        # Try to read and parse JSON
        try:
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
        except json.JSONDecodeError:
            print("❌ ERROR: Invalid JSON format in credentials file")
            return False
         # Check required fields
        required_fields = {
            'type': 'Service account type',
            'project_id': 'Project ID',
            'private_key_id': 'Private key ID',
            'private_key': 'Private key',
            'client_email': 'Client email',
            'client_id': 'Client ID',
            'auth_uri': 'Auth URI',
            'token_uri': 'Token URI',
            'auth_provider_x509_cert_url': 'Auth provider cert URL',
            'client_x509_cert_url': 'Client cert URL'
        }
        
        print("\n🔍 Checking required fields:")
        missing_fields = []
        
        for field, description in required_fields.items():
            if field not in creds_data:
                missing_fields.append(field)
                print(f"❌ Missing: {description}")
            else:
                print(f"✅ Found: {description}")
                
        if missing_fields:
            print("\n❌ ERROR: Missing required fields in credentials file")
            return False
            
        # Verify private key format
        if not creds_data['private_key'].startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ ERROR: Invalid private key format")
            return False
            
        # Print important info
        print("\n📋 Credentials Summary:")
        print(f"Project ID: {creds_data['project_id']}")
        print(f"Client Email: {creds_data['client_email']}")
        print(f"Auth URI: {creds_data['auth_uri']}")
        
        # Try to initialize storage client
        try:
            storage_client = storage.Client.from_service_account_json(creds_path)
            print("\n✅ Successfully initialized storage client")
            
            # Try to list buckets as a final test
            try:
                list(storage_client.list_buckets(max_results=1))
                print("✅ Successfully listed buckets")
            except Exception as e:
                print(f"⚠️ Warning: Could not list buckets: {str(e)}")
                print("This might be a permissions issue rather than a credentials issue")
                
        except Exception as e:
            print(f"\n❌ ERROR: Failed to initialize storage client: {str(e)}")
            return False
            
        print("\n✅ Credentials file appears valid!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error while verifying credentials: {str(e)}")
        return False

# Usage
if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    if verify_google_credentials():
        print("🎉 Credentials verification successful!")
    else:
        print("❌ Credentials verification failed!")