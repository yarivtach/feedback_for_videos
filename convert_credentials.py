import json

# Read the JSON file
with open('D:/BGU UNIVERSITY/PROJECT/additional files/google_cloud_key.json', 'r') as f:
    credentials = json.load(f)

# Convert to single line and save to a file
with open('credentials_single_line.txt', 'w') as f:
    f.write(json.dumps(credentials))

# Also print to console
print("Your credentials in single line format:")
print(json.dumps(credentials))
