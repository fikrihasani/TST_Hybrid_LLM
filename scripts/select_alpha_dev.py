#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
select_alpha_dev.py
===================
Memilih nilai alpha untuk hybrid early fusion pada DEVELOPMENT SET, bukan pada
test set.

Mengapa
-------
Sebelumnya kelima nilai alpha dijalankan pada test set yang sama, lalu yang
"optimal" dipilih dari hasil test set itu. Reviewer 1 meminta pemilihan alpha
berbasis development set. Script ini adalah pemilih, bukan penghasil: ia membaca
hasil evaluasi pada alpha_dev lalu menerapkan kriteria yang sudah ditetapkan.

Kriteria
--------
Kriteria harus ditetapkan lebih dulu dan ditulis di naskah. Kriteria bawaan
adalah rata-rata harmonik antara akurasi gaya biner dan content preservation:

    H = 2 * acc * cp / (acc + cp)

Alasan pemilihan: paper ini tentang trade-off antara gaya dan konten, sehingga
kriteria yang menghukum ketimpangan lebih sesuai daripada rata-rata aritmetik
yang membolehkan satu sisi menutupi sisi lain. Rata-rata harmonik juga dipakai
untuk menegaskan bahwa keduanya diperlukan, bukan salah satu saja.

Pemakaian
---------
    python select_alpha_dev.py --dir <folder evaluated alpha_dev> \
        --accuracy-col style_accuracy --content-col content_preservation \
        --out alpha_star.json

Dengan kriteria lain:
    python select_alpha_dev.py --dir <folder> --criterion content \
        --min-accuracy 0.5 --out alpha_star.json
    # maksimalkan content preservation dengan syarat akurasi gaya minimal 0.5
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

META = ["style_target", "retrieval_method", "alpha"]


def harmonic(acc, cp):
    if not np.isfinite(acc) or not np.isfinite(cp) or (acc + cp) <= 0:
        return float("nan")
    return 2 * acc * cp / (acc + cp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="folder evaluated_*.csv pada alpha_dev")
    ap.add_argument("--accuracy-col", default="style_accuracy")
    ap.add_argument("--content-col", default="content_preservation")
    ap.add_argument("--criterion", default="harmonic",
                    choices=["harmonic", "accuracy", "content", "accuracy_min_content"])
    ap.add_argument("--min-accuracy", type=float, default=0.5,
                    help="ambang akurasi untuk kriteria accuracy_min_content")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, "evaluated_*.csv")))
    files = [f for f in files if "hybrid_early" in os.path.basename(f)]
    if not files:
        sys.exit(f"tidak ada berkas hybrid_early di {args.dir}")

    rows = []
    for f in files:
        df = pd.read_csv(f)
        if args.accuracy_col not in df.columns or args.content_col not in df.columns:
            print(f"lewat: {os.path.basename(f)} tidak punya kolom yang diminta")
            continue
        acc = float(pd.to_numeric(df[args.accuracy_col], errors="coerce").mean())
        cp = float(pd.to_numeric(df[args.content_col], errors="coerce").mean())
        rows.append({
            "file": os.path.basename(f),
            "style_target": str(df["style_target"].iloc[0]),
            "alpha": float(df["alpha"].iloc[0]),
            "n": len(df),
            "accuracy": round(acc, 5),
            "content_preservation": round(cp, 5),
            "harmonic": round(harmonic(acc, cp), 5),
        })
    if not rows:
        sys.exit("tidak ada berkas yang dapat diproses")

    df = pd.DataFrame(rows).sort_values(["style_target", "alpha"]).reset_index(drop=True)
    pd.set_option("display.width", 200)
    print(f"\nSapuan alpha pada development set (kriteria: {args.criterion})\n")
    print(df.to_string(index=False))

    picks = {}
    for target, sub in df.groupby("style_target"):
        if args.criterion == "harmonic":
            best = sub.loc[sub["harmonic"].idxmax()]
        elif args.criterion == "accuracy":
            best = sub.loc[sub["accuracy"].idxmax()]
        elif args.criterion == "content":
            best = sub.loc[sub["content_preservation"].idxmax()]
        else:
            ok = sub[sub["accuracy"] >= args.min_accuracy]
            if ok.empty:
                print(f"\nPERINGATAN: target {target} tidak punya alpha dengan akurasi >= "
                      f"{args.min_accuracy}; alpha tidak dipilih")
                continue
            best = ok.loc[ok["content_preservation"].idxmax()]
        picks[target] = {"alpha": float(best["alpha"]),
                         "accuracy": float(best["accuracy"]),
                         "content_preservation": float(best["content_preservation"]),
                         "harmonic": float(best["harmonic"])}
        print(f"  alpha* untuk target {target}: {best['alpha']} "
              f"(akurasi {best['accuracy']:.4f}, konten {best['content_preservation']:.4f}, "
              f"H {best['harmonic']:.4f})")

    payload = {
        "criterion": args.criterion,
        "min_accuracy": args.min_accuracy if args.criterion == "accuracy_min_content" else None,
        "accuracy_column": args.accuracy_col,
        "content_column": args.content_col,
        "source_dir": os.path.abspath(args.dir),
        "n_files": len(df),
        "picks": picks,
        "sweep": df.to_dict(orient="records"),
    }
    out = args.out or os.path.join(args.dir, "alpha_star.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nDisimpan: {out}")
    print("Laporkan kurva sapuan lengkap di naskah, bukan hanya alpha terpilih.")


if __name__ == "__main__":
    main()
