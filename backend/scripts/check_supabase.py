import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Insert a mock student
insert_response = supabase.table("students").insert({
    "full_name": "Test Student",
    "phone_number": "+23200000000",
    "programme": "BSc Software Engineering",
    "otp_verified": False
}).execute()

print("Inserted:", insert_response.data)

# Read it back
read_response = supabase.table("students").select("*").eq("phone_number", "+23200000000").execute()

print("Read back:", read_response.data)