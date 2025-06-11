from pymongo import MongoClient, errors
from dotenv import load_dotenv
import logging
import certifi
import os

class Database:
    def __init__(self):
        load_dotenv()
        mongo_uri = os.getenv('MONGO_URI')
        try:
            # Try multiple connection strategies for Render compatibility
            connection_attempts = [
                # Attempt 1: Basic connection (let URI handle SSL)
                {
                    'serverSelectionTimeoutMS': 10000,
                    'connectTimeoutMS': 10000,
                    'socketTimeoutMS': 10000,
                },
                # Attempt 2: With explicit timeouts only
                {
                    'serverSelectionTimeoutMS': 15000,
                    'connectTimeoutMS': 15000,
                    'socketTimeoutMS': 15000,
                    'maxPoolSize': 10,
                },
                # Attempt 3: Minimal connection
                {
                    'serverSelectionTimeoutMS': 5000,
                }
            ]
            
            last_error = None
            for i, config in enumerate(connection_attempts, 1):
                try:
                    print(f"🔄 MongoDB connection attempt {i}/3...")
                    self.client = MongoClient(mongo_uri, **config)
                    break  # Success - exit the loop
                except Exception as e:
                    last_error = e
                    print(f"❌ Attempt {i} failed: {str(e)[:100]}...")
                    if i < len(connection_attempts):
                        continue
                    else:
                        # All attempts failed, raise the last error
                        raise last_error
            
            # Ping the server to ensure the connection is alive
            self.client.admin.command('ping')
            db_name = mongo_uri.split('/')[-1].split('?')[0]
            print(f"Database name extracted: '{db_name}'")  # Debug print
            if not db_name:
                raise ValueError("Database name is empty. Check your MONGO_URI.")
            self.db = self.client.get_database(db_name)
            print(f"✅ Connected to MongoDB at {mongo_uri}, Database: {db_name}")
            
            
        except errors.ConnectionFailure as e:
            logging.error("Failed to connect to MongoDB: Connection Failure", exc_info=True)
            raise e
        except Exception as e:
            logging.error("Failed to connect to MongoDB", exc_info=True)
            raise e

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def insert_data(self, collection_name, data):
        if self.db is not None:
            collection = self.db[collection_name]
            result = collection.insert_one(data)
            logging.info(f"Inserted data into {collection_name}: {result.inserted_id}")
            return result
        else:
            logging.error("Database connection not initialized.")
            raise Exception("Database connection not initialized.")

    def get_data(self, collection_name):
        collection = self.db[collection_name]
        data = list(collection.find({}))
        logging.info(f"Retrieved data from {collection_name}: {data}")
        return data
    
    def save_feedback(self, feedback_data):
        """Save feedback to the database"""
        try:
            result = self.db.feedbacks.insert_one(feedback_data)
            return result.acknowledged
        except Exception as e:
            print(f"Database error saving feedback: {str(e)}")
            return False
    
    def get_feedback(self):
        """Get all feedback from the database"""
        return list(self.db.feedbacks.find({}))
    
    def save_video_session(self, session_data):
        """Save complete video session data (feedback + questionnaire)"""
        try:
            result = self.db.video_sessions.insert_one(session_data)
            print(f"✅ Video session saved with ID: {result.inserted_id}")
            return result.acknowledged
        except Exception as e:
            print(f"❌ Database error saving video session: {str(e)}")
            return False
    
    def save_video_feedback(self, feedback_data):
        """Save individual video feedback (from C key presses)"""
        try:
            result = self.db.video_feedbacks.insert_one(feedback_data)
            print(f"✅ Video feedback saved with ID: {result.inserted_id}")
            return result.acknowledged
        except Exception as e:
            print(f"❌ Database error saving video feedback: {str(e)}")
            return False
    
    def get_user_session_data(self, user_email, video_name):
        """Get all data for a specific user and video"""
        return {
            'feedbacks': list(self.db.video_feedbacks.find({
                'user_email': user_email, 
                'video_name': video_name
            })),
            'questionnaire': list(self.db.video_sessions.find({
                'user_email': user_email, 
                'video_name': video_name
            }))
        }
    
    def get_all_session_data(self):
        """Get all video session data for analysis"""
        return {
            'video_feedbacks': list(self.db.video_feedbacks.find({})),
            'video_sessions': list(self.db.video_sessions.find({})),
            'legacy_feedbacks': list(self.db.feedbacks.find({}))
        }
    
    def insert_comment(self, data):
        return self.db.comments.insert_one(data)
    
    def get_comments(self, collection_name):
        return list(self.db[collection_name].find({}))
    
    def insert_comment_to_feedback(self, collection_name, comment_data):
        collection = self.db[collection_name]
        #add comment to the comment at the feedback of a specific video to specific user
        result = collection.update_one({'video_name': comment_data['video_name'], 'user_email': comment_data['user_email']}, {'$push': {'comments': comment_data}})
        logging.info(f"Inserted comment into {collection_name}: {result.modified_count}")
        return result
        
    