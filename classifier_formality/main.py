import pandas as pd
import torch
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, f1_score
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
    set_seed
)
import numpy as np
import os

set_seed(42)

MODEL_NAME = "flax-community/indonesian-roberta-base"
MAX_LENGTH = 128
BATCH_SIZE = 16
EPOCHS = 10
LEARNING_RATE = 2e-5
OUTPUT_DIR = "./model_results_dir/formality_model_roberta"
DATA_PATH = "data/combined_stif.csv"
SPLIT_SAVE_DIR = "./data/formality_splits"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Menggunakan perangkat: {device}")

df = pd.read_csv(DATA_PATH)
unique_labels = sorted(df['formality'].unique())
label2id = {label: i for i, label in enumerate(unique_labels)}
id2label = {i: label for label, i in label2id.items()}
df['label_id'] = df['formality'].map(label2id)

SPLIT_DIR = "data/formality_splits_v2"
train_df = pd.read_csv(f"{SPLIT_DIR}/train_set.csv")
val_df = pd.read_csv(f"{SPLIT_DIR}/val_set.csv")
test_df = pd.read_csv(f"{SPLIT_DIR}/test_set.csv")

print(f"Distribusi Split v2 - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

train_texts, train_labels = train_df['text'].tolist(), train_df['label_id'].tolist()
val_texts, val_labels = val_df['text'].tolist(), val_df['label_id'].tolist()
test_texts, test_labels = test_df['text'].tolist(), test_df['label_id'].tolist()

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_function(texts):
    return tokenizer(texts, padding="max_length", truncation=True, max_length=MAX_LENGTH, return_tensors="pt")

train_encodings = tokenize_function(train_texts)
val_encodings = tokenize_function(val_texts)
test_encodings = tokenize_function(test_texts)

class TextDataset(Dataset):
    def __init__(self, encodings, labels):
        self.input_ids = encodings['input_ids']
        self.attention_mask = encodings['attention_mask']
        self.labels = torch.tensor(labels, dtype=torch.long)
    def __len__(self): return len(self.labels)
    def __getitem__(self, idx):
        return {'input_ids': self.input_ids[idx], 'attention_mask': self.attention_mask[idx], 'labels': self.labels[idx]}

train_dataset = TextDataset(train_encodings, train_labels)
val_dataset = TextDataset(val_encodings, val_labels)
test_dataset = TextDataset(test_encodings, test_labels)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=len(label2id), id2label=id2label, label2id=label2id
)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    learning_rate=LEARNING_RATE,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_dir=f"{OUTPUT_DIR}/logs",
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    save_total_limit=2,
    bf16=torch.cuda.is_available(),
    report_to="none"
)

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    return {"accuracy": accuracy_score(labels, preds)}

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
)

print("Mulai pelatihan Formality...")
trainer.train()

test_preds = trainer.predict(test_dataset)
y_test_pred = test_preds.predictions.argmax(-1)
test_report_str = classification_report(test_labels, y_test_pred, target_names=list(label2id.keys()), zero_division=0, digits=4)

print("\nCLASSIFICATION REPORT - TEST SET")
print(test_report_str)

os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(os.path.join(OUTPUT_DIR, "classification_report_test.txt"), "w", encoding="utf-8") as f:
    f.write(test_report_str)

model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"\nModel dan data split berhasil disimpan di direktori {OUTPUT_DIR} dan {SPLIT_SAVE_DIR}")
