#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import glob
import json
import os
import sys
from collections import defaultdict

import pandas as pd

REQUIRED_COLUMNS = [
    "sample_index", "sample_seed", "run_seed", "retrieved_exemplars",
    "retrieval_fallback", "n_exemplars", "prompt_chars", "output_tokens",
    "eos_reached", "output_chars",
]
EXPECTED_META = ["model_id", "original_style", "style_target", "retrieval_method",
                 "alpha", "original_message", "paraphrased_message", "is_human_eval"]

def check_file(path, num_examples, results):
    name = os.path.basename(path)
    df = pd.read_csv(path)

    def rec(item, ok, detail=""):
        results.append({"berkas": name, "pemeriksaan": item, "lulus": bool(ok),
                        "keterangan": detail})

    for col in EXPECTED_META + REQUIRED_COLUMNS:
        rec(f"kolom {col}", col in df.columns,
            "" if col in df.columns else "HILANG, patch bagian 5.6 protokol belum diterapkan")
    if not all(c in df.columns for c in REQUIRED_COLUMNS):
        return

    method = str(df["retrieval_method"].iloc[0])
    rec("tidak ada keluaran ERROR",
        not df["paraphrased_message"].astype(str).str.contains("ERROR").any(),
        f"{int(df['paraphrased_message'].astype(str).str.contains('ERROR').sum())} baris bermasalah")

    n_fb = int(df["retrieval_fallback"].astype(bool).sum())
    rec("tidak ada fallback ke retrieve_random", n_fb == 0,
        f"{n_fb} dari {len(df)} sampel memakai fallback. Bila tidak nol, laporkan konfigurasi "
        f"dan penyebabnya pada RUN_LOG.md")

    rec("sample_index unik", df["sample_index"].is_unique,
        f"{len(df) - df['sample_index'].nunique()} duplikat")

    if method == "zero_shot":
        rec("zero_shot tidak memuat eksemplar", (df["n_exemplars"] == 0).all(),
            "mode tanpa eksemplar seharusnya bernilai nol")
    else:
        try:
            parsed = [json.loads(v) if isinstance(v, str) else v for v in df["retrieved_exemplars"]]
            n_have = sum(1 for p in parsed if p)
            rec("eksemplar terisi", n_have == len(df),
                f"{n_have} dari {len(df)} baris berisi eksemplar")
            lens = {len(p) for p in parsed if p}
            rec(f"jumlah eksemplar sesuai k={num_examples}",
                lens == {num_examples}, f"panjang yang ditemukan: {sorted(lens)}")
        except Exception as e:
            rec("eksemplar dapat diurai sebagai JSON", False, str(e))

    if method == "centroid":
        try:
            parsed = [json.dumps(p, sort_keys=True, ensure_ascii=False)
                      for p in (json.loads(v) if isinstance(v, str) else v
                                for v in df["retrieved_exemplars"])]
            uniq = len(set(parsed))
            rec("eksemplar centroid identik untuk semua sampel", uniq == 1,
                f"{uniq} himpunan eksemplar berbeda. Metode centroid bersifat "
                f"query-independent, jadi harus tepat satu")
            if uniq == 1:
                n_distinct = len({t for t in json.loads(parsed[0])})
                rec("informasi jumlah teks berbeda dalam eksemplar centroid", True,
                    f"{n_distinct} teks berbeda dari {num_examples} eksemplar. "
                    f"Angka ini dilaporkan di manuscript dan bukan kegagalan")
        except Exception as e:
            rec("pemeriksaan query-independence centroid", False, str(e))

    rec("output tidak kosong", (df["output_chars"] > 0).all(),
        f"{int((df['output_chars'] == 0).sum())} baris kosong")
    rec("seed per sampel terisi", df["sample_seed"].notna().all(), "")

def check_sample_index_consistency(files, results):
    by_target = defaultdict(list)
    for f in files:
        df = pd.read_csv(f, usecols=lambda c: c in ("style_target", "retrieval_method",
                                                    "sample_index", "alpha"))
        if "sample_index" not in df.columns:
            continue
        key = (str(df["style_target"].iloc[0]),)
        by_target[key].append((os.path.basename(f), set(df["sample_index"])))
    for key, items in by_target.items():
        sets = [s for _, s in items]
        same = all(s == sets[0] for s in sets)
        results.append({
            "berkas": f"target {key[0]}",
            "pemeriksaan": "himpunan sample_index sama di seluruh metode",
            "lulus": same,
            "keterangan": (f"{len(items)} berkas, {len(sets[0])} sampel" if same else
                           "ADA PERBEDAAN, perbandingan berpasangan menjadi tidak sah"),
        })

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--num-examples", type=int, default=5)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    if args.file:
        files = [args.file]
    elif args.dir:
        files = sorted(glob.glob(os.path.join(args.dir, "*_results.csv")))
        files = [f for f in files if not f.endswith("_HUMAN_EVAL.csv")]
    else:
        sys.exit("pakai --dir atau --file")
    if not files:
        sys.exit("tidak ada berkas hasil ditemukan")

    results = []
    for f in files:
        check_file(f, args.num_examples, results)
    check_sample_index_consistency(files, results)

    print(f"Gerbang uji jalur, {len(files)} berkas\n" + "=" * 78)
    current = None
    for r in results:
        if r["berkas"] != current:
            current = r["berkas"]
            print(f"\n{r['berkas']}")
        mark = "OK   " if r["lulus"] else "GAGAL"
        print(f"  {mark} {r['pemeriksaan']:58s} {r['keterangan']}")

    bad = [r for r in results if not r["lulus"]]
    print("\n" + "=" * 78)
    print(f"{len(results) - len(bad)} lulus, {len(bad)} gagal")
    if bad:
        print("\nGAGAL. Perbaiki lebih dulu, jangan lanjut ke Langkah 4 protokol.")
        for r in bad[:20]:
            print(f"  - {r['berkas']}: {r['pemeriksaan']}")
    else:
        print("\nLOLOS. Jalur pipeline siap dipakai untuk eksperimen panjang.")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Hasil disimpan: {args.json}")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
