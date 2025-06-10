#!/usr/bin/env python3
"""
Check if thumbnail files exist in GCS bucket
"""

from app import app

def check_thumbnails_exist():
    print("=== Checking if Thumbnails Exist in GCS ===\n")
    
    with app.app_context():
        bucket = app.config.get('bucket')
        if not bucket:
            print("❌ No bucket connection available")
            return
        
        video_names = ['corner', 'door', 'obstacles', 'people']
        
        for video_name in video_names:
            thumbnail_blob_name = f"Videos/thumbnails/{video_name}.jpg"
            blob = bucket.blob(thumbnail_blob_name)
            
            try:
                exists = blob.exists()
                if exists:
                    print(f"✅ {thumbnail_blob_name} - EXISTS")
                    
                    # Get additional info
                    blob.reload()
                    print(f"   Size: {blob.size} bytes")
                    print(f"   Content Type: {blob.content_type}")
                    print(f"   Updated: {blob.updated}")
                else:
                    print(f"❌ {thumbnail_blob_name} - DOES NOT EXIST")
                    
            except Exception as e:
                print(f"❌ {thumbnail_blob_name} - ERROR: {e}")
        
        print(f"\n=== Summary ===")
        print("If thumbnails don't exist, you can:")
        print("1. Upload .jpg thumbnail files to Videos/thumbnails/ folder in your GCS bucket")
        print("2. Or use the gradient placeholders (which look nice too!)")
        print("3. Or generate thumbnails from the videos automatically")

if __name__ == "__main__":
    check_thumbnails_exist() 