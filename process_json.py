from collections import defaultdict
from sortedcontainers import SortedList
import matplotlib.pyplot as plt
import random
import json
import math
import matplotlib.pyplot as plt
import random

class CommentProcessor:
    def __init__(self, json_file, time_step=0.5):
        with open(json_file, "r") as f:
            self.json_data = json.load(f)
        self.time_step = time_step
        self.parsed_data = self.parse_original_comments(self.json_data)
        self.processed_data = self.process_video_data(self.parsed_data)
        self.comment_matrices = self.create_comment_matrices(self.processed_data)
        self.comment_intervals = self.generate_comment_intervals(self.comment_matrices)


    def parse_original_comments(self, json_data):
        parsed_data = defaultdict(list)
        for entry in json_data:
            video_name = entry["video_name"]
            user_email = entry["user_email"]
            original_comments = eval(entry["comments"].split("\n")[0].replace("Original comment: ", ""))
            for comment in original_comments:
                start, end = map(float, comment['time'].split(" - "))
                parsed_data[video_name].append({
                    "user_email": user_email,
                    "start_time": start,
                    "end_time": end,
                    "comment": comment["comment"],
                })
        return parsed_data

    def process_video_data(self, video_data):
        result = {}
        
        for video_name, entries in video_data.items():
            # Group entries by user_email
            grouped_by_email = defaultdict(list)
            for entry in entries:
                grouped_by_email[entry['user_email']].append(entry)
            
            # Flatten the grouped data and prepare output
            reorganized_data = []
            for user_email, user_entries in grouped_by_email.items():
                reorganized_data.extend(user_entries)
            
            # Calculate stats
            unique_emails = len(grouped_by_email)
            min_start_time = min(entry['start_time'] for entry in entries)
            max_end_time = max(entry['end_time'] for entry in entries)
            
            # Store in result
            result[video_name] = {
                'reorganized_data': reorganized_data,
                'unique_user_count': unique_emails,
                'min_start_time': min_start_time,
                'max_end_time': max_end_time
            }
        
        return result


    def create_comment_matrices(self, processed_data, a=0.5):
        matrices = {}
        
        for video_name, stats in processed_data.items():
            unique_users = list(set(entry['user_email'] for entry in stats['reorganized_data']))
            unique_user_count = len(unique_users)
            min_start_time = stats['min_start_time']
            max_end_time = stats['max_end_time']
            
            # Calculate matrix dimensions
            num_rows = math.floor((max_end_time - min_start_time) / a)
            num_cols = unique_user_count
            matrix = [["" for _ in range(num_cols)] for _ in range(num_rows)]
            
            # Map user_email to column index
            email_to_col = {email: idx for idx, email in enumerate(unique_users)}
            
            # Populate the matrix
            for entry in stats['reorganized_data']:
                user_email = entry['user_email']
                start_time = entry['start_time']
                end_time = entry['end_time']
                comment = entry['comment']
                col = email_to_col[user_email]
                
                # Find the rows that correspond to the entry's time range
                start_row = math.floor((start_time - min_start_time) / a)
                end_row = math.floor((end_time - min_start_time) / a)
                
                # Fill the rows with the comment
                for row in range(start_row, min(end_row + 1, num_rows)):
                    matrix[row][col] = comment
            
            # Store the matrix
            matrices[video_name] = {
                "matrix": matrix,
                "users": unique_users,
                "min_start_time": min_start_time,
                "max_end_time": max_end_time,
                "time_step": a
            }
        
        return matrices

    def generate_comment_intervals(self, matrices):
        video_intervals = {}

        for video_name, matrix_info in matrices.items():
            matrix = matrix_info['matrix']
            users = matrix_info['users']
            min_start_time = matrix_info['min_start_time']
            time_step = matrix_info['time_step']

            intervals = []
            active_comments = {}  # Store the current active comments for all users
            start_time = min_start_time  # Start time for the current interval

            for row_idx, row in enumerate(matrix):
                current_time = min_start_time + row_idx * time_step
                new_active_comments = {}

                # Collect comments from the current row
                for col_idx, comment in enumerate(row):
                    user_email = users[col_idx]
                    if comment != '':
                        new_active_comments[user_email] = comment

                # Check if the current row's comments differ from the active ones
                if active_comments != new_active_comments:
                    # Create a new interval for the previous active comments
                    if active_comments:
                        intervals.append({
                            "start_time": start_time,
                            "end_time": current_time,
                            "user_emails": list(active_comments.keys()),
                            "comments": active_comments,
                        })

                    # Start a new interval
                    active_comments = new_active_comments
                    start_time = current_time

            # Finalize the last interval at the end of the matrix
            final_time = min_start_time + len(matrix) * time_step
            if active_comments:
                intervals.append({
                    "start_time": start_time,
                    "end_time": final_time,
                    "user_emails": list(active_comments.keys()),
                    "comments": active_comments,
                })

            video_intervals[video_name] = intervals

        return video_intervals


    def visualize_comment_intervals(self, video_intervals, time_step=0.5):
        """
        Visualizes the comment intervals for each video.

        Parameters:
            video_intervals (dict): The intervals for each video, as generated by `generate_comment_intervals_v3`.
            time_step (float): The time step size used for interval calculations.
        """
        for video_name, intervals in video_intervals.items():
            if not intervals:  # Skip empty intervals
                print(f"Skipping visualization for '{video_name}' as it has no intervals.")
                continue
            print(f"Visualizing video: {video_name}")

            # Extract all unique users for consistent color mapping
            all_users = {user for interval in intervals for user in interval['user_emails']}
            user_colors = {user: f"#{random.randint(0, 0xFFFFFF):06x}" for user in all_users}

            fig, ax = plt.subplots(figsize=(12, len(all_users) * 1.2))
            yticks = []
            ylabels = []
            
            for idx, user in enumerate(sorted(all_users)):
                yticks.append(idx)
                ylabels.append(user)

                # Plot intervals for this user
                for interval in intervals:
                    if user in interval['user_emails']:
                        start_time = interval['start_time']
                        end_time = interval['end_time']
                        comment = interval['comments'][user]

                        # Draw the bar
                        ax.barh(idx, end_time - start_time, left=start_time, color=user_colors[user], edgecolor='black', alpha=0.7)
                        
                        # Annotate with the comment
                        ax.text((start_time + end_time) / 2, idx, comment, ha='center', va='center', fontsize=9, color='black')

            ax.set_yticks(yticks)
            ax.set_yticklabels(ylabels)
            ax.set_xlabel('Time (seconds)')
            ax.set_title(f"Comment Intervals for {video_name}")
            ax.grid(axis='x', linestyle='--', alpha=0.6)

            plt.tight_layout()
            plt.show()
        
    def print_processed_data(self):
        for video_name, stats in self.processed_data.items():
            print(f"Video: {video_name}")
            print(f"  Unique user count: {stats['unique_user_count']}")
            print(f"  Min start time: {stats['min_start_time']}")
            print(f"  Max end time: {stats['max_end_time']}")
            print(f"  Reorganized data: {stats['reorganized_data']}")
    
    def print_comment_matrices(self):
        for video_name, matrix_info in self.comment_matrices.items():
            print(f"Video: {video_name}")
            print("Users:", matrix_info['users'])
            print("Matrix:")
            for row in matrix_info['matrix']:
                print(row)
    
    def print_comment_intervals(self):
        for video_name, intervals in self.comment_intervals.items():
            print(f"Video: {video_name}")
            for interval in intervals:
                print(interval)


#analysis = CommentProcessor(r"C:\Users\elias_9no3kg0\OneDrive\Escritorio\Research\Thesis\LLM\data.json")

#analysis.visualize_comment_intervals(analysis.comment_intervals)
