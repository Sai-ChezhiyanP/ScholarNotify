# create_teacher.py
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
import getpass
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['student_dashboard']
teachers = db['teachers']

def add_teacher(username, real_name, password, phone):
    existing = teachers.find_one({"username": username})
    if existing:
        print(f"User '{username}' already exists.")
        return
    hashed = generate_password_hash(password)
    teachers.insert_one({
        "username": username,
        "password_hash": hashed,
        "name": real_name,
        "phone": phone
    })
    print(f"Added teacher {username}")

if __name__ == "__main__":
    username = input("Username: ").strip()
    real_name = input("Display name (e.g. John Doe): ").strip()
    password = getpass.getpass("Password (hidden): ")
    phone = input("Teacher phone (+countrycode...): ").strip()
    add_teacher(username, real_name, password, phone)
