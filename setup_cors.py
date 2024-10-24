from google.cloud import storage

def setup_cors(bucket_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    bucket.cors = [
        {
            'origin': ['https://your-render-app.onrender.com'],  # Replace with your Render URL
            'responseHeader': [
                'Content-Type',
                'x-goog-meta-foo',
                'x-amz-meta-foo',
            ],
            'method': ['GET', 'HEAD'],
            'maxAgeSeconds': 3600
        }
    ]
    bucket.patch()

if __name__ == '__main__':
    setup_cors('feedbackbucket14')  # Replace with your bucket name
