import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def parse_data(csv_path):
    df = pd.read_csv(csv_path)
    
    def get_shots(filename):
        match = re.search(r'_(\d+)_results\.csv', filename)
        return int(match.group(1)) if match else 0
    
    df['num_shots'] = df['file_name'].apply(get_shots)
    
    def format_method(row):
        method = str(row['retrieval_method'])
        if method == 'hybrid_early':
            return f"Hybrid (α={row['alpha']})"
        return method.capitalize()
    
    df['method_label'] = df.apply(format_method, axis=1)
    return df

def plot_and_save(df, metric_col, title, ylabel, output_dir, filename, is_lower_better=False):
    if df.empty:
        return

    plt.figure(figsize=(14, 7))
    sns.set_theme(style="whitegrid")
    
    order = [
        'Random', 'Bm25', 'Centroid', 'Dense',
        'Hybrid (α=0.1)', 'Hybrid (α=0.3)', 'Hybrid (α=0.5)', 
        'Hybrid (α=0.7)', 'Hybrid (α=0.9)'
    ]
    order = [m for m in order if m in df['method_label'].unique()]
    
    unique_shots = df['num_shots'].nunique()
    
    ax = sns.barplot(
        data=df, 
        x='method_label', 
        y=metric_col, 
        hue='num_shots',
        order=order,
        palette="mako" if unique_shots > 1 else ["#2b7bba"]
    )
    
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Retrieval Method', fontsize=12, fontweight='bold')
    plt.ylabel(ylabel, fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    
    plt.legend(title='Few-Shot Count', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    if is_lower_better:
        plt.title(f"{title}\n(Lower is Better)", fontsize=14, pad=10)
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Tersimpan: {save_path}")

def generate_visualizations(csv_file, mode="average", target_shots=None):
    if not os.path.exists(csv_file):
        print(f"File tidak ditemukan: {csv_file}")
        return
        
    print(f"\n[{mode.upper()}] Membaca data dari: {csv_file}")
    df = parse_data(csv_file)
    
    if target_shots is not None:
        if isinstance(target_shots, int):
            target_shots = [target_shots]
        if isinstance(target_shots, list):
            df = df[df['num_shots'].isin(target_shots)].copy()
            if df.empty:
                print(f"Peringatan: Tidak ada data untuk num_shots {target_shots}")
                return
            print(f"Memfilter visualisasi untuk {target_shots}-shot saja.")
    
    df_formal = df[df['style_target'] == 'formal'].copy()
    df_informal = df[df['style_target'] == 'informal'].copy()
    
    prefix = "avg_" if mode == "average" else "median_"
    title_prefix = "Average" if mode == "average" else "Median"
    
    metrics = [
        {
            "col": f"{prefix}style_strength", 
            "title": f"{title_prefix} Style Strength Comparison", 
            "ylabel": "Style Strength (Probability)", 
            "filename": "style_strength.png",
            "is_lower_better": False
        },
        {
            "col": f"{prefix}content_preservation", 
            "title": f"{title_prefix} Content Preservation Comparison", 
            "ylabel": "Cosine Similarity", 
            "filename": "content_preservation.png",
            "is_lower_better": False
        },
        {
            "col": f"{prefix}fluency_ppl", 
            "title": f"{title_prefix} Fluency Comparison (Perplexity)", 
            "ylabel": "Perplexity", 
            "filename": "fluency_perplexity.png",
            "is_lower_better": True
        }
    ]
    
    formal_out_dir = os.path.join("visualizations", mode, "formal")
    informal_out_dir = os.path.join("visualizations", mode, "informal")
    
    print(f"--- Generating FORMAL Visualizations ({mode}) ---")
    for m in metrics:
        if m["col"] in df_formal.columns:
            plot_and_save(
                df_formal, m["col"], 
                f"{m['title']} - Formal Target", 
                m["ylabel"], 
                formal_out_dir, 
                m["filename"],
                m["is_lower_better"]
            )
            
    print(f"--- Generating INFORMAL Visualizations ({mode}) ---")
    for m in metrics:
        if m["col"] in df_informal.columns:
            plot_and_save(
                df_informal, m["col"], 
                f"{m['title']} - Informal Target", 
                m["ylabel"], 
                informal_out_dir, 
                m["filename"],
                m["is_lower_better"]
            )

if __name__ == "__main__":
    EVAL_DIR = "evaluation_result"
    MODEL_DIR = "google_gemma-3-4b-it"
    
    AVG_CSV_PATH = os.path.join(EVAL_DIR, MODEL_DIR, "summary_average_metrics.csv")
    MEDIAN_CSV_PATH = os.path.join(EVAL_DIR, MODEL_DIR, "summary_median_metrics.csv")
    
    TARGET_SHOTS = 5 
    
    generate_visualizations(AVG_CSV_PATH, mode="average", target_shots=TARGET_SHOTS)
    
    generate_visualizations(MEDIAN_CSV_PATH, mode="median", target_shots=TARGET_SHOTS)
