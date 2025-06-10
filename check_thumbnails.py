#!/usr/bin/env python3
"""
Check thumbnails and videos in GCS bucket
"""

from app import app

def check_bucket_contents():
    print("=== Checking GCS Bucket Contents ===\n")
    
    bucket = app.config.get('bucket')
    if not bucket:
        print("❌ No bucket connection available")
        return
    
    print("=== Available Thumbnails ===")
    thumbnail_blobs = list(bucket.list_blobs(prefix='Videos/thumbnails/'))
    if thumbnail_blobs:
        for blob in thumbnail_blobs:
            print(f"✅ {blob.name} ({blob.size} bytes, updated: {blob.updated})")
    else:
        print("❌ No thumbnails found in Videos/thumbnails/")
    
    print("\n=== Available Videos ===")
    video_blobs = list(bucket.list_blobs(prefix='Videos/'))
    video_files = [blob for blob in video_blobs if blob.name.endswith('.mp4')]
    if video_files:
        for blob in video_files:
            video_name = blob.name.replace('Videos/', '')
            thumbnail_name = video_name.replace('.mp4', '.jpg')
            thumbnail_path = f"Videos/thumbnails/{thumbnail_name}"
            
            # Check if corresponding thumbnail exists
            has_thumbnail = any(t.name == thumbnail_path for t in thumbnail_blobs)
            status = "✅" if has_thumbnail else "❌"
            
            print(f"{status} Video: {blob.name} ({blob.size} bytes)")
            print(f"    Expected thumbnail: {thumbnail_path}")
            print(f"    Thumbnail exists: {'Yes' if has_thumbnail else 'No'}")
            print()
    else:
        print("❌ No video files found")
    
    print("=== Summary ===")
    print(f"Videos found: {len(video_files)}")
    print(f"Thumbnails found: {len(thumbnail_blobs)}")
    
    # Count videos with thumbnails
    videos_with_thumbnails = 0
    for blob in video_files:
        thumbnail_name = blob.name.replace('Videos/', '').replace('.mp4', '.jpg')
        thumbnail_path = f'Videos/thumbnails/{thumbnail_name}'
        if any(t.name == thumbnail_path for t in thumbnail_blobs):
            videos_with_thumbnails += 1
    
    print(f"Videos with thumbnails: {videos_with_thumbnails}")

if __name__ == "__main__":
    check_bucket_contents()
 