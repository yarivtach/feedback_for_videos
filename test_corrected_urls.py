#!/usr/bin/env python3
"""
Test script to verify corrected URL formats
"""

from app import app, list_videos

def test_corrected_urls():
    print("=== Testing Corrected URL Formats ===\n")
    
    with app.app_context():
        videos = list_videos()
        
        print(f"Found {len(videos)} videos:")
        for video_id, video_data in videos.items():
            print(f"\nVideo: {video_id}")
            print(f"  Title: {video_data['title']}")
            print(f"  Video URL: {video_data['url']}")
            print(f"  Thumbnail URL: {video_data.get('thumbnail', 'NO THUMBNAIL')}")
            
            # Verify URL format
            video_url = video_data['url']
            thumbnail_url = video_data.get('thumbnail', '')
            
            if 'storage.googleapis.com' in video_url:
                print(f"  ✅ Video URL format correct")
            else:
                print(f"  ❌ Video URL format incorrect")
                
            if 'storage.googleapis.com' in thumbnail_url:
                print(f"  ✅ Thumbnail URL format correct")
            else:
                print(f"  ❌ Thumbnail URL format incorrect")
        
        print(f"\n=== Example URLs ===")
        if videos:
            first_video = list(videos.values())[0]
            print(f"Video URL: {first_video['url']}")
            print(f"Thumbnail URL: {first_video.get('thumbnail', 'N/A')}")

if __name__ == "__main__":
    test_corrected_urls() 