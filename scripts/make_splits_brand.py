#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from sklearn.model_selection import StratifiedGroupKFold
except ImportError:
    sys.exit("scikit-learn terlalu lama: StratifiedGroupKFold butuh scikit-learn >= 0.24")

BUNDLE = Path(__file__).resolve().parent.parent
SEED = 42
TEXT, STYLE, GROUP = "cleaned_text", "personality", "conversation_id_str"
SRC_NAME = "Combined Aaker Brand Personality - Cleaned v0.csv"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def normalize(s):
    return " ".join(str(s).lower().split())

def build(src_path, alpha_dev=False, seed=SEED):
    df = pd.read_csv(src_path).dropna(subset=[TEXT, STYLE]).copy()
    df[TEXT] = df[TEXT].astype(str)
    df = df.reset_index(drop=True)
    n_raw = len(df)

    df["_norm"] = [normalize(t) for t in df[TEXT]]
    df = df.drop_duplicates(subset="_norm").reset_index(drop=True)
    n_dedup = len(df)

    sgkf = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=seed)
    fold = np.empty(len(df), dtype=int)
    for k, (_, vidx) in enumerate(sgkf.split(df, df[STYLE].values, groups=df[GROUP].values)):
        fold[vidx] = k
    df["_fold"] = fold

    if alpha_dev:
        mapping = {"test_set": [0], "retrieval_pool": [1, 2, 3], "val_set": [4],
                   "alpha_dev": [5], "train_set": [6, 7, 8, 9]}
    else:
        mapping = {"test_set": [0], "retrieval_pool": [1, 2, 3], "val_set": [4],
                   "train_set": [5, 6, 7, 8, 9]}

    out = {name: df[df._fold.isin(f)].drop(columns=["_norm", "_fold"]).reset_index(drop=True)
           for name, f in mapping.items()}
    return out, {"n_raw": n_raw, "n_dedup": n_dedup}

def verify(out):
    problems = []
    total = sum(len(v) for v in out.values())
    for a in out:
        for b in out:
            if a >= b:
                continue
            ta = set(normalize(x) for x in out[a][TEXT])
            tb = set(normalize(x) for x in out[b][TEXT])
            shared = ta & tb
            if shared:
                problems.append(f"{len(shared)} teks identik antara {a} dan {b}")
            ga, gb = set(out[a][GROUP]), set(out[b][GROUP])
            gshared = ga & gb
            if gshared:
                rows = int(out[b][GROUP].isin(ga).sum())
                problems.append(f"{len(gshared)} percakapan bersama antara {a} dan {b} "
                                f"({rows} baris {b})")
    base = out["train_set"][STYLE].value_counts(normalize=True)
    for name, sub in out.items():
        d = sub[STYLE].value_counts(normalize=True)
        for cls in base.index:
            if abs(d.get(cls, 0) - base[cls]) > 0.02:
                problems.append(f"{name} kelas {cls} proporsinya {d.get(cls, 0):.3f}, "
                                f"train {base[cls]:.3f}")
    return problems, total

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(BUNDLE / "classifier_brand" / "data" / SRC_NAME))
    ap.add_argument("--out", default=None)
    ap.add_argument("--also", default=str(BUNDLE / "fewshot_aaker" / "data" / "brand_splits_v2"))
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--alpha-dev", action="store_true",
                    help="sisihkan fold 5 (5%%) sebagai alpha-dev untuk pemilihan alpha")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    src = Path(args.src)
    out_dir = Path(args.out) if args.out else Path(str(BUNDLE / "classifier_brand" / "data" / "brand_splits_v2"))
    if not src.exists():
        sys.exit(f"berkas sumber tidak ditemukan: {src}")

    out, stats = build(src, args.alpha_dev, args.seed)
    total = sum(len(v) for v in out.values())
    print(f"  baris awal          : {stats['n_raw']}")
    print(f"  setelah deduplikasi : {stats['n_dedup']} "
          f"(dibuang {stats['n_raw'] - stats['n_dedup']}, "
          f"{100 * (stats['n_raw'] - stats['n_dedup']) / stats['n_raw']:.1f}%)")
    for name, sub in out.items():
        print(f"  {name:15s} n={len(sub):6d} ({100 * len(sub) / total:4.1f}%)  "
              f"kelas={sub[STYLE].value_counts().to_dict()}")

    problems, total = verify(out)
    if problems:
        print("\nPEMERIKSAAN GAGAL:")
        for p in problems:
            print("   -", p)
        sys.exit(1)
    print("\nPemeriksaan lolos: nol teks identik, nol percakapan bersama antar split, "
          "dan distribusi kelas seimbang.")

    if args.check:
        print("\nMode --check: tidak ada berkas yang ditulis.")
        return

    targets = [out_dir]
    if args.also and Path(args.also) != out_dir:
        targets.append(Path(args.also))
    for t in targets:
        t.mkdir(parents=True, exist_ok=True)
        for name, sub in out.items():
            sub.to_csv(t / f"{name}.csv", index=False)
        print(f"  ditulis ke {t}")

    manifest = {
        "corpus": "Aaker brand personality",
        "protocol": "deduplikasi teks ternormalisasi + StratifiedGroupKFold per conversation_id_str",
        "seed": args.seed,
        "alpha_dev_disetujui": bool(args.alpha_dev),
        "sizes": {k: int(len(v)) for k, v in out.items()},
        "rows_raw": stats["n_raw"],
        "rows_after_dedup": stats["n_dedup"],
        "rows_dropped": stats["n_raw"] - stats["n_dedup"],
        "accounts": int(out["train_set"]["username"].nunique()),
        "source_file": {"path": str(src), "sha256": sha256(src)},
        "catatan": "pengelompokan level akun tidak mungkin: hanya 24 akun brand di seluruh korpus",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "sklearn": __import__("sklearn").__version__,
        "pandas": pd.__version__,
    }
    for t in targets:
        (t / "split_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("  manifest ditulis: split_manifest.json")

if __name__ == "__main__":
    main()
