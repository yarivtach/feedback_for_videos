#!/usr/bin/env python3
"""
Test script to verify the updated routes work correctly
"""

import requests
from app import app
import json

def test_routes():
    print("=== Testing Updated Routes ===\n")
    
    with app.test_client() as client:
        
        # Test 1: List videos
        print("1. Testing list_videos() function...")
        from app import list_videos
        videos = list_videos()
        
        print(f"Found {len(videos)} videos:")
        for video_id, video in videos.items():
            print(f"  - {video_id}: {video['title']}")
            print(f"    URL: {video['url']}")
            print(f"    Thumbnail: {video['thumbnail']}")
            print()
        
        # Test 2: Test video serving route
        print("2. Testing video serving routes...")
        
        test_videos = ['corner.mp4', 'door.mp4', 'obstacles.mp4']
        for video in test_videos:
            print(f"Testing /static/Videos/{video}")
            response = client.get(f'/static/Videos/{video}', follow_redirects=False)
            if response.status_code == 302:
                print(f"  ✅ Redirects to: {response.location}")
            else:
                print(f"  ❌ Status: {response.status_code}")
            
            # Test direct route
            print(f"Testing /video/{video}")
            response = client.get(f'/video/{video}', follow_redirects=False)
            if response.status_code == 302:
                print(f"  ✅ Redirects to: {response.location}")
            else:
                print(f"  ❌ Status: {response.status_code}")
            print()
        
        # Test 3: Test thumbnail route
        print("3. Testing thumbnail routes...")
        test_thumbnails = ['corner', 'door', 'obstacles']
        for thumb in test_thumbnails:
            print(f"Testing /thumbnail/{thumb}.mp4")
            response = client.get(f'/thumbnail/{thumb}.mp4', follow_redirects=False)
            if response.status_code == 302:
                print(f"  ✅ Redirects to: {response.location}")
            else:
                print(f"  ❌ Status: {response.status_code}")
        
        print("\n=== Testing Complete ===")

if __name__ == "__main__":
    test_routes() 