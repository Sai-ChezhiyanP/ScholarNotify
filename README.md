# Student Risk Assessment & Parent Notification Dashboard 🎓

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-green.svg)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive educational tool built to help teachers identify at-risk students and automate communication with parents. The system analyzes marks and attendance, categorizes students by risk level, and provides actionable advice for improvement.

## 🚀 Key Features
- **Smart Data Ingestion:** Automatically imports and cleans student data from Excel (`.xlsx`) or CSV into a MongoDB database.
- **Predictive Risk Logic:** Categorizes students into **Red**, **Amber**, and **Green** zones based on custom academic thresholds.
- **Automated Alerts:** Integrated with **Twilio API** to send instant SMS notifications to parents for students in the high-risk zones.
- **Mock Mode:** Includes a developer testing mode to simulate SMS sending without consuming Twilio credits.
- **Secure Authentication:** Teacher-only access protected by hashed passwords and session management.

---

## 📊 Risk Assessment Logic
The dashboard applies the following rules to every student record:

| Status | Academic Performance | Attendance | Recommended Action |
| :--- | :--- | :--- | :--- |
| **🔴 Red** | Marks < 35% | Attendance < 60% | Immediate parent meeting & remedial plan. |
| **🟡 Amber** | Marks 35% - 50% | Attendance 60% - 75% | Extra tutoring and monitor attendance. |
| **🟢 Green** | Marks > 50% | Attendance > 75% | Maintain current progress. |

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/student-risk-dashboard.git](https://github.com/YOUR_USERNAME/student-risk-dashboard.git)
cd student-risk-dashboard

### 2. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

### 3. Install Requirements
pip install -r requirements.txt

### 4. Configuration (.env)
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/
TWILIO_SID=your_twilio_sid
TWILIO_AUTH=your_twilio_auth_token
TWILIO_FROM=your_twilio_phone_number
SECRET_KEY=your_flask_secret_key
SMS_MODE=mock  # Change to "twilio" for real SMS alerts

🖥️ Execution Flow

    Seed the Database: Ensure your student list is in student_data.xlsx, then run:
    Bash

    python ingest_data.py

    Create Admin Account: Run the helper script to create your login:
    Bash

    python create_teacher.py

    Run the Dashboard:
    Bash

    python app.py

    Access the dashboard at: http://127.0.0.1:5000

📁 Project Structure

    app.py: The heart of the application (Flask routes & logic).

    ingest_data.py: Handles data conversion from Excel to NoSQL.

    create_teacher.py: Secure CLI for managing teacher credentials.

    templates/: Contains the frontend dashboard (index.html).

    sms_mock_log.txt: A local log file where SMS messages are saved when in mock mode.

🤝 Contact & Credits

Sai Chezhiyan Engineering Student @ SRM Institute of Science and Technology CEO, SAI TECHFIX SERVICES