#!/usr/bin/env python3
"""
Script to create the Google Cloud Storage bucket if it doesn't exist
"""

import os
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import base64
import json

def create_bucket_if_not_exists():
    print("=== Creating/Checking Google Cloud Storage Bucket ===\n")
    
    load_dotenv()
    
    try:
        # Get credentials from environment
        base64_credentials = os.getenv('GOOGLE_CREDENTIALS_BASE64')
        if not base64_credentials:
            print("❌ GOOGLE_CREDENTIALS_BASE64 not found in environment")
            return False
        
        # Decode credentials
        decoded_bytes = base64.b64decode(base64_credentials)
        decoded_str = decoded_bytes.decode('utf-8')
        service_account_info = json.loads(decoded_str)
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Create storage client
        project_id = service_account_info.get('project_id')
        client = storage.Client(credentials=credentials, project=project_id)
        
        # Bucket details
        bucket_name = os.getenv('BUCKET_NAME', 'videos-robot-project')
        
        print(f"Project ID: {project_id}")
        print(f"Bucket Name: {bucket_name}")
        print(f"Service Account: {service_account_info.get('client_email')}")
        
        # Check if bucket exists
        try:
            bucket = client.bucket(bucket_name)
            if bucket.exists():
                print(f"✅ Bucket '{bucket_name}' already exists")
                
                # List some contents
                blobs = list(client.list_blobs(bucket_name, max_results=10))
                print(f"Bucket contains {len(blobs)} objects (showing first 10)")
                for blob in blobs:
                    print(f"  - {blob.name}")
                
                return True
            else:
                print(f"❌ Bucket '{bucket_name}' does not exist in project '{project_id}'")
                
                # Try to create bucket
                print(f"Attempting to create bucket...")
                bucket = client.create_bucket(bucket_name, location='US')
                print(f"✅ Bucket '{bucket_name}' created successfully!")
                
                # Create initial folders
                print("Creating initial folder structure...")
                
                # Create Videos/ folder
                videos_blob = bucket.blob("Videos/.keep")
                videos_blob.upload_from_string("")
                
                # Create thumbnails/ folder
                thumbnails_blob = bucket.blob("thumbnails/.keep")
                thumbnails_blob.upload_from_string("")
                
                print("✅ Initial folder structure created")
                return True
                
        except Exception as bucket_error:
            print(f"❌ Error with bucket operations: {bucket_error}")
            print(f"This might be a permissions issue or the bucket might be in a different project")
            
            # Try to list buckets in the project
            print(f"\nListing all buckets in project '{project_id}':")
            try:
                buckets = client.list_buckets()
                bucket_list = list(buckets)
                if bucket_list:
                    for bucket in bucket_list:
                        print(f"  - {bucket.name}")
                else:
                    print("  No buckets found in this project")
            except Exception as list_error:
                print(f"  Error listing buckets: {list_error}")
            
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_bucket_if_not_exists() 