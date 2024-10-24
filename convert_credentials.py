import json

# Read the JSON file
with open('your-credentials.json', 'r') as f:
    credentials = json.load(f)

# Convert to single line
single_line = json.dumps(credentials)
print(single_line)
