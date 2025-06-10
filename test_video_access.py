#!/usr/bin/env python3
"""
Test video access with proper file extensions
"""

from app import app

def test_video_access():
    print("=== Testing Video Access ===\n")
    
    with app.test_client() as client:
        # Test secure video routes with different formats
        test_videos = [
            'corner.mp4',  # With extension
            'corner',      # Without extension  
            'door.mp4',
            'door'
        ]
        
        for video in test_videos:
            print(f"Testing secure video route: /secure_video/{video}")
            response = client.get(f'/secure_video/{video}', follow_redirects=False)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 302:
                print(f"  ✅ Redirects successfully")
                location = response.location
                if 'googleapis.com' in location:
                    print(f"  ✅ Redirects to Google Storage")
                else:
                    print(f"  ⚠️ Redirects to: {location[:100]}...")
            elif response.status_code == 404:
                print(f"  ❌ Video not found")
            elif response.status_code == 500:
                print(f"  ❌ Server error")
            else:
                print(f"  ❌ Unexpected status: {response.status_code}")
            print()
        
        # Test video page route
        print("Testing video page routes:")
        test_pages = ['corner', 'door', 'obstacles', 'people']
        
        # First set up session
        with client.session_transaction() as sess:
            sess['user_email'] = 'test@example.com'
        
        for video_id in test_pages:
            print(f"Testing video page: /static/Videos/{video_id}")
            response = client.get(f'/static/Videos/{video_id}')
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ Video page loads successfully")
            elif response.status_code == 404:
                print(f"  ❌ Video page not found")
            else:
                print(f"  ❌ Error: {response.status_code}")
            print()

if __name__ == "__main__":
    test_video_access() 