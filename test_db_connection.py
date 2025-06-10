#!/usr/bin/env python3
"""
Test MongoDB connection and create sample data
"""

from db import Database
import datetime

def test_database_connection():
    print("🔍 Testing MongoDB Connection...")
    
    try:
        # Initialize database
        db = Database()
        print("✅ Database connection established!")
        
        # Test basic database operations
        print("\n📊 Testing database operations...")
        
        # Test 1: Save a sample video feedback
        sample_feedback = {
            'user_email': 'test@example.com',
            'video_name': 'corner',
            'timestamp': '5.2 - 8.7',
            'environment': 'Indoor hallway with obstacles',
            'nearby_objects': 'White containers, wall',
            'desired_action': 'Remote Control',
            'desired_velocity': 'Slow',
            'cause_for_action': 'Objects',
            'reason_for_action': 'Need to navigate around obstacles carefully',
            'created_at': datetime.datetime.now().isoformat(),
            'session_id': 'test_session_001'
        }
        
        result1 = db.save_video_feedback(sample_feedback)
        if result1:
            print("✅ Video feedback save: SUCCESS")
        else:
            print("❌ Video feedback save: FAILED")
        
        # Test 2: Save a sample complete session
        sample_session = {
            'user_email': 'test@example.com',
            'video_name': 'corner',
            'questionnaire': {
                'safety': 4,
                'speed': 3,
                'convenience': 5
            },
            'comments': [
                {'time': '2.1 - 3.4', 'comment': 'Robot moved too fast here'},
                {'time': '7.8 - 9.2', 'comment': 'Good navigation around obstacles'}
            ],
            'video_feedbacks': [sample_feedback],
            'total_feedback_count': 1,
            'total_comment_count': 2,
            'session_id': 'test_session_001',
            'created_at': datetime.datetime.now().isoformat(),
            'completed_at': datetime.datetime.now().isoformat()
        }
        
        result2 = db.save_video_session(sample_session)
        if result2:
            print("✅ Complete session save: SUCCESS")
        else:
            print("❌ Complete session save: FAILED")
        
        # Test 3: Retrieve data
        print("\n📖 Testing data retrieval...")
        all_data = db.get_all_session_data()
        
        print(f"📈 Database Stats:")
        print(f"   Video Sessions: {len(all_data['video_sessions'])}")
        print(f"   Video Feedbacks: {len(all_data['video_feedbacks'])}")
        print(f"   Legacy Feedbacks: {len(all_data['legacy_feedbacks'])}")
        
        print("\n🎉 Database test completed successfully!")
        print(f"🌐 You can now view your data at: http://localhost:5000/view_data")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your MONGO_URI in the .env file")
        print("2. Make sure your IP address is whitelisted in MongoDB Atlas")
        print("3. Verify your username and password are correct")
        print("4. Check your internet connection")
        
        import traceback
        print(f"\n📋 Full error details:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database_connection() 