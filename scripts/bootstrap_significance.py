#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bootstrap_significance.py
=========================
Uji signifikansi berpasangan antar metode retrieval pada sampel uji yang sama,
beserta interval keyakinan bootstrap.

Mengapa berpasangan
-------------------
Seluruh metode dijalankan pada indeks sampel uji yang identik, sehingga
perbandingannya berpasangan. Uji berpasangan lebih peka daripada uji bebas,
dan reviewer meminta perbedaan beberapa perseratus tidak lagi ditafsirkan
sebagai bermakna tanpa pengujian.

Prosedur
--------
1. Setiap berkas dibaca dan diberi kunci sampel. Kunci diambil dari
   (original_style, original_message) bila unik; bila tidak, dipakai posisi
   baris sebagai kunci dengan peringatan.
2. Hanya sampel yang muncul di kedua metode yang dibandingkan (irisan).
3. Untuk setiap pasangan metode, dihitung selisih rata-rata berpasangan,
   interval keyakinan bootstrap persentil, dan uji Wilcoxon signed-rank
   (memakai scipy bila tersedia, bila tidak memakai uji permutasi tanda).

Pemakaian
---------
    python bootstrap_significance.py --dir <folder evaluated> --metric style_accuracy
    python bootstrap_significance.py --dir <folder> --metric content_preservation \
        --baseline dense --out hasil_uji.csv
"""
import argparse
import glob
import os
import re
import sys
from itertools import combinations

import numpy as np
import pandas as pd

META = ["style_target", "retrieval_method", "alpha"]
PAIR_COLS = ["original_style", "original_message"]


def normalize(s):
    return " ".join(str(s).lower().split())


def load(path):
    df = pd.read_csv(path)
    df = df[~df["paraphrased_message"].astype(str).str.contains("ERROR")].copy()
    # kalau hasil rerun menyertakan sample_index, pakai itu sebagai kunci yang eksplisit
    if "sample_index" in df.columns:
        df["_key"] = df["sample_index"].astype(str)
        return df, None
    if all(c in df.columns for c in PAIR_COLS):
        key = df[PAIR_COLS[0]].astype(str) + " || " + df[PAIR_COLS[1]].map(normalize)
        if key.nunique() == len(df):
            df["_key"] = key
            return df, None
    df["_key"] = np.arange(len(df)).astype(str)
    return df, True


def k_dari_nama(path):
    """Jumlah contoh (k) dari nama berkas.

    Berkas hasil tidak memuat kolom k, sedangkan nama berkasnya selalu memuat k sebelum penanda seed.
    Tanpa ini, dua konfigurasi yang hanya berbeda pada k mendapat label yang sama sehingga salah
    satunya tertimpa tanpa peringatan, dan analisis kepekaan k menjadi tidak mungkin.
    """
    m = re.search(r"_(\d+)_seed\d+_", os.path.basename(path or ""))
    return m.group(1) if m else None


def label_of(df, path=None):
    m = str(df["retrieval_method"].iloc[0])
    a = str(df["alpha"].iloc[0])
    t = str(df["style_target"].iloc[0])
    k = k_dari_nama(path) if path else None
    return f"{t}|{m}" + (f"|a{a}" if a not in ("N/A", "nan") else "") + (f"|k{k}" if k else "")


def target_of(label):
    """Target gaya dari sebuah label. Dipakai menyaring pasangan lintas target."""
    return label.split("|")[0]


def paired_bootstrap(diff, n_boot=10000, seed=42, alpha=0.05):
    diff = np.asarray(diff, dtype=float)
    n = len(diff)
    if n < 3:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    means = diff[idx].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(diff.mean()), float(lo), float(hi)


def sign_flip_test(diff, n_perm=10000, seed=42):
    """Uji permutasi tanda, pengganti Wilcoxon bila scipy tidak tersedia."""
    diff = np.asarray(diff, dtype=float)
    diff = diff[np.isfinite(diff)]
    n = len(diff)
    if n < 3:
        return float("nan")
    obs = abs(diff.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_perm, n))
    perm = np.abs((signs * diff).mean(axis=1))
    return float((perm >= obs).mean())


def wilcoxon(diff):
    try:
        from scipy.stats import wilcoxon as _w
    except ImportError:
        return None
    d = np.asarray(diff, dtype=float)
    d = d[np.isfinite(d)]
    if len(d) < 3 or np.allclose(d, 0):
        return None
    try:
        return float(_w(d, zero_method="wilcox").pvalue)
    except Exception:
        return None


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
    ap.add_argument("--dir", required=True)
    ap.add_argument("--metric", default="style_accuracy",
                    help="kolom yang diuji, mis. style_accuracy, content_preservation, "
                         "style_strength_calibrated, replication_rate_8")
    ap.add_argument("--baseline", default=None,
                    help="bila diisi, hanya membandingkan setiap metode terhadap baseline ini")
    ap.add_argument("--out", default=None)
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42,
                    help="seed acak untuk bootstrap, bukan penanda seed berkas")
    ap.add_argument("--only-seed", type=int, default=None,
                    help="hanya pakai berkas dengan penanda _seed<N>_, sehingga statistik tidak "
                         "mencampur seed. Bila tidak diisi dan ditemukan lebih dari satu seed, "
                         "skrip ini memberi peringatan")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, "evaluated_*.csv")))
    files = saring_seed(files, args.only_seed)
    if not files:
        sys.exit(f"tidak ada evaluated_*.csv di {args.dir}")

    store, warns, store_nama = {}, [], {}
    for f in files:
        df, warn = load(f)
        if warn:
            warns.append(os.path.basename(f))
        if args.metric not in df.columns:
            print(f"lewat: {os.path.basename(f)} tidak punya kolom {args.metric}")
            continue
        lbl = label_of(df, f)
        if lbl in store:
            print(f"PERINGATAN: label {lbl} muncul lebih dari sekali ({store_nama[lbl]} dan "
                  f"{os.path.basename(f)}). Berkas kedua dilewati agar tidak tertimpa diam-diam.")
            continue
        store_nama[lbl] = os.path.basename(f)
        store[lbl] = df[["_key", args.metric]].rename(columns={args.metric: "v"})

    if warns:
        print(f"catatan: pada {len(warns)} berkas kunci teks tidak unik, sehingga dipakai posisi "
              f"baris sebagai kunci. Ini sah bila seluruh metode dijalankan pada urutan sampel "
              f"yang sama. Periksa kolom sample_index pada hasil rerun untuk memastikannya.")
        # pastikan urutan sampel memang seragam per target
        by_target = {}
        for f in files:
            df = pd.read_csv(f)
            by_target.setdefault(str(df["style_target"].iloc[0]), []).append(
                (os.path.basename(f), len(df)))
        inconsistent = {t: v for t, v in by_target.items() if len({n for _, n in v}) > 1}
        if inconsistent:
            print("  PERINGATAN: jumlah baris berbeda antar metode pada target yang sama:")
            for t, v in inconsistent.items():
                print(f"    {t}: {sorted({n for _, n in v})}")
        else:
            print("  jumlah baris seragam per target, sehingga pemasangan posisional sah.")
    if len(store) < 2:
        sys.exit("butuh minimal dua konfigurasi dengan kolom metrik yang diminta")

    rows = []
    dilewati_lintas = 0
    for a, b in combinations(sorted(store), 2):
        if target_of(a) != target_of(b):
            dilewati_lintas += 1
            continue
        if args.baseline:
            if args.baseline not in a and args.baseline not in b:
                continue
            if args.baseline not in a:
                a, b = b, a
        da, db = store[a], store[b]
        m = da.merge(db, on="_key", suffixes=("_a", "_b"))
        if len(m) < 3:
            continue
        diff = m["v_a"].astype(float).values - m["v_b"].astype(float).values
        diff = diff[np.isfinite(diff)]
        if len(diff) < 3:
            continue
        mean_d, lo, hi = paired_bootstrap(diff, args.n_boot, args.seed)
        rows.append({
            "metrik": args.metric,
            "konfigurasi_a": a,
            "konfigurasi_b": b,
            "n_pasangan": len(diff),
            "selisih_mean": round(mean_d, 5),
            "ci95_bawah": round(lo, 5),
            "ci95_atas": round(hi, 5),
            "bermakna_95": bool(lo > 0 or hi < 0),
            "p_wilcoxon": (lambda p: None if p is None else round(p, 5))(wilcoxon(diff)),
            "p_permutasi_tanda": round(sign_flip_test(diff, args.n_boot, args.seed), 5),
        })

    if not rows:
        sys.exit("tidak ada pasangan yang dapat dibandingkan")
    out = pd.DataFrame(rows).sort_values(["konfigurasi_a", "konfigurasi_b"]).reset_index(drop=True)
    pd.set_option("display.width", 250)
    print(f"\nMetrik: {args.metric} | konfigurasi: {len(store)} | pasangan sebanding: {len(out)}")
    if dilewati_lintas:
        print(f"{dilewati_lintas} pasangan lintas target dilewati, karena membandingkan dua target "
              f"gaya yang berbeda tidak bermakna")
    print()
    print(out.to_string(index=False))
    print("\nCatatan: 'bermakna_95' berarti interval keyakinan 95% selisih berpasangan "
          "tidak memuat nol. Bila kolom p_wilcoxon kosong, scipy tidak terpasang dan "
          "dipakai uji permutasi tanda.")
    if args.out:
        out.to_csv(args.out, index=False)
        print(f"Hasil disimpan: {args.out}")


if __name__ == "__main__":
    main()
