from flask import Flask, request, jsonify  # ✅ Needed import
from flask_cors import CORS
import joblib
import re
import os
import pandas as pd
import json
from datetime import datetime  # ✅ For timestamping live alerts

app = Flask(__name__)
CORS(app)  # 🔥 Enables CORS for all routes

FEEDBACK_FILE = 'alerts.json'
LIVE_ALERTS = []  # ✅ Stores predictions for /api/messages

# -------------------------- Feedback Storage --------------------------

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json()

    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w") as f:
            json.dump([], f)

    with open(FEEDBACK_FILE, "r") as f:
        existing = json.load(f)

    data["timestamp"] = datetime.now().isoformat()  # ✅ Add timestamp if not already present
    existing.append(data)

    with open(FEEDBACK_FILE, "w") as f:
        json.dump(existing, f, indent=2)

    return jsonify({"status": "success"})

@app.route("/get_alerts", methods=["GET"])
def get_alerts():
    if not os.path.exists(FEEDBACK_FILE):
        return jsonify([])
    with open(FEEDBACK_FILE, "r") as f:
        alerts = json.load(f)
    return jsonify(alerts)

# -------------------------- Load Models --------------------------

nb_model = joblib.load("honeytrap_detector_model.pkl")
lr_model = joblib.load("logistic_detector_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

RISK_LABELS = ["honeytrap", "jobfraud", "scam"]
BLOCK_THRESHOLD = 0.65

def clean(text):
    return re.sub(r'[^\w\s]', '', text).lower()

# -------------------------- Predict Route --------------------------

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    message = clean(data.get("message", ""))
    model_choice = data.get("model", "nb")  # "nb" or "lr"

    vec = vectorizer.transform([message])
    if model_choice == "lr":
        probs = lr_model.predict_proba(vec)[0]
        pred = lr_model.predict(vec)[0]
        conf = max(probs)
    else:
        probs = nb_model.predict_proba(vec)[0]
        pred = nb_model.predict(vec)[0]
        conf = max(probs)

    block_flag = bool(pred in RISK_LABELS and conf >= BLOCK_THRESHOLD)

    print(f"🔎 {model_choice.upper()} | {message} → {pred} ({conf:.2f})")

    # ✅ Store alert for live tracking
    LIVE_ALERTS.append({
        "text": message,
        "bert_label": pred,
        "risk_score": int(conf * 100),
        "timestamp": datetime.now().isoformat(),
        "url": data.get("url", None),
        "model": model_choice  # ✅ FIX: this was missing
    })

    return jsonify({
        "label": pred,
        "confidence": round(conf, 2),
        "block": block_flag
    })

# -------------------------- API to Get Live Messages --------------------------

@app.route("/api/messages", methods=["GET"])
def get_messages():
    return jsonify(LIVE_ALERTS)

# -------------------------- Feedback CSV Logger (Optional) --------------------------

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    message = data.get("message", "")
    label = data.get("label", "")
    feedback_file = "feedback_log.csv"

    df = pd.DataFrame([[label, message]], columns=["label", "message"])
    if os.path.exists(feedback_file):
        df.to_csv(feedback_file, mode='a', header=False, index=False)
    else:
        df.to_csv(feedback_file, index=False)

    return jsonify({"status": "Feedback received ✅"})

# -------------------------- Run Server --------------------------

if __name__ == "__main__":
    app.run(port=8000)
