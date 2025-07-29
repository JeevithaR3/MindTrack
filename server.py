from flask import Flask, request, jsonify
import joblib
import re
import pandas as pd
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 🔥 Enables CORS for all routes (HTML/extension safe)

# Load models and vectorizer
nb_model = joblib.load("honeytrap_detector_model.pkl")
lr_model = joblib.load("logistic_detector_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# Risk classification labels and threshold
RISK_LABELS = ["honeytrap", "jobfraud", "scam"]
BLOCK_THRESHOLD = 0.65  # tweak as needed

def clean(text):
    return re.sub(r'[^\w\s]', '', text).lower()

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

    return jsonify({
        "label": pred,
        "confidence": round(conf, 2),
        "block": block_flag
    })

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

if __name__ == "__main__":
    app.run(port=8000)
