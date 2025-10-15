# predict_intent.py
import joblib
import argparse
import numpy as np

def topk_predictions(pipe, text, k=3):
    proba = pipe.predict_proba([text])[0]
    labels = pipe.classes_
    idx = np.argsort(proba)[::-1]
    return [(labels[i], float(proba[i])) for i in idx[:k]]

def predict_with_threshold(pipe, text, threshold=0.45):
    top = topk_predictions(pipe, text, k=1)[0]
    label, prob = top
    if prob < threshold:
        return "fallback", prob
    return label, prob

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/intent_pipeline.joblib")
    parser.add_argument("--text", required=True)
    parser.add_argument("--threshold", type=float, default=0.45)
    args = parser.parse_args()

    pipe = joblib.load(args.model)
    label, prob = predict_with_threshold(pipe, args.text, args.threshold)
    print(f"Top label: {label} (prob={prob:.3f})")
    print("Top-3:")
    for l, p in topk_predictions(pipe, args.text, 3):
        print(f"  {l}: {p:.3f}")

    # --- Debug: Print predictions for a set of example queries ---
    example_queries = [
        "can yoga improve stamina?",
        "can hobbies improve mental health?",
        "are multivitamins necessary?",
        "how to reduce back pain naturally?",
        "how to make healthy habits stick?",
        "how to respond to a choking adult?",
        "how to manage cramps after exercise?",
        "what are the symptoms of eczema?",
        "can I take painkillers every day?",
        "goodbye, till next time",
        "see you again"
    ]
    print("\n--- Example Query Predictions ---")
    for q in example_queries:
        pred, conf = predict_with_threshold(pipe, q, args.threshold)
        print(f'Q: "{q}"\n  Predicted intent: {pred} (confidence: {conf:.2f})')
