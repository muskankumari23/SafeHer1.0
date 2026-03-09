from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
import os
import joblib
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "safeher_production_secret_key"

DB_PATH = "database/users.db"
MODEL_PATH = "model/risk_model.pkl"

# Initialize DB if not exists
if not os.path.exists(DB_PATH):
    import create_db
    print("Initializing Database...")

# Load ML Model
try:
    risk_model = joblib.load(MODEL_PATH)
    print("Risk Model Loaded Successfully.")
except Exception as e:
    print(f"Warning: Risk model not found at {MODEL_PATH}. {e}")
    risk_model = None

# ----------------- DB Helpers -----------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user

def create_user(name, phone, email, password, contact1, contact2):
    conn = get_db_connection()
    hashed_pw = generate_password_hash(password)
    conn.execute(
        "INSERT INTO users (name, phone, email, password, contact1, contact2) VALUES (?, ?, ?, ?, ?, ?)",
        (name, phone, email, hashed_pw, contact1, contact2)
    )
    conn.commit()
    conn.close()

# ----------------- Web Routes -----------------

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email_or_phone = request.form.get("email_or_phone")
        password = request.form.get("password")

        # Support login by email OR phone
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? OR phone = ?", (email_or_phone, email_or_phone)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["contact1"] = user["contact1"]
            session["contact2"] = user["contact2"]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials.")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        contact1 = request.form.get("contact1")
        contact2 = request.form.get("contact2", "")

        if not name or not phone or not email or not password or not contact1:
            return render_template("signup.html", error="Please fill all required fields")

        if get_user_by_email(email):
            return render_template("signup.html", error="Email already exists")

        create_user(name, phone, email, password, contact1, contact2)
        return render_template("signup.html", success="Account created! Please login.")

    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template(
        "dashboard.html", 
        username=session.get("name"),
        contact1=session.get("contact1", "+11234567890"),  # Fallbacks
        contact2=session.get("contact2", "+10987654321")
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/contacts", methods=["GET", "POST"])
def emergency_contacts():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    success_msg = None
    if request.method == "POST":
        new_c1 = request.form.get("contact1")
        new_c2 = request.form.get("contact2")
        
        conn = get_db_connection()
        conn.execute("UPDATE users SET contact1 = ?, contact2 = ? WHERE id = ?", (new_c1, new_c2, session["user_id"]))
        conn.commit()
        conn.close()
        
        # Update session
        session["contact1"] = new_c1
        session["contact2"] = new_c2
        success_msg = "Emergency contacts updated successfully!"

    return render_template("emergency_contacts.html", success=success_msg)

@app.route("/risk_analysis", methods=["GET", "POST"])
def risk_analysis():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    risk_level = None
    bg_color = None
    text_color = None
    recommendation = None
    
    if request.method == "POST":
        suspicious_count = int(request.form.get("suspicious_count", 0))
        unfamiliar = int(request.form.get("unfamiliar_location", 0))
        threat = int(request.form.get("threat_level", 0))
        
        # Simple Logic-Based Model Weighting
        score = (suspicious_count * 10) + (unfamiliar * 20) + (threat * 50)
        
        if score >= 50:
            risk_level = "HIGH"
            bg_color = "#fff0f0"
            text_color = "#ff3b3b" # Red
            recommendation = "You are in a high-risk situation. Trigger the SOS alert immediately or call emergency services."
        elif score >= 20:
            risk_level = "MEDIUM"
            bg_color = "#fff9e6"
            text_color = "#f57c00" # Orange
            recommendation = "Stay alert. Move to a well-lit, crowded area and share your live location with a trusted contact."
        else:
            risk_level = "LOW"
            bg_color = "#f0fff0"
            text_color = "#2e7d32" # Green
            recommendation = "You appear to be safe. Continue to stay aware of your surroundings."

    return render_template("risk_analysis.html", 
        risk_level=risk_level, bg_color=bg_color, text_color=text_color, recommendation=recommendation)

@app.route("/safety_tips")
def safety_tips():
    return render_template("safety_tips.html")

@app.route("/helpline")
def helpline():
    return render_template("helpline.html")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    
    return render_template("profile.html", user=user)

# ----------------- API Endpoints -----------------

@app.route("/api/risk-score", methods=["POST"])
def calculate_risk():
    """
    Receives frontend sensor data, runs through the ML model, 
    and returns Risk Level (LOW, MEDIUM, HIGH)
    """
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if risk_model is None:
         return jsonify({"error": "ML Model not loaded"}), 500

    data = request.json
    try:
        # Extract features matching the trained model columns
        features = [
            int(data.get("voice_detected", 0)),
            int(data.get("shake_detected", 0)),
            int(data.get("fall_detected", 0)),
            int(data.get("running_detected", 0)),
            int(data.get("loud_noise", 0)),
            int(data.get("late_night", 0)),
            int(data.get("unknown_location", 0)),
            float(data.get("heart_rate", 80)),      # Synthetic wearable data
            float(data.get("stress_level", 3))       # Synthetic wearable data
        ]

        # Reshape for sklearn prediction
        input_vector = np.array(features).reshape(1, -1)
        
        # Predict
        predicted_risk = risk_model.predict(input_vector)[0]
        
        return jsonify({
            "status": "success",
            "risk_level": predicted_risk
        })

    except Exception as e:
        print(f"Error in prediction: {e}")
        return jsonify({"error": str(e)}), 400

@app.route("/api/alert", methods=["POST"])
def trigger_alert():
    """
    Simulates sending an emergency alert via SMS/Call.
    In a real app, integrate Twilio here.
    """
    data = request.json
    lat = data.get("lat")
    lng = data.get("lng")
    risk_level = data.get("risk_level", "HIGH")
    
    maps_link = f"https://maps.google.com/?q={lat},{lng}" if lat and lng else "Location Unavailable"
    user_name = session.get("name", "User")
    
    # Get contacts to alert
    contacts_to_alert = [c for c in [session.get('contact1'), session.get('contact2'), '+19998887777'] if c]
    
    message = (
        f"SafeHer ALARM from {user_name}! "
        f"Detected Risk: {risk_level}. "
        f"Location: {maps_link} "
        "Triggering Emergency APIs..."
    )
    
    print("\n" + "="*50)
    print("🚨 EMERGENCY ALERT TRIGGERED 🚨")
    print(f"Message Sent to Contacts: {', '.join(contacts_to_alert)}")
    print(message)
    print("="*50 + "\n")

    return jsonify({"status": "alert_sent", "message": message, "alerted_contacts": contacts_to_alert})


if __name__ == "__main__":
    app.run(debug=True, port=5000)