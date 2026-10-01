#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
replication_metric.py
=====================
Menghitung laju replikasi templat: seberapa besar output generasi menyalin
eksemplar yang benar-benar diambil untuk sampel tersebut.

Mengapa metrik ini ada
----------------------
Reviewer 2 (butir 3 dan 9) menduga skor gaya tinggi pada metode centroid
berasal dari penyalinan eksemplar, bukan dari transfer gaya. Dugaan itu benar
pada korpus brand personality: pool memuat satu teks Telkom yang terulang 414
kali, sehingga centroid tertarik ke boilerplate itu, dan LLM menyalinnya.
Angka dari hasil lama: 76,6% output metode centroid memuat 8-gram eksemplar,
dibandingkan 0,4% pada metode dense.

Dua sumber eksemplar
--------------------
1. `--from-column` (hasil rerun): kolom `retrieved_exemplars` pada berkas
   evaluated_*.csv, berisi daftar JSON eksemplar per sampel. Ini yang benar
   karena memakai eksemplar yang benar-benar diambil.
2. `--from-cache` (hasil lama): mencocokkan ulang eksemplar teratas dari cache
   embedding pool. Hanya sah untuk metode centroid dan hybrid, karena keduanya
   memakai centroid yang tidak bergantung query. Untuk metode dense dan bm25,
   eksemplar tidak dapat direkonstruksi dari cache, sehingga dilaporkan sebagai
   tidak tersedia.

Pemakaian
---------
    python replication_metric.py --dir <folder evaluated> --from-column
    python replication_metric.py --dir ../fewshot_aaker/evaluation_result/google_gemma-3-4b-it \
        --from-cache --cache ../fewshot_aaker/outputs/cache --k 5 --out replikasi_lama.csv
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import OrderedDict

import numpy as np
import pandas as pd

META = ["style_target", "retrieval_method", "alpha"]


def ngrams(text, n):
    words = re.findall(r"\w+", str(text).lower())
    return set(tuple(words[i:i + n]) for i in range(max(0, len(words) - n + 1)))


def overlap_ratio(output, exemplars, n):
    og = ngrams(output, n)
    if not og:
        return float("nan")
    eg = set()
    for e in exemplars:
        eg |= ngrams(e, n)
    if not eg:
        return 0.0
    return len(og & eg) / len(og)


def exemplars_from_column(df):
    """Kembalikan daftar eksemplar per baris dari kolom retrieved_exemplars."""
    out = []
    for v in df["retrieved_exemplars"]:
        try:
            got = json.loads(v) if isinstance(v, str) else v
            if isinstance(got, dict):
                got = got.get("examples", [])
            out.append(list(got) if got else [])
        except Exception:
            out.append([])
    return out


def centroid_exemplars(cache_dir, tag, k):
    emb_path = os.path.join(cache_dir, f"embeddings_{tag}_pool.npy")
    txt_path = os.path.join(cache_dir, f"texts_{tag}_pool.json")
    if not (os.path.exists(emb_path) and os.path.exists(txt_path)):
        return None
    emb = np.load(emb_path).astype(np.float32)
    texts = json.load(open(txt_path, encoding="utf-8"))
    c = emb.mean(axis=0, keepdims=True)
    e = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)
    cn = c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-12)
    sims = (e @ cn.T).ravel()
    top = np.argsort(sims)[-k:][::-1]
    return [texts[i] for i in top]


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
    ap.add_argument("--n", type=int, default=8, help="ukuran n-gram (default 8)")
    ap.add_argument("--from-column", action="store_true",
                    help="pakai kolom retrieved_exemplars (hasil rerun)")
    ap.add_argument("--from-cache", action="store_true",
                    help="rekonstruksi eksemplar centroid dari cache (hasil lama)")
    ap.add_argument("--cache", default=None, help="folder outputs/cache")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only-seed", type=int, default=None,
                    help="hanya pakai berkas dengan penanda _seed<N>_, sehingga statistik tidak "
                         "mencampur seed. Bila tidak diisi dan ditemukan lebih dari satu seed, "
                         "skrip ini memberi peringatan")
    args = ap.parse_args()

    if not (args.from_column or args.from_cache):
        sys.exit("pilih --from-column atau --from-cache")

    files = sorted(glob.glob(os.path.join(args.dir, "evaluated_*.csv")))
    files = saring_seed(files, args.only_seed)
    if not files:
        sys.exit(f"tidak ada evaluated_*.csv di {args.dir}")

    rows = []
    cache_pool = {}
    for f in files:
        df = pd.read_csv(f)
        target = str(df["style_target"].iloc[0])
        method = str(df["retrieval_method"].iloc[0])
        alpha = str(df["alpha"].iloc[0])

        if args.from_column:
            if "retrieved_exemplars" not in df.columns:
                print(f"lewat: {os.path.basename(f)} tidak punya kolom retrieved_exemplars")
                continue
            per_row = exemplars_from_column(df)
            source = "kolom retrieved_exemplars"
        else:
            if args.cache is None:
                sys.exit("--from-cache memerlukan --cache")
            if method not in ("centroid", "hybrid_early"):
                rows.append(OrderedDict([
                    ("file", os.path.basename(f)), ("style_target", target),
                    ("retrieval_method", method), ("alpha", alpha),
                    ("n", len(df)), ("sumber_eksemplar", "tidak tersedia"),
                    ("catatan", "hanya centroid dan hybrid yang dapat direkonstruksi dari cache"),
                ]))
                continue
            key = target
            if key not in cache_pool:
                cache_pool[key] = centroid_exemplars(args.cache, target, args.k)
            ex = cache_pool[key]
            if ex is None:
                print(f"lewat: cache untuk pool '{target}' tidak ditemukan")
                continue
            per_row = [ex] * len(df)
            source = f"rekonstruksi centroid dari cache (k={args.k})"

        ratios = [overlap_ratio(t, e, args.n) for t, e in zip(df["paraphrased_message"], per_row)]
        ratios = np.array([r for r in ratios if np.isfinite(r)])
        if ratios.size == 0:
            continue
        rows.append(OrderedDict([
            ("file", os.path.basename(f)), ("style_target", target),
            ("retrieval_method", method), ("alpha", alpha),
            ("n", len(df)), ("sumber_eksemplar", source),
            (f"overlap{args.n}_mean", round(float(ratios.mean()), 4)),
            ("pct_output_dengan_overlap", round(100 * float((ratios > 0).mean()), 1)),
            ("pct_output_overlap_tinggi", round(100 * float((ratios > 0.2).mean()), 1)),
        ]))

    if not rows:
        sys.exit("tidak ada hasil yang dapat dihitung")
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(f"\nLaju replikasi templat, n-gram={args.n}\n")
    print(out.to_string(index=False))
    if args.out:
        out.to_csv(args.out, index=False)
        print(f"\nDisimpan: {args.out}")


if __name__ == "__main__":
    main()
