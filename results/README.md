# Results

Computed outputs underlying every table and statistic in *Hybrid Semantic and Stylistic Embedding Retrieval Strategies for Indonesian Text Style Transfer using a Large Language Model* (JCCE-10619). All primary folders below correspond to the operational symmetric target-aware prompt (`generation_prompt_v2_id.txt`, 10 configurations per target, 40 configurations / 15,000 test generations total). The unlabeled-target prompt ablation (omitting the explicit target-style block) is archived under `ablation_unlabeled_prompt/`.

## Folder Guide

| Folder | Contents |
|---|---|
| `tables/manuscript/` | Exact CSV tables backing manuscript Tables 4-11 (`Table4_Formality_Main_v2.csv` through `Table11_Error_Brand_Excitement_v2.csv`) |
| `tables/formality/` | Paired bootstrap/Wilcoxon/sign-flip tables (`uji_formality_*.csv`) and Holm-Bonferroni adjusted tables (`uji_formality_*_holm.csv`) across all 90 pairs per metric |
| `tables/brand_personality/` | Equivalent paired significance and Holm-adjusted tables (`uji_aaker_*.csv`, `uji_aaker_*_holm.csv`) across all 90 pairs per metric |
| `supplementary/` | Online diagnostic tables (`SUPPLEMENTARY_TABLES_S1_S5.md` and CSVs `S1_Configuration_Inventory.csv`, `S3_Short_Output_Replication_Sensitivity_v2.csv`, `S4_Holm_Summary_v2.csv`, `S5_Prompt_Sensitivity_v1_vs_v2.csv`) |
| `per_sample/formality/` | Per-sample evaluation CSVs for all 20 formality test configurations (10 methods x 2 targets, `n = 250` per target; 5,000 outputs) |
| `per_sample/brand_personality/` | Per-sample evaluation CSVs for all 20 brand personality test configurations (10 methods x 2 targets, `n = 500` per target; 10,000 outputs) |
| `raw_generations/formality/` | Raw generation CSVs and 25-item human-eval slices for all 20 formality configurations |
| `raw_generations/brand_personality/` | Raw generation CSVs and 25-item human-eval slices for all 20 brand personality configurations |
| `alpha_dev/` | Evaluated development-set alpha sweep (`alpha ∈ {0.1, 0.3, 0.5, 0.7, 0.9}`; 2,500 formality + 5,000 brand generations) |
| `pilot/` | Development-set prompt-wording pilot outputs (`pilot_summary.json` + 20 pilot CSVs) |
| `calibration/` | Classifier temperature-scaling calibration (`calibration_formality.json`, `calibration_aaker.json`) and development-set hybrid weight selections (`alpha_star_formality.json`, `alpha_star_aaker.json`) |
| `error_analysis/` | Per-sample qualitative metadata backing Section 4.3 and Tables 8-11 (`error_analysis_v2_meta.json`) |
| `human_evaluation/` | Shared 25-item export files (`EVAL_MANUSIA_formality.csv`, `EVAL_MANUSIA_aaker.csv`) |
| `ablation_unlabeled_prompt/` | Complete archived outputs from the unlabeled-target prompt ablation (`fewshot_generation_prompt.txt`), enabling independent verification of the prompt ablation table |

## Key Column Definitions (`per_sample/*.csv`)

- `style_accuracy`: binary classifier match (`1` if predicted class equals `style_target`, `0` otherwise).
- `style_strength_calibrated`: temperature-scaled target-class probability (`calibration.json`).
- `content_preservation_LaBSE`: LaBSE cosine similarity between source and generated text (reported in the manuscript). `content_preservation` retains the legacy SimCSE-IndoBERT encoder for comparison only.
- `fluency_ppl` and `ppl_degenerate`: Sahabat-AI (`Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct`) perplexity and degeneracy flag (`fluency_ppl > 1000`).
- `replication_rate_8`: 8-gram template replication (`Rep8`) over lowercased alphanumeric word tokens (`re.findall(r'\w+', text.lower())`) against retrieved exemplars (`0.0` when fewer than 8 word tokens are generated).
- `template_version`, `prompt_sha256`, `target_label`, `target_definition`: exact operational prompt provenance recorded per generated item.
