#!/usr/bin/env python3
"""
Test script to verify the video gallery route works
"""

from app import app

def test_video_gallery():
    print("=== Testing Video Gallery Route ===\n")
    
    with app.test_client() as client:
        
        # Test 1: Try to access video gallery without login (should redirect)
        print("1. Testing video gallery without login...")
        response = client.get('/video_gallery', follow_redirects=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 302:
            print(f"✅ Correctly redirects to: {response.location}")
        else:
            print(f"❌ Expected redirect, got status {response.status_code}")
        print()
        
        # Test 2: Try to access video gallery with login
        print("2. Testing video gallery with login...")
        
        # First, simulate login by setting session
        with client.session_transaction() as sess:
            sess['user_email'] = 'test@example.com'
        
        response = client.get('/video_gallery', follow_redirects=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Video gallery loads successfully!")
            
            # Check if we got HTML content
            content = response.get_data(as_text=True)
            if 'video' in content.lower():
                print("✅ Response contains video-related content")
            else:
                print("⚠️ Response doesn't seem to contain video content")
                
        elif response.status_code == 503:
            print("❌ Storage service unavailable error")
        elif response.status_code == 404:
            print("⚠️ No videos available (this might be expected)")
        elif response.status_code == 500:
            print("❌ Internal server error")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
        print()
        
        # Test 3: Try the sign_in route
        print("3. Testing sign_in route...")
        response = client.post('/sign_in', data={'user_email': 'test@example.com'}, follow_redirects=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 302:
            print(f"✅ Sign-in redirects to: {response.location}")
            if 'video_gallery' in response.location:
                print("✅ Correctly redirects to video gallery!")
            else:
                print("⚠️ Redirects somewhere else")
        else:
            print(f"❌ Expected redirect, got status {response.status_code}")

if __name__ == "__main__":
    test_video_gallery() 