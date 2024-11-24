from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
from db import Database
import logging

class DataAnalyzer:
    def __init__(self):
        """
        Initialize the DataAnalyzer with MongoDB connection
        """
        try:
            self.db = Database()
            self.raw_data = None
            self.processed_data = None
            self.analysis_results = {}
            logging.info("DataAnalyzer initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize DataAnalyzer: {e}")
            raise

    def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch data from MongoDB collections
        
        Returns:
            Dictionary containing the raw data
        """
        try:
            # Fetch feedback data
            feedback_data = self.db.retrieve_feedback()
            
            # Convert MongoDB cursor to pandas DataFrame
            feedback_df = pd.DataFrame(feedback_data)
            
            # Remove MongoDB's _id field if not needed
            if '_id' in feedback_df.columns:
                feedback_df = feedback_df.drop('_id', axis=1)
            
            self.raw_data = {
                'feedback': feedback_df
            }
            
            logging.info(f"Successfully fetched data: {len(feedback_df)} records")
            return self.raw_data
            
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
            return None

    def parse_data(self) -> Dict[str, Any]:
        """
        Parse and clean the raw data
        
        Returns:
            Dictionary containing parsed data
        """
        if self.raw_data is None:
            raise ValueError("No data to parse. Call fetch_data() first.")

        try:
            parsed_data = {
                'comments': self._parse_comments(),
                'metadata': self._generate_metadata()
            }
            
            self.processed_data = parsed_data
            logging.info("Data parsed successfully")
            return parsed_data
            
        except Exception as e:
            logging.error(f"Error parsing data: {e}")
            return None

    def _parse_comments(self) -> pd.DataFrame:
        """Parse and clean comments data"""
        feedback_df = self.raw_data['feedback'].copy()
        
        # Extract comments from feedback data
        comments_data = []
        for _, row in feedback_df.iterrows():
            if 'comments' in row:
                for comment in row['comments']:
                    comment_entry = {
                        'user_id': row.get('user_id', 'unknown'),
                        'video_name': row.get('video_name', 'unknown'),
                        'timestamp_start': comment.get('time', '').split(' - ')[0],
                        'timestamp_end': comment.get('time', '').split(' - ')[1],
                        'comment_text': comment.get('comment', '')
                    }
                    comments_data.append(comment_entry)
        
        comments_df = pd.DataFrame(comments_data)
        
        # Convert timestamps to float for calculations
        comments_df['timestamp_start'] = comments_df['timestamp_start'].astype(float)
        comments_df['timestamp_end'] = comments_df['timestamp_end'].astype(float)
        
        # Calculate duration and word count
        comments_df['duration'] = comments_df['timestamp_end'] - comments_df['timestamp_start']
        comments_df['word_count'] = comments_df['comment_text'].str.split().str.len()
        
        return comments_df

    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate metadata about the dataset"""
        comments_df = self._parse_comments()
        return {
            'total_users': len(comments_df['user_id'].unique()),
            'total_videos': len(comments_df['video_name'].unique()),
            'total_comments': len(comments_df),
            'analysis_timestamp': datetime.now().isoformat(),
            'average_comment_length': comments_df['word_count'].mean(),
            'average_duration': comments_df['duration'].mean()
        }

    def analyze_comments(self) -> Dict[str, Any]:
        """
        Analyze comments data
        
        Returns:
            Dictionary containing analysis results
        """
        if self.processed_data is None:
            raise ValueError("No processed data. Call parse_data() first.")

        comments_df = self.processed_data['comments']
        
        analysis = {
            'comment_patterns': self._analyze_comment_patterns(comments_df),
            'time_analysis': self._analyze_timestamps(comments_df),
            'user_behavior': self._analyze_user_behavior(comments_df),
            'video_analysis': self._analyze_video_patterns(comments_df)
        }
        
        self.analysis_results['comments'] = analysis
        logging.info("Comment analysis completed")
        return analysis

    def _analyze_comment_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in comments"""
        return {
            'avg_comment_length': df['word_count'].mean(),
            'comment_length_distribution': df['word_count'].value_counts().sort_index().to_dict(),
            'total_words': df['word_count'].sum(),
            'comments_per_video': df.groupby('video_name').size().to_dict()
        }

    def _analyze_timestamps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze timestamp patterns"""
        return {
            'avg_duration': df['duration'].mean(),
            'duration_distribution': df['duration'].describe().to_dict(),
            'timestamp_clusters': self._identify_timestamp_clusters(df),
            'comments_timeline': self._analyze_comments_timeline(df)
        }

    def _analyze_user_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        return {
            'comments_per_user': df.groupby('user_id').size().describe().to_dict(),
            'avg_comments_per_user': len(df) / len(df['user_id'].unique()),
            'user_engagement_patterns': self._calculate_user_engagement(df)
        }

    def _analyze_video_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns specific to videos"""
        return {
            'comments_per_video': df.groupby('video_name').size().to_dict(),
            'avg_comments_per_video': len(df) / len(df['video_name'].unique()),
            'video_engagement_metrics': self._calculate_video_engagement(df)
        }

    def _identify_timestamp_clusters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify clusters of timestamps where multiple users commented"""
        clusters = defaultdict(list)
        for video in df['video_name'].unique():
            video_df = df[df['video_name'] == video]
            # Add clustering logic here
            clusters[video] = {
                'comment_count': len(video_df),
                'timestamp_ranges': video_df['timestamp_start'].describe().to_dict()
            }
        return dict(clusters)

    def _analyze_comments_timeline(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """Analyze the distribution of comments over video timeline"""
        timeline_data = {}
        for video in df['video_name'].unique():
            video_df = df[df['video_name'] == video]
            timeline_data[video] = video_df['timestamp_start'].tolist()
        return timeline_data

    def _calculate_user_engagement(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate user engagement metrics"""
        engagement_metrics = {
            'total_users': len(df['user_id'].unique()),
            'comments_distribution': df.groupby('user_id').size().describe().to_dict(),
            'avg_comment_length_per_user': df.groupby('user_id')['word_count'].mean().to_dict()
        }
        return engagement_metrics

    def _calculate_video_engagement(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate video-specific engagement metrics"""
        video_metrics = {
            'total_videos': len(df['video_name'].unique()),
            'comments_per_video': df.groupby('video_name').size().to_dict(),
            'avg_duration_per_video': df.groupby('video_name')['duration'].mean().to_dict()
        }
        return video_metrics

    def export_results(self, format: str = 'json') -> Any:
        """Export analysis results"""
        if not self.analysis_results:
            raise ValueError("No analysis results to export")

        if format == 'json':
            return pd.json_normalize(self.analysis_results).to_json()
        elif format == 'csv':
            return pd.json_normalize(self.analysis_results).to_csv()
        else:
            raise ValueError(f"Unsupported format: {format}")