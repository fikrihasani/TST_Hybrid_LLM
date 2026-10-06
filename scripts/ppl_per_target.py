from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

def trimmed_mean(values: np.ndarray, trim: float = 0.10) -> float:
    values = np.sort(values)
    k = int(np.floor(len(values) * trim))
    core = values[k : len(values) - k] if len(values) - k > k else values
    return float(np.mean(core))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--threshold", type=float, default=1000.0)
    ap.add_argument("--pattern", default="evaluated_v2_*_seed42_results.csv")
    ap.add_argument("--col", default="fluency_ppl")
    ap.add_argument("--out", default="TABEL_ppl_formality_per_target.csv")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, "**", args.pattern), recursive=True))
    if not files:
        print(f"Tidak ada berkas cocok di {args.dir}", file=sys.stderr)
        return 2

    frames = []
    for path in files:
        df = pd.read_csv(path)
        if args.col not in df.columns:
            print(f"Kolom {args.col} tidak ada di {os.path.basename(path)}", file=sys.stderr)
            continue
        df = df.copy()
        df["__file"] = os.path.basename(path)
        if "alpha" in df.columns and "retrieval_method" in df.columns:
            df["__konfig"] = (
                df["retrieval_method"].astype(str)
                + df["alpha"].apply(lambda a: "" if pd.isna(a) else f"_a{a}")
            )
        else:
            df["__konfig"] = df["__file"]
        frames.append(df)

    data = pd.concat(frames, ignore_index=True)
    print(f"Berkas terbaca: {len(files)}")
    print(f"Total baris: {len(data)}")
    print()

    out_rows = []

    def summarise(sub: pd.DataFrame, label: str) -> dict:
        v = pd.to_numeric(sub[args.col], errors="coerce")
        n = int(len(v))
        n_degen = int((v > args.threshold).sum())
        valid = v.dropna().to_numpy()
        row = {
            "kelompok": label,
            "n": n,
            "n_degenerate": n_degen,
            "pct_degenerate": round(100.0 * n_degen / n, 2) if n else float("nan"),
            "mean": round(float(np.mean(valid)), 2) if len(valid) else float("nan"),
            "median": round(float(np.median(valid)), 2) if len(valid) else float("nan"),
            "trimmed10": round(trimmed_mean(valid), 2) if len(valid) else float("nan"),
            "sd": round(float(np.std(valid, ddof=1)), 2) if len(valid) > 1 else float("nan"),
            "min": round(float(np.min(valid)), 2) if len(valid) else float("nan"),
            "max": round(float(np.max(valid)), 2) if len(valid) else float("nan"),
        }
        return row

    print("== Per target ==")
    for target in sorted(data["style_target"].unique()):
        sub = data[data["style_target"] == target]
        row = summarise(sub, f"target={target}")
        out_rows.append(row)
        print(row)

    print()
    print("== Per (target, metode) ==")
    for target in sorted(data["style_target"].unique()):
        for metode in sorted(data["retrieval_method"].unique()):
            sub = data[(data["style_target"] == target) & (data["retrieval_method"] == metode)]
            if len(sub) == 0:
                continue
            row = summarise(sub, f"target={target}|metode={metode}")
            out_rows.append(row)
            print(row)

    out_path = args.out
    try:
        pd.DataFrame(out_rows).to_csv(out_path, index=False)
        print()
        print(f"Ditulis: {out_path}")
    except Exception as exc:
        print(f"Gagal menulis {out_path}: {exc}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
