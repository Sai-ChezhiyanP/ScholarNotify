# ingest_data.py
import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")  # put in .env

client = MongoClient(MONGO_URI)
db = client['student_dashboard']
collection = db['students']

# Clear existing
collection.delete_many({})

# Read excel
df = pd.read_excel('student_data.xlsx', dtype=str)  # read as strings to preserve phone formats
# Normalize column names if needed
df = df.rename(columns=lambda c: c.strip())
data = df.to_dict(orient='records')

# optional: ensure phone column exists
for r in data:
    # normalize keys and ensure default fields
    r.setdefault('Parent Phone', None)
    r.setdefault('Name', r.get('Name') or r.get('name') or 'Unknown')
    # convert numeric strings to keep leading + if any
collection.insert_many(data)

print(f"Successfully ingested {len(data)} student records into MongoDB.")
