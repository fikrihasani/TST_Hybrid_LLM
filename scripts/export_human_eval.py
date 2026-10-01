#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""export_human_eval.py
=====================
Langkah 10 protokol: ekspor sampel untuk evaluasi manusia.

Tidak menjalankan penilaian apa pun; hanya mengekspor berkas sampel. Ambil 25 sampel dengan
sample_index terkecil dari empat metode utama (dense, centroid, bm25, hybrid_early), untuk satu
target per korpus. Himpunan sample_index dipatok dari berkas pertama yang lolos penyaring, lalu
dipakai sama untuk seluruh berkas berikutnya, supaya penilaian dapat dibandingkan lintas metode.

Keluaran: EVAL_MANUSIA_formality.csv dan EVAL_MANUSIA_aaker.csv di akar bundel.

Pemakaian:
    python export_human_eval.py
"""
from __future__ import annotations

import glob
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METODE_UTAMA = ("dense", "centroid", "bm25", "hybrid_early")


def ekspor(repo_tag: str, target: str) -> str | None:
    src = glob.glob(
        os.path.join(ROOT, f"fewshot_{repo_tag}", "model_results_dir", "google_gemma-3-4b-it",
                     f"*{target}*_seed42*_results.csv")
    )
    picks, keys = {}, None
    for f in sorted(src):
        name = os.path.basename(f)
        if not any(m in name for m in METODE_UTAMA):
            continue
        d = pd.read_csv(f)
        if "sample_index" not in d.columns:
            continue
        idx = sorted(d["sample_index"].unique())[:25]
        if keys is None:
            keys = set(idx)
        idx = sorted(keys)
        picks[name] = d[d["sample_index"].isin(idx)][
            ["sample_index", "original_message", "paraphrased_message"]]
    out = []
    for name, d in picks.items():
        out.append(d.assign(method_file=name))
    if not out:
        print(f"tidak ada berkas yang cocok untuk {repo_tag}/{target}")
        return None
    df = pd.concat(out, ignore_index=True)
    p = os.path.join(ROOT, f"EVAL_MANUSIA_{repo_tag}.csv")
    df.to_csv(p, index=False)
    print(f"ditulis {p}: {len(df)} baris, {df['sample_index'].nunique()} kalimat sumber, "
          f"{df['method_file'].nunique()} berkas metode")
    return p


def main() -> int:
    for repo_tag, target in [("formality", "informal"), ("aaker", "competence")]:
        ekspor(repo_tag, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
