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
    def __init__(self, model_id="Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct"):
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
                    
                    # Mengambil probabilitas berdasarkan TARGET, bukan prediksi model
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
# 4. AGGRESSIVE VRAM CLEANER
# ==========================================
def aggressive_vram_cleaner():
    """Memaksa PyTorch untuk melepas memori yang di-cache ke OS."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    print(f"[VRAM Cleaner] Sisa VRAM teralokasi: {torch.cuda.memory_allocated() / 1024**2:.2f} MB\n")

# ==========================================
# MAIN EXECUTION (PHASE-BASED)
# ==========================================
def process_results_sequential(input_dir, base_output_dir, classifier_model_dir):
    model_folder = os.path.basename(os.path.normpath(input_dir))
    output_dir = os.path.join(base_output_dir, model_folder)
    os.makedirs(output_dir, exist_ok=True)

    # Dapatkan semua file hasil yang valid
    files = [f for f in os.listdir(input_dir) if f.endswith(".csv") and not f.endswith("_HUMAN_EVAL.csv")]
    if not files:
        print("Tidak ada file untuk dievaluasi.")
        return

    # Inisialisasi dictionary untuk menyimpan hasil per file
    evaluation_results = {file: {} for file in files}

    # ====================================================
    # FASE 1: CONTENT PRESERVATION (SimCSE)
    # ====================================================
    print("\n" + "="*50)
    print("FASE 1: CONTENT PRESERVATION EVALUATION")
    print("="*50)
    content_evaluator = ContentPreservationEvaluator()
    
    for file in files:
        file_path = os.path.join(input_dir, file)
        df = pd.read_csv(file_path)
        orig_msgs = df["original_message"].astype(str).tolist()
        para_msgs = df["paraphrased_message"].astype(str).tolist()
        
        sim_scores = content_evaluator.calculate_similarity_batch(orig_msgs, para_msgs)
        evaluation_results[file]["content_preservation"] = sim_scores
        
        # Simpan metadata struktur
        evaluation_results[file]["df_base"] = df

    # Hapus model dan bersihkan VRAM
    del content_evaluator
    aggressive_vram_cleaner()

    # ====================================================
    # FASE 2: STYLE STRENGTH (XLM-RoBERTa)
    # ====================================================
    print("="*50)
    print("FASE 2: STYLE STRENGTH EVALUATION")
    print("="*50)
    style_evaluator = StyleStrengthEvaluator(model_dir=classifier_model_dir)
    
    for file in files:
        df = evaluation_results[file]["df_base"]
        para_msgs = df["paraphrased_message"].astype(str).tolist()
        target_styles = df["style_target"].astype(str).tolist()
        
        style_preds, style_probs, style_acc = style_evaluator.evaluate_batch(para_msgs, target_styles)
        evaluation_results[file]["style_predicted"] = style_preds
        evaluation_results[file]["style_accuracy"] = style_acc
        evaluation_results[file]["style_strength"] = style_probs

    # Hapus model dan bersihkan VRAM
    del style_evaluator
    aggressive_vram_cleaner()

    # ====================================================
    # FASE 3: FLUENCY (LLaMA-3 8B)
    # ====================================================
    print("="*50)
    print("FASE 3: FLUENCY PPL EVALUATION")
    print("="*50)
    fluency_evaluator = FluencyEvaluator()
    
    for file in files:
        df = evaluation_results[file]["df_base"]
        para_msgs = df["paraphrased_message"].astype(str).tolist()
        sim_scores = evaluation_results[file]["content_preservation"]
        
        ppl_scores = []
        for i, msg in enumerate(tqdm(para_msgs, desc=f"PPL: {file}")):
            if "ERROR" in str(msg):
                ppl_scores.append(float('nan'))
                sim_scores[i] = float('nan')
            else:
                ppl_scores.append(fluency_evaluator.calculate_ppl(str(msg)))
                
        evaluation_results[file]["fluency_ppl"] = ppl_scores

    # Hapus model dan bersihkan VRAM
    del fluency_evaluator
    aggressive_vram_cleaner()

    # ====================================================
    # FASE 4: AGREGASI & PENYIMPANAN
    # ====================================================
    print("="*50)
    print("FASE 4: SAVING & AGGREGATION")
    print("="*50)
    
    summary_avg_data = []
    summary_median_data = []

    for file in files:
        df = evaluation_results[file]["df_base"]
        df["content_preservation"] = evaluation_results[file]["content_preservation"]
        df["style_predicted"] = evaluation_results[file]["style_predicted"]
        df["style_accuracy"] = evaluation_results[file]["style_accuracy"]
        df["style_strength"] = evaluation_results[file]["style_strength"]
        df["fluency_ppl"] = evaluation_results[file]["fluency_ppl"]
        
        # Simpan file detail
        output_path = os.path.join(output_dir, f"evaluated_{file}")
        df.to_csv(output_path, index=False)
        
        # Tarik Metadata
        target_style_val = df["style_target"].iloc[0] if "style_target" in df.columns else "N/A"
        retrieval_method_val = df["retrieval_method"].iloc[0] if "retrieval_method" in df.columns else "N/A"
        alpha_val = df["alpha"].iloc[0] if "alpha" in df.columns else "N/A"

        # Kalkulasi Agregat
        avg_acc = df["style_accuracy"].mean()
        avg_sim = df["content_preservation"].mean()
        avg_str = df["style_strength"].mean()
        avg_ppl = df["fluency_ppl"].mean()
        
        median_acc = df["style_accuracy"].median()
        median_sim = df["content_preservation"].median()
        median_str = df["style_strength"].median()
        median_ppl = df["fluency_ppl"].median()

        # Kalkulasi G-Score (berbasis PPL Median agar outlier tidak merusak skor)
        safe_ppl = max(median_ppl, 1.0) if not pd.isna(median_ppl) else float('nan')
        g_score = (avg_str * avg_sim * (1.0 / safe_ppl)) ** (1.0 / 3.0) if not pd.isna(safe_ppl) else float('nan')

        # Simpan metrik
        base_metric = {
            "file_name": file, "style_target": target_style_val,
            "retrieval_method": retrieval_method_val, "alpha": alpha_val, "g_score": g_score
        }
        
        summary_avg_data.append({**base_metric, "avg_content_preservation": avg_sim, "avg_style_accuracy": avg_acc, "avg_style_strength": avg_str, "avg_fluency_ppl": avg_ppl})
        summary_median_data.append({**base_metric, "median_content_preservation": median_sim, "median_style_accuracy": median_acc, "median_style_strength": median_str, "median_fluency_ppl": median_ppl})

    # Simpan file rekapitulasi
    if summary_avg_data and summary_median_data:
        pd.DataFrame(summary_avg_data).to_csv(os.path.join(output_dir, "summary_average_metrics.csv"), index=False)
        pd.DataFrame(summary_median_data).to_csv(os.path.join(output_dir, "summary_median_metrics.csv"), index=False)
        print("Seluruh evaluasi selesai dan berhasil disimpan.")

if __name__ == "__main__":
    RESULT_DIR = "model_results_dir/google_gemma-3-4b-it"
    BASE_EVAL_DIR = "evaluation_result"
    CLASSIFIER_DIR = "style_classifier" 
    
    process_results_sequential(RESULT_DIR, BASE_EVAL_DIR, CLASSIFIER_DIR)