from google.cloud import speech_v1
import os
from pydub import AudioSegment
import io
import logging
from datetime import datetime
from db import Database
class VoiceFeedback:
        def __init__(self, language_code="en-US" , db_manager = None):
            """
            Initialize the VoiceFeedback class
       
            Args:
                language_code (str): The language code for speech recognition (default: en-US)
            """
            try:
                self.client = speech_v1.SpeechClient()
                self.language_code = language_code
                self.supported_formats = ['.wav', '.flac', '.mp3', '.m4a', '.ogg', '.webm', '.aac']
                self.current_recording = None
                self.current_transcript = None
                self.db_manager = db_manager
                self.timestampSTART = None
                self.timestampEND = None
                logging.info("VoiceFeedback initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize VoiceFeedback: {e}")
                raise
       
        def start_recording(self, video_timestamp):
           """
           Start recording user's voice while watching video
           
           Args:
           video_timestamp (float): Current timestamp in the video
       Returns:
           bool: Success status
       """
            try:
                self.current_recording = {
                    'timestamp': video_timestamp,
                    'start_time': datetime.now()
                }
                return True
            
            except Exception as e:
                print(f"Error starting recording: {str(e)}")
                return False
        
        
    def stop_recording(self, audio_data):
        """
        Stop recording user's voice
        """
        try:
            self.current_recording = None
            audio_content = self.convert_audio_to_wav(audio_data)
            #write audio content to a temporary file
            transcript = self.transcribe_audio_file(audio_content)
            if transcript:
                comment_data = {
                    'timestamp': self.current_recording['timestamp'],
                    'text': transcript,
                    'date_time': datetime.now()
                }
                self.current_transcript = comment_data
                return comment_data
            else:
                return None
        except Exception as e:
            print(f"Error stopping recording: {str(e)}")
            return None
        
        
    def save_comment(self, edited_text = None):
        """
        Save the comment to the database and potentially editted comment
        """
        if not self.current_transcript:
            return False
        try:
            final_text = edited_text if edited_text else self.current_transcript['text']
            comment_data = {
                'timestamp': self.current_transcript['timestamp'],
                'text': final_text,
            }
            self.db_manager.insert_comment_to_feedback('feedbacks', comment_data)

            return True
        except Exception as e:
            print(f"Error saving comment: {str(e)}")
            return False
       
       
    def convert_audio_to_wav(self, audio_file_path):
       """
       Convert audio file to WAV format if needed
       
       Args:
           audio_file_path (str): Path to the audio file
           
       Returns:
           bytes: Audio content in WAV format
       """
       audio = AudioSegment.from_file(audio_file_path)
       wav_io = io.BytesIO()
       audio.export(wav_io, format='wav')
       return wav_io.getvalue()
   
    def transcribe_audio_file(self, audio_file_path):
       """
       Transcribe an audio file to text
       
       Args:
           audio_file_path (str): Path to the audio file
           
       Returns:
           str: Transcribed text
       """
       try:
           # Check file format and convert if necessary
           file_ext = os.path.splitext(audio_file_path)[1].lower()
           if file_ext not in self.supported_formats:
               raise ValueError(f"Unsupported audio format: {file_ext}")
            # Convert to WAV if not already
           if file_ext != '.wav':
               audio_content = self.convert_audio_to_wav(audio_file_path)
           else:
               with open(audio_file_path, 'rb') as audio_file:
                   audio_content = audio_file.read()
            # Configure audio and recognition settings
           audio = speech_v1.RecognitionAudio(content=audio_content)
           config = speech_v1.RecognitionConfig(
               encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
               language_code=self.language_code,
               enable_automatic_punctuation=True
           )
            # Perform the transcription
           response = self.client.recognize(config=config, audio=audio)
           
           # Combine all transcriptions
           transcript = ' '.join(result.alternatives[0].transcript 
                              for result in response.results)
           
           return transcript
        except Exception as e:
           print(f"Error during transcription: {str(e)}")
           return None
       
       
    def transcribe_stream(self, audio_stream):
       """
       Transcribe audio from a stream (for real-time transcription)
       
       Args:
           audio_stream: Audio stream to transcribe
           
       Returns:
           str: Transcribed text
       """
       # Implementation for streaming recognition
       pass
   
   
    def save_transcript(self, transcript, output_path):
       """
       Save transcript to a file
       
       Args:
           transcript (str): Transcribed text
           output_path (str): Path to save the transcript
       """
       try:
           with open(output_path, 'w') as f:
               f.write(transcript)
           return True
       except Exception as e:
           print(f"Error saving transcript: {str(e)}")
           return False