import os
import pandas as pd
import torch
import math
import numpy as np
import gc
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModelForSequenceClassification, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer, util

# ==========================================
# 1. FLUENCY EVALUATOR (LLaMA-3 8B 4-bit)
# ==========================================
class FluencyEvaluator:
    def __init__(self, model_id="Sahabat-AI/llama3-8b-cpt-sahabatai-v1-instruct"):
        print(f"Loading Fluency evaluation model: {model_id}")
        
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        self.model.eval()

    def calculate_ppl(self, text):
        if not isinstance(text, str) or len(text.strip()) == 0:
            return float('nan')

        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        input_ids = inputs["input_ids"]
        
        with torch.no_grad():
            outputs = self.model(input_ids, labels=input_ids)
            neg_log_likelihood = outputs.loss
            
        return math.exp(neg_log_likelihood.item())

# ==========================================
# 2. CONTENT PRESERVATION EVALUATOR (SimCSE)
# ==========================================
class ContentPreservationEvaluator:
    def __init__(self, model_id="LazarusNLP/simcse-indobert-base"):
        print(f"Loading Content Preservation model: {model_id}")
        self.model = SentenceTransformer(model_id)

    def calculate_similarity_batch(self, original_texts, paraphrased_texts):
        print("Encoding messages for Content Preservation...")
        orig_embeddings = self.model.encode(original_texts, convert_to_tensor=True, show_progress_bar=True)
        para_embeddings = self.model.encode(paraphrased_texts, convert_to_tensor=True, show_progress_bar=True)
        
        cosine_scores = util.cos_sim(orig_embeddings, para_embeddings)
        pairwise_scores = torch.diagonal(cosine_scores).cpu().numpy().tolist()
        return pairwise_scores

# ==========================================
# 3. STYLE STRENGTH EVALUATOR (Custom RoBERTa)
# ==========================================
class StyleStrengthEvaluator:
    def __init__(self, model_dir="style_classifier"):
        print(f"Loading Style Classifier model from: {model_dir}")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(self.device)
        self.model.eval()
        
        self.label2id = self.model.config.label2id
        self.id2label = self.model.config.id2label

    def evaluate_batch(self, texts, target_styles, batch_size=32):
        print("Evaluating Style Strength...")
        predicted_labels = []
        target_probs = []
        is_correct = []

        for i in tqdm(range(0, len(texts), batch_size), desc="Calculating Style"):
            batch_texts = texts[i:i+batch_size]
            batch_targets = target_styles[i:i+batch_size]

            valid_indices = [j for j, txt in enumerate(batch_texts) if "ERROR" not in str(txt)]
            
            batch_preds = ["ERROR"] * len(batch_texts)
            batch_probs = [float('nan')] * len(batch_texts)
            batch_correct = [float('nan')] * len(batch_texts)

            if valid_indices:
                valid_texts = [batch_texts[j] for j in valid_indices]
                inputs = self.tokenizer(
                    valid_texts, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True, 
                    max_length=128
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    pred_ids = torch.argmax(probs, dim=-1).cpu().numpy()
                    probs_np = probs.cpu().numpy()

                for j, valid_idx in enumerate(valid_indices):
                    target_str = str(batch_targets[valid_idx]).lower().strip()
                    pred_str = self.id2label[pred_ids[j]].lower().strip()
                    
                    batch_preds[valid_idx] = pred_str
                    batch_correct[valid_idx] = 1 if pred_str == target_str else 0
                    
                    # PERBAIKAN: Mengambil probabilitas berdasarkan TARGET, bukan prediksi model
                    if target_str in self.label2id:
                        actual_target_id = self.label2id[target_str]
                        batch_probs[valid_idx] = probs_np[j][actual_target_id]
                    else:
                        batch_probs[valid_idx] = float('nan')

            predicted_labels.extend(batch_preds)
            target_probs.extend(batch_probs)
            is_correct.extend(batch_correct)
            
        return predicted_labels, target_probs, is_correct

# ==========================================
# MAIN EXECUTION
# ==========================================
def process_results(input_dir, base_output_dir):
    fluency_evaluator = FluencyEvaluator()
    content_evaluator = ContentPreservationEvaluator()
    style_evaluator = StyleStrengthEvaluator(model_dir="style_classifier")
    
    model_folder = os.path.basename(os.path.normpath(input_dir))
    output_dir = os.path.join(base_output_dir, model_folder)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Filter: Abaikan sample human eval
    files = [f for f in os.listdir(input_dir) if f.endswith(".csv") and not f.endswith("_HUMAN_EVAL.csv")]
    
    summary_avg_data = []
    summary_median_data = []
    
    for file in files:
        file_path = os.path.join(input_dir, file)
        df = pd.read_csv(file_path)
        
        print(f"\nEvaluating: {file}")
        
        orig_msgs = df["original_message"].astype(str).tolist()
        para_msgs = df["paraphrased_message"].astype(str).tolist()
        target_styles = df["style_target"].astype(str).tolist()
        
        # 1. Evaluasi Content Preservation
        sim_scores = content_evaluator.calculate_similarity_batch(orig_msgs, para_msgs)
        
        # 2. Evaluasi Style Strength
        style_preds, style_probs, style_acc = style_evaluator.evaluate_batch(para_msgs, target_styles)
        
        # 3. Evaluasi Fluency
        ppl_scores = []
        for i, msg in enumerate(tqdm(para_msgs, desc="Calculating PPL")):
            if "ERROR" in str(msg):
                ppl_scores.append(float('nan'))
                sim_scores[i] = float('nan')
            else:
                ppl_scores.append(fluency_evaluator.calculate_ppl(str(msg)))
        
        df["content_preservation"] = sim_scores
        df["style_predicted"] = style_preds
        df["style_accuracy"] = style_acc
        df["style_strength"] = style_probs
        df["fluency_ppl"] = ppl_scores
        
        # Simpan file hasil evaluasi detail
        output_path = os.path.join(output_dir, f"evaluated_{file}")
        df.to_csv(output_path, index=False)
        print(f"Saved to: {output_path}")
        
        target_style_val = df["style_target"].iloc[0] if "style_target" in df.columns else "N/A"
        retrieval_method_val = df["retrieval_method"].iloc[0] if "retrieval_method" in df.columns else "N/A"
        alpha_val = df["alpha"].iloc[0] if "alpha" in df.columns else "N/A"

        # Variabel Agregat
        avg_acc = df["style_accuracy"].mean()
        avg_sim = df["content_preservation"].mean()
        avg_str = df["style_strength"].mean()
        avg_ppl = df["fluency_ppl"].mean()
        
        median_acc = df["style_accuracy"].median()
        median_sim = df["content_preservation"].median()
        median_str = df["style_strength"].median()
        median_ppl = df["fluency_ppl"].median()

        # Kalkulasi G-Score berbasis Median PPL
        safe_ppl = max(median_ppl, 1.0) if not pd.isna(median_ppl) else float('nan')
        g_score = (avg_acc * avg_sim * (1.0 / safe_ppl)) ** (1.0 / 3.0) if not pd.isna(safe_ppl) else float('nan')

        # 4. Agregasi Rata-rata
        summary_avg_data.append({
            "file_name": file,
            "style_target": target_style_val,
            "retrieval_method": retrieval_method_val,
            "alpha": alpha_val,
            "avg_content_preservation": avg_sim,
            "avg_style_accuracy": avg_acc,
            "avg_style_strength": avg_str,
            "avg_fluency_ppl": avg_ppl,
            "g_score": g_score
        })
        
        # 5. Agregasi Median
        summary_median_data.append({
            "file_name": file,
            "style_target": target_style_val,
            "retrieval_method": retrieval_method_val,
            "alpha": alpha_val,
            "median_content_preservation": median_sim,
            "median_style_accuracy": median_acc,
            "median_style_strength": median_str,
            "median_fluency_ppl": median_ppl,
            "g_score": g_score
        })

        # Manajemen VRAM: Kosongkan cache setelah tiap file selesai
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # Simpan file rekapitulasi (Average dan Median)
    if summary_avg_data and summary_median_data:
        df_avg_summary = pd.DataFrame(summary_avg_data)
        df_median_summary = pd.DataFrame(summary_median_data)
        
        avg_summary_path = os.path.join(output_dir, "summary_average_metrics.csv")
        median_summary_path = os.path.join(output_dir, "summary_median_metrics.csv")
        
        df_avg_summary.to_csv(avg_summary_path, index=False)
        df_median_summary.to_csv(median_summary_path, index=False)
        
        print("\n" + "="*50)
        print(f"File agregat berhasil disimpan di:")
        print(f"- {avg_summary_path}")
        print(f"- {median_summary_path}")
        print("="*50)

if __name__ == "__main__":
    RESULT_DIR = "model_results_dir/google_gemma-3-4b-it"
    BASE_EVAL_DIR = "evaluation_result"
    
    process_results(RESULT_DIR, BASE_EVAL_DIR)