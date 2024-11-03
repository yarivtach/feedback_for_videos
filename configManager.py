import os
import json
from google.cloud import storage
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from dotenv import load_dotenv
import base64
import tests.verify_credentials


class ConfigManager:
    def __init__(self, base_dir=None):
        load_dotenv()  # Load environment variables from .env files
        self.base_dir = base_dir if base_dir else os.path.abspath(os.path.dirname(__file__))
        self.credentials_path = os.path.join(self.base_dir, 'credentials', 'google_cloud_key.json')
        self.storage_client = None
        self.bucket = None
        self.credentials = None
        if not self.initialize_credentials():
            self.logger.error("Failed to initialize credentials.")
            
            
    def initialize_credentials(self):
        """Load and initialize credentials from environment or file."""
        if creds_json := os.getenv('GOOGLE_CREDENTIALS_JSON'):
            return self.load_credentials_from_json(creds_json)
        else:
            return self.load_credentials_from_file()
        
    def load_credentials_from_json(self, creds_json):
        """Initialize credentials from JSON string."""
        try:
            creds_dict = json.loads(creds_json)
            if 'private_key' in creds_dict:
                creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            self.credentials = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            self.initialize_storage_client()
            return True
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format in environment credentials: {e}")
            return False
        
    def load_credentials_from_file(self):
        """Load credentials from a file if not loaded from environment."""
        if os.path.exists(self.credentials_path):
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            self.initialize_storage_client()
            return True
        else:
            self.logger.error(f"Credentials file not found at {self.credentials_path}")
            return False

    def get_storage_client(self):
        """Get the storage client"""
        if not self.storage_client:
            print("❌ Storage client not initialized")
            return None
        return self.storage_client
    
    
    def format_credentials_json(self, credentials_str):
        print("\n=== Formatting Credentials JSON ===")
        try:
            # Parse the JSON string
            if isinstance(credentials_str, str):
                creds_dict = json.loads(credentials_str)
            else:
                creds_dict = credentials_str

            # Fix private key formatting
            if 'private_key' in creds_dict:
                private_key = creds_dict['private_key']
            
                # Replace escaped newlines with actual newlines
                private_key = private_key.replace('\\n', '\n')
            
                # Ensure proper PEM format
                if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                    private_key = f"-----BEGIN PRIVATE KEY-----\n{private_key}"
                if not private_key.endswith('-----END PRIVATE KEY-----'):
                    private_key = f"{private_key}\n-----END PRIVATE KEY-----"
            
            creds_dict['private_key'] = private_key
            
            print("✅ Private key formatted successfully")
            
            # Verify the structure
            print("\nVerifying credential structure:")
            print(f"- Project ID: {creds_dict.get('project_id')}")
            print(f"- Client Email: {creds_dict.get('client_email')}")
            print(f"- Private Key ID: {creds_dict.get('private_key_id')}")
            
            return creds_dict
        except Exception as e:
            print(f"❌ Error formatting credentials: {str(e)}")
            return None

    def verify_credentials_exist(self):
        """Verify the existence of the credentials file."""
        return os.path.exists(self.credentials_path)

    def get_credentials(self):
        """Get credentials from environment or file"""
        try:
            print("\n=== Loading credentials ===")
            
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            
            if creds_json:
                print("Found credentials in environment variable")
            
            if not creds_json:
                print("❌ No credentials found in environment")
                return None
        
                        # Format the credentials
            formatted_creds = self.format_credentials_json(creds_json)
            if not formatted_creds:
                print("❌ Failed to format credentials")
                return None
                
            try:
                # Create credentials object with scopes
                self.credentials = service_account.Credentials.from_service_account_info(
                    formatted_creds
                ).with_scopes([
                    'https://www.googleapis.com/auth/cloud-platform',
                    'https://www.googleapis.com/auth/devstorage.read_write'
                ])
                print(f"✅ Credentials loaded for: {formatted_creds.get('client_email')}")
                return True
            except Exception as e:
                print(f"❌ Error creating credentials: {e}")
                return False
            # Fallback to file if no environment credentials
            # if os.path.exists(self.credentials_path):
            #     print(f"Loading credentials from file: {self.credentials_path}")
            #     self.credentials = service_account.Credentials.from_service_account_file(
            #         self.credentials_path
            #     )
            # else:
            #     print("❌ No valid credentials found!")
            #     return None
        
            # print("\nCredentials verification:")
            # print(f"✓ type: {creds_dict.get('type')}")
            # print(f"✓ project_id: {creds_dict.get('project_id')}")
            # print(f"✓ private_key_id: {creds_dict.get('private_key_id')}")
            # print(f"✓ client_email: {creds_dict.get('client_email')}")
            # credentials = service_account.Credentials.from_service_account_info(creds_dict)
            # scoped_credentials = credentials.with_scopes([
            #     'https://www.googleapis.com/auth/cloud-platform',
            #     'https://www.googleapis.com/auth/devstorage.read_write'
            # ])
            # self.credentials = scoped_credentials
            
            
            # return self.credentials

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format: {e}")
        return None
    
    def initialize_bucket(self, bucket_name='feedbackbucket14'):
        """Initialize bucket connection"""
        try:
            if not self.storage_client:
                print("❌ Storage client not initialized")
                return False


            print(f"Attempting to access bucket: {bucket_name} while storage client is {self.storage_client}")
            self.bucket = self.storage_client.bucket(bucket_name)
                        
            # Verify bucket exists
            if self.bucket.exists():
                print(f"✅ Connected to bucket: {bucket_name}")
                return True
            else:
                print(f"❌ Bucket not found: {bucket_name}")
                return False

        except Exception as e:
            print(f"❌ Error accessing bucket: {e}")
            return False
   
    def init_app(self):
        print("\n=== Initializing Application ===")
        try:
            # step 1: get credentials
            if not self.get_credentials():
                print("❌ Failed to load credentials")
                return False
            
            # Step 2: Initialize storage client
            if not self.initialize_storage_client():
                print("❌ Failed to initialize storage client")
                return False
            
            # Step 3: Initialize bucket
            if not self.initialize_bucket():
                print("❌ Failed to initialize bucket")
                return False
        
            print("✅ Application initialized successfully")
            return True
        
        except Exception as e:
            print(f"❌ Error initializing app: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


    def decode_credentials(self):
        # Retrieve the Base64-encoded string from the environment variable
        encoded_credentials = os.getenv('GOOGLE_CREDENTIALS_BASE64')

        if encoded_credentials:
            # Decode the Base64 string
            decoded_bytes = base64.b64decode(encoded_credentials)
            # Convert bytes to string
            decoded_str = decoded_bytes.decode('utf-8')
            # Parse the JSON string
            credentials = json.loads(decoded_str)
            print(credentials)
        else:
            print("Environment variable 'GOOGLE_CREDENTIALS_BASE64' is not set.")

    def get_bucket(self):
        """Get the bucket"""
        if not self.bucket:
            print("❌ Bucket not initialized")
            return None
        return self.bucket
    
    def verify_credentials_file(self):
        try:
            print("\n=== Verifying Credentials File ===")
        
        # Get the absolute path to credentials
            base_dir = os.path.dirname(os.path.abspath(__file__))
            creds_path = os.path.join(base_dir, 'credentials', 'google_cloud_key.json')

            print(f"Looking for credentials at: {creds_path}")
        
        # Check if file exists
            if not os.path.exists(creds_path):
                print("❌ Credentials file not found!")
                return False

            try:
        # Try to read and parse the JSON
                with open(creds_path, 'r') as f:
                    creds_data = json.load(f)
            
        # Verify required fields
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                for field in required_fields:
                    if field not in creds_data:
                        print(f"❌ Missing required field: {field}")
                        return False
                
        # Set environment variable
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
                print("✅ Credentials file verified successfully")
                return True
            
            except json.JSONDecodeError:
                print("❌ Invalid JSON format in credentials file")
                return False
        except Exception as e:
            print(f"❌ Error verifying credentials: {e}")
            return False
    
    def initialize_storage_client(self):
        try:
            if not self.credentials:
                print("❌ No credentials found")
                return False
            
            self.storage_client = storage.Client(
                credentials=self.credentials,
                project=self.credentials.project_id
            )
            
            print("✅ Storage client initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing storage client: {e}")
            return False
        


# Verify the path exists
    def verify_credentials(self):
        try:
            print("\n=== Checking Credentials Path ===")
            print(f"Base directory: {self.base_dir}")
            print(f"Looking for credentials at: {self.credentials_path}")
            
            if not os.path.exists(self.credentials_path):
                print("❌ Credentials file not found!")
                return False
            
        # Set the environment variable
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
            print(f"✅ Found credentials file")
            return True
        
        except Exception as e:
            print(f"❌ Error verifying credentials: {e}")
            return False

    def initialize_with_base64_credentials(self):
        """Initialize storage client and bucket using base64 credentials"""
        print("\n=== Initializing With Base64 Credentials ===")
        try:
            # Get base64 credentials from environment
            base64_credentials = os.getenv('GOOGLE_CREDENTIALS_BASE64')
            print(f"Debug - Credentials type: {type(base64_credentials)}")
            print(f"Debug - Credentials value: {base64_credentials[:50]}...") # Print first 50 chars
            
            if not base64_credentials:
                print("❌ GOOGLE_CREDENTIALS_BASE64 environment variable is not set")
                return False
            
            if isinstance(base64_credentials, tuple):
                base64_credentials = base64_credentials[0]
            print(f"✅ Base64 credentials found")
            base64_credentials = str(base64_credentials).strip()
            
            # Decode credentials 
            try:
                decoded_bytes = base64.b64decode(base64_credentials)
                print(f"Debug - Decoded bytes type: {type(decoded_bytes)}")
                
                decoded_str = decoded_bytes.decode('utf-8')
                print(f"Debug - JSON string type: {type(decoded_str)}")
                
                service_account_info = json.loads(decoded_str)
                print(f"Debug - Service account info type: {type(service_account_info)}")

                print("✅ Successfully decoded credentials")


            # Create credentials object
                print("Creating credentials object...")
                self.credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
            
                print(f"Debug - Credentials object type: {type(self.credentials)}")
                # Create storage client with explicit project
                print("Creating storage client...")
                project_id = service_account_info.get('project_id')
                print(f"Debug - Project ID: {project_id}")
                try:    
                    # Initialize storage client
                    self.storage_client = storage.Client(credentials=self.credentials, project=project_id)
                    print("✅ Storage client created successfully")

            
                # Get bucket
                    print("Getting bucket name...")
                    bucket_name = os.getenv('BUCKET_NAME', 'feedbackbucket14')
                    print(f"Debug - Bucket name type: {type(bucket_name)}")
                    print(f"Debug - Bucket name: {bucket_name}")
                    if isinstance(bucket_name, tuple):
                        bucket_name = bucket_name[0]
                    bucket_name = str(bucket_name).strip() if bucket_name else 'feedbackbucket14'
                    print(f"Debug - Bucket name type: {type(bucket_name)}")
                    print(f"Debug - Bucket name: {bucket_name}")
                    
                    
                # Verify bucket access
                    try:
                        self.bucket = self.storage_client.bucket(bucket_name)
                        
                        
                        if self.bucket.exists():
                            print(f"✅ Successfully connected to bucket: {bucket_name}")
                            return True
                        else:
                            print(f"❌ Bucket {bucket_name} does not exist")
                            return False
                    except Exception as e:
                        print(f"❌ Error accessing bucket: {e}")
                        return False
                except Exception as e:
                    print(f"❌ Error creating storage client: {str(e)}")
                    print(f"Error type: {type(e)}")
                    return False
            
            except base64.binascii.Error:
                print("❌ Invalid base64 encoding")
                return False
        except json.JSONDecodeError:
            print("❌ Invalid JSON format after decoding")
            return False
            
        except Exception as e:
            print(f"❌ Initialization failed: {str(e)}")
            return False
        
    def get_bucket_name(self):
        """Get bucket name from environment with proper error handling"""
        bucket_name = os.getenv('BUCKET_NAME')
        
        # Handle tuple case
        if isinstance(bucket_name, tuple):
            bucket_name = bucket_name[0]
    
        # Convert to string and clean
        bucket_name = str(bucket_name).strip() if bucket_name else 'feedbackbucket14'
    
        return bucket_name