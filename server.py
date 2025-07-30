from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import re
import os
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Constants
FEEDBACK_FILE = 'alerts.json'
LIVE_ALERTS = []
BLOCK_THRESHOLD = 0.65
RISK_LABELS = ["honeytrap", "jobfraud", "scam"]

# Load Models and Vectorizer
nb_model = joblib.load("honeytrap_detector_model.pkl")
lr_model = joblib.load("logistic_detector_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# ----------------------- Utils -----------------------
def clean(text):
    return re.sub(r'[^\w\s]', '', text).lower()

# ----------------------- Prediction Endpoint -----------------------
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    message = clean(data.get("message", ""))
    model_choice = data.get("model", "nb")

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

    # Log alert
    LIVE_ALERTS.append({
        "text": message,
        "bert_label": pred,
        "risk_score": int(conf * 100),
        "timestamp": datetime.now().isoformat(),
        "url": data.get("url", None),
        "model": model_choice
    })

    return jsonify({
        "label": pred,
        "confidence": round(conf, 2),
        "block": block_flag
    })

# ----------------------- Red Teaming -----------------------
@app.route("/simulate_response", methods=["POST"])
def simulate_response():
    data = request.get_json()
    message = clean(data.get("message", ""))
    model_choice = data.get("model", "nb")

    vec = vectorizer.transform([message])
    if model_choice == "lr":
        pred = lr_model.predict(vec)[0]
    else:
        pred = nb_model.predict(vec)[0]

    bait_responses = {
        "honeytrap": "Hey! You seem interesting. Wanna video call? 😊",
        "jobfraud": "That sounds great! Can I pay upfront and start now?",
        "scam": "I’m ready to share my OTP if that’s required!"
    }

    bait = bait_responses.get(pred, "Sorry, could you clarify what you meant?")

    return jsonify({
        "label": pred,
        "bait_reply": bait
    })

# ----------------------- Feedback API -----------------------
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json()
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w") as f:
            json.dump([], f)

    with open(FEEDBACK_FILE, "r") as f:
        existing = json.load(f)

    data["timestamp"] = datetime.now().isoformat()
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

# ----------------------- Lightweight Feedback Logging -----------------------
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

# ----------------------- Get Live Messages -----------------------
@app.route("/api/messages", methods=["GET"])
def get_messages():
    return jsonify(LIVE_ALERTS)

# ----------------------- Run -----------------------
if __name__ == "__main__":
    app.run(port=8000)
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import joblib
# import re
# import os
# import pandas as pd
# import json
# from datetime import datetime

# app = Flask(__name__)
# CORS(app)

# FEEDBACK_FILE = 'alerts.json'
# LIVE_ALERTS = []

# nb_model = joblib.load("honeytrap_detector_model.pkl")
# lr_model = joblib.load("logistic_detector_model.pkl")
# vectorizer = joblib.load("vectorizer.pkl")

# RISK_LABELS = ["honeytrap", "jobfraud", "scam"]
# BLOCK_THRESHOLD = 0.65

# # ----------------------- Text Cleaning -----------------------
# def clean(text):
#     return re.sub(r'[^\w\s]', '', text).lower()

# # ----------------------- Prediction API -----------------------
# @app.route("/predict", methods=["POST"])
# def predict():
#     data = request.get_json()
#     message = clean(data.get("message", ""))
#     model_choice = data.get("model", "nb")

#     vec = vectorizer.transform([message])
#     if model_choice == "lr":
#         probs = lr_model.predict_proba(vec)[0]
#         pred = lr_model.predict(vec)[0]
#         conf = max(probs)
#     else:
#         probs = nb_model.predict_proba(vec)[0]
#         pred = nb_model.predict(vec)[0]
#         conf = max(probs)

#     block_flag = bool(pred in RISK_LABELS and conf >= BLOCK_THRESHOLD)

#     LIVE_ALERTS.append({
#         "text": message,
#         "bert_label": pred,
#         "risk_score": int(conf * 100),
#         "timestamp": datetime.now().isoformat(),
#         "url": data.get("url", None),
#         "model": model_choice
#     })

#     return jsonify({
#         "label": pred,
#         "confidence": round(conf, 2),
#         "block": block_flag
#     })

# # ----------------------- Red Teaming Endpoint -----------------------
# @app.route("/simulate_response", methods=["POST"])
# def simulate_response():
#     data = request.get_json()
#     message = clean(data.get("message", ""))
#     model_choice = data.get("model", "nb")

#     vec = vectorizer.transform([message])
#     if model_choice == "lr":
#         pred = lr_model.predict(vec)[0]
#     else:
#         pred = nb_model.predict(vec)[0]

#     bait_responses = {
#         "honeytrap": "Hey! You seem interesting. Wanna video call? 😊",
#         "jobfraud": "That sounds great! Can I pay upfront and start now?",
#         "scam": "I’m ready to share my OTP if that’s required!"
#     }

#     bait = bait_responses.get(pred, "Sorry, could you clarify what you meant?")

#     return jsonify({
#         "label": pred,
#         "bait_reply": bait
#     })

# # ----------------------- Feedback Endpoints -----------------------
# @app.route("/submit_feedback", methods=["POST"])
# def submit_feedback():
#     data = request.get_json()
#     if not os.path.exists(FEEDBACK_FILE):
#         with open(FEEDBACK_FILE, "w") as f:
#             json.dump([], f)

#     with open(FEEDBACK_FILE, "r") as f:
#         existing = json.load(f)

#     data["timestamp"] = datetime.now().isoformat()
#     existing.append(data)

#     with open(FEEDBACK_FILE, "w") as f:
#         json.dump(existing, f, indent=2)

#     return jsonify({"status": "success"})

# @app.route("/get_alerts", methods=["GET"])
# def get_alerts():
#     if not os.path.exists(FEEDBACK_FILE):
#         return jsonify([])
#     with open(FEEDBACK_FILE, "r") as f:
#         alerts = json.load(f)
#     return jsonify(alerts)

# @app.route("/feedback", methods=["POST"])
# def feedback():
#     data = request.get_json()
#     message = data.get("message", "")
#     label = data.get("label", "")
#     feedback_file = "feedback_log.csv"

#     df = pd.DataFrame([[label, message]], columns=["label", "message"])
#     if os.path.exists(feedback_file):
#         df.to_csv(feedback_file, mode='a', header=False, index=False)
#     else:
#         df.to_csv(feedback_file, index=False)

#     return jsonify({"status": "Feedback received ✅"})

# @app.route("/api/messages", methods=["GET"])
# def get_messages():
#     return jsonify(LIVE_ALERTS)

# # ----------------------- Run Server -----------------------
# if __name__ == "__main__":
#     app.run(port=8000)
