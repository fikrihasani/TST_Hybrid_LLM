#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bandingkan akurasi gaya per target antara hasil run LAMA dan hasil sapuan alpha-dev BARU.

Tujuan: menentukan apakah akurasi gaya target formal yang rendah pada sapuan alpha-dev
(0,108 sampai 0,136) merupakan regresi yang diperkenalkan patch revisi, atau memang sifat
yang sudah ada pada run lama. Tugas ini klasifikasi biner, sehingga tebakan acak bernilai 0,5.

Read-only. Tidak menulis apa pun.
"""
import glob
import os
import sys

import pandas as pd

BUNDLE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = [
    ("formality", os.path.join(BUNDLE, "fewshot_formality")),
    ("aaker", os.path.join(BUNDLE, "fewshot_aaker")),
]


def ringkas(paths, label):
    if not paths:
        print(f"  {label}: tidak ada berkas")
        return None
    frames = []
    for p in paths:
        try:
            d = pd.read_csv(p)
        except Exception as e:
            print(f"    gagal baca {os.path.basename(p)}: {e}")
            continue
        d["__file"] = os.path.basename(p)
        frames.append(d)
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    print(f"  {label}: {len(paths)} berkas, {len(df)} baris")
    if "style_target" not in df.columns or "style_accuracy" not in df.columns:
        print(f"    kolom tidak lengkap: {list(df.columns)[:12]}")
        return None
    g = df.groupby("style_target")["style_accuracy"]
    out = g.agg(["count", "mean", "min", "max"]).round(4)
    print(out.to_string())
    # sebaran prediksi, untuk melihat apakah model menghasilkan satu gaya saja
    if "style_predicted" in df.columns:
        print("    sebaran style_predicted per target:")
        for tgt, sub in df.groupby("style_target"):
            vc = sub["style_predicted"].value_counts(dropna=False)
            items = ", ".join(f"{k}={v}" for k, v in vc.items())
            print(f"      target {tgt}: {items}")
    return df


print("=" * 78)
print("AKURASI GAYA PER TARGET: RUN LAMA vs SAPUAN ALPHA-DEV BARU")
print("=" * 78)

for tag, repo in REPOS:
    print(f"\n### {tag}  ({repo})")
    old_eval = sorted(glob.glob(os.path.join(repo, "evaluation_result", "*", "evaluated_*.csv")))
    old_eval = [p for p in old_eval if "HUMAN" not in p]
    ringkas(old_eval, "RUN LAMA (evaluation_result)")

    new_eval = sorted(glob.glob(os.path.join(repo, "evaluation_result_alphadev", "*", "evaluated_v2_*.csv")))
    if not new_eval:
        new_eval = sorted(glob.glob(os.path.join(repo, "evaluation_result_alphadev", "*", "*.csv")))
    new_eval = [p for p in new_eval if "HUMAN" not in p]
    ringkas(new_eval, "SAPUAN ALPHA-DEV (evaluation_result_alphadev)")

print("\n" + "=" * 78)
print("CATATAN: tugas biner, tebakan acak = 0,50. Nilai jauh di bawah 0,50 berarti")
print("keluaran sistematis berlawanan dengan target, bukan sekadar gagal berpindah gaya.")
print("=" * 78)
