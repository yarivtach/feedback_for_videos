from flask import Flask, jsonify, render_template, request, redirect, session, url_for, send_from_directory
import csv
import requests
import json
import os
from dotenv import load_dotenv
from db import Database

basedir = os.path.abspath(os.path.dirname(__file__))
static_folder = os.path.join(basedir, 'static')
app = Flask(__name__, static_folder=static_folder)#), stat(message_spec=None))
app.secret_key = 'your_secret_key'  # Needed for session management
load_dotenv()  # Load environment variables from a .env file

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
    videos = ['corner', 'door', 'obstacles', 'people'] if user_email else []
    return render_template('home.html', videos=videos, user_email=user_email)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    user_email = request.form.get('user_email')
    session['user_email'] = user_email
    if validate_email(user_email):
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
    videos_folder = os.path.join(app.static_folder, 'Videos')
    print(f"Videos folder: {videos_folder}")
    if not os.path.exists(videos_folder):
        app.logger.error(f"Videos folder not found: {videos_folder}")
        return "Videos folder not found", 404
    
    all_files = os.listdir(videos_folder)
    videos = [f for f in all_files if f.endswith(('.mp4', '.avi', '.mov'))]
    # for filename in os.listdir(videos_folder):
    #     if filename.endswith(('.mp4', '.avi', '.mov')):
    #         #videos.append(os.path.splitext(filename)[0]) 
    #         videos.append(filename)
    return render_template('videos.html', videos=videos)



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


@app.route('/static/videos/<video_name>')
def video_page(video_name):
    # return render_template('video_page.html', video_name=video_name)
    return send_from_directory(app.config['VIDEOS_FOLDER'], video_name)

@app.route('/static/videos/<video_name>')
def serve_video(filename):
    return send_from_directory(app.config['VIDEOS_FOLDER'], filename)


        
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
    session.pop('user_email', None)
    return render_template('thank_you.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return '', 204  # Return no content for sendBeacon**

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
    app.run(host='0.0.0.0', port=port, debug=True, static_folder=static_folder, static_url_path='/static')