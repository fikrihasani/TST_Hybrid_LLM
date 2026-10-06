#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import glob
import os
import sys

import pandas as pd

SPLITS = ["train_set", "val_set", "retrieval_pool", "test_set"]

def normalize(s):
    return " ".join(str(s).lower().split())

def load_dir(d, text_col):
    out = {}
    for name in SPLITS:
        p = os.path.join(d, f"{name}.csv")
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        if text_col not in df.columns:
            raise SystemExit(f"{p} tidak punya kolom '{text_col}'. Kolom yang ada: {list(df.columns)}")
        out[name] = df
    for extra in sorted(glob.glob(os.path.join(d, "*.csv"))):
        name = os.path.splitext(os.path.basename(extra))[0]
        if name not in out and name not in ("split_manifest",):
            df = pd.read_csv(extra)
            if text_col in df.columns:
                out[name] = df
    return out

def report(label, splits, text_col, style_col, group_col, account_col):
    total = sum(len(v) for v in splits.values())
    print(f"\n{'-' * 78}\n{label}\n{'-' * 78}")
    print(f"{'split':16s} {'n':>7s} {'%':>7s}  kelas")
    for name, df in splits.items():
        share = 100 * len(df) / total
        dist = df[style_col].value_counts().to_dict() if style_col in df.columns else {}
        print(f"{name:16s} {len(df):7d} {share:6.1f}%  {dist}")
    print(f"{'total':16s} {total:7d}")

    metrics = {}
    print("\n  teks identik antar split, per kelas:")
    classes = sorted(splits[SPLITS[0]][style_col].unique()) if style_col in splits[SPLITS[0]].columns else [None]
    worst = 0
    for cls in classes:
        sets = {}
        for name, df in splits.items():
            sub = df if cls is None else df[df[style_col] == cls]
            sets[name] = set(normalize(t) for t in sub[text_col])
        pairs = {}
        for a in sets:
            for b in sets:
                if a >= b:
                    continue
                n = len(sets[a] & sets[b])
                if n:
                    pairs[f"{a} vs {b}"] = n
        tag = f"kelas {cls}" if cls is not None else "semua kelas"
        if pairs:
            print(f"    {tag}: {pairs}")
            worst = max(worst, max(pairs.values()))
        else:
            print(f"    {tag}: nol")
    metrics["teks_identik_maks"] = worst

    if group_col and group_col in splits[SPLITS[0]].columns:
        print("\n  percakapan bersama antar split:")
        g = {name: set(df[group_col].dropna()) for name, df in splits.items()}
        found = False
        for a in g:
            for b in g:
                if a >= b:
                    continue
                shared = g[a] & g[b]
                if shared:
                    rows = int(splits[b][group_col].isin(g[a]).sum())
                    pct = 100 * rows / max(len(splits[b]), 1)
                    print(f"    {a} vs {b}: {len(shared)} percakapan ({rows} baris {b}, {pct:.1f}%)")
                    found = True
        if not found:
            print("    nol")
        metrics["grup_bersama"] = 1 if found else 0

    if account_col and account_col in splits[SPLITS[0]].columns:
        acc = {name: set(df[account_col].dropna()) for name, df in splits.items()}
        allu = set().union(*acc.values())
        print(f"\n  akun unik di seluruh korpus: {len(allu)}")
        for a in acc:
            for b in acc:
                if a >= b:
                    continue
                inter = len(acc[a] & acc[b])
                if inter:
                    print(f"    akun yang muncul di {a} sekaligus {b}: {inter} dari {len(allu)}")
        metrics["akun_unik"] = len(allu)
    return metrics

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", action="append", required=True, help="folder split, boleh diulang")
    ap.add_argument("--text-col", default=None)
    ap.add_argument("--style-col", default=None)
    ap.add_argument("--group-col", default=None)
    ap.add_argument("--account-col", default=None)
    ap.add_argument("--gate", action="store_true",
                    help="keluar kode 1 bila folder terakhir masih memuat teks identik antar split")
    ap.add_argument("--tolerance", type=int, default=0,
                    help="jumlah teks identik antar split yang masih ditoleransi sebelum gerbang "
                         "dinyatakan gagal. Pakai nilai kecil (mis. 5) untuk korpus yang berkas "
                         "sumbernya sendiri memuat baris ganda, dan laporkan angka sebenarnya")
    args = ap.parse_args()

    text_col = args.text_col
    style_col = args.style_col
    if text_col is None or style_col is None:
        probe = pd.read_csv(os.path.join(args.dir[0], "test_set.csv"))
        if "cleaned_text" in probe.columns:
            text_col, style_col = text_col or "cleaned_text", style_col or "personality"
            group_col = args.group_col or ("conversation_id_str"
                                           if "conversation_id_str" in probe.columns else None)
            account_col = args.account_col or ("username" if "username" in probe.columns else None)
        else:
            text_col, style_col = text_col or "text", style_col or "formality"
            group_col, account_col = args.group_col, args.account_col
        print(f"kolom terdeteksi: text='{text_col}', style='{style_col}', "
              f"group='{group_col}', account='{account_col}'")
    else:
        group_col, account_col = args.group_col, args.account_col

    last = {}
    for d in args.dir:
        splits = load_dir(d, text_col)
        if not splits:
            print(f"lewat: {d} tidak berisi berkas split"); continue
        last = report(d, splits, text_col, style_col, group_col, account_col)

    if args.gate:
        n_dup = last.get("teks_identik_maks", 0)
        if n_dup > args.tolerance:
            print(f"\nGERBANG GAGAL: masih ada {n_dup} teks identik antar split pada folder "
                  f"terakhir, sedangkan toleransi {args.tolerance}.")
            sys.exit(1)
        if last.get("grup_bersama"):
            print("\nGERBANG GAGAL: masih ada percakapan bersama antar split pada folder terakhir.")
            sys.exit(1)
        if n_dup:
            print(f"\nGERBANG LOLOS dengan catatan: {n_dup} teks identik antar split, masih di "
                  f"dalam toleransi {args.tolerance}. Angka ini harus dilaporkan apa adanya.")
        else:
            print("\nGERBANG LOLOS: tidak ada teks identik maupun percakapan bersama antar split.")

if __name__ == "__main__":
    main()
