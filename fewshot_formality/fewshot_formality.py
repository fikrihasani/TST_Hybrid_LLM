import gc
import json
import logging
import os
import random
import re
import sys
import time
import numpy as np
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from transformers import logging as hf_logging

# Import modul utilitas retrieval
from retrieval_utils import (
    retrieve_bm25,
    retrieve_centroid,
    retrieve_dense,
    retrieve_hybrid_early_fusion,
    retrieve_random,
)

try:
    from rank_bm25 import BM25Plus
except ImportError:
    BM25Plus = None

from sentence_transformers import SentenceTransformer

hf_logging.set_verbosity_error()

# --- 0. DEFAULT CONFIG & PROMPTS GENERATOR ---
DEFAULT_CONFIG = {
    "model_id": "google/gemma-3-4b-it",
    "hf_token": os.environ.get("HF_TOKEN", ""),
    "sentence_model": "LazarusNLP/simcse-indobert-base",
    "split_dir": "data/formality_splits", # MENGARAH KE DIREKTORI HASIL SPLIT CLASSIFIER
    "message_col": "text", 
    "style_col": "formality", 
    "rag_personality_col": "formality",
    "rag_text_col": "text",
    "target_personality": ['formal', 'informal'],
    "context_messages": 0,
    "num_samples": "all",  # Menggunakan seluruh 10% test set
    "human_eval_samples": 40, 
    "global_anchor_seed": 42,
    "retrieval_methods": ["dense", "centroid", "bm25", "hybrid_early"],
    "num_examples_range": [5, 10],
    "hybrid_alphas": [0.1, 0.3, 0.5, 0.7, 0.9], 
    "max_new_tokens": 1500,
    "temperature": 0.7,
    "top_p": 0.9,
    "skip_existing": False,
    "show_debug_samples": True,
    "debug_samples": 5,
    "output_dirs": {
        "logs": "outputs/fewshot_logs",
        "cache": "outputs/cache",
        "results": "model_results_dir", # DISAMAKAN DENGAN KONVENSI
        "samples_file": "outputs/fixed_samples_stif.csv"
    }
}

FEWSHOT_GENERATION_PROMPT_TEMPLATE = """### TUGAS TRANSFER GAYA TEKS
Tulis ulang "Teks Sumber" di bawah ini sehingga sepenuhnya mengadopsi pola, nada, leksikal, dan struktur dari kumpulan "Contoh Referensi" yang diberikan. 
Abaikan gaya penulisan asli dari "Teks Sumber" dan pastikan hasil akhir secara konsisten mencerminkan gaya bahasa dari "Contoh Referensi".

### CONTOH REFERENSI
{style_examples_str}

### TEKS SUMBER UNTUK DIUBAH
"{original_message}"

### Instruksi Operasional:
- Ekstrak intisari informasi dari "Teks Sumber".
- Bentuk ulang teks secara struktural dan stilistika agar selaras dengan karakteristik, diksi, dan tata bahasa pada "Contoh Referensi".
- Hanya keluarkan teks hasil penulisan ulang.
- Jangan tambahkan penjelasan, pembuka, penutup, atau catatan apapun.

### HASIL TEKS TARGET:"""

def ensure_setup():
    if not os.path.exists("fewshot_config.json"):
        with open("fewshot_config.json", "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print("Created default fewshot_config.json.")
        
    os.makedirs("prompts", exist_ok=True)
    if not os.path.exists("prompts/fewshot_generation_prompt.txt"):
        with open("prompts/fewshot_generation_prompt.txt", "w", encoding="utf-8") as f:
            f.write(FEWSHOT_GENERATION_PROMPT_TEMPLATE)

# --- 1. SETUP: CONFIGURATION AND LOGGING ---
def validate_and_prepare_personalities(config):
    target_personality = config.get('target_personality')
    if isinstance(target_personality, str): return [target_personality]
    elif isinstance(target_personality, list): return target_personality
    logging.error("Invalid 'target_personality' format in config.")
    return None

def load_config(config_path="fewshot_config.json"):
    with open(config_path, 'r') as f: return json.load(f)

def sanitize_model_name(model_id):
    return re.sub(r'[<>:"|?*\\]', '', model_id.replace("/", "_")).strip()

def cleanup_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

def setup_logging(config):
    base_log_dir = config["output_dirs"]["logs"]
    model_name_safe = sanitize_model_name(config["model_id"])
    model_log_dir = os.path.join(base_log_dir, model_name_safe)
    os.makedirs(model_log_dir, exist_ok=True)
    log_filename = os.path.join(model_log_dir, f"fewshot_experiment_{time.strftime('%Y%m%d-%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()]
    )

def load_prompt_template(filename):
    with open(os.path.join("prompts", filename), "r", encoding="utf-8") as f:
        return f.read()

# --- 2. OPTIMIZED MODEL INITIALIZATION ---
def initialize_models(config):
    try:
        sentence_model = SentenceTransformer(config["sentence_model"])
    except Exception as e:
        logging.error(f"Failed to load sentence transformer: {e}")
        return None, None, None

    hf_model_id = config["model_id"]
    hf_token = os.getenv("HF_TOKEN") or config.get("hf_token")
    
    logging.info(f"Loading Hugging Face model: {hf_model_id}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(hf_model_id, token=hf_token)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        
        hf_model = AutoModelForCausalLM.from_pretrained(
            hf_model_id,
            quantization_config=bnb_config,
            device_map="auto",
            low_cpu_mem_usage=True,
            token=hf_token
        )
    except Exception as e:
        logging.error(f"Gagal memuat model Hugging Face: {e}")
        return None, None, None

    return hf_model, tokenizer, sentence_model

# --- 3. HELPER AND DATA PREPARATION FUNCTIONS ---
def clean_text(text):
    text = str(text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"@[A-Za-z0-9_]+", "", text)
    text = re.sub(r"#[A-Za-z0-9_]+", "", text)
    return re.sub(r"\s+", " ", text).strip()

def load_or_create_rag_embeddings(config, df_pool, sentence_model, personality):
    cache_dir = config["output_dirs"]["cache"]
    os.makedirs(cache_dir, exist_ok=True)
    sanitized_pers = re.sub(r"\W+", "", personality)
    
    texts_path = os.path.join(cache_dir, f"texts_{sanitized_pers}_pool.json")
    emb_path = os.path.join(cache_dir, f"embeddings_{sanitized_pers}_pool.npy")
    
    filtered_df = df_pool[df_pool[config["rag_personality_col"]].str.lower() == personality.lower()]
    if filtered_df.empty: return None
    
    if os.path.exists(texts_path) and os.path.exists(emb_path):
        with open(texts_path, "r", encoding="utf-8") as f: cleaned_texts = json.load(f)
        embeddings = np.load(emb_path)
    else:
        cleaned_texts = [clean_text(t) for t in filtered_df[config["rag_text_col"]].dropna().astype(str).tolist()]
        embeddings = np.vstack([sentence_model.encode(batch, show_progress_bar=False) 
                                for batch in [cleaned_texts[i:i+100] for i in range(0, len(cleaned_texts), 100)]]).astype(np.float16)
                                
        with open(texts_path, "w", encoding="utf-8") as f: json.dump(cleaned_texts, f)
        np.save(emb_path, embeddings)
        
    centroid_emb = np.mean(embeddings, axis=0).reshape(1, -1)
    bm25_model = BM25Plus([t.lower().split() for t in cleaned_texts]) if BM25Plus else None
    
    return {
        "texts": cleaned_texts, 
        "embeddings": embeddings, 
        "centroid": centroid_emb, 
        "bm25_model": bm25_model
    }

def print_debug_samples_from_df(results_df, num_samples=5):
    if results_df.empty: return
    num_to_show = min(num_samples, len(results_df))
    random_indices = random.sample(range(len(results_df)), num_to_show)
    
    personality = results_df.iloc[0]["style_target"]
    method = results_df.iloc[0]["retrieval_method"]
    alpha_val = results_df.iloc[0].get("alpha", "N/A")
    
    title_str = f"# DEBUG SAMPLES: TARGET {personality.upper()} | {method.upper()}"
    if alpha_val != "N/A": title_str += f" | ALPHA: {alpha_val}"
        
    print("\n" + "#" * 60)
    print(title_str)
    print("#" * 60)
    for idx, i in enumerate(random_indices, 1):
        row = results_df.iloc[i]
        print(f"\nSample {idx}/{num_to_show}")
        print(f"ORIGINAL TEXT ({row['original_style']}):\n{row['original_message']}")
        print(f"{'-' * 30}")
        print(f"TRANSFERRED ({personality}):\n{row['paraphrased_message']}")
    print("\n" + "#" * 60 + "\n")

# --- 4. CORE EXPERIMENT LOGIC ---
def get_style_examples(rag_data, sentence_model, num_examples, anchor_message,
                       method="dense", alpha=0.5, seed=None):
    """Mengembalikan (examples, used_fallback). Kosong berarti zero-shot."""
    if method == "zero_shot":
        return [], False
    if not rag_data:
        return [], True
    texts = rag_data["texts"]
    embeddings = rag_data["embeddings"]
    centroid = rag_data["centroid"]

    query_emb = sentence_model.encode([clean_text(anchor_message)])

    try:
        if method == "dense":
            return retrieve_dense(query_emb, embeddings, texts, num_examples), False
        elif method == "centroid":
            return retrieve_centroid(centroid, embeddings, texts, num_examples), False
        elif method == "bm25":
            return retrieve_bm25(clean_text(anchor_message), rag_data.get("bm25_model"),
                                 texts, num_examples), False
        elif method == "hybrid_early":
            return retrieve_hybrid_early_fusion(query_emb, centroid, embeddings, texts,
                                                num_examples, alpha), False
        elif method == "random":
            return retrieve_random(texts, num_examples, seed=seed), False
        else:
            return retrieve_random(texts, num_examples, seed=seed), True
    except Exception as e:
        logging.warning(f"Retrieval {method} gagal, fallback random: {e}")
        return retrieve_random(texts, num_examples, seed=seed), True

def format_few_shot_examples(style_examples):
    return "".join([f'[Contoh Referensi {i}]:\n"{str(ex).strip()}"\n\n' for i, ex in enumerate(style_examples, 1)])

def robust_chat_completion(hf_model, tokenizer, messages, options, seed=None):
    """Mengembalikan (teks, n_token_baru, eos_tercapai)."""
    try:
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(hf_model.device)

        gen_kwargs = dict(
            max_new_tokens=options.get("max_new_tokens", 1500),
            temperature=options.get("temperature", 0.7),
            top_p=options.get("top_p", 0.9),
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
        if seed is not None:
            # transformers 5.x tidak menerima kwarg 'generator' pada generate();
            # penyemaian dilakukan pada RNG torch sebelum generate dipanggil
            torch.manual_seed(int(seed))

        outputs = hf_model.generate(**inputs, **gen_kwargs)

        input_length = inputs.input_ids.shape[1]
        new_ids = outputs[0][input_length:]
        response = tokenizer.decode(new_ids, skip_special_tokens=True)
        n_new = int(new_ids.shape[0])
        eos = bool(n_new > 0 and int(new_ids[-1]) == tokenizer.eos_token_id)
        return response.strip(), n_new, eos
    except Exception as e:
        logging.error(f"Hugging Face generation failed: {e}")
        return "ERROR: Gagal memproses hasil.", 0, False

def generate_paraphrases_sequential(
    config, hf_model, tokenizer, sample_indices, df_test, rag_data, sentence_model, personality, method, num_examples, alpha=None, run_seed=None
):
    gen_template = load_prompt_template("fewshot_generation_prompt.txt")
    rec = {"paraphrased": [], "exemplars": [], "fallback": [], "prompt_len": [],
           "n_new_tokens": [], "eos": [], "sample_index": [], "sample_seed": []}

    desc_str = f"Target: {personality} | {method}"
    if alpha is not None: desc_str += f" (\u03b1={alpha})"
    if run_seed is not None: desc_str += f" | seed={run_seed}"

    with tqdm(total=len(sample_indices), desc=desc_str, leave=True, ncols=100) as pbar:
        for i, msg_idx in enumerate(sample_indices):
            orig_msg = df_test.loc[msg_idx, config["message_col"]]
            sample_seed = None if run_seed is None else int(run_seed) * 100000 + i

            examples, used_fallback = get_style_examples(
                rag_data, sentence_model, num_examples, orig_msg, method,
                alpha if alpha is not None else 0.5, seed=sample_seed
            )

            if examples:
                user_prompt = gen_template.format(
                    style_examples_str=format_few_shot_examples(examples),
                    original_message=orig_msg
                )
            else:
                # cabang zero-shot: hilangkan blok contoh referensi
                user_prompt = gen_template.replace(
                    "### CONTOH REFERENSI\n{style_examples_str}\n\n", "").format(
                    style_examples_str="", original_message=orig_msg
                )

            messages = [
                {"role": "system", "content": "Anda adalah asisten linguistik ahli yang memodifikasi gaya bahasa teks (formality transfer)."},
                {"role": "user", "content": user_prompt},
            ]

            options = {
                "max_new_tokens": config.get("max_new_tokens", 1500),
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.9)
            }

            text, n_new, eos = robust_chat_completion(hf_model, tokenizer, messages, options,
                                                      seed=sample_seed)
            rec["paraphrased"].append(text)
            rec["exemplars"].append(examples)
            rec["fallback"].append(used_fallback)
            rec["prompt_len"].append(len(user_prompt))
            rec["n_new_tokens"].append(n_new)
            rec["eos"].append(eos)
            rec["sample_index"].append(int(msg_idx))
            rec["sample_seed"].append(sample_seed)
            pbar.update(1)

    return rec

# --- 5. MAIN EXECUTION SCRIPT ---
def main():
    ensure_setup()
    config = load_config()
    # Jalankan hanya satu seed ulangan, mis. `python fewshot_formality.py --only-seed 43`
    if len(sys.argv) > 2 and sys.argv[1] == "--only-seed":
        config["run_seeds"] = [int(sys.argv[2])]
    setup_logging(config)
    
    model_name_safe = sanitize_model_name(config["model_id"])
    model_results_dir = os.path.join(config["output_dirs"]["results"], model_name_safe)
    os.makedirs(model_results_dir, exist_ok=True)
    
    hf_model, tokenizer, sentence_model = initialize_models(config)
    if hf_model is None or tokenizer is None or sentence_model is None:
        return

    # PEMBACAAN DATA ABSOLUT UNTUK MENCEGAH DATA LEAKAGE
    try:
        split_dir = config.get("split_dir", "data/formality_splits")
        
        pool_path = os.path.join(split_dir, "retrieval_pool.csv")
        test_path = os.path.join(split_dir, "test_set.csv")
        
        df_pool = pd.read_csv(pool_path)
        df_test = pd.read_csv(test_path)
        
        # Bersihkan NaN jika ada sisa
        df_pool = df_pool.dropna(subset=[config["message_col"], config["style_col"]]).reset_index(drop=True)
        df_test = df_test.dropna(subset=[config["message_col"], config["style_col"]]).reset_index(drop=True)
        
        logging.info(f"Berhasil memuat dataset yang sudah dipecah dari klasifikasi.")
        logging.info(f"Style Pool / Retrieval Index (30%): {len(df_pool)} kalimat.")
        logging.info(f"Test Set (10%): {len(df_test)} kalimat.")
        
    except Exception as e:
        logging.error(f"Gagal memuat data split: {e}. Pastikan script klasifikasi formality sudah selesai dieksekusi terlebih dahulu.")
        return

    personalities = validate_and_prepare_personalities(config)
    for personality in personalities:
        config["target_personality"] = personality
        
        rag_data = load_or_create_rag_embeddings(config, df_pool, sentence_model, personality)
        if not rag_data:
            continue

        valid_sample_indices = [
            idx for idx in df_test.index
            if str(df_test.loc[idx, config["style_col"]]).strip().lower() != personality.lower()
        ]
        
        if not valid_sample_indices:
            continue
            
        # LOGIKA PEMILIHAN SAMPLE: ALL ATAU SEBAGIAN
        if str(config.get("num_samples")).lower() == "all":
            test_indices = valid_sample_indices
            logging.info(f"Mengeksekusi seluruh Test Set: {len(test_indices)} data menuju target {personality}.")
        else:
            max_samples = min(int(config.get("num_samples", 100)), len(valid_sample_indices))
            test_indices = valid_sample_indices[:max_samples]
            logging.info(f"Mengeksekusi {max_samples} data menuju target {personality}.")

        # LOGIKA PEMILIHAN 40 SAMPEL UNTUK HUMAN EVALUATION
        num_human = min(int(config.get("human_eval_samples", 40)), len(test_indices))
        random.seed(config.get("global_anchor_seed", 42)) # Seed agar reproducibility terjaga
        human_eval_indices = set(random.sample(test_indices, num_human))

        for run_seed in config.get("run_seeds", [42]):
            for num_examples in config.get("num_examples_range", [5, 10]):
                for method in config.get("retrieval_methods", []):

                    # Mode zero-shot tidak memakai eksemplar, jadi cukup dijalankan sekali
                    if method == "zero_shot" and num_examples != min(config.get("num_examples_range", [5])):
                        continue

                    alphas_to_test = config.get("hybrid_alphas", [0.5]) if method == "hybrid_early" else [None]

                    for alpha in alphas_to_test:
                        filename_suffix = f"_{method}_alpha{alpha}_{num_examples}" if alpha is not None else f"_{method}_{num_examples}"
                        filename_suffix = f"{filename_suffix}_seed{run_seed}"
                        output_csv = os.path.join(
                            model_results_dir, f"STIF_{personality}_fewshot{filename_suffix}_results.csv"
                        )

                        if os.path.exists(output_csv) and config.get("skip_existing", False):
                            continue

                        run_rec = generate_paraphrases_sequential(
                            config, hf_model, tokenizer, test_indices, df_test, rag_data,
                            sentence_model, personality, method, num_examples, alpha,
                            run_seed=run_seed
                        )

                        results_df = pd.DataFrame({
                            "model_id": [config["model_id"]] * len(test_indices),
                            "original_style": [df_test.loc[idx, config["style_col"]] for idx in test_indices],
                            "style_target": [personality] * len(test_indices),
                            "retrieval_method": [method] * len(test_indices),
                            "alpha": [alpha if alpha is not None else "N/A"] * len(test_indices),
                            "original_message": [df_test.loc[idx, config["message_col"]] for idx in test_indices],
                            "paraphrased_message": run_rec["paraphrased"],
                            "is_human_eval": [True if idx in human_eval_indices else False for idx in test_indices],
                            "sample_index": run_rec["sample_index"],
                            "sample_seed": run_rec["sample_seed"],
                            "run_seed": [run_seed] * len(test_indices),
                            "retrieved_exemplars": [json.dumps(e, ensure_ascii=False) for e in run_rec["exemplars"]],
                            "retrieval_fallback": run_rec["fallback"],
                            "n_exemplars": [len(e) for e in run_rec["exemplars"]],
                            "prompt_chars": run_rec["prompt_len"],
                            "output_tokens": run_rec["n_new_tokens"],
                            "eos_reached": run_rec["eos"],
                            "output_chars": [len(t) for t in run_rec["paraphrased"]],
                        })

                        if config.get("show_debug_samples", True):
                            print_debug_samples_from_df(results_df, config.get("debug_samples", 5))

                        # Simpan full data untuk Automatic Evaluation
                        results_df.to_csv(output_csv, index=False, encoding="utf-8")

                        # Simpan subset khusus untuk Human Evaluation
                        human_output_csv = output_csv.replace("_results.csv", "_HUMAN_EVAL.csv")
                        results_df[results_df["is_human_eval"] == True].to_csv(human_output_csv, index=False, encoding="utf-8")

                        cleanup_memory()

    logging.info("ALL FEW-SHOT EXPERIMENTS COMPLETED.")
    del hf_model
    del tokenizer
    cleanup_memory()

if __name__ == "__main__":
    main()