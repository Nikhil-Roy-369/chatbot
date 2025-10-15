import joblib
import streamlit as st
from sklearn.metrics import accuracy_score
import pandas as pd

# Load model
pipe = joblib.load("../backend/models/intent_pipeline.joblib")

# Load test data
# You may need to adjust the path if running from a different directory
try:
    df = pd.read_csv("../backend/data/intents.csv").fillna("")
    X = df['text'].values
    y = df['intent'].values
    preds = pipe.predict(X)
    acc = accuracy_score(y, preds)
    st.info(f"Model accuracy on all data: {acc:.3f}")
except Exception as e:
    st.error(f"Could not compute accuracy: {e}")
