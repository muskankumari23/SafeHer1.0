import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

# Sample training data for Real-Time Risk Detection
# Features match the requested inputs + risk output
data = [
    # voice, shake, fall, run, loud, late_night, unknown_loc, hr, stress, RISK_LEVEL
    [0, 0, 0, 0, 0, 0, 0, 80, 2, "LOW"],
    [1, 0, 0, 0, 0, 0, 0, 90, 3, "LOW"],
    [0, 0, 0, 1, 0, 0, 0, 110, 4, "LOW"],
    [1, 1, 0, 1, 0, 1, 0, 105, 5, "MEDIUM"],
    [0, 1, 0, 0, 1, 0, 1, 115, 6, "MEDIUM"],
    [1, 0, 1, 0, 1, 1, 0, 120, 7, "HIGH"],
    [0, 0, 0, 1, 0, 1, 0, 98, 4, "LOW"],
    [1, 1, 0, 0, 1, 1, 1, 122, 7, "HIGH"],
    [1, 1, 1, 1, 1, 1, 1, 130, 8, "HIGH"],
    [0, 1, 1, 0, 1, 0, 1, 125, 7, "HIGH"],
    [0, 0, 0, 0, 1, 0, 0, 88, 3, "LOW"],
    [1, 0, 0, 1, 1, 1, 0, 110, 6, "MEDIUM"],
    [1, 1, 1, 0, 1, 1, 1, 140, 9, "HIGH"],
    [1, 1, 1, 1, 1, 0, 1, 135, 8, "HIGH"], # screaming, shaking, falling, running, loud, diff loc
    [0, 0, 1, 0, 0, 0, 0, 95, 4, "MEDIUM"], # JUST a fall
    [0, 0, 0, 0, 0, 1, 1, 85, 3, "MEDIUM"], # late night + unknown location
]

columns = [
    "voice_detected",     # 'help', 'danger'
    "shake_detected",     # accelerometer
    "fall_detected",      # sudden drop in accel
    "running_detected",   # fast motion
    "loud_noise",         # loud sound
    "late_night",         # time
    "unknown_location",   # location history anom
    "heart_rate",         # wearable
    "stress_level",       # wearable
    "risk_level"          # Target
]

df = pd.DataFrame(data, columns=columns)

X = df.drop("risk_level", axis=1)
y = df["risk_level"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train simple RF model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)
print(classification_report(y_test, predictions))

# Ensure model directory exists
os.makedirs("model", exist_ok=True)

# Save Model
joblib.dump(model, "model/risk_model.pkl")
print("Model saved as model/risk_model.pkl")
