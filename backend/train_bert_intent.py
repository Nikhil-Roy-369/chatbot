# train_bert_intent.py
import pandas as pd
from datasets import Dataset
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from sklearn.preprocessing import LabelEncoder
import torch
import joblib
from sklearn.metrics import accuracy_score
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load dataset
df = pd.read_csv("data/intents_clean.csv")

# Encode labels
le = LabelEncoder()
df["label"] = le.fit_transform(df["intent"])

# Save label mapping for later use
joblib.dump(le, "models/label_encoder.joblib")

# Convert to HF dataset
dataset = Dataset.from_pandas(df[["text", "label"]])

# 2. Tokenizer
tokenizer = BertTokenizer.from_pretrained("bert-base-multilingual-cased")

def tokenize(batch):
    return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=64)

dataset = dataset.map(tokenize, batched=True)
dataset = dataset.rename_column("label", "labels")
dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

# Train/test split
dataset = dataset.train_test_split(test_size=0.2, seed=42)
train_dataset = dataset["train"]
test_dataset = dataset["test"]

# 3. Load model
model = BertForSequenceClassification.from_pretrained(
    "bert-base-multilingual-cased",
    num_labels=len(le.classes_)
)

# 4. Training arguments (⚡ fixed eval_strategy for transformers>=4.56.0)
training_args = TrainingArguments(
    output_dir="models/bert-intent",
    eval_strategy="epoch",         # ✅ changed
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    weight_decay=0.01,
    logging_dir="logs",
    logging_steps=10,
    load_best_model_at_end=True
)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=1)
    acc = accuracy_score(labels, predictions)
    return {"accuracy": acc}

# 5. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics 
)

# 6. Train

# Train the model
trainer.train()

# Evaluate on test set and print accuracy

# Evaluate on test set and print accuracy
metrics = trainer.evaluate()
if "accuracy" in metrics:
    print(f"Test Accuracy: {metrics['accuracy']:.4f}")
else:
    print(metrics)


# Get true and predicted labels for test set

# Use test_dataset directly (HuggingFace Dataset)

# Convert test_dataset to pandas DataFrame for easy slicing
test_df = test_dataset.to_pandas()
test_texts = test_df['text'].tolist()
test_labels = test_df['labels'].tolist()

model.eval()
all_preds = []
batch_size = 16
for i in range(0, len(test_texts), batch_size):
    batch = test_texts[i:i+batch_size]
    inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=64)
    with torch.no_grad():
        outputs = model(**inputs)
        preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
        all_preds.extend(preds)

print("\nClassification Report:")
print(classification_report(test_labels, all_preds, target_names=le.classes_))

cm = confusion_matrix(test_labels, all_preds)
plt.figure(figsize=(10,8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=le.classes_, yticklabels=le.classes_)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.tight_layout()
plt.show()

# Save model + tokenizer
model.save_pretrained("models/bert-intent")
tokenizer.save_pretrained("models/bert-intent")
print("✅ BERT model fine-tuned and saved at models/bert-intent")
