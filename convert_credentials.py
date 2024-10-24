import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_credentials():
    try:
        # Base credentials dictionary
        creds_json = {
            "type": "service_account",
            "project_id": "citric-earth-439216-r8",
            "private_key_id": "d0cb6a2b8da78a48684f9894d6f5e9233f06a79d",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDP5RPMO1i9I1OL\nS7Z02bulvVcssYXtN+Mqnp1ULSHeV9LsAD/6Yd2cAt4001g3AXuN+N+rfgX+eRAf\nmSH3Y/K1SbPvmROuuaITgaD2zPTOv4ZSlyGdZ+ac4qhOn7kjgSMXdD5JhQ0/kVUj\npBlrdfQek5wCq8kH085pHxtnCcwBia6SBjQt0jGbav0KmT5tYU/mZe/NY1GrZ38h\ntZQjKV6YPfqn1Su4cniNrK7xdr55g1nqWHxonapC9AKIQ1SdAp1Op3CCO5eboiS7\nEWwro9NVFrbkQVUn4FDtFH3glGRZ51/+ZCx4R/Yugn0u6Se8NU38ikcxAjVUp3Tu\nlcqJ0+xtAgMBAAECggEABmS9pKDInFx7Q8Pq0xIlJrY5eZrmCwMWfeeN4BpZOczK\npE5nqUwcNCGUctxzEJH/mkCmpFAGYCqZ99bOSBzvSGsBWSOEivGTjfUFHcH032zd\ndSnHs18QJRAFbBGWcISWrzB4f+tTGnreOu/fhkIE5XHVsPFWh+KYLPxza8pN11g1\n59xbBp5EgrTWC8dZJX2LXdyTdRKNa+RpqIYXUKVfrgFbqbSSV7bdsrP9Sfqyd5VE\ng4KFOsGai5G2mPG1FPjlXS8pRwQgTO6Y5HyYJ0LYp2rw8P//A4LkUQDXEEuq+m7P\ns1OODdSnEvoXibx6Gc2NtxW22mG2s8ru45REiS5jgQKBgQD3wxznSYq79cPolGTG\nH8W4VjRDpzFKJQxJI6HtNJN+A3ipuKABQrzv0Y8uG0Z6Qfo8Xy2Kh5YL+2O1n0Px\n2sb8+k7ctMrEXNJ+eNmAX8gaSzg6dk99X152eauB92xdYPJ6XdrLLvRf/5HBkojn\n60uieTOKkJTZqbWp7SFSge9awQKBgQDWzp/F0F0pse3b7NnakftAwpAhru0wDMKI\nHbxJKhF8UVIXc6e6VQojPZV4dSZ+OjyTgYKeZQUqrGGZ3JMqRwfTICOuIr50e/tt\nud5ruCvA4UaHnUQVcsifdyMd7wh+GbCb8McwNZzjAuiJ17C8AHXklsf6qV+Q8zL+\nEHyFDnGYrQKBgQDmZ+ovJHMCDLFdTvLQVKe4n2IHMCpkO0PLmHlzcBtharUBkJIr\n2fZ+RzGRvQezljuxfQmK9EATcHrvYeb7uWqnw9cm5HJUXcXam2QZP/mEikMGCxQt\nEU11e/yE5qU9yXR1W2am4UmdJLxVeYIbuvMhavkFeSMTsAEiv0Tnx7HhgQKBgQC0\nNVJa/Qw7f5dCSvkVYiT8Vn3elEdOaVYGJZQheVaECiEppZCQROmlWPP9w6KQgUDy\nqtMvGSb1fvq+vwsDi+WnnK3yWBmZ1a3Ahw9vJWonfZbTDP/iUpK3HZbrdO6WA+1j\nVeN1sXS2CmmVwsr1XhmJtWl+A/w1uaIM/T3Jzq1EXQKBgAnVC8Az53AVp/qRhRI/\nzQ+Uf4nMPWaRizgjR9FPGt3NYIpTGu36Fu8tsPE0i/pVNGIDUix3mkPgPaLlESeQ\n05CxWpl8fVlHpRSYr8r40ia/ptJ4HNOrNlpymwHz98EGOxqeJ4b7eLNggADrhzE6\ny8VH1zmfDIk0f8q4P/B3KbbS\n-----END PRIVATE KEY-----\n",
            "client_email": "feedback-project@citric-earth-439216-r8.iam.gserviceaccount.com",
            "client_id": "106025898490615963937",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/feedback-project%40citric-earth-439216-r8.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }

        # Ensure private key is properly formatted
        if not creds_json["private_key"].startswith("-----BEGIN PRIVATE KEY-----\n"):
            print("Warning: Private key format might be incorrect")
            
        print("Credentials loaded successfully")
        return creds_json
            
    except Exception as e:
        print(f"Error in get_credentials: {str(e)}")
        return None

# Read the JSON file
credentials = get_credentials()

# Convert to single line and save to a file
with open('credentials_single_line.txt', 'w') as f:
    f.write(json.dumps(credentials))

# Also print to console
print("Your credentials in single line format:")
print(json.dumps(credentials))
