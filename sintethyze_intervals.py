from groq import Groq
from process_json import CommentProcessor

import numpy as np
from collections import Counter

class CommentAnalysis:
    def __init__(self, json_file):
        self.comment_processor = CommentProcessor(json_file)
        self.comment_intervals = self.comment_processor.comment_intervals
        self.client = Groq(api_key='Your API key here')

    def get_lower_first_interquartile(self, user_counts):
        """
        Calculate the lower first interquartile (Q1) for the user email counts.
        """
        return np.percentile(user_counts, 50)

    def clean_intervals(self):
        """
        Process the intervals by eliminating intervals with fewer user emails than the Q1 value.
        """
        for video_name, intervals in self.comment_intervals.items():
            if not intervals:  # Skip empty intervals
                continue
            # Extract the number of user_emails for each interval
            user_counts = [len(interval['user_emails']) for interval in intervals]
            lower_first_quartile = self.get_lower_first_interquartile(user_counts)

            # Filter out intervals with fewer user emails than the lower first quartile
            filtered_intervals = []
            for interval in intervals:
                num_users = len(interval['user_emails'])
                if num_users >= lower_first_quartile:
                    filtered_intervals.append(interval)

            # Update the intervals with the filtered ones
            self.comment_intervals[video_name] = filtered_intervals

    def get_most_frequent_comment(self):
        """
        Iterates over all video names and intervals to replace all comments in each interval with the most frequent one.
        The comment key will be 'max'.
        """
        for video_name, intervals in self.comment_intervals.items():
            for interval in intervals:
                # Find the most frequent comment in the interval
                all_comments = list(interval['comments'].values())
                most_common_comment, _ = Counter(all_comments).most_common(1)[0]
                # Replace all comments with the most frequent one and set the key to 'max'
                
                #interval['comments'] = {'max': most_common_comment}

                # Update all user comments to the most frequent one
                for user_email in interval['user_emails']:
                    interval['comments'][user_email] = most_common_comment

    def get_summary_comments(self):
        for video_name, intervals in self.comment_intervals.items():
            for interval in intervals:
                # Join the comments of all users in the interval into one string separated by "-"
                comments = " - ".join(interval['comments'].values())

                # API call to summarize the comments
                completion = self.client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {
                            "role": "user",
                            "content": "You are provided with a list of comments in the following format: each comment type is separated by a hyphen (-). "
                "Your task is to analyze the comments and return a concise summary of the most frequent comment type. "
                "The output should include only the most frequent type of comment, represented as a short and concise string, "
                "enclosed within angle brackets (< and >). Please ensure that there is only **one set of angle brackets** around the summary "
                "and no other angle brackets in your response. Here are the comments: " + comments
                        },
                    ],
                    temperature=1,
                    max_tokens=1024,
                    top_p=1,
                    stream=True,
                    stop=None,
                )

                # Read the response stream and find the summary comment
                summary_comment = ""
                for chunk in completion:
                    summary_comment += chunk.choices[0].delta.content or ""

                # Extract the comment inside the angle brackets < > and replace all the comments with the summary
                start_idx = summary_comment.find("<")
                end_idx = summary_comment.find(">", start_idx)

                if start_idx != -1 and end_idx != -1:
                    concise_comment = summary_comment[start_idx + 1:end_idx]
                    
                    # Replace the original comments with the concise summary comment
                    #interval['comments'] = {email: concise_comment for email in interval['comments'].keys()}
                    for user_email in interval['user_emails']:
                        interval['comments'][user_email] = concise_comment
            



analysis = CommentAnalysis(r"C:\Users\elias_9no3kg0\OneDrive\Escritorio\Research\Thesis\LLM\random_data.json")

analysis.clean_intervals()

print()
print("clean intervals")

print(analysis.comment_intervals)

analysis.comment_processor.visualize_comment_intervals(analysis.comment_intervals)

# print()
# print("max comment")

# analysis.get_most_frequent_comment()

# print(analysis.comment_intervals)

# analysis.comment_processor.visualize_comment_intervals(analysis.comment_intervals)


print()
print("Summary comment")

analysis.get_summary_comments()

print(analysis.comment_intervals)

analysis.comment_processor.visualize_comment_intervals(analysis.comment_intervals)

