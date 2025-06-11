from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for, send_from_directory
import csv
from google.cloud import storage
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import datetime
from datetime import timedelta
import requests
import json
import os
from dotenv import load_dotenv
from db import Database
import tests.verify_credentials
from configManager import ConfigManager
import random

basedir = os.path.abspath(os.path.dirname(__file__))
static_folder = os.path.join(basedir, 'static')
CREDENTIALS_PATH = os.path.join(basedir,'credentials','google_cloud_key.json')
config_manager = ConfigManager()

app = Flask(__name__, static_folder='static') # the change to 'static' is to fetch the static folder from the root of the project
app.secret_key = 'your_secret_key'  # Needed for session management
load_dotenv()  # Load environment variables from a .env file

print("\n=== Initializing Application ===")
try:
    # First verify environment variables
    bucket_name = config_manager.get_bucket_name()
    print(f"Using bucket: {bucket_name}")
    
    if config_manager.initialize_with_base64_credentials():
        storage_client = config_manager.get_storage_client()
        bucket = config_manager.get_bucket()
        
        if storage_client and bucket:
            app.config['storage_client'] = storage_client
            app.config['bucket'] = bucket
            
            # Initialize video storage manager
            try:
                from video_storage_manager import VideoStorageManager
                video_storage = VideoStorageManager(config_manager)
                
                # Test if the storage manager is working
                test_result = video_storage.list_videos()
                print(f"✅ Video storage manager initialized successfully (found {len(test_result)} videos)")
                
                # Store in app config for global access
                app.config['video_storage'] = video_storage
                
            except Exception as e:
                print(f"❌ Failed to initialize video storage manager: {e}")
                app.config['video_storage'] = None
            
            print("✅ Application initialized successfully")
        else:
            print("❌ Failed to get storage client or bucket")
            app.config['storage_client'] = None
            app.config['bucket'] = None
            app.config['video_storage'] = None
    else:
        print("❌ Failed to initialize with credentials")
        app.config['storage_client'] = None
        app.config['bucket'] = None
        app.config['video_storage'] = None
        
except Exception as e:
    print(f"❌ Error during initialization: {str(e)}")
    app.config['storage_client'] = None
    app.config['bucket'] = None
    app.config['video_storage'] = None



videos_folder = os.path.join(basedir, 'Videos')
app.config['VIDEOS_FOLDER'] = videos_folder


# Database connection (optional)
mongo_uri = os.getenv('MONGO_URI')
if mongo_uri and mongo_uri.strip():
    print("Connecting to the database")
    try:
        db = Database()
        app.config['MONGO_URI'] = mongo_uri
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("⚠️  App will continue without database functionality")
        db = None
else:
    print("📝 Database disabled - running in video-only mode")
    db = None
VIDEOS_FOLDER = os.path.join(os.getcwd(), 'Videos')
app.config['VIDEOS_FOLDER'] = VIDEOS_FOLDER

# Home page with links to each video
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user_email = request.form.get('user_email')
        session['user_email'] = user_email
        return redirect(url_for('home'))

    user_email = session.get('user_email', None)
    videos = list_videos() if user_email else {}
    return render_template('home.html', videos=videos, user_email=user_email)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    user_email = request.form.get('user_email')
    if validate_email(user_email):
        session['user_email'] = user_email
        return redirect(url_for('video_gallery'))
    else:
        return "Invalid Email", 401  # Or some form of error handling


def validate_email(email):
    # Dummy validation function
    return "@" in email  # Simple check to see if '@' is in the email

@app.route('/submit-questionnaire', methods=['POST'])
def submit_questionnaire():
    user_email = session.get('user_email')
    if not user_email:
        return "User email is missing.", 400

    try:
        # Get form data
        video_name = request.form.get('video_name')
        safety = int(request.form.get('safety', 0))
        speed = int(request.form.get('speed', 0))
        convenience = int(request.form.get('convenience', 0))
        
        # Get comments from localStorage (if any)
        comments_json = request.form.get('comments', '[]')
        try:
            comments = json.loads(comments_json) if comments_json else []
        except json.JSONDecodeError:
            comments = []
        
        # Get feedbacks from localStorage (from video watching)
        feedbacks_json = request.form.get('feedbacks', '[]')
        try:
            video_feedbacks = json.loads(feedbacks_json) if feedbacks_json else []
        except json.JSONDecodeError:
            video_feedbacks = []
        
        print(f"📝 Questionnaire submission:")
        print(f"  User: {user_email}")
        print(f"  Video: {video_name}")
        print(f"  Ratings - Safety: {safety}, Speed: {speed}, Convenience: {convenience}")
        print(f"  Comments: {len(comments)} items")
        print(f"  Video Feedbacks: {len(video_feedbacks)} items")
        
        # Create comprehensive session data
        session_data = {
            'user_email': user_email,
            'video_name': video_name,
            'questionnaire': {
                'safety': safety,
                'speed': speed,
                'convenience': convenience
            },
            'comments': comments,
            'video_feedbacks': video_feedbacks,
            'total_feedback_count': len(video_feedbacks),
            'total_comment_count': len(comments),
            'session_id': session.get('session_id', str(datetime.datetime.now().timestamp())),
            'created_at': datetime.datetime.now().isoformat(),
            'completed_at': datetime.datetime.now().isoformat()
        }
        
        # Save to database
        if db:
            success = db.save_video_session(session_data)
        else:
            print("⚠️  Database not available - feedback not saved")
            success = True  # Continue without database
        
        if success:
            print(f"✅ Complete session data saved for {user_email} - {video_name}")
            
            # Mark video as watched
            if 'watched_videos' not in session:
                session['watched_videos'] = []
            if video_name not in session['watched_videos']:
                session['watched_videos'].append(video_name)
                session.modified = True
            
            return redirect(url_for('thank_you'))
        else:
            return "Failed to save questionnaire data", 500
            
    except Exception as e:
        print(f"❌ Error saving questionnaire: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500


@app.route('/video_gallery')
def video_gallery():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('home'))
    
    # Use app.config for storage components, but don't require all of them
    storage_client = app.config.get('storage_client')
    bucket = app.config.get('bucket')
    video_storage = app.config.get('video_storage')
    
    # Only require basic storage client and bucket, video_storage is optional
    if not storage_client or not bucket:
        print("Basic storage client not available, but trying fallback...")
        # Even without storage client, we can still use the fallback system
    
    try:
        videos = list_videos()
        
        # Check if we got any videos (either from GCS or fallback)
        if not videos:
            print("No videos found from any source")
            return "No videos available", 404
        
        videos_shuffled = shuffle_videos_dict(videos)
        watched_videos = session.get('watched_videos', [])
        print(f"Watched videos: {watched_videos}")
        
        bucket_name = config_manager.get_bucket_name()
        return render_template('videos.html', videos=videos_shuffled, bucket_name=bucket_name, watched_videos=watched_videos)
        
    except Exception as e:
        print(f"Error in video gallery: {e}")
        import traceback
        traceback.print_exc()
        return "An error occurred", 500
    

def convert_comments_to_json(original_comment):
    # Create a dictionary to hold the feedback
    feedback_dict = {
        "original_comment": original_comment,
        # "analyzed_feedback": analyzed_feedback
    }
    # Convert the dictionary to a JSON string
    json_string = json.dumps(feedback_dict)
    return json_string

@app.route('/questionnaire')
def questionnaire_form():
    video_name = request.args.get('video_name', 'DefaultVideo')  # Default value if not provided
    return render_template('questionnaire.html', video_name=video_name)


@app.route('/video/<video_name>')
def serve_video_direct(video_name):
    """Alternative route for direct video serving"""
    print(f"Serving video directly: {video_name}")
    
    # Get signed URL from video storage manager for secure access
    video_storage = app.config.get('video_storage')
    if video_storage:
        videos = video_storage.list_videos()
        for video in videos:
            if video['name'] == video_name:
                return redirect(video['signed_url'])
    
    # Fallback to direct GCS URL using correct format
    base_url = "https://storage.googleapis.com/videos-robot-project/Videos"
    video_url = f"{base_url}/{video_name}"
    return redirect(video_url)

@app.route('/thumbnail/<video_name>')
def serve_thumbnail(video_name):
    """Serve thumbnail from Google Cloud Storage"""
    # Extract base name (without extension) 
    base_name = os.path.splitext(video_name)[0]
    
    # Try to get signed URL from bucket with name variations
    bucket = app.config.get('bucket')
    if bucket:
        try:
            # Try different thumbnail naming patterns due to mismatches in bucket
            thumbnail_variations = [
                f"Videos/thumbnails/{base_name}.jpg",  # Standard naming
            ]
            
            # Add specific known mismatches
            if base_name == 'obstacles':
                thumbnail_variations.append("Videos/thumbnails/obstacle.jpg")  # Missing 's'
            elif base_name == 'people':
                thumbnail_variations.append("Videos/thumbnails/pepole.jpg")  # Misspelling
            
            # Try each variation until we find one that exists
            for blob_name in thumbnail_variations:
                blob = bucket.blob(blob_name)
                
                # Check if thumbnail exists
                if blob.exists():
                    # Generate a signed URL valid for 1 hour
                    signed_url = blob.generate_signed_url(
                        version="v4",
                        expiration=3600,  # 1 hour
                        method="GET",
                    )
                    return redirect(signed_url)
            
            print(f"Thumbnail not found for any variation of {base_name}")
        except Exception as e:
            print(f"Error generating signed URL for thumbnail: {e}")
    
    # Fallback: try direct GCS URL using correct format (though this may not work due to auth)
    thumbnail_name = f"{base_name}.jpg"
    thumbnail_url = f"https://storage.googleapis.com/videos-robot-project/Videos/thumbnails/{thumbnail_name}"
    print(f"Serving thumbnail fallback: {thumbnail_url}")
    return redirect(thumbnail_url)

@app.route('/save_parsed_anlyazed_comment', methods=['POST'])
def save_parsed_anlyazed_comment(comments, video_name, user_email, grades):
    
    comment_parsed = comment_parse(comments)
    print(f"Comment parsed in save_parsed_anlyazed_comment: {comment_parsed}")
    safety , speed, convenience = grades['safety'], grades['speed'], grades['convenience']   
    # comment_with_paramters = f"{comment_parsed} ,analyze this with the next parameters: video_name:{video_name}\n user_email:{user_email}\n the next grades is 1-5 when 1 is the lowest and 5 is the highest\n safety:{safty}\n speed:{speed}\n convenience:{convenience}" 
    comment_with_paramters = f"""
    {comment_parsed}
    Analyze this with the following parameters:
    - Video Name: {video_name}
    - User ID: {user_email}
    The next grades are from 1 to 5, where 1 is the lowest and 5 is the highest:
    - Safety: {safety}
    - Speed: {speed}
    - Convenience: {convenience}
"""
    return comment_parsed


@app.route('/comment_parse')
def comment_parse(comments):
    parsed_comment = ""
    i=1
    for i, comment_data in enumerate(comments, start=1):
        comment = comment_data['comment']
        time = comment_data['time']
        parsed_comment += f"Comment number {i}\nTime: {time}\nComment: {comment}\n"
    return parsed_comment
    
@app.route('/thank_you')
def thank_you():
    # session.pop('user_email', None) # remove the user_email from the session
    return render_template('thank_you.html')

@app.route('/logout')
def logout():    
    session.pop('user_email', None)
    session.pop('watched_videos', None)
    session.clear()
    
    return redirect(url_for('home'))

@app.route('/save_feedback', methods=['POST'])
def save_feedback():
    if 'user_email' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.json
        video_name = data.get('video_name')
        feedback = data.get('feedback')
        
        if not video_name or not feedback:
            return jsonify({'error': 'Missing data'}), 400
        
        # Structure the feedback data properly
        feedback_entry = {
            'user_email': session['user_email'],
            'video_name': video_name,
            'timestamp': feedback.get('time', ''),
            'environment': feedback.get('environment', ''),
            'nearby_objects': feedback.get('nearby_objects', ''),
            'desired_action': feedback.get('desired_action', ''),
            'desired_velocity': feedback.get('desired_velocity', ''),
            'cause_for_action': feedback.get('cause_for_action', ''),
            'reason_for_action': feedback.get('reason_for_action', ''),
            'created_at': datetime.datetime.now().isoformat(),
            'session_id': session.get('session_id', str(datetime.datetime.now().timestamp()))
        }
        
        print(f"💾 Saving video feedback: {feedback_entry}")
        
        # Save to database using the new method
        if db:
            success = db.save_video_feedback(feedback_entry)
        else:
            print("⚠️  Database not available - video feedback not saved")
            success = True  # Continue without database
        
        if success:
            return jsonify({'success': True, 'message': 'Video feedback saved successfully'})
        else:
            return jsonify({'error': 'Failed to save video feedback'}), 500
            
    except Exception as e:
        print(f"Error saving video feedback: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    if 'user_email' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # Get data from request
        data = request.json
        
        # Add username and timestamp
        data['user_email'] = session['user_email']
        data['created_at'] = datetime.now().isoformat()
        
        # Save to database
        result = db.save_feedback(data)
        
        if result:
            return jsonify({'success': True, 'message': 'Feedback saved successfully'})
        else:
            return jsonify({'error': 'Failed to save feedback'}), 500
            
    except Exception as e:
        print(f"Error saving feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/auto-logout')
def auto_logout():
    """Handle automatic logout when user closes tab/browser"""
    try:
        # Get user info before clearing for logging
        user_id = session.get('user_id', 'Unknown')
        
        # Clear ALL session variables
        session.clear()
        
        # Set a flag in the session to indicate auto-logout
        session['show_logout_message'] = True
        
        # Log the automatic logout
        app.logger.info(f"User {user_id} automatically logged out due to tab/browser close")
        
        # For AJAX requests, return a response that will trigger redirect
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "status": "success", 
                "message": "Logged out successfully",
                "redirect": url_for('logout', auto=True)
            })
        
        # For direct access, redirect to the regular logout with auto parameter
        return redirect(url_for('logout', auto=True))
    except Exception as e:
        app.logger.error(f"Error during auto-logout: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/manage_videos')
def manage_videos():
    """Admin page to manage videos"""
    try:
        video_storage = app.config.get('video_storage')
        if not video_storage:
            return "Video storage not available", 500
        
        # Get videos from storage manager and convert to template format
        gcs_videos = video_storage.list_videos()
        videos = {}
        
        for video_info in gcs_videos:
            video_id = os.path.splitext(video_info['name'])[0]
            videos[video_id] = {
                'title': video_info['name'].replace('_', ' ').replace('.mp4', ''),
                'raw_name': video_info['name'],
                'blob_name': video_info['blob_name'],
                'size': video_info['size'],
                'updated': video_info['updated'],
                'content_type': video_info.get('content_type', 'video/mp4'),
                'url': video_info['signed_url']
            }
            
            # Add thumbnail if available
            if 'thumbnail' in video_info:
                videos[video_id]['thumbnail'] = video_info['thumbnail']
        
        return render_template('manage_videos.html', videos=videos)
        
    except Exception as e:
        print(f"Error in manage videos: {str(e)}")
        return "An error occurred", 500

def list_videos():
    """List videos from Google Cloud Storage using VideoStorageManager"""
    videos = {}
    try:
        print("\n=== DEBUG: list_videos() from Google Cloud Storage ===")
        
        video_storage = app.config.get('video_storage')
        if not video_storage:
            print("ERROR: Video storage manager not available")
            # Fallback: create videos manually from known structure
            known_videos = ['corner.mp4', 'door.mp4', 'obstacles.mp4', 'people.mp4']
            for video_name in known_videos:
                video_id = os.path.splitext(video_name)[0]
                videos[video_id] = {
                    'title': video_name.replace('_', ' ').replace('.mp4', ''),
                    'url': url_for('serve_secure_video', video_name=video_name, _external=True),
                    'raw_name': video_name,
                    'blob_name': f"Videos/{video_name}",
                    'size': 0,  # Unknown
                    'updated': None,
                    'public_url': f"https://storage.googleapis.com/videos-robot-project/Videos/{video_name}",
                    'content_type': 'video/mp4',
                    'thumbnail': url_for('serve_secure_thumbnail', video_name=video_name, _external=True)
                }
            return videos
        
        # Get videos from GCS using the video storage manager
        gcs_videos = video_storage.list_videos()
        video_count = 0
        
        for video_info in gcs_videos:
            video_count += 1
            # Extract video ID from filename (without extension)
            video_id = os.path.splitext(video_info['name'])[0]
            
            # Create video entry compatible with existing template structure
            videos[video_id] = {
                'title': video_info['name'].replace('_', ' ').replace('.mp4', ''),
                'url': url_for('serve_secure_video', video_name=video_info['name'], _external=True),  # Use secure route
                'signed_url': video_info['signed_url'],  # Keep signed URL as backup
                'raw_name': video_info['name'],
                'blob_name': video_info['blob_name'],  # Full blob path in GCS
                'size': video_info['size'],
                'updated': video_info['updated'],
                'public_url': f"https://storage.googleapis.com/videos-robot-project/Videos/{video_info['name']}",
                'content_type': video_info.get('content_type', 'video/mp4')
            }
            
            # Add thumbnail URL using secure route
            videos[video_id]['thumbnail'] = url_for('serve_secure_thumbnail', video_name=video_info['name'], _external=True)
            
            print(f"Added video {video_count}:")
            print(f"  ID: {video_id}")
            print(f"  Name: {video_info['name']}")
            print(f"  Size: {video_info['size']} bytes")
            print(f"  Blob: {video_info['blob_name']}")
            print(f"  URL: {videos[video_id]['url']}")
            print(f"  Thumbnail: {videos[video_id]['thumbnail']}")
            
            # Add metadata if available
            if 'metadata' in video_info:
                videos[video_id]['metadata'] = video_info['metadata']
        
        print(f"\nSummary:")
        print(f"Total videos found in GCS: {video_count}")
        
        if video_count == 0:
            print("\nNo videos found in Google Cloud Storage.")
            print("To add videos:")
            print("1. Go to /upload_video to upload new videos")
            print("2. Or manually upload .mp4 files to your GCS bucket")
        
        print("=== END DEBUG ===\n")
        
    except Exception as e:
        print("\n=== ERROR in list_videos() ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
        print("=== END ERROR ===\n")
    
    return videos

def shuffle_videos_dict(videos_dict):
    """
    Takes a dictionary of videos and returns a new dictionary with the same items in random order
    """
    # Get list of items
    items = list(videos_dict.items())
    # Shuffle the items
    random.shuffle(items)
    # Return a new dictionary with shuffled items
    return dict(items)

@app.route('/static/Videos/<video_name>')
@app.route('/video_page/<video_name>')
def video_page(video_name):
    # Initialize watched_videos in session if it doesn't exist
    if 'watched_videos' not in session:
        session['watched_videos'] = []
        
    # Add the video to watched list if not already there
    if video_name not in session['watched_videos']:
        session['watched_videos'].append(video_name)
        session.modified = True
    
    videos = list_videos()
    video = videos.get(video_name)
    if not video:
        # If video not found by ID, try by filename
        for vid_id, vid_data in videos.items():
            if vid_data['raw_name'] == video_name:
                video = vid_data
                video_name = vid_id
                break
    
    if not video:
        return "Video not found", 404
        
    # Get the actual video URL - use the secure route for better reliability
    video_filename = video['raw_name']  # This should include .mp4
    video_url = url_for('serve_secure_video', video_name=video_filename, _external=True)
    
    # Override the video URL to use our secure route
    video['url'] = video_url
    
    print(f"Video page for: {video_name}")
    print(f"Video filename: {video_filename}")
    print(f"Video URL: {video_url}")
    
    return render_template('video_page.html', video=video, video_name=video_name, video_url=video_url)

@app.route('/stream_video/<video_name>')
def stream_video(video_name):
    """Stream video with proper authentication handling"""
    try:
        videos = list_videos()
        video = None
        
        # Find the video
        for vid_id, vid_data in videos.items():
            if vid_id == video_name or vid_data['raw_name'] == video_name:
                video = vid_data
                break
        
        if not video:
            return "Video not found", 404
        
        # For now, redirect to the direct GCS URL with a helpful message
        # In production, you would implement proper video streaming here
        video_url = video['url']
        
        return f"""
        <html>
        <body>
            <h2>Video: {video['title']}</h2>
            <p>This video requires Google Cloud Storage authentication.</p>
            <p><strong>Options to view:</strong></p>
            <ol>
                <li><a href="{video_url}" target="_blank">Direct link to video</a> (may require Google sign-in)</li>
                <li>Contact administrator for access</li>
            </ol>
            <p><a href="javascript:history.back()">← Go Back</a></p>
            
            <script>
                // Try to load the video in an iframe (may work with authentication)
                const iframe = document.createElement('iframe');
                iframe.src = '{video_url}';
                iframe.width = '800';
                iframe.height = '450';
                iframe.style.border = 'none';
                iframe.onerror = function() {{
                    console.log('Iframe failed to load video');
                }};
                document.body.appendChild(iframe);
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"Error in stream_video: {e}")
        return "Error loading video", 500

@app.route('/secure_video/<video_name>')
def serve_secure_video(video_name):
    """Serve video using signed URL for secure access"""
    try:
        bucket = app.config.get('bucket')
        if not bucket:
            print("❌ No bucket connection available")
            return "Storage not available", 500
        
        # Ensure video_name has .mp4 extension
        if not video_name.endswith('.mp4'):
            video_name = f"{video_name}.mp4"
        
        # Create blob reference
        blob_name = f"Videos/{video_name}"
        blob = bucket.blob(blob_name)
        
        print(f"Checking for video blob: {blob_name}")
        
        # Check if video exists
        if not blob.exists():
            print(f"❌ Video not found: {blob_name}")
            return f"Video not found: {blob_name}", 404
        
        print(f"✅ Video found: {blob_name}")
        
        # Generate signed URL valid for 4 hours
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=14400,  # 4 hours in seconds
            method="GET",
        )
        
        print(f"✅ Generated signed URL for {video_name}")
        print(f"Signed URL: {signed_url[:100]}...")  # Print first 100 chars for debugging
        return redirect(signed_url)
        
    except Exception as e:
        print(f"❌ Error generating signed URL for video {video_name}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error accessing video: {str(e)}", 500

@app.route('/secure_thumbnail/<video_name>')
def serve_secure_thumbnail(video_name):
    """Serve thumbnail using signed URL for secure access"""
    try:
        bucket = app.config.get('bucket')
        if not bucket:
            print("❌ No bucket connection available for thumbnail")
            return "Storage not available", 500
        
        # Extract base name and create thumbnail path
        base_name = os.path.splitext(video_name)[0]
        
        # Try different thumbnail naming patterns due to mismatches in bucket
        thumbnail_variations = [
            f"Videos/thumbnails/{base_name}.jpg",  # Standard naming
        ]
        
        # Add specific known mismatches
        if base_name == 'obstacles':
            thumbnail_variations.append("Videos/thumbnails/obstacle.jpg")  
        elif base_name == 'people':
            thumbnail_variations.append("Videos/thumbnails/pepole.jpg")  
        
        print(f"Checking for thumbnail variations: {thumbnail_variations}")
        
        # Try each variation until we find one that exists
        for blob_name in thumbnail_variations:
            blob = bucket.blob(blob_name)
            print(f"Checking for thumbnail blob: {blob_name}")
            
            if blob.exists():
                print(f"✅ Thumbnail found: {blob_name}")
                
                # Generate signed URL valid for 4 hours
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=14400,  # 4 hours
                    method="GET",
                )
                
                print(f"✅ Generated signed URL for thumbnail {blob_name}")
                return redirect(signed_url)
        
        # If no thumbnail found
        print(f"❌ No thumbnail found for any variation of {base_name}")
        return "Thumbnail not found", 404
        
    except Exception as e:
        print(f"❌ Error generating signed URL for thumbnail {video_name}: {e}")
        import traceback
        traceback.print_exc()
        return f"Thumbnail error: {str(e)}", 500

@app.route('/view_data')
def view_data():
    """Admin route to view all collected data"""
    try:
        # Get all session data
        all_data = db.get_all_session_data()
        
        # Get summary statistics
        stats = {
            'total_sessions': len(all_data['video_sessions']),
            'total_video_feedbacks': len(all_data['video_feedbacks']),
            'total_legacy_feedbacks': len(all_data['legacy_feedbacks']),
            'unique_users': len(set(session.get('user_email', 'unknown') for session in all_data['video_sessions'])),
            'videos_watched': {}
        }
        
        # Count videos watched
        for session in all_data['video_sessions']:
            video = session.get('video_name', 'unknown')
            if video not in stats['videos_watched']:
                stats['videos_watched'][video] = 0
            stats['videos_watched'][video] += 1
        
        return render_template('view_data.html', 
                             data=all_data, 
                             stats=stats)
        
    except Exception as e:
        print(f"Error viewing data: {str(e)}")
        return f"Error loading data: {str(e)}", 500

@app.route('/export_data')
def export_data():
    """Export all data as JSON for analysis"""
    try:
        all_data = db.get_all_session_data()
        
        from flask import Response
        import json
        
        response = Response(
            json.dumps(all_data, indent=2, default=str),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=feedback_data.json'}
        )
        
        return response
        
    except Exception as e:
        print(f"Error exporting data: {str(e)}")
        return f"Error exporting data: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
