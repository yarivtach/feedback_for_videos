#!/usr/bin/env python3
"""
Simple test to verify Google Cloud Storage setup
"""

from video_storage_manager import VideoStorageManager
from configManager import ConfigManager
from dotenv import load_dotenv

def simple_test():
    print("=== Simple GCS Test ===\n")
    
    load_dotenv()
    
    # Initialize managers
    config_manager = ConfigManager()
    video_storage = VideoStorageManager(config_manager)
    
    print("Testing connection...")
    
    if config_manager.initialize_with_base64_credentials():
        print("✅ Credentials OK")
        
        # Test listing videos
        print("\nTesting video listing...")
        videos = video_storage.list_videos()
        
        print(f"Found {len(videos)} videos:")
        for video in videos:
            print(f"  - {video['name']} ({video['size']:,} bytes)")
            print(f"    Blob: {video['blob_name']}")
            print(f"    URL: {video['signed_url'][:50]}...")
            if 'thumbnail' in video:
                print(f"    Thumbnail: Available")
            else:
                print(f"    Thumbnail: Missing")
            print()
            
        return True
    else:
        print("❌ Failed to initialize")
        return False

if __name__ == "__main__":
    simple_test() 