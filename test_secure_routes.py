#!/usr/bin/env python3
"""
Test the secure video and thumbnail routes
"""

from app import app

def test_secure_routes():
    print("=== Testing Secure Routes ===\n")
    
    with app.test_client() as client:
        # Test secure video route
        print("1. Testing secure video route...")
        response = client.get('/secure_video/corner.mp4', follow_redirects=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 302:
            print(f"✅ Redirects to signed URL")
        elif response.status_code == 500:
            print(f"❌ Storage not available")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
        
        # Test secure thumbnail route  
        print("\n2. Testing secure thumbnail route...")
        response = client.get('/secure_thumbnail/corner.mp4', follow_redirects=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 302:
            print(f"✅ Redirects to signed URL or placeholder")
        elif response.status_code == 500:
            print(f"❌ Storage not available")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
        
        # Test with login session
        print("\n3. Testing video gallery with secure routes...")
        with client.session_transaction() as sess:
            sess['user_email'] = 'test@example.com'
        
        response = client.get('/video_gallery')
        if response.status_code == 200:
            content = response.get_data(as_text=True)
            if 'secure_video' in content:
                print("✅ Video gallery uses secure routes")
            else:
                print("❌ Video gallery not using secure routes")
        else:
            print(f"❌ Video gallery error: {response.status_code}")

if __name__ == "__main__":
    test_secure_routes() 