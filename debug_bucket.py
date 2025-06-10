#!/usr/bin/env python3
"""
Debug script to check bucket access and permissions
"""

import os
import json
import base64
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

def debug_bucket_access():
    print("=== Debugging Bucket Access ===\n")
    
    load_dotenv()
    
    try:
        # Get credentials
        base64_credentials = os.getenv('GOOGLE_CREDENTIALS_BASE64')
        if not base64_credentials:
            print("❌ No GOOGLE_CREDENTIALS_BASE64 found")
            return
        
        # Decode credentials
        decoded_bytes = base64.b64decode(base64_credentials)
        decoded_str = decoded_bytes.decode('utf-8')
        service_account_info = json.loads(decoded_str)
        
        project_id = service_account_info.get('project_id')
        client_email = service_account_info.get('client_email')
        
        print(f"Service Account: {client_email}")
        print(f"Project ID: {project_id}")
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Create storage client
        client = storage.Client(credentials=credentials, project=project_id)
        
        print(f"\n=== Checking Project: {project_id} ===")
        
        # List all buckets in this project
        print("Listing all buckets in your project:")
        try:
            buckets = list(client.list_buckets())
            if buckets:
                print(f"Found {len(buckets)} buckets:")
                for bucket in buckets:
                    print(f"  - {bucket.name}")
                    
                    # Check if one of them is our target bucket
                    if bucket.name == "videos-robot-project":
                        print(f"    ✅ Found target bucket!")
            else:
                print("  No buckets found in this project")
        except Exception as e:
            print(f"  ❌ Error listing buckets: {e}")
        
        # Try to access the specific bucket
        print(f"\n=== Testing Access to 'videos-robot-project' ===")
        target_bucket = "videos-robot-project"
        
        try:
            bucket = client.bucket(target_bucket)
            
            # Try different operations to see what works
            print("Testing bucket operations:")
            
            # Test 1: Check if bucket exists (requires storage.buckets.get)
            try:
                exists = bucket.exists()
                print(f"  ✅ bucket.exists(): {exists}")
            except Exception as e:
                print(f"  ❌ bucket.exists() failed: {e}")
            
            # Test 2: Try to list objects (requires storage.objects.list)
            try:
                blobs = list(client.list_blobs(target_bucket, max_results=5))
                print(f"  ✅ list_blobs(): Found {len(blobs)} objects")
                for blob in blobs[:3]:  # Show first 3
                    print(f"    - {blob.name}")
            except Exception as e:
                print(f"  ❌ list_blobs() failed: {e}")
            
            # Test 3: Try to get bucket metadata
            try:
                bucket.reload()
                print(f"  ✅ bucket.reload(): Success")
                print(f"    Location: {bucket.location}")
                print(f"    Storage class: {bucket.storage_class}")
            except Exception as e:
                print(f"  ❌ bucket.reload() failed: {e}")
        
        except Exception as e:
            print(f"❌ Error creating bucket object: {e}")
        
        # Check if the bucket might be in a different project
        print(f"\n=== Checking if bucket is public or in different project ===")
        
        # Try accessing without authentication (public bucket)
        try:
            public_client = storage.Client.create_anonymous_client()
            public_bucket = public_client.bucket(target_bucket)
            
            if public_bucket.exists():
                print(f"✅ Bucket exists and is publicly accessible")
                
                # Try to list some objects
                blobs = list(public_client.list_blobs(target_bucket, max_results=5))
                print(f"  Found {len(blobs)} public objects:")
                for blob in blobs[:3]:
                    print(f"    - {blob.name}")
            else:
                print(f"❌ Bucket not found or not public")
                
        except Exception as e:
            print(f"❌ Public access failed: {e}")
        
        print(f"\n=== Recommendations ===")
        print(f"1. If bucket exists in your project but access fails:")
        print(f"   - Grant 'Storage Object Viewer' role to: {client_email}")
        print(f"   - Grant 'Storage Legacy Bucket Reader' role")
        print(f"2. If bucket not found in your project:")
        print(f"   - Check if bucket belongs to a different project")
        print(f"   - Create the bucket in project: {project_id}")
        print(f"3. If bucket is public:")
        print(f"   - Update code to use anonymous client for reading")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_bucket_access() 