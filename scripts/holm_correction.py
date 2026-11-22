#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
holm_correction.py - Holm-Bonferroni multiplicity correction for paired significance tables.

Reads all pairwise significance CSV files (`uji_*.csv`) in a directory, takes each pair's
conservative primary p-value as max(p_wilcoxon, p_sign_flip) matching the triple-concordance
criterion, and applies Holm-Bonferroni adjustment within each 90-pair family.

Usage:
    python scripts/holm_correction.py --dir results/tables/formality
    python scripts/holm_correction.py --dir results/tables/brand_personality
"""
from __future__ import annotations

import argparse
import csv
import glob
import os

ALPHA = 0.05


def read_csv_rows(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def primary_p(row):
    vals = []
    for k in ("p_wilcoxon", "p_permutasi_tanda"):
        v = (row.get(k) or "").strip()
        try:
            vals.append(float(v))
        except ValueError:
            pass
    return max(vals) if vals else None


def triple_concordance(row):
    """True when the 95% bootstrap CI excludes zero and both nonparametric tests give p < 0.05."""
    if (row.get("bermakna_95") or "").strip() != "True":
        return False
    p = primary_p(row)
    return p is not None and p < ALPHA


def holm_adjust(pairs):
    """Apply Holm-Bonferroni step-down adjustment while preserving original pair order."""
    valid = [(k, p) for k, p in pairs if p is not None]
    ordered = sorted(valid, key=lambda x: x[1])
    m = len(ordered)
    adj = {}
    running = 0.0
    for i, (k, p) in enumerate(ordered):
        val = min(1.0, p * (m - i))
        running = max(running, val)
        adj[k] = running
    return [(k, p, adj.get(k), (adj.get(k) is not None and adj[k] < ALPHA)) for k, p in pairs]


def main():
    ap = argparse.ArgumentParser(description="Apply Holm-Bonferroni adjustment to pairwise test tables.")
    ap.add_argument("--dir", required=True, help="Directory containing uji_*.csv pairwise tables")
    ap.add_argument("--out", default=None, help="Optional Markdown summary output path")
    args = ap.parse_args()

    files = sorted(
        f for f in glob.glob(os.path.join(args.dir, "uji_*.csv"))
        if not f.endswith("_holm.csv")
    )
    if not files:
        raise SystemExit(f"No uji_*.csv files found in {args.dir}")

    lines = [
        "# Holm-Bonferroni Multiplicity Correction Summary",
        "",
        f"Threshold: alpha = {ALPHA}. Primary p-value per pair is max(p_wilcoxon, p_sign_flip). "
        "Significant pairs require both 95% bootstrap CI exclusion of zero and agreement of both nonparametric tests.",
        "",
    ]
    summary = []
    for path in files:
        name = os.path.basename(path).replace("uji_", "").replace(".csv", "")
        rows = read_csv_rows(path)
        pairs = [(f"{r.get('konfigurasi_a')} vs {r.get('konfigurasi_b')}", primary_p(r)) for r in rows]
        adjusted = holm_adjust(pairs)
        before = sum(1 for r in rows if triple_concordance(r))
        after = sum(
            1 for r, (_, p, adj, _) in zip(rows, adjusted)
            if triple_concordance(r) and adj is not None and adj < ALPHA
        )
        summary.append((name, len(rows), before, after))
        out_csv = path.replace(".csv", "_holm.csv")
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "konfigurasi_a", "konfigurasi_b", "selisih_mean", "ci95_bawah", "ci95_atas",
                "bermakna_95", "p_utama", "p_holm", "triple_concordance",
                "bermakna_setelah_holm",
            ])
            for r, (_, p, adj, _) in zip(rows, adjusted):
                writer.writerow([
                    r.get("konfigurasi_a"), r.get("konfigurasi_b"), r.get("selisih_mean"),
                    r.get("ci95_bawah"), r.get("ci95_atas"), r.get("bermakna_95"),
                    "" if p is None else f"{p:.6g}",
                    "" if adj is None else f"{adj:.6g}",
                    triple_concordance(r),
                    bool(triple_concordance(r) and adj is not None and adj < ALPHA),
                ])
        dropped = before - after
        lines += [
            f"## {name}",
            "",
            f"- pairs: {len(rows)}",
            f"- uncorrected triple concordance: {before}",
            f"- Holm-adjusted triple concordance: {after}",
            f"- dropped after Holm adjustment: {dropped}",
            "",
        ]

    lines += ["## Summary", "", "| Family | Pairs | Uncorrected | Post-Holm |", "|---|---|---|---|"]
    for name, n, before, after in summary:
        lines.append(f"| {name} | {n} | {before} | {after} |")

    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
