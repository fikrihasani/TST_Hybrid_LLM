# Hybrid Semantic and Stylistic Embedding Retrieval Strategies for Indonesian Text Style Transfer

Code, operational prompt templates, locked data splits, per-sample evaluation outputs, significance tables, and Supplementary Tables S1–S5 for the manuscript *Hybrid Semantic and Stylistic Embedding Retrieval Strategies for Indonesian Text Style Transfer using a Large Language Model* (Journal of Computational and Cognitive Engineering, JCCE-10619).

## Layout

| Path | Contents |
|---|---|
| `fewshot_formality/` | Few-shot generation pipeline for the formality corpus (STIF-Indonesia): generation script (`fewshot_formality.py`), retrieval utilities (`retrieval_utils.py`), target-aware prompt renderer (`prompt_utils.py`), prompt templates (`prompts/`), configuration (`fewshot_config.json`), and locked splits |
| `fewshot_aaker/` | Matching pipeline for the brand personality corpus (ID-Aaker): `main.py`, `retrieval_utils.py`, `prompt_utils.py`, `prompts/`, `fewshot_config.json`, and locked splits |
| `classifier_formality/` | Training script and splits for the two-class IndoBERT/RoBERTa formality style classifier |
| `classifier_brand/` | Training script and splits for the five-class brand personality style classifier |
| `scripts/` | Shared tools: split construction and leakage checks, classifier calibration, development-set alpha selection, prompt parity check (`check_prompt_parity.py`), evaluation (`evaluate_results.py`), paired significance testing (`bootstrap_significance.py`), Holm multiplicity adjustment (`holm_correction.py`), metric reporting, and human-evaluation export |
| `results/` | All primary manuscript results (Tables 4–11, Supplementary Tables S1–S5, 40 per-sample CSVs, raw generations, 90-pair Holm significance tables, dev-set alpha sweep, pilot runs, calibration, error-analysis metadata) plus the archived unlabeled-target prompt ablation (`results/ablation_unlabeled_prompt/`). See `results/README.md` |
| `requirements.txt` | Python dependencies with minimum versions |

## Environment

- **Hardware:** Single workstation with one NVIDIA GeForce RTX 4070 Ti (12 GB VRAM, driver 610.88). Both the 4B generation model (`google/gemma-3-4b-it`) and the 9B perplexity model (`Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct`) are loaded in 4-bit nf4 quantization so they fit on 12 GB VRAM.
- **Software:** Python 3.14.4 with CUDA 12.6, `torch 2.11.0+cu126`, `transformers 5.8.0`, `sentence-transformers 5.4.1`, `accelerate 1.13.0`, `bitsandbytes 0.49.2`, `numpy 2.4.4`, `pandas 3.0.2`, `scikit-learn 1.8.0`, and `scipy 1.17.1`.
- Install with `pip install -r requirements.txt` (install the matching CUDA build of PyTorch from https://pytorch.org/get-started/locally/ if needed).
- Export a Hugging Face token for gated models: `export HF_TOKEN=hf_...` (PowerShell: `$env:HF_TOKEN="hf_..."`). No credentials or tokens are stored in this repository.
- Verify the environment before running: `python scripts/preflight.py`.

## Experimental Design and Operational Prompt

Both corpora share an identical 10-configuration grid per target (`k = 5` exemplars for retrieval conditions, `k = 0` for Zero-shot): three single-paradigm baselines (`Dense`, `BM25+`, `Centroid`), five Hybrid Early Fusion weights (`alpha ∈ {0.1, 0.3, 0.5, 0.7, 0.9}`), and two controls (`Random-k` and `Zero-shot`), yielding `C(10, 2) = 45` within-target pairs (`90` comparable pairs per corpus per metric; Supplementary Table S1).

Every condition uses the symmetric target-aware Indonesian prompt template (`prompts/generation_prompt_v2_id.txt`; English translation in `prompts/generation_prompt_v2_en.txt`), which includes an explicit `### GAYA TARGET` (`### TARGET STYLE`) block naming the target label and a concise one-clause definition (`prompts/targets.json`). Zero-shot differs from retrieval solely by leaving the body of `### CONTOH REFERENSI` empty. Verify template parity programmatically:

```bash
python scripts/check_prompt_parity.py \
    --template fewshot_formality/prompts/generation_prompt_v2_id.txt \
               fewshot_formality/prompts/generation_prompt_v2_en.txt \
    --targets fewshot_formality/prompts/targets.json
```

The unlabeled-target prompt ablation (`prompts/fewshot_generation_prompt.txt`, omitting `### GAYA TARGET`) is archived in `results/ablation_unlabeled_prompt/` and compared configuration-by-configuration in Supplementary Table S5 (`results/supplementary/S5_Prompt_Sensitivity_v1_vs_v2.csv`).

## Data and Locked Splits

| Corpus | Source | Locked Splits | Test Evaluation Scope |
|---|---|---|---|
| Formality (STIF-Indonesia) | `fewshot_formality/data/stif_formal.txt`, `stif_informal.txt` | `fewshot_formality/data/formality_splits_v2/` | All `n = 250` opposite-register test items per target (`formal`, `informal`) |
| Brand personality (ID-Aaker) | `fewshot_aaker/data/Combined Aaker Brand Personality - Cleaned *.csv` | `fewshot_aaker/data/brand_splits_v2/` | `n = 500` non-target test items per target (`Competence`, `Excitement`), sampled uniformly without replacement (seed 42) from pools of 4,594 and 5,082 eligible items |

Each split folder contains `train_set.csv`, `val_set.csv`, `test_set.csv`, `retrieval_pool.csv`, and `split_manifest.json` (plus `alpha_dev.csv` for development-set hybrid weight tuning).

## Summary of Main Results

Full tables and exact per-sample outputs are in `results/tables/manuscript/` and `results/supplementary/SUPPLEMENTARY_TABLES_S1_S5.md`.

| Corpus / Target | Zero-shot (Acc / CP) | Best Single-Paradigm Style (Acc / CP) | Highlighted Retrieval Trade-off (Acc / CP) |
|---|---|---|---|
| Formality — `formal` (`n = 250`) | 0.872 / 0.630 | Dense: 0.868 / 0.643 (Random-k: 0.900 / 0.621) | BM25+ adds +0.023 CP (`p_holm = 0.043`); Centroid drops Acc to 0.724 (`p_holm < 0.001`) |
| Formality — `informal` (`n = 250`) | 0.988 / 0.728 | BM25+ / Centroid / Hybrids: 1.000 (all ns vs Zero-shot) | BM25+ reaches highest CP at 0.749 (+0.021 vs Zero-shot, `p_holm = 0.007`) |
| Brand — `Competence` (`n = 500`) | 0.180 / 0.631 | Centroid: 0.852 / 0.496 | Hybrid `alpha = 0.3` (dev-selected): 0.838 / 0.535 (`p_holm < 0.001` vs Zero-shot) |
| Brand — `Excitement` (`n = 500`) | 0.054 / 0.698 | Centroid: 0.190 / 0.676 | Hybrid `alpha = 0.1`–`0.3`: 0.204–0.186 Acc (near 0.200 five-class chance), 0.683–0.704 CP |

## Reproducing the Results

Run shared scripts from the repository root; run generation and classifier training scripts from inside their module folders.

**1. Rebuild and verify locked splits**

```bash
python scripts/make_splits_formality.py --check
python scripts/make_splits_formality.py
python scripts/make_splits_brand.py --check
python scripts/make_splits_brand.py --alpha-dev
python scripts/verify_splits.py --dir fewshot_aaker/data/brand_splits_v2 \
    --style-col personality --group-col conversation_id_str --gate
```

**2. Train and calibrate the style classifiers**

```bash
cd classifier_formality && python main.py && cd ..
cd classifier_brand     && python main.py && cd ..

python scripts/calibrate_classifier.py \
    --classifier classifier_formality/model_results_dir/formality_model_roberta \
    --val classifier_formality/data/formality_splits_v2/val_set.csv \
    --style-col formality --text-col text
```

**3. Select hybrid semantic weight (`alpha`) on the development set**

```bash
python scripts/select_alpha_dev.py \
    --dir results/alpha_dev/brand_personality \
    --accuracy-col style_accuracy --content-col content_preservation_LaBSE \
    --out results/calibration/alpha_star_aaker.json

python scripts/select_alpha_dev.py \
    --dir results/alpha_dev/formality \
    --accuracy-col style_accuracy --content-col content_preservation_LaBSE \
    --out results/calibration/alpha_star_formality.json
```

**4. Generate transferred texts (target-aware prompt `generation_prompt_v2_id.txt`)**

```bash
cd fewshot_formality && python fewshot_formality.py && cd ..
cd fewshot_aaker     && python main.py              && cd ..
```

**5. Evaluate every configuration**

```bash
python scripts/evaluate_results.py \
    --results      fewshot_formality/model_results_dir/google_gemma-3-4b-it \
    --classifier   fewshot_formality/style_classifier \
    --out          fewshot_formality/evaluation_v2/google_gemma-3-4b-it \
    --encoder      LaBSE=sentence-transformers/LaBSE \
    --legacy-encoder LazarusNLP/simcse-indobert-base \
    --calibration  fewshot_formality/style_classifier/calibration.json
```

**6. Paired significance tests and Holm-Bonferroni adjustment**

```bash
python scripts/bootstrap_significance.py --dir results/per_sample/formality \
    --metric style_accuracy --out results/tables/formality/uji_formality_style_accuracy.csv
python scripts/holm_correction.py --dir results/tables/formality
python scripts/holm_correction.py --dir results/tables/brand_personality
```

Run `bootstrap_significance.py` across all four metrics (`style_accuracy`, `style_strength_calibrated`, `content_preservation_LaBSE`, `replication_rate_8`) for both corpora; `holm_correction.py` computes `p_holm` on `max(p_wilcoxon, p_sign_flip)` within each 90-pair family.

## What Is Not Included

The four fine-tuned RoBERTa style-classifier checkpoints (`model.safetensors`, ~475 MB each, ~1.9 GB total) are excluded via `.gitignore` due to GitHub file-size limits. All training scripts, locked splits, tokenizers, configs, and calibration files (`calibration.json`) are included so the classifiers can be rebuilt with Step 2 above.

## Notes for Reproduction

- Each configuration is identified by retrieval method, exemplar count `k`, and (for Hybrid Early Fusion) semantic weight `alpha`, e.g. `AAKER_competence_fewshot_hybrid_early_alpha0.3_5_seed42`.
- Global random seed `42` fixes data splits, test subset sampling, and exemplar sampling (`sample_seed = run_seed * 100000 + i`); sampling at temperature `0.7` (`top_p = 0.9`, `max_new_tokens = 1500`) introduces small hardware-dependent variation across GPU runs.
- Content preservation is reported with LaBSE (`content_preservation_LaBSE`) only; the legacy `content_preservation` column is retained for comparison and is not reported in the manuscript.
