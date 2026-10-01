#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""k_sensitivity.py
=================
Kepekaan jumlah contoh (k) untuk korpus yang menjalankan lebih dari satu nilai k.

Berkas hasil tidak memuat kolom k, sehingga perbandingan k=5 melawan k=10 hanya mungkin setelah
label konfigurasi memuat k (lihat bootstrap_significance.py versi baru). Skrip ini membaca tabel
uji keluaran bootstrap_significance.py dan menyaring pasangan yang HANYA berbeda pada k, lalu
menyusunnya sebagai tabel siap pakai untuk R2-12 dan R3-W2.

Selisih selalu disajikan sebagai k_besar - k_kecil (mis. k10 - k5), apa pun urutan label pada
berkas tabel uji.

Pemakaian:
    python k_sensitivity.py --dir <folder berisi TABEL_uji_*.csv> --corpus formality \
        --out TABEL_kepekaan_k_formality.csv
"""
from __future__ import annotations

import argparse
import glob
import os
import re

import pandas as pd

KRE = re.compile(r"\|k(\d+)$")
METRICS = [
    "style_accuracy",
    "style_strength_calibrated",
    "content_preservation",
    "content_preservation_LaBSE",
    "replication_rate_8",
]


def strip_k(label: str) -> str:
    return KRE.sub("", label)


def k_of(label: str):
    m = KRE.search(label)
    return int(m.group(1)) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="folder berisi TABEL_uji_<corpus>_<metrik>.csv")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--metrics", nargs="*", default=METRICS)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rows = []
    for metric in args.metrics:
        path = os.path.join(args.dir, f"TABEL_uji_{args.corpus}_{metric}.csv")
        if not os.path.exists(path):
            print(f"lewat (tidak ada): {path}")
            continue
        d = pd.read_csv(path)
        n_metric = 0
        for _, r in d.iterrows():
            a, b = r["konfigurasi_a"], r["konfigurasi_b"]
            ka, kb = k_of(a), k_of(b)
            if ka is None or kb is None or ka == kb:
                continue
            if strip_k(a) != strip_k(b):
                continue
            # mau besar - kecil
            big, small = (ka, kb) if ka > kb else (kb, ka)
            if ka == big:
                dmean, lo, hi = r["selisih_mean"], r["ci95_bawah"], r["ci95_atas"]
            else:
                dmean, lo, hi = -r["selisih_mean"], -r["ci95_atas"], -r["ci95_bawah"]
            rows.append({
                "metrik": metric,
                "target_dan_metode": strip_k(a),
                "k_besar": big,
                "k_kecil": small,
                "selisih_kbesar_kurang_kkecil": round(float(dmean), 5),
                "ci95_bawah": round(float(lo), 5),
                "ci95_atas": round(float(hi), 5),
                "bermakna_95": bool(lo > 0 or hi < 0),
                "n_pasangan": int(r["n_pasangan"]),
            })
            n_metric += 1
        print(f"{metric}: {n_metric} pasangan k")

    if not rows:
        print("tidak ada pasangan yang hanya berbeda pada k")
        return 1
    out = pd.DataFrame(rows).sort_values(["metrik", "target_dan_metode"]).reset_index(drop=True)
    pd.set_option("display.width", 250)
    print()
    print(out.to_string(index=False))
    if args.out:
        out.to_csv(args.out, index=False)
        print(f"\nHasil disimpan: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
