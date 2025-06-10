#!/usr/bin/env python3
"""
Test thumbnail access after fixing filename mismatches
"""

from app import app

def test_thumbnails():
    print("=== Testing Thumbnail Access After Fixes ===\n")
    
    with app.test_client() as client:
        # Test all video thumbnails
        test_videos = ['corner.mp4', 'door.mp4', 'obstacles.mp4', 'people.mp4']
        
        for video in test_videos:
            print(f"Testing secure thumbnail route: /secure_thumbnail/{video}")
            response = client.get(f'/secure_thumbnail/{video}', follow_redirects=False)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 302:
                print(f"  ✅ Redirects successfully")
                location = response.location
                if 'googleapis.com' in location:
                    print(f"  ✅ Redirects to Google Storage")
                else:
                    print(f"  ⚠️ Redirects to: {location[:100]}...")
            elif response.status_code == 404:
                print(f"  ❌ Thumbnail not found")
            elif response.status_code == 500:
                print(f"  ❌ Server error")
            else:
                print(f"  ❌ Unexpected status: {response.status_code}")
            print()
        
        # Test without extensions too
        print("Testing thumbnails without .mp4 extension:")
        test_names = ['corner', 'door', 'obstacles', 'people']
        
        for video in test_names:
            print(f"Testing: /secure_thumbnail/{video}")
            response = client.get(f'/secure_thumbnail/{video}', follow_redirects=False)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 302:
                print(f"  ✅ Works!")
            elif response.status_code == 404:
                print(f"  ❌ Not found")
            print()

if __name__ == "__main__":
    test_thumbnails() 