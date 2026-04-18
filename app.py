# app.py
import os
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

# Twilio
from twilio.rest import Client as TwilioClient

load_dotenv()

# Config from .env
MONGO_URI = os.getenv("MONGO_URI")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = os.getenv("TWILIO_FROM")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
SMS_MODE = os.getenv("SMS_MODE", "mock").lower()  # "mock" or "twilio"

# Flask app
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
app.secret_key = SECRET_KEY
CORS(app)

# Mongo
client = MongoClient(MONGO_URI)
db = client['student_dashboard']
students_collection = db['students']
teachers_collection = db['teachers']

# Twilio client (only initialize if twilio mode)
twilio_client = None
if SMS_MODE == "twilio":
    if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_FROM]):
        raise RuntimeError("TWILIO_SID, TWILIO_AUTH and TWILIO_FROM must be set for twilio mode")
    twilio_client = TwilioClient(TWILIO_SID, TWILIO_AUTH)

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

class Teacher(UserMixin):
    def __init__(self, username, display_name=None):
        self.id = username
        self.display_name = display_name or username

@login_manager.user_loader
def load_user(username):
    t = teachers_collection.find_one({"username": username})
    if t:
        return Teacher(username, display_name=t.get("name"))
    return None

# Risk calculation (same as your previous)
def calculate_risk(student):
    risk_score = 0
    risk_reasons = []
    actionable_advice = []
    try:
        exam_marks = float(student.get('Exam Marks', 0) or 0)
    except:
        exam_marks = 0
    try:
        internal_marks = float(student.get('Internal Marks', 0) or 0)
    except:
        internal_marks = 0
    try:
        attendance_percentage = float(student.get('Attendance Percentage', 100) or 100)
    except:
        attendance_percentage = 100

    if (exam_marks + internal_marks) < 50:
        risk_score += 2
        risk_reasons.append("Low total score (<50)")
        actionable_advice.append("Suggest a remedial session to improve core concepts.")
    if exam_marks < 30:
        risk_score += 1
        risk_reasons.append("Low exam marks (<30)")
        actionable_advice.append("Focus on exam preparation and past papers.")
    if internal_marks < 15:
        risk_score += 1
        risk_reasons.append("Low internal marks (<15)")
        actionable_advice.append("Review project-based work and assignments with the mentor.")
    if attendance_percentage < 75:
        risk_score += 1
        risk_reasons.append("Low attendance (<75%)")
        actionable_advice.append("Alert the student's parents about attendance.")

    if risk_score <= 1:
        risk_level = "Green"
    elif risk_score == 2:
        risk_level = "Amber"
    else:
        risk_level = "Red"

    return {
        **student,
        'risk_level': risk_level,
        'risk_reasons': risk_reasons,
        'actionable_advice': actionable_advice
    }

# Routes: login/logout/index
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        teacher = teachers_collection.find_one({"username": username})
        if teacher and check_password_hash(teacher.get('password_hash', ''), password):
            user = Teacher(username, display_name=teacher.get('name'))
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', teacher_name=current_user.display_name)

@app.route('/students', methods=['GET'])
@login_required
def get_students():
    students = list(students_collection.find({}, {'_id': 0}))
    students_with_risk = [calculate_risk(s) for s in students]
    return jsonify(students_with_risk)

# --- Notification route ---
@app.route('/notify', methods=['POST'])
@login_required
def notify_parents():
    students = list(students_collection.find({}, {'_id': 0}))
    to_notify = []
    for s in students:
        enriched = calculate_risk(s)
        if enriched['risk_level'] in ('Amber', 'Red'):
            to_notify.append(enriched)

    parents_notified = 0
    failed = []

    for s in to_notify:
        parent_phone = s.get('Parent Phone') or s.get('ParentPhone') or s.get('parent_phone')
        if not parent_phone:
            failed.append({"name": s.get('Name'), "reason": "no_parent_phone"})
            continue

        # Compose message
        reasons = ', '.join(s.get('risk_reasons') or [])
        msg = (f"Alert: {s.get('Name')} is at {s.get('risk_level')} risk. Issues: {reasons}. "
               "Please contact the school/teacher for help.")

        if SMS_MODE == "twilio":
            try:
                twilio_client.messages.create(
                    body=msg,
                    from_=TWILIO_FROM,
                    to=parent_phone
                )
                parents_notified += 1
            except Exception as e:
                failed.append({"name": s.get('Name'), "phone": parent_phone, "error": str(e)})
        else:
            # mock mode: write to log file and print to console
            line = f"[MOCK SMS] To: {parent_phone} | {msg}\n"
            print(line)
            with open("sms_mock_log.txt", "a", encoding="utf-8") as f:
                f.write(line)
            parents_notified += 1

    # Optionally notify the teacher with a summary using teacher phone stored in teachers collection
    teacher_data = teachers_collection.find_one({'username': current_user.id})
    teacher_phone = teacher_data.get('phone') if teacher_data else None
    teacher_msg = f"Notification summary: {parents_notified} parents notified for Amber/Red students."

    if teacher_phone:
        if SMS_MODE == "twilio":
            try:
                twilio_client.messages.create(body=teacher_msg, from_=TWILIO_FROM, to=teacher_phone)
            except Exception as e:
                print("Failed to notify teacher:", e)
        else:
            line = f"[MOCK SMS] To: {teacher_phone} | {teacher_msg}\n"
            print(line)
            with open("sms_mock_log.txt", "a", encoding="utf-8") as f:
                f.write(line)

    return jsonify({
        "status": "success",
        "parents_notified": parents_notified,
        "failed": failed
    })
# --- Data ingestion route ---
@app.route('/ingest', methods=['POST'])
def ingest_data():
    """Load student data from Excel into MongoDB"""
    import pandas as pd

    # Get file path from request or default to local student_data.xlsx
    file_path = request.form.get('file_path', 'student_data.xlsx')

    if not os.path.exists(file_path):
        return jsonify({"error": f"File not found: {file_path}"}), 404

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        return jsonify({"error": f"Failed to read Excel: {e}"}), 500

    data = df.to_dict(orient='records')
    if not data:
        return jsonify({"error": "No data found in Excel file"}), 400

    # Clear old records and insert new ones
    students_collection.delete_many({})
    students_collection.insert_many(data)

    return jsonify({
        "status": "Data successfully ingested",
        "records": len(data)
    })


# --- Optional: Auto-ingest data at startup ---
def auto_ingest_on_startup():
    """Automatically ingest student_data.xlsx when the app starts (if collection is empty)."""
    import pandas as pd
    if students_collection.count_documents({}) == 0 and os.path.exists("student_data.xlsx"):
        try:
            df = pd.read_excel("student_data.xlsx")
            data = df.to_dict(orient="records")
            if data:
                students_collection.insert_many(data)
                print(f"✅ Auto-ingested {len(data)} records from student_data.xlsx")
        except Exception as e:
            print(f"⚠️ Auto-ingest failed: {e}")
    else:
        print("ℹ️ Students collection already populated or Excel not found.")


if __name__ == '__main__':
    # Auto-ingest when starting the app
    auto_ingest_on_startup()

    # For development: use_reloader=False avoids duplicate threads on Windows
    app.run(debug=True, use_reloader=False)

