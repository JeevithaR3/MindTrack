import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
import joblib

df = pd.read_csv("cleaned_dataset.csv", on_bad_lines='skip')

X = df['message']
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

nb = MultinomialNB().fit(X_train_vec, y_train)
lr = LogisticRegression(max_iter=1000).fit(X_train_vec, y_train)

joblib.dump(nb, "honeytrap_detector_model.pkl")
joblib.dump(lr, "logistic_detector_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
print("✅ Models saved.")
