#!/usr/bin/env python3
"""
Check environment variables loading
"""

import os
from dotenv import load_dotenv

print("🔍 Checking Environment Setup...")

# Load .env file
load_dotenv()

# Check if MONGO_URI exists
mongo_uri = os.getenv('MONGO_URI')

if mongo_uri:
    print("✅ MONGO_URI found in environment")
    print(f"📋 Connection string: {mongo_uri[:50]}...{mongo_uri[-20:]}")
    
    # Check if it has the right format
    if "mongodb+srv://" in mongo_uri:
        print("✅ Connection string format looks correct")
    else:
        print("❌ Connection string format is wrong")
        
    if "videofeedback" in mongo_uri:
        print("✅ Username found in connection string")
    else:
        print("❌ Username not found in connection string")
        
    if "/feedbacks?" in mongo_uri:
        print("✅ Database name 'feedbacks' found")
    else:
        print("❌ Database name 'feedbacks' missing - add '/feedbacks' before the '?'")
        
else:
    print("❌ MONGO_URI not found!")
    print("🔧 Please create a .env file with:")
    print("MONGO_URI=your_connection_string_here")

print("\n📁 Current directory:", os.getcwd())
print("📄 .env file exists:", os.path.exists('.env'))

if os.path.exists('.env'):
    print("\n📖 .env file contents:")
    with open('.env', 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            if 'MONGO_URI' in line:
                print(f"   Line {i}: {line.strip()[:70]}...")
            else:
                print(f"   Line {i}: {line.strip()}") 