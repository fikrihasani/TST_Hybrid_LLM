# Supplementary Tables S1–S5

Companion supplementary tables for *Hybrid Semantic and Stylistic Embedding Retrieval Strategies for Indonesian Text Style Transfer using a Large Language Model* (Journal of Computational and Cognitive Engineering, manuscript JCCE-10619). Machine-readable CSV versions of S1, S3, S4, and S5 are stored alongside this file, and the complete 90-row Holm-adjusted pairwise tables (`uji_*_holm.csv`) are stored under `results/tables/formality/` and `results/tables/brand_personality/`.

## Supplementary Table S1: Configuration Inventory and Pairwise Family Enumeration

Each corpus evaluates 10 configurations per target (`k = 5` for retrieval conditions, `k = 0` for zero-shot; see `S1_Configuration_Inventory.csv`). Within each target, all `C(10, 2) = 45` unordered pairs are compared on identical test items, yielding `2 × 45 = 90` comparable pairs per corpus per metric.

| Corpus | Target | Configuration | k | Seed | Test_n | Prompt_Version |
| --- | --- | --- | --- | --- | --- | --- |
| Formality (STIF) | formal | BM25+ | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | formal | Centroid | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | formal | Dense | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | formal | Hybrid α=0.1 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | formal | Hybrid α=0.3 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | formal | Hybrid α=0.5 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | formal | Hybrid α=0.7 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | formal | Hybrid α=0.9 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | formal | Random-k | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | formal | Zero-shot | 0 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | BM25+ | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | Centroid | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | Dense | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | Hybrid α=0.1 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | Hybrid α=0.3 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | Hybrid α=0.5 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | Hybrid α=0.7 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | Hybrid α=0.9 | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | Random-k | 5 | 42 | 250 | v2-L1 |
| Formality (STIF) | informal | Zero-shot | 0 | 42 | 250 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | BM25+ | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | Centroid | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | Dense | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | Hybrid α=0.1 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | Hybrid α=0.3 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | Hybrid α=0.5 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | Hybrid α=0.7 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | Hybrid α=0.9 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | Random-k | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Competence | Zero-shot | 0 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | BM25+ | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | Centroid | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | Dense | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | Hybrid α=0.1 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | Hybrid α=0.3 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | Hybrid α=0.5 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | Hybrid α=0.7 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | Hybrid α=0.9 | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | Random-k | 5 | 42 | 500 | v2-L1 |
| Brand Personality (ID-Aaker) | Excitement | Zero-shot | 0 | 42 | 500 | v2-L1 |

## Supplementary Table S2: Prompt Templates and Parity Verification

- Operational target-aware Indonesian template (`generation_prompt_v2_id.txt`) SHA-256: `d26ba80565271060d1651bfb6f7d8a9624b44e35dc2e2d8ec5c41ed9b83e1d60`
- English translation (`generation_prompt_v2_en.txt`) SHA-256: `82275a71b7bf0e3f4b5959f1cbefab6987595d9f5f9c63878df0489f29f9f1df`
- Automated parity verification (`python scripts/check_prompt_parity.py`): `OK: 4 targets, 16 renders, 0 issues` (zero-shot differs from retrieval solely in the empty body of `### CONTOH REFERENSI` / `### REFERENCE EXAMPLES`).

### Unlabeled-Target Prompt Ablation Template (`fewshot_generation_prompt.txt`, Prompt v1)
```text
### TUGAS TRANSFER GAYA TEKS
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

### HASIL TEKS TARGET:
```

### Operational Target-Aware Prompt (`generation_prompt_v2_id.txt`, Prompt v2-L1)
```text
### TUGAS TRANSFER GAYA TEKS
Tulis ulang "Teks Sumber" di bawah ini sehingga sepenuhnya mengadopsi pola, nada, leksikal, dan struktur dari GAYA TARGET yang ditetapkan.

### GAYA TARGET
{target_label}: {target_definition}
Terapkan gaya target ini secara konsisten pada seluruh keluaran.

### CONTOH REFERENSI
{style_examples_str}

### TEKS SUMBER UNTUK DIUBAH
"{original_message}"

### Instruksi Operasional:
- Ekstrak intisari informasi dari "Teks Sumber".
- Bentuk ulang teks secara struktural dan stilistika agar selaras dengan karakteristik, diksi, dan tata bahasa pada GAYA TARGET.
- Hanya keluarkan teks hasil penulisan ulang.
- Jangan tambahkan penjelasan, pembuka, penutup, atau catatan apapun.

### HASIL TEKS TARGET:
```

### Operational Target-Aware Prompt: English Translation (`generation_prompt_v2_en.txt`)
```text
### TEXT STYLE TRANSFER TASK
Rewrite the "Source Text" below so that it fully adopts the patterns, tone, vocabulary, and structure of the TARGET STYLE defined below.

### TARGET STYLE
{target_label}: {target_definition}
Apply this target style consistently across the whole output.

### REFERENCE EXAMPLES
{style_examples_str}

### SOURCE TEXT TO BE MODIFIED
"{original_message}"

### Operational Instructions:
- Extract the essence of the information from the "Source Text".
- Reshape the text structurally and stylistically so that it matches the characteristics, diction, and grammar of the TARGET STYLE.
- Output only the rewritten text.
- Do not add explanations, openings, closings, or notes of any kind.

### RESULTING TARGET TEXT:
```

## Supplementary Table S3: Short-Output Shares and Replication Sensitivity (>=8 Word Tokens)

In `scripts/evaluate_results.py`, `Rep8` computes 8-grams over lowercased alphanumeric word tokens (`re.findall(r'\w+', text.lower())`). Across all 15,000 test generations (40 configurations), 1,223 outputs (8.15%) contain fewer than 8 alphanumeric word tokens and thus have an empty 8-gram set scored as zero (nearly identical to 1,232 outputs, or 8.21%, under whitespace splitting; by comparison, 171 outputs, or 1.14%, fall below 8 Sahabat-AI BPE subword tokens). Across the 20 brand configurations, the tie-adjusted Spearman rank correlation between `<8` word-token share and mean `Rep8` is `rho = -0.138` (and `rho = -0.748`, `p = 0.013` across all 10 Competence configurations). Restricting mean `Rep8` to outputs with at least 8 word tokens shifts no configuration mean by more than 0.002 (maximum shift `+0.0017`, from 0.0135 to 0.0152 on Competence Hybrid `alpha = 0.5`) and leaves all configuration rankings unchanged. See `S3_Short_Output_Replication_Sensitivity_v2.csv`.

| Corpus | Target | Method | n | Output_lt8_word_tokens_n | Output_lt8_word_tokens_pct | Output_lt8_bpe_tokens_pct | Rep8_All | Rep8_ge8_word_tokens | Delta_Rep8_word_tokens | Copy_Any_pct | Copy_Full_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STIF | formal | BM25+ | 250 | 18 | 7.20 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | formal | Centroid | 250 | 5 | 2.00 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | formal | Dense | 250 | 13 | 5.20 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | formal | Hybrid α=0.1 | 250 | 9 | 3.60 | 0.40 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | formal | Hybrid α=0.3 | 250 | 13 | 5.20 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | formal | Hybrid α=0.5 | 250 | 10 | 4.00 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | formal | Hybrid α=0.7 | 250 | 12 | 4.80 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | formal | Hybrid α=0.9 | 250 | 14 | 5.60 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | formal | Random-k | 250 | 9 | 3.60 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | formal | Zero-shot | 250 | 8 | 3.20 | 0.40 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | BM25+ | 250 | 33 | 13.20 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | Centroid | 250 | 30 | 12.00 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | Dense | 250 | 32 | 12.80 | 0.40 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | Hybrid α=0.1 | 250 | 29 | 11.60 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | Hybrid α=0.3 | 250 | 32 | 12.80 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | Hybrid α=0.5 | 250 | 28 | 11.20 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | Hybrid α=0.7 | 250 | 33 | 13.20 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | Hybrid α=0.9 | 250 | 32 | 12.80 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | Random-k | 250 | 36 | 14.40 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| STIF | informal | Zero-shot | 250 | 36 | 14.40 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| AAKER | competence | BM25+ | 500 | 41 | 8.20 | 0.40 | 0.012 | 0.013 | +0.001 | 5.8 | 0.0 |
| AAKER | competence | Centroid | 500 | 0 | 0.00 | 0.00 | 0.023 | 0.023 | +0.000 | 21.2 | 0.0 |
| AAKER | competence | Dense | 500 | 91 | 18.20 | 4.60 | 0.000 | 0.000 | +0.000 | 0.4 | 0.0 |
| AAKER | competence | Hybrid α=0.1 | 500 | 0 | 0.00 | 0.00 | 0.071 | 0.071 | +0.000 | 35.0 | 0.2 |
| AAKER | competence | Hybrid α=0.3 | 500 | 2 | 0.40 | 0.20 | 0.060 | 0.061 | +0.000 | 27.8 | 0.2 |
| AAKER | competence | Hybrid α=0.5 | 500 | 57 | 11.40 | 2.40 | 0.013 | 0.015 | +0.002 | 6.6 | 0.0 |
| AAKER | competence | Hybrid α=0.7 | 500 | 85 | 17.00 | 4.00 | 0.003 | 0.004 | +0.001 | 2.2 | 0.0 |
| AAKER | competence | Hybrid α=0.9 | 500 | 90 | 18.00 | 3.80 | 0.002 | 0.002 | +0.000 | 1.0 | 0.0 |
| AAKER | competence | Random-k | 500 | 24 | 4.80 | 0.40 | 0.001 | 0.001 | +0.000 | 0.6 | 0.0 |
| AAKER | competence | Zero-shot | 500 | 75 | 15.00 | 4.40 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| AAKER | excitement | BM25+ | 500 | 35 | 7.00 | 0.60 | 0.000 | 0.000 | +0.000 | 0.2 | 0.0 |
| AAKER | excitement | Centroid | 500 | 7 | 1.40 | 0.00 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| AAKER | excitement | Dense | 500 | 48 | 9.60 | 2.20 | 0.000 | 0.000 | +0.000 | 0.2 | 0.0 |
| AAKER | excitement | Hybrid α=0.1 | 500 | 10 | 2.00 | 0.20 | 0.000 | 0.000 | +0.000 | 0.2 | 0.0 |
| AAKER | excitement | Hybrid α=0.3 | 500 | 35 | 7.00 | 1.60 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| AAKER | excitement | Hybrid α=0.5 | 500 | 43 | 8.60 | 2.40 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| AAKER | excitement | Hybrid α=0.7 | 500 | 46 | 9.20 | 2.60 | 0.000 | 0.000 | +0.000 | 0.2 | 0.0 |
| AAKER | excitement | Hybrid α=0.9 | 500 | 45 | 9.00 | 2.60 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| AAKER | excitement | Random-k | 500 | 30 | 6.00 | 0.40 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |
| AAKER | excitement | Zero-shot | 500 | 27 | 5.40 | 0.80 | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 |

## Supplementary Table S4: Holm Multiplicity Correction Summary (90 Pairs per Family)

Primary p-value per pair is `max(p_wilcoxon, p_sign_flip)`. Complete 90-row CSV tables are provided as `results/tables/formality/uji_formality_*_holm.csv` and `results/tables/brand_personality/uji_aaker_*_holm.csv`, with the summary in `S4_Holm_Summary_v2.csv`.

| Family | Pairs | CI95_Excludes_Zero | Triple_Concordance_Uncorrected | Triple_Concordance_Holm | Dropped_After_Holm |
| --- | --- | --- | --- | --- | --- |
| aaker_content_preservation_LaBSE | 90 | 73 | 72 | 62 | 10 |
| aaker_replication_rate_8 | 90 | 37 | 35 | 30 | 5 |
| aaker_style_accuracy | 90 | 67 | 66 | 51 | 15 |
| aaker_style_strength_calibrated | 90 | 68 | 65 | 53 | 12 |
| formality_content_preservation_LaBSE | 90 | 56 | 50 | 31 | 19 |
| formality_replication_rate_8 | 90 | 0 | 0 | 0 | 0 |
| formality_style_accuracy | 90 | 20 | 18 | 7 | 11 |
| formality_style_strength_calibrated | 90 | 55 | 48 | 28 | 20 |

## Supplementary Table S5: Unlabeled-Target Prompt Ablation (Prompt v1 vs Operational Target-Aware Prompt v2-L1)

Comparison between the unlabeled-target prompt ablation (`v1`, archived in `results/ablation_unlabeled_prompt/`) and the operational target-aware prompt (`v2`, primary `results/`). See `S5_Prompt_Sensitivity_v1_vs_v2.csv`.

| Corpus | Target | Method | Acc_v1 | Acc_v2 | dAcc | SS_v1 | SS_v2 | dSS | CP_v1 | CP_v2 | dCP | MedPPL_v1 | MedPPL_v2 | Deg_v1_pct | Deg_v2_pct | Rep8_v1 | Rep8_v2 | dRep8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STIF | formal | BM25+ | 0.132 | 0.856 | +0.724 | 0.153 | 0.658 | +0.505 | 0.771 | 0.654 | -0.118 | 208.86 | 51.37 | 14.80 | 0.80 | 0.001 | 0.000 | -0.001 |
| STIF | formal | Centroid | 0.252 | 0.724 | +0.472 | 0.259 | 0.597 | +0.338 | 0.697 | 0.566 | -0.131 | 102.58 | 30.38 | 2.80 | 0.40 | 0.000 | 0.000 | +0.000 |
| STIF | formal | Dense | 0.128 | 0.868 | +0.740 | 0.160 | 0.653 | +0.493 | 0.762 | 0.643 | -0.118 | 186.53 | 51.63 | 13.20 | 1.60 | 0.006 | 0.000 | -0.006 |
| STIF | formal | Hybrid α=0.1 | 0.192 | 0.796 | +0.604 | 0.197 | 0.621 | +0.424 | 0.695 | 0.583 | -0.111 | 142.27 | 34.51 | 6.80 | 1.20 | 0.013 | 0.000 | -0.013 |
| STIF | formal | Hybrid α=0.3 | 0.176 | 0.824 | +0.648 | 0.196 | 0.628 | +0.433 | 0.721 | 0.611 | -0.110 | 169.66 | 44.54 | 8.40 | 1.20 | 0.009 | 0.000 | -0.009 |
| STIF | formal | Hybrid α=0.5 | 0.112 | 0.816 | +0.704 | 0.150 | 0.638 | +0.488 | 0.746 | 0.633 | -0.113 | 190.80 | 48.51 | 12.40 | 1.20 | 0.002 | 0.000 | -0.002 |
| STIF | formal | Hybrid α=0.7 | 0.152 | 0.848 | +0.696 | 0.179 | 0.648 | +0.469 | 0.750 | 0.639 | -0.111 | 192.07 | 45.57 | 14.80 | 2.00 | 0.000 | 0.000 | +0.000 |
| STIF | formal | Hybrid α=0.9 | 0.120 | 0.852 | +0.732 | 0.159 | 0.646 | +0.487 | 0.758 | 0.647 | -0.111 | 197.44 | 49.38 | 12.40 | 1.60 | 0.003 | 0.000 | -0.003 |
| STIF | formal | Random-k | 0.064 | 0.900 | +0.836 | 0.094 | 0.666 | +0.572 | 0.752 | 0.621 | -0.131 | 194.13 | 44.39 | 9.60 | 0.40 | 0.004 | 0.000 | -0.004 |
| STIF | formal | Zero-shot | 0.780 | 0.872 | +0.092 | 0.612 | 0.677 | +0.065 | 0.559 | 0.630 | +0.071 | 39.82 | 51.93 | 2.80 | 2.00 | 0.000 | 0.000 | +0.000 |
| STIF | informal | BM25+ | 0.904 | 1.000 | +0.096 | 0.892 | 0.970 | +0.078 | 0.801 | 0.749 | -0.052 | 212.41 | 113.81 | 14.80 | 1.60 | 0.001 | 0.000 | -0.001 |
| STIF | informal | Centroid | 0.952 | 1.000 | +0.048 | 0.933 | 0.958 | +0.025 | 0.769 | 0.723 | -0.046 | 217.72 | 96.70 | 10.00 | 0.80 | 0.011 | 0.000 | -0.011 |
| STIF | informal | Dense | 0.952 | 0.996 | +0.044 | 0.938 | 0.973 | +0.035 | 0.786 | 0.745 | -0.041 | 222.69 | 114.60 | 16.40 | 2.80 | 0.002 | 0.000 | -0.002 |
| STIF | informal | Hybrid α=0.1 | 0.960 | 1.000 | +0.040 | 0.932 | 0.963 | +0.031 | 0.768 | 0.720 | -0.048 | 151.00 | 86.65 | 4.80 | 0.80 | 0.011 | 0.000 | -0.011 |
| STIF | informal | Hybrid α=0.3 | 0.984 | 1.000 | +0.016 | 0.961 | 0.968 | +0.007 | 0.770 | 0.728 | -0.042 | 239.69 | 101.57 | 14.80 | 2.40 | 0.008 | 0.000 | -0.008 |
| STIF | informal | Hybrid α=0.5 | 0.968 | 1.000 | +0.032 | 0.947 | 0.970 | +0.023 | 0.776 | 0.737 | -0.040 | 243.90 | 100.25 | 13.60 | 1.20 | 0.010 | 0.000 | -0.010 |
| STIF | informal | Hybrid α=0.7 | 0.936 | 1.000 | +0.064 | 0.935 | 0.973 | +0.038 | 0.778 | 0.742 | -0.036 | 257.10 | 121.07 | 14.80 | 2.80 | 0.010 | 0.000 | -0.010 |
| STIF | informal | Hybrid α=0.9 | 0.960 | 1.000 | +0.040 | 0.944 | 0.975 | +0.030 | 0.786 | 0.740 | -0.045 | 224.96 | 117.06 | 16.80 | 3.20 | 0.000 | 0.000 | +0.000 |
| STIF | informal | Random-k | 0.988 | 1.000 | +0.012 | 0.968 | 0.979 | +0.011 | 0.758 | 0.734 | -0.024 | 219.28 | 110.07 | 10.40 | 4.00 | 0.003 | 0.000 | -0.003 |
| STIF | informal | Zero-shot | 0.136 | 0.988 | +0.852 | 0.356 | 0.935 | +0.579 | 0.587 | 0.728 | +0.140 | 36.85 | 77.17 | 1.20 | 0.80 | 0.000 | 0.000 | +0.000 |
| AAKER | competence | BM25+ | 0.230 | 0.286 | +0.056 | 0.228 | 0.281 | +0.053 | 0.710 | 0.659 | -0.051 | 75.93 | 33.33 | 4.40 | 1.00 | 0.031 | 0.012 | -0.018 |
| AAKER | competence | Centroid | 0.850 | 0.852 | +0.002 | 0.818 | 0.819 | +0.001 | 0.391 | 0.496 | +0.105 | 34.41 | 31.10 | 0.20 | 0.40 | 0.188 | 0.023 | -0.165 |
| AAKER | competence | Dense | 0.162 | 0.230 | +0.068 | 0.165 | 0.231 | +0.065 | 0.716 | 0.680 | -0.036 | 83.44 | 41.74 | 10.20 | 3.60 | 0.009 | 0.000 | -0.009 |
| AAKER | competence | Hybrid α=0.1 | 0.864 | 0.876 | +0.012 | 0.834 | 0.846 | +0.011 | 0.421 | 0.487 | +0.066 | 34.71 | 29.06 | 0.60 | 0.00 | 0.339 | 0.071 | -0.267 |
| AAKER | competence | Hybrid α=0.3 | 0.842 | 0.838 | -0.004 | 0.811 | 0.807 | -0.004 | 0.497 | 0.535 | +0.037 | 48.41 | 34.03 | 0.80 | 0.40 | 0.220 | 0.060 | -0.160 |
| AAKER | competence | Hybrid α=0.5 | 0.514 | 0.542 | +0.028 | 0.498 | 0.522 | +0.024 | 0.666 | 0.639 | -0.027 | 74.10 | 39.39 | 8.00 | 2.20 | 0.055 | 0.013 | -0.041 |
| AAKER | competence | Hybrid α=0.7 | 0.244 | 0.310 | +0.066 | 0.242 | 0.303 | +0.061 | 0.714 | 0.674 | -0.039 | 73.58 | 38.48 | 10.00 | 3.60 | 0.019 | 0.003 | -0.015 |
| AAKER | competence | Hybrid α=0.9 | 0.200 | 0.238 | +0.038 | 0.199 | 0.236 | +0.037 | 0.719 | 0.680 | -0.039 | 83.71 | 44.24 | 11.40 | 3.40 | 0.009 | 0.002 | -0.007 |
| AAKER | competence | Random-k | 0.298 | 0.276 | -0.022 | 0.290 | 0.274 | -0.016 | 0.675 | 0.615 | -0.060 | 64.39 | 25.86 | 2.00 | 0.60 | 0.009 | 0.001 | -0.009 |
| AAKER | competence | Zero-shot | 0.222 | 0.180 | -0.042 | 0.223 | 0.183 | -0.040 | 0.480 | 0.631 | +0.151 | 23.88 | 33.63 | 3.40 | 1.60 | 0.000 | 0.000 | +0.000 |
| AAKER | excitement | BM25+ | 0.228 | 0.122 | -0.106 | 0.225 | 0.123 | -0.102 | 0.756 | 0.715 | -0.041 | 77.06 | 42.34 | 9.20 | 0.00 | 0.023 | 0.000 | -0.023 |
| AAKER | excitement | Centroid | 0.274 | 0.190 | -0.084 | 0.262 | 0.181 | -0.081 | 0.713 | 0.676 | -0.037 | 71.33 | 37.18 | 1.00 | 0.00 | 0.002 | 0.000 | -0.002 |
| AAKER | excitement | Dense | 0.262 | 0.100 | -0.162 | 0.260 | 0.115 | -0.145 | 0.754 | 0.713 | -0.041 | 67.72 | 38.32 | 9.80 | 2.20 | 0.025 | 0.000 | -0.025 |
| AAKER | excitement | Hybrid α=0.1 | 0.330 | 0.204 | -0.126 | 0.322 | 0.200 | -0.123 | 0.688 | 0.683 | -0.005 | 76.98 | 38.17 | 2.80 | 0.00 | 0.028 | 0.000 | -0.028 |
| AAKER | excitement | Hybrid α=0.3 | 0.340 | 0.186 | -0.154 | 0.336 | 0.188 | -0.148 | 0.719 | 0.704 | -0.014 | 86.51 | 40.39 | 6.40 | 2.00 | 0.034 | 0.000 | -0.034 |
| AAKER | excitement | Hybrid α=0.5 | 0.300 | 0.172 | -0.128 | 0.296 | 0.172 | -0.123 | 0.739 | 0.711 | -0.028 | 83.73 | 40.33 | 8.40 | 1.60 | 0.028 | 0.000 | -0.028 |
| AAKER | excitement | Hybrid α=0.7 | 0.310 | 0.128 | -0.182 | 0.303 | 0.131 | -0.172 | 0.742 | 0.716 | -0.026 | 72.87 | 42.07 | 9.60 | 2.60 | 0.037 | 0.000 | -0.036 |
| AAKER | excitement | Hybrid α=0.9 | 0.272 | 0.110 | -0.162 | 0.270 | 0.126 | -0.143 | 0.758 | 0.714 | -0.044 | 72.72 | 39.33 | 9.40 | 2.60 | 0.028 | 0.000 | -0.028 |
| AAKER | excitement | Random-k | 0.154 | 0.144 | -0.010 | 0.160 | 0.147 | -0.013 | 0.708 | 0.689 | -0.018 | 89.21 | 46.58 | 7.00 | 0.80 | 0.001 | 0.000 | -0.001 |
| AAKER | excitement | Zero-shot | 0.058 | 0.054 | -0.004 | 0.069 | 0.068 | -0.001 | 0.531 | 0.698 | +0.167 | 21.16 | 32.65 | 2.60 | 1.20 | 0.000 | 0.000 | +0.000 |
