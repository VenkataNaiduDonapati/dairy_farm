import requests
from werkzeug.security import generate_password_hash

# Supabase credentials
SUPABASE_URL = "https://stwiytvuedovkfxpcevc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0d2l5dHZ1ZWRvdmtmeHBjZXZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIxNDY1ODMsImV4cCI6MjA3NzcyMjU4M30.VmBwl7wNJ9PVT_O-BPpw9uwiMV3RVqta_3yeqde8pm0"

# User details
username = "Naidu"
password = "Naidu123@"
hashed_password = generate_password_hash(password)

# Prepare headers and payload
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

data = {
    "username": username,
    "password_hash": hashed_password
}

# Insert into Supabase staff table
response = requests.post(f"{SUPABASE_URL}/rest/v1/staff", headers=headers, json=data)

if response.status_code == 201:
    print("✅ Staff user created successfully.")
else:
    print("❌ Error:", response.text)