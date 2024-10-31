import os
import json
from google.cloud import storage
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self, base_dir=None):
        load_dotenv()  # Load environment variables from .env files
        self.base_dir = base_dir if base_dir else os.path.abspath(os.path.dirname(__file__))
        self.credentials_path = os.path.join(self.base_dir, 'credentials', 'google_cloud_key.json')
        self.storage_client = None
        self.bucket = None
        self.initialize_credentials()

    def initialize_credentials(self):
        """Initialize the storage client with credentials."""
        try:
            if os.path.exists(self.credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.storage_client = storage.Client(credentials=credentials, project=credentials.project_id)
                print("✅ Storage client initialized successfully.")
            else:
                print(f"❌ Credentials file not found at {self.credentials_path}")
        except Exception as e:
            print(f"❌ Error initializing storage client: {e}")

    def get_storage_client(self):
        """Return the initialized storage client."""
        return self.storage_client

    def verify_credentials_exist(self):
        """Verify the existence of the credentials file."""
        return os.path.exists(self.credentials_path)
