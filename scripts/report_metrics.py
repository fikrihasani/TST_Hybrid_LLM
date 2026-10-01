#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
report_metrics.py
=================
Menghitung statistik ringkas dari berkas evaluasi per sampel
(`evaluated_*.csv`) dan menulis tabel siap pakai untuk manuskrip.

Mengapa bukan mean saja
-----------------------
Pelaporan mean saja membuat kolom fluency tidak terbaca: pada korpus Aaker
sebagian output memiliki PPL sekitar 6,9 x 10^10, sehingga mean satu
konfigurasi mencapai 276.051.597 sedangkan mediannya 75,55. Script ini
melaporkan median, trimmed mean, dan proporsi output degenerate berdampingan.

Kolom yang dikenali
-------------------
Berkas hasil evaluasi memuat kolom berikut (nama lama dan nama baru):
    style_strength              probabilitas kelas target (mentah)
    style_strength_calibrated   probabilitas setelah temperature scaling (baru)
    style_accuracy              benar atau tidaknya prediksi kelas target
    content_preservation        cosine similarity encoder lama
    content_preservation_<tag>   encoder independen tambahan (baru)
    fluency_ppl                 perplexity per sampel
    replication_rate_8          overlap n-gram dengan eksemplar (baru)

Nama kolom yang tidak ada akan dilewati dengan pesan, sehingga script ini juga
dapat dipakai untuk membedah hasil lama sebelum rerun.

Pemakaian
---------
    python report_metrics.py --dir ../fewshot_formality/evaluation_result/google_gemma-3-4b-it
    python report_metrics.py --dir <folder> --csv out.csv --degenerate-threshold 1000
"""
import argparse
import glob
import os
import re
import sys
from collections import OrderedDict

import numpy as np
import pandas as pd

META = ["style_target", "retrieval_method", "alpha"]
DEGENERATE_DEFAULT = 1000.0


def trimmed_mean(x, proportion=0.10):
    x = np.asarray([v for v in x if np.isfinite(v)], dtype=float)
    if x.size == 0:
        return float("nan")
    if x.size < 10:
        return float(x.mean())
    k = int(np.floor(x.size * proportion))
    if k == 0:
        return float(x.mean())
    return float(np.sort(x)[k:-k].mean())


def summarise_series(x, threshold=None):
    x = pd.to_numeric(x, errors="coerce")
    finite = x[np.isfinite(x)]
    out = OrderedDict()
    out["n"] = int(len(x))
    out["n_valid"] = int(len(finite))
    if len(finite) == 0:
        for k in ["mean", "median", "trimmed10", "min", "max", "sd"]:
            out[k] = float("nan")
        return out
    out["mean"] = float(finite.mean())
    out["median"] = float(finite.median())
    out["trimmed10"] = trimmed_mean(finite, 0.10)
    out["min"] = float(finite.min())
    out["max"] = float(finite.max())
    out["sd"] = float(finite.std(ddof=1)) if len(finite) > 1 else 0.0
    if threshold is not None:
        n_bad = int((finite > threshold).sum())
        out["n_degenerate"] = n_bad
        out["pct_degenerate"] = round(100 * n_bad / len(finite), 3)
    return out


def evaluate_file(path, threshold):
    df = pd.read_csv(path)
    row = OrderedDict()
    row["file"] = os.path.basename(path)
    for c in META:
        row[c] = df[c].iloc[0] if c in df.columns else "N/A"

    n_style = len(df)
    for col in ["style_strength", "style_strength_calibrated", "style_accuracy",
                "content_preservation", "fluency_ppl", "replication_rate_8"]:
        if col not in df.columns:
            continue
        thr = threshold if col == "fluency_ppl" else None
        for k, v in summarise_series(df[col], thr).items():
            row[f"{col}__{k}"] = v

    for col in [c for c in df.columns if c.startswith("content_preservation_")]:
        for k, v in summarise_series(df[col]).items():
            row[f"{col}__{k}"] = v

    if "paraphrased_message" in df.columns:
        err = int(df["paraphrased_message"].astype(str).str.contains("ERROR").sum())
        row["n_output_error"] = err
        row["pct_output_error"] = round(100 * err / max(n_style, 1), 3)
    if "eos_reached" in df.columns:
        row["pct_eos_reached"] = round(100 * float(df["eos_reached"].astype(bool).mean()), 2)
    if "retrieval_fallback" in df.columns:
        row["n_retrieval_fallback"] = int(df["retrieval_fallback"].astype(bool).sum())
    return row


SEED_RE = re.compile(r"_seed(\d+)_")


def saring_seed(files, only_seed):
    """Batasi berkas ke satu seed saja.

    Nama berkas hasil memuat penanda _seed<N>_ sehingga seed dapat dipisahkan dari nama. Tanpa
    penyaring ini, statistik mencampur beberapa seed tanpa peringatan.
    """
    seeds = set()
    for f in files:
        seeds.update(SEED_RE.findall(os.path.basename(f)))
    if only_seed is not None:
        dipilih = [f for f in files if f"_seed{only_seed}_" in os.path.basename(f)]
        if not dipilih:
            sys.exit(f"tidak ada berkas dengan penanda _seed{only_seed}_ di antara {len(files)} "
                     f"berkas. Seed yang ditemukan: {sorted(seeds) if seeds else 'tidak ada'}")
        return dipilih
    if len(seeds) > 1:
        print(f"PERHATIAN: berkas yang dipilih memuat {len(seeds)} seed berbeda "
              f"({', '.join(sorted(seeds))}), sehingga statistik di bawah mencampur seed. "
              f"Pakai --only-seed <N> untuk memilih satu seed.")
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="folder berisi evaluated_*.csv")
    ap.add_argument("--out", default=None, help="berkas CSV ringkasan keluaran")
    ap.add_argument("--degenerate-threshold", type=float, default=DEGENERATE_DEFAULT,
                    help=f"ambang PPL untuk output degenerate (default {DEGENERATE_DEFAULT:g})")
    ap.add_argument("--pattern", default="evaluated_*.csv",
                    help="pola berkas (default evaluated_*.csv)")
    ap.add_argument("--only-seed", type=int, default=None,
                    help="hanya pakai berkas dengan penanda _seed<N>_, sehingga statistik tidak "
                         "mencampur seed. Bila tidak diisi dan ditemukan lebih dari satu seed, "
                         "skrip ini memberi peringatan")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, args.pattern)))
    files = [f for f in files if not os.path.basename(f).endswith("_HUMAN_EVAL.csv")]
    files = saring_seed(files, args.only_seed)
    if not files:
        sys.exit(f"tidak ada berkas cocok '{args.pattern}' di {args.dir}")

    rows = [evaluate_file(f, args.degenerate_threshold) for f in files]
    df = pd.DataFrame(rows)
    sort_cols = [c for c in META if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 80)
    pd.set_option("display.float_format", lambda v: f"{v:,.4f}")

    keep = ["file"] + [c for c in META if c in df.columns] + [
        "style_strength__median", "style_strength__mean",
        "style_strength_calibrated__median",
        "style_accuracy__mean",
        "content_preservation__mean", "content_preservation__median",
        "fluency_ppl__median", "fluency_ppl__trimmed10", "fluency_ppl__mean",
        "fluency_ppl__pct_degenerate",
        "replication_rate_8__mean",
    ]
    keep = [c for c in keep if c in df.columns]
    print(f"\n{len(files)} berkas dari {args.dir}\n")
    print(df[keep].to_string(index=False))

    print(f"\nRingkasan degenerasi (ambang {args.degenerate_threshold:g}):")
    for col in [c for c in df.columns if c.endswith("__pct_degenerate")]:
        base = col.replace("__pct_degenerate", "")
        tot_n = int(df[f"{base}__n_valid"].sum()) if f"{base}__n_valid" in df else 0
        tot_bad = int(df[f"{base}__n_degenerate"].sum()) if f"{base}__n_degenerate" in df else 0
        if tot_n:
            print(f"  {base}: {tot_bad} dari {tot_n} ({100 * tot_bad / tot_n:.2f}%)")
    for col in [c for c in df.columns if c.startswith("n_retrieval_fallback")]:
        print(f"  jumlah sampel yang jatuh ke retrieve_random: {int(df[col].sum())}")

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"\nTabel lengkap disimpan: {args.out}")


if __name__ == "__main__":
    main()
