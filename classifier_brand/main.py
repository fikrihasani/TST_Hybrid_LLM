import os
import gc
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
from sklearn.utils.class_weight import compute_class_weight
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    set_seed,
    EvalPrediction
)

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
set_seed(42)

MODEL_ID = "flax-community/indonesian-roberta-base"
DATA_PATH = "data/Combined Aaker Brand Personality - Cleaned v0.csv"

OUTPUT_DIR = "./model_results_dir/brand_model_roberta"
SPLIT_SAVE_DIR = "./data/brand_splits"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SPLIT_SAVE_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH).dropna(subset=['cleaned_text', 'personality'])
df['cleaned_text'] = df['cleaned_text'].astype(str)

label2id = {label: i for i, label in enumerate(sorted(df['personality'].unique()))}
id2label = {i: label for label, i in label2id.items()}
df['label'] = df['personality'].map(label2id)

classes = np.unique(df['label'])
class_weights = torch.tensor(compute_class_weight('balanced', classes=classes, y=df['label'].values), dtype=torch.float32)

SPLIT_DIR = "data/brand_splits_v2"
train_df = pd.read_csv(f"{SPLIT_DIR}/train_set.csv")
val_df = pd.read_csv(f"{SPLIT_DIR}/val_set.csv")
test_df = pd.read_csv(f"{SPLIT_DIR}/test_set.csv")

for _frame in (train_df, val_df, test_df):
    _frame['label'] = _frame['personality'].map(label2id)

print(f"Data split v2 dibaca. Ukuran Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
print(f"Label tidak terpetakan: {int(train_df['label'].isna().sum() + val_df['label'].isna().sum() + test_df['label'].isna().sum())}")

train_dataset = Dataset.from_pandas(train_df[['cleaned_text', 'label']])
val_dataset = Dataset.from_pandas(val_df[['cleaned_text', 'label']])
test_dataset = Dataset.from_pandas(test_df[['cleaned_text', 'label']])

class WeightedTrainer(Trainer):
    def __init__(self, class_weights=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        loss_fct = torch.nn.CrossEntropyLoss(weight=self.class_weights.to(outputs.logits.device))
        loss = loss_fct(outputs.logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

def compute_metrics(eval_pred: EvalPrediction):
    preds = np.argmax(eval_pred.predictions[0] if isinstance(eval_pred.predictions, tuple) else eval_pred.predictions, axis=-1)
    return {"macro_f1": f1_score(eval_pred.label_ids, preds, average="macro")}

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
if tokenizer.pad_token is None: tokenizer.pad_token = tokenizer.eos_token

def tokenize(examples): return tokenizer(examples['cleaned_text'], truncation=True, max_length=128)
train_tok = train_dataset.map(tokenize, batched=True, remove_columns=['cleaned_text'])
val_tok = val_dataset.map(tokenize, batched=True, remove_columns=['cleaned_text'])
test_tok = test_dataset.map(tokenize, batched=True, remove_columns=['cleaned_text'])

model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, num_labels=len(label2id), id2label=id2label, label2id=label2id)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=64,
    num_train_epochs=10,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="macro_f1",
    greater_is_better=True,
    logging_dir=f"{OUTPUT_DIR}/logs",
    fp16=torch.cuda.is_available(),
    report_to="none"
)

trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=train_tok,
    eval_dataset=val_tok,
    data_collator=DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="pt"),
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    class_weights=class_weights
)

print("Memulai pelatihan Brand Personality...")
trainer.train()

print("\nMengevaluasi Test Set...")
pred_output = trainer.predict(test_tok)
macro_f1 = pred_output.metrics.get('test_macro_f1', 0)

true_labels = pred_output.label_ids
preds = np.argmax(pred_output.predictions[0] if isinstance(pred_output.predictions, tuple) else pred_output.predictions, axis=-1)
report = classification_report(true_labels, preds, target_names=[id2label[i] for i in range(len(label2id))])

print(f"Test Macro-F1: {macro_f1:.4f}")
print(report)

trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
with open(os.path.join(OUTPUT_DIR, "test_report.txt"), "w") as f:
    f.write(report)
