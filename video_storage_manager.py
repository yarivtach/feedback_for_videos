import os
import json
import uuid
from datetime import datetime, timedelta
from google.cloud import storage
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from werkzeug.utils import secure_filename
import mimetypes
from configManager import ConfigManager

class VideoStorageManager:
    def __init__(self, config_manager=None):
        """Initialize the video storage manager with GCS client"""
        self.config_manager = config_manager or ConfigManager()
        self.storage_client = None
        self.bucket = None
        self.bucket_name = None
        self.initialize()
    
    def initialize(self):
        """Initialize the storage client and bucket"""
        try:
            if self.config_manager.initialize_with_base64_credentials():
                self.storage_client = self.config_manager.get_storage_client()
                self.bucket = self.config_manager.get_bucket()
                self.bucket_name = self.config_manager.get_bucket_name()
                print(f"✅ Video Storage Manager initialized with bucket: {self.bucket_name}")
                return True
            else:
                print("❌ Failed to initialize video storage manager")
                return False
        except Exception as e:
            print(f"❌ Error initializing video storage manager: {str(e)}")
            return False
    
    def upload_video(self, video_file, video_name=None, folder="Videos/"):
        """
        Upload a video file to Google Cloud Storage
        
        Args:
            video_file: File object or file path
            video_name: Custom name for the video (optional)
            folder: Folder path in bucket (default: "Videos/")
        
        Returns:
            dict: Upload result with status, file_url, and metadata
        """
        try:
            if not self.storage_client or not self.bucket:
                return {"status": "error", "message": "Storage not initialized"}
            
            # Generate video name if not provided
            if not video_name:
                if hasattr(video_file, 'filename'):
                    video_name = secure_filename(video_file.filename)
                else:
                    video_name = f"video_{uuid.uuid4().hex[:8]}.mp4"
            
            # Ensure video has proper extension
            if not video_name.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm')):
                video_name += '.mp4'
            
            # Create blob path (Videos/ folder to match existing structure)
            blob_path = f"{folder}{video_name}"
            blob = self.bucket.blob(blob_path)
            
            # Set content type
            content_type, _ = mimetypes.guess_type(video_name)
            if not content_type or not content_type.startswith('video/'):
                content_type = 'video/mp4'
            
            # Upload the file
            if hasattr(video_file, 'read'):
                # File object
                video_file.seek(0)  # Reset file pointer
                blob.upload_from_file(video_file, content_type=content_type)
            else:
                # File path
                blob.upload_from_filename(video_file, content_type=content_type)
            
            # Set metadata
            metadata = {
                'uploaded_at': datetime.now().isoformat(),
                'content_type': content_type,
                'size': blob.size
            }
            blob.metadata = metadata
            blob.patch()
            
            print(f"✅ Video uploaded successfully: {blob_path}")
            
            return {
                "status": "success",
                "message": "Video uploaded successfully",
                "blob_name": blob_path,
                "video_name": video_name,
                "public_url": f"https://storage.googleapis.com/{self.bucket_name}/{blob_path}",
                "metadata": metadata
            }
            
        except Exception as e:
            print(f"❌ Error uploading video: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_signed_url(self, blob_name, expiration_hours=1):
        """
        Generate a signed URL for secure video access
        
        Args:
            blob_name: Name of the blob in storage
            expiration_hours: URL expiration time in hours
        
        Returns:
            str: Signed URL or None if error
        """
        try:
            if not self.storage_client or not self.bucket:
                return None
            
            blob = self.bucket.blob(blob_name)
            
            # Generate a signed URL that expires in specified hours
            url = blob.generate_signed_url(
                expiration=datetime.now() + timedelta(hours=expiration_hours),
                method="GET"
            )
            
            return url
            
        except Exception as e:
            print(f"❌ Error generating signed URL: {str(e)}")
            return None
    
    def list_videos(self, folder="Videos/"):
        """
        List all videos in the specified folder
        
        Args:
            folder: Folder path to list videos from (default: "Videos/")
        
        Returns:
            list: List of video information dictionaries
        """
        try:
            if not self.storage_client or not self.bucket:
                return []
            
            videos = []
            blobs = self.bucket.list_blobs(prefix=folder)
            
            for blob in blobs:
                # Skip folders and non-video files, also skip thumbnails folder
                if (blob.name.endswith('/') or 
                    not blob.name.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm')) or
                    '/thumbnails/' in blob.name):
                    continue
                
                # Get video info
                video_info = {
                    'name': os.path.basename(blob.name),
                    'blob_name': blob.name,
                    'size': blob.size,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'content_type': blob.content_type,
                    'public_url': f"https://storage.googleapis.com/{self.bucket_name}/{blob.name}",
                    'signed_url': self.get_signed_url(blob.name, 24)  # 24-hour expiration
                }
                
                # Check for thumbnail in Videos/thumbnails/ folder
                video_base_name = os.path.splitext(video_info['name'])[0]
                thumbnail_path = f"Videos/thumbnails/{video_base_name}.jpg"
                
                # Check if thumbnail exists
                thumbnail_blob = self.bucket.blob(thumbnail_path)
                if thumbnail_blob.exists():
                    video_info['thumbnail'] = f"https://storage.googleapis.com/{self.bucket_name}/{thumbnail_path}"
                    video_info['thumbnail_signed_url'] = self.get_signed_url(thumbnail_path, 24)
                
                # Add metadata if available
                if blob.metadata:
                    video_info['metadata'] = blob.metadata
                
                videos.append(video_info)
            
            return videos
            
        except Exception as e:
            print(f"❌ Error listing videos: {str(e)}")
            return []
    
    def delete_video(self, blob_name):
        """
        Delete a video from Google Cloud Storage
        
        Args:
            blob_name: Name of the blob to delete
        
        Returns:
            dict: Delete result with status and message
        """
        try:
            if not self.storage_client or not self.bucket:
                return {"status": "error", "message": "Storage not initialized"}
            
            blob = self.bucket.blob(blob_name)
            
            if blob.exists():
                blob.delete()
                print(f"✅ Video deleted successfully: {blob_name}")
                return {"status": "success", "message": "Video deleted successfully"}
            else:
                return {"status": "error", "message": "Video not found"}
                
        except Exception as e:
            print(f"❌ Error deleting video: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def download_video(self, blob_name, local_path):
        """
        Download a video from Google Cloud Storage to local file
        
        Args:
            blob_name: Name of the blob to download
            local_path: Local file path to save the video
        
        Returns:
            dict: Download result with status and message
        """
        try:
            if not self.storage_client or not self.bucket:
                return {"status": "error", "message": "Storage not initialized"}
            
            blob = self.bucket.blob(blob_name)
            
            if blob.exists():
                # Ensure directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Download the file
                blob.download_to_filename(local_path)
                print(f"✅ Video downloaded successfully: {local_path}")
                return {"status": "success", "message": "Video downloaded successfully", "local_path": local_path}
            else:
                return {"status": "error", "message": "Video not found in storage"}
                
        except Exception as e:
            print(f"❌ Error downloading video: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_video_info(self, blob_name):
        """
        Get information about a specific video
        
        Args:
            blob_name: Name of the blob
        
        Returns:
            dict: Video information or None if not found
        """
        try:
            if not self.storage_client or not self.bucket:
                return None
            
            blob = self.bucket.blob(blob_name)
            
            if blob.exists():
                blob.reload()  # Refresh blob metadata
                
                return {
                    'name': os.path.basename(blob.name),
                    'blob_name': blob.name,
                    'size': blob.size,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'content_type': blob.content_type,
                    'public_url': f"https://storage.googleapis.com/{self.bucket_name}/{blob.name}",
                    'signed_url': self.get_signed_url(blob.name, 24),
                    'metadata': blob.metadata or {}
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error getting video info: {str(e)}")
            return None
    
    def create_thumbnail_folder(self):
        """Create a Videos/thumbnails folder in the bucket"""
        try:
            # Create a placeholder file in Videos/thumbnails folder
            thumbnail_folder_blob = self.bucket.blob("Videos/thumbnails/.keep")
            thumbnail_folder_blob.upload_from_string("")
            print("✅ Videos/thumbnails folder created")
            return True
        except Exception as e:
            print(f"❌ Error creating Videos/thumbnails folder: {str(e)}")
            return False
    
    def upload_thumbnail(self, thumbnail_file, video_name):
        """
        Upload a thumbnail for a video to the Videos/thumbnails/ folder
        
        Args:
            thumbnail_file: Thumbnail file object or path
            video_name: Associated video name
        
        Returns:
            dict: Upload result
        """
        try:
            # Create thumbnail name based on video name
            video_base_name = os.path.splitext(video_name)[0]
            thumbnail_name = f"{video_base_name}.jpg"
            blob_path = f"Videos/thumbnails/{thumbnail_name}"
            blob = self.bucket.blob(blob_path)
            
            if hasattr(thumbnail_file, 'read'):
                thumbnail_file.seek(0)
                blob.upload_from_file(thumbnail_file, content_type='image/jpeg')
            else:
                blob.upload_from_filename(thumbnail_file, content_type='image/jpeg')
            
            return {
                "status": "success",
                "thumbnail_url": f"https://storage.googleapis.com/{self.bucket_name}/{blob_path}",
                "blob_name": blob_path
            }
            
        except Exception as e:
            print(f"❌ Error uploading thumbnail: {str(e)}")
            return {"status": "error", "message": str(e)} 