from flask import Flask, jsonify, render_template, request, redirect, session, url_for, send_from_directory
import csv
from google.cloud import storage
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import datetime
import requests
import json
import os
from dotenv import load_dotenv
from db import Database
import tests.verify_credentials
from configManager import ConfigManager

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
            print("✅ Application initialized successfully")
        else:
            print("❌ Failed to get storage client or bucket")
            app.config['storage_client'] = None
            app.config['bucket'] = None
    else:
        print("❌ Failed to initialize with credentials")
        app.config['storage_client'] = None
        app.config['bucket'] = None
        
except Exception as e:
    print(f"❌ Error during initialization: {str(e)}")
    app.config['storage_client'] = None
    app.config['bucket'] = None


# #bucket_name = 'feedbackbucket14'
# google_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
# storage_client = config_manager.initialize_storage_client()
# if storage_client:
#     bucket = config_manager.get_bucket()
    
# else:
#     print("Storage client not initialized")
#     bucket = None

videos_folder = os.path.join(basedir, 'videos')
app.config['VIDEOS_FOLDER'] = videos_folder


#connect to the database
print("Connecting to the database")
db = Database()
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
VIDEOS_FOLDER = os.path.join(os.getcwd(), 'videos')
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
    user_email = session.get('user_email')  # Retrieve user ID from session
    if not user_email:
        return "User ID is missing.", 400  # Handle cases where there is no user ID

    comments = json.loads(request.form.get('comments', '[]'))
    summarized_comments = []
    to_saved_comment = f"Original comment: {comments}\nAnalyzed comment: {summarized_comments}"

    # Retrieve the form data
    data = {
        'user_email': user_email,
        'video_name': request.form.get('video_name'),
        'safety': request.form.get('safety'),
        'speed': request.form.get('speed'),
        'convenience': request.form.get('convenience'),
        'comments':  to_saved_comment
             
    }
    
    db.insert_data('feedbacks', data)
    return redirect(url_for('thank_you'))


@app.route('/video_gallery')
def video_gallery():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('home'))
    if not storage_client or not bucket:
        print("Storage client not available")
        return "Storage service unavailable", 503
    try:
        videos = list_videos()
        if not videos and not storage_client:
            return "Error connecting to storage", 500
        return render_template('videos.html', videos=videos, bucket_name=bucket_name)
    except Exception as e:
        print(f"Error in video gallery: {e}")
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


@app.route('/static/Videos/<video_name>')
def video_page(video_name):
    # return render_template('video_page.html', video_name=video_name)
    videos = list_videos()
    video = videos.get(video_name)
    if not video:
        return "Video not found", 404
    return render_template('video_page.html', video=video, video_name=video_name)

def list_videos():
    videos = {}
    try:
        print("\n=== DEBUG: list_videos() ===")
        print(f"Storage Client Status: {'Initialized' if storage_client else 'Not Initialized'}")
        print(f"Bucket Name: {bucket_name}")
        
        if not storage_client or not bucket:
            print("ERROR: Storage client or bucket not initialized")
            return videos
        
        print("Attempting to list blobs...")
        blobs = bucket.list_blobs()
        blob_count = 0
        video_count = 0
        
        # List all blobs for debugging
        for blob in blobs:
            blob_count += 1
            print(f"Found blob: {blob.name}")
            
            if blob.name.endswith('.mp4'):
                video_count += 1
                video_id = os.path.splitext(blob.name)[0]
                video_url = f"https://storage.googleapis.com/{bucket_name}/{blob.name}"
                
                # Create video entry
                videos[video_id] = {
                    'title': blob.name.replace('_', ' ').replace('.mp4', ''),
                    'url': video_url,
                    'raw_name': blob.name,
                    'size': blob.size,
                    'updated': blob.updated.isoformat(),
                    'public_url': blob.public_url if hasattr(blob, 'public_url') else None,
                }
                      # Try to generate thumbnail URL if exists
                thumbnail_name = f"{video_id}.jpg"
                if any(b.name == thumbnail_name for b in bucket.list_blobs(prefix=thumbnail_name)):
                    videos[video_id]['thumbnail'] = f"https://storage.googleapis.com/{bucket_name}/{thumbnail_name}"
                
                print(f"Added video {video_count}:")
                print(f"  ID: {video_id}")
                print(f"  URL: {video_url}")
                print(f"  Size: {blob.size} bytes")
                print(f"  Last Updated: {blob.updated}")
        
        print(f"\nSummary:")
        print(f"Total blobs found: {blob_count}")
        print(f"Total videos added: {video_count}")
        
        if video_count == 0:
            print("\nTroubleshooting suggestions:")
            print("1. Verify bucket contains .mp4 files")
            print("2. Check bucket permissions")
            print("3. Verify bucket name is correct")
            print(f"4. Current bucket name: {bucket_name}")
        
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


@app.route('/static/videos/<video_name>')
def serve_video(video_name):
    print(f"Serving video: {video_name}")
    videos = list_videos()
    video = videos.get(video_name)
    if not video:
        return "Video not found", 404
    return redirect(video['url'])


        
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
    session.clear()
    return redirect(url_for('home'))


# Function to save answers to a CSV file
def save_answers_csv(user_email, video_name, safety, speed, convenience, time=None, comment=None):
    # Define the full path to the CSV file
    csv_file_path = os.path.join(os.getcwd(), 'answers.csv')

    # Open a CSV file and append the data
    with open(csv_file_path, 'a', newline='') as csvfile:
        fieldnames = ['user_email', 'video_name', 'safety', 'speed', 'convenience', 'time', 'comment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Check if we need to write headers (simplified check)
        csvfile.seek(0, 2)  # Seek to the end of the file
        if csvfile.tell() == 0:  # If file is empty, write the header
            writer.writeheader()

        # Write the data row
        writer.writerow({
            'user_email': user_email,
            'video_name': video_name, 
            'safety': safety, 
            'speed': speed, 
            'convenience': convenience,
            'time': time,
            'comment': comment
        })
        
        


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
