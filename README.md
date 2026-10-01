# Hybrid Semantic and Stylistic Embedding Retrieval Strategies for Indonesian Text Style Transfer

Code, data splits, and results for the manuscript *Hybrid Semantic and Stylistic Embedding Retrieval
Strategies for Indonesian Text Style Transfer using a Large Language Model* (Journal of Computational and
Cognitive Engineering). This repository lets a reader inspect every number reported in the paper and rebuild it
from the locked data splits.

## Layout

| Path | Contents |
|---|---|
| `fewshot_formality/` | few-shot pipeline for the formality corpus: generation script, retrieval utilities, prompt template, configuration, and the corpus splits |
| `fewshot_aaker/` | the same pipeline for the brand personality corpus |
| `classifier_formality/` | training script and splits for the two-class formality style classifier |
| `classifier_brand/` | training script and splits for the five-class brand personality classifier |
| `scripts/` | shared tools: split construction and verification, calibration, alpha selection, evaluation, significance tests, metric reporting, human-evaluation export |
| `results/` | every computed result: per-sample outputs, test tables, raw generations, human-evaluation sample, calibration files. See `results/README.md` |
| `docs/` | split protocol and leakage checks for both corpora |
| `requirements.txt` | dependencies, with minimum versions |

## Environment

- Python 3.14 with CUDA 12.6. The reported experiments ran with torch 2.11.0+cu126, transformers 5.8.0,
  sentence-transformers 5.4.1, accelerate 1.13.0, bitsandbytes 0.49.2, numpy 2.4.4, pandas 3.0.2,
  scikit-learn 1.8.0, and scipy 1.17.1.
- **One GPU with at least 12 GB of VRAM.** The generation model (`google/gemma-3-4b-it`) and the perplexity
  model (`Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct`) are both loaded in 4-bit nf4. The reported runs used
  a single NVIDIA RTX 4070 Ti with 12 GB; a smaller card will not fit the pipeline.
- Install with `pip install -r requirements.txt`, and install the CUDA build of torch for your machine from
  https://pytorch.org/get-started/locally/ if the default one does not match your driver.
- The gated models need a Hugging Face token. Export it once and the scripts pick it up:
  `export HF_TOKEN=hf_...` (PowerShell: `$env:HF_TOKEN="hf_..."`). No token is stored in any file in this
  repository.
- Check the environment before the first long run: `python scripts/preflight.py`

## Data and locked splits

Both corpora are public, and this repository ships the exact splits used in the paper.

| Corpus | Source | Splits |
|---|---|---|
| Formality (STIF-Indonesia) | `fewshot_formality/data/stif_formal.txt`, `stif_informal.txt` | `fewshot_formality/data/formality_splits_v2/` |
| Brand personality (ID-Aaker) | `fewshot_aaker/data/Combined Aaker Brand Personality - Cleaned *.csv` | `fewshot_aaker/data/brand_splits_v2/` |

Each split directory holds `train_set.csv`, `val_set.csv`, `test_set.csv`, `retrieval_pool.csv`, and a
`split_manifest.json` recording sizes and hashes. The brand personality split also provides `alpha_dev.csv`, the
development set reserved for choosing the hybrid weight. The construction rules, the conversation-level
grouping that prevents leakage, and the deduplication are documented in `docs/PROTOKOL_SPLIT_JCCE-10619.md`
(written in Indonesian).

## Reproducing the results

Run the shared scripts from the repository root. The two pipeline modules resolve their configuration and their
`data/` directory relative to their own folder, so run those from inside the module folder.

**1. Rebuild and verify the splits**

```bash
python scripts/make_splits_formality.py --check     # dry run, prints the sizes
python scripts/make_splits_formality.py
python scripts/make_splits_brand.py --check
python scripts/make_splits_brand.py --alpha-dev
python scripts/verify_splits.py --dir fewshot_aaker/data/brand_splits_v2 \
    --style-col personality --group-col conversation_id_str --gate
```

`--gate` exits non-zero if any test item shares a conversation or an author with the training pool.

**2. Train and calibrate the style classifiers**

```bash
cd classifier_formality && python main.py && cd ..
cd classifier_brand     && python main.py && cd ..

python scripts/calibrate_classifier.py \
    --classifier classifier_formality/model_results_dir/formality_model_roberta \
    --val classifier_formality/data/formality_splits_v2/val_set.csv \
    --style-col formality --text-col text
```

Training writes the checkpoint and a test-set classification report; calibration fits temperature scaling on
the validation split and writes `calibration.json` beside the checkpoint. The paper reads style strength on
that calibrated scale.

**3. Choose the hybrid semantic weight on the development set**

```bash
python scripts/select_alpha_dev.py \
    --dir results/per_sample/brand_personality \
    --accuracy-col style_accuracy --content-col content_preservation_LaBSE \
    --out fewshot_aaker/alpha_star.json
```

**4. Generate the transferred texts**

```bash
cd fewshot_formality && python fewshot_formality.py && cd ..
cd fewshot_aaker     && python main.py            && cd ..
```

Both modules read their `fewshot_config.json`: the model id, the retrieval methods, the exemplar counts `k`,
the seeds, and the 25-item human-evaluation sample. Generation writes one CSV per configuration into
`<module>/model_results_dir/google_gemma-3-4b-it/`.

**5. Evaluate every configuration**

```bash
python scripts/evaluate_results.py \
    --results      fewshot_formality/model_results_dir/google_gemma-3-4b-it \
    --classifier   fewshot_formality/style_classifier \
    --out          fewshot_formality/evaluation_result_v2/google_gemma-3-4b-it \
    --encoder      LaBSE=sentence-transformers/LaBSE \
    --legacy-encoder LazarusNLP/simcse-indobert-base \
    --calibration  fewshot_formality/style_classifier/calibration.json
```

This step produces the per-sample files: calibrated style strength and style accuracy from the classifier,
content preservation from LaBSE, perplexity from the fluency model, the eight-gram replication rate against the
retrieved exemplars, and the degenerate-output flag. The files in `results/per_sample/` are the output of this
step.

**6. Significance tests, tables, and summaries**

```bash
python scripts/bootstrap_significance.py --dir results/per_sample/formality --metric style_accuracy \
    --out results/tables/formality/TABEL_uji_formality_style_accuracy.csv
python scripts/ppl_per_target.py --dir results/per_sample/formality
python scripts/replication_metric.py --dir results/per_sample/formality --from-column
python scripts/report_metrics.py --dir results/per_sample/formality --csv hasil_ringkas.csv
```

`bootstrap_significance.py` runs the paired bootstrap confidence intervals together with the Wilcoxon and
sign-flip tests reported in the paper; run it once per metric (`style_accuracy`,
`style_strength_calibrated`, `content_preservation_LaBSE`, `replication_rate_8`) and once per corpus.

**7. Export the human-evaluation sample**

```bash
python scripts/export_human_eval.py
```

This writes the rating files: 25 shared sample indices per target, across every configuration, with the three
dimensions to be rated (style, content, fluency).

## Results

`results/` collects the artifacts the manuscript reports, organized so that each number can be traced to the
configuration that produced it: per-sample outputs for all 29 configurations, the summary and significance
tables, the raw generations, the human-evaluation sample, the error-analysis sample, and the calibration files.
`results/README.md` lists each folder and documents the column names.

## What is not included

The four fine-tuned classifier checkpoints (`model.safetensors`, about 475 MB each, roughly 1.9 GB in total)
are not committed because of their size. The training scripts, the locked splits, and the tokenizer and
configuration files they need are all here, so the checkpoints can be rebuilt with step 2 above. Everything
else needed to inspect and to reproduce the reported results is included.

## Notes for reproduction

- Every configuration is identified by its retrieval method, the exemplar count `k`, and, for the hybrid
  method, the semantic weight `alpha`: for example `STIF_formal_fewshot_hybrid_early_alpha0.5_10_seed42`.
- The generation seed is 42. It fixes the partition, the exemplar sampling, and the human-evaluation sample,
  while sampling at temperature 0.7 still varies the generated text itself.
- Content preservation is reported with LaBSE only. The `content_preservation` column without a suffix in the
  per-sample files is the earlier encoder, kept for comparison, and it is not a reported result.
