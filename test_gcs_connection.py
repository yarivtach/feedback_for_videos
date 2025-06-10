#!/usr/bin/env python3
"""
Test script to verify Google Cloud Storage connection and list existing videos
"""

import os
from configManager import ConfigManager
from video_storage_manager import VideoStorageManager
from dotenv import load_dotenv

def test_gcs_connection():
    print("=== Testing Google Cloud Storage Connection ===\n")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize configuration manager
        config_manager = ConfigManager()
        
        # Initialize video storage manager
        video_storage = VideoStorageManager(config_manager)
        
        # Test bucket connection
        bucket_name = config_manager.get_bucket_name()
        print(f"Testing connection to bucket: {bucket_name}")
        
        if config_manager.initialize_with_base64_credentials():
            print("✅ Credentials initialized successfully")
            
            # List existing videos
            print("\n=== Listing existing videos ===")
            videos = video_storage.list_videos()
            
            if videos:
                print(f"Found {len(videos)} videos:")
                for i, video in enumerate(videos, 1):
                    print(f"\n{i}. {video['name']}")
                    print(f"   Size: {video['size']:,} bytes ({video['size']/(1024*1024):.2f} MB)")
                    print(f"   Type: {video['content_type']}")
                    print(f"   Updated: {video['updated']}")
                    print(f"   Blob path: {video['blob_name']}")
                    if 'thumbnail' in video:
                        print(f"   Thumbnail: Available")
                    else:
                        print(f"   Thumbnail: Not found")
            else:
                print("No videos found in the Videos/ folder")
                
            # Test listing thumbnails
            print("\n=== Checking thumbnails folder ===")
            storage_client = config_manager.get_storage_client()
            bucket = config_manager.get_bucket()
            
            thumbnails = list(bucket.list_blobs(prefix="thumbnails/"))
            if thumbnails:
                print(f"Found {len(thumbnails)} items in thumbnails folder:")
                for thumb in thumbnails:
                    if not thumb.name.endswith('/'):
                        print(f"   - {thumb.name}")
            else:
                print("No thumbnails found")
                
        else:
            print("❌ Failed to initialize credentials")
            return False
            
        print("\n✅ Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing connection: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gcs_connection() 