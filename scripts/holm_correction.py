#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
holm.py - koreksi multiplisitas Holm untuk tabel uji berpasangan.

Membaca seluruh uji_*.csv pada satu folder, mengambil nilai p utama setiap pasangan sebagai
nilai terbesar antara uji Wilcoxon dan uji permutasi tanda (aturan triple-concordance
mensyaratkan keduanya sepakat), lalu menerapkan koreksi Holm di dalam setiap berkas.

Pemakaian:
    python holm.py --dir harness/out --out harness/out/HOLM_v2.md
"""
from __future__ import annotations

import argparse
import csv
import glob
import os

ALFA = 0.05


def baca(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def p_utama(row):
    nilai = []
    for k in ("p_wilcoxon", "p_permutasi_tanda"):
        v = (row.get(k) or "").strip()
        try:
            nilai.append(float(v))
        except ValueError:
            pass
    return max(nilai) if nilai else None


def triple_concordance(row):
    """Definisi naskah: interval tidak memuat nol DAN kedua uji sepakat pada 0,05."""
    if (row.get("bermakna_95") or "").strip() != "True":
        return False
    p = p_utama(row)
    return p is not None and p < ALFA


def holm(pasangan):
    """pasangan: daftar (kunci, p). Mengembalikan daftar (kunci, p, p_adj, tolak) dengan urutan asli."""
    sah = [(k, p) for k, p in pasangan if p is not None]
    urut = sorted(sah, key=lambda x: x[1])
    m = len(urut)
    adj = {}
    berjalan = 0.0
    for i, (k, p) in enumerate(urut):
        nilai = min(1.0, p * (m - i))
        berjalan = max(berjalan, nilai)
        adj[k] = berjalan
    return [(k, p, adj.get(k), (adj.get(k) is not None and adj[k] < ALFA)) for k, p in pasangan]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    berkas = sorted(f for f in glob.glob(os.path.join(args.dir, "uji_*.csv"))
                    if not f.endswith("_holm.csv"))
    if not berkas:
        raise SystemExit(f"tidak ada uji_*.csv di {args.dir}")

    baris = ["# Koreksi Holm untuk keluarga uji putaran 2", "",
             f"Ambang: alpha = {ALFA}. Nilai p utama setiap pasangan adalah yang terbesar antara "
             "Wilcoxon dan permutasi tanda. Pasangan dihitung bermakna memakai definisi naskah "
             "(triple concordance): interval tidak memuat nol dan kedua uji sepakat.", ""]
    ringkas = []
    for path in berkas:
        nama = os.path.basename(path).replace("uji_", "").replace(".csv", "")
        rows = baca(path)
        pasangan = []
        for i, r in enumerate(rows):
            kunci = f"{r.get('konfigurasi_a')} vs {r.get('konfigurasi_b')}"
            pasangan.append((kunci, p_utama(r)))
        hasil = holm(pasangan)
        sebelum = sum(1 for r in rows if triple_concordance(r))
        sesudah = sum(1 for r, (_, p, adj, _) in zip(rows, hasil)
                      if triple_concordance(r) and adj is not None and adj < ALFA)
        ringkas.append((nama, len(rows), sebelum, sesudah))
        out_csv = path.replace(".csv", "_holm.csv")
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["konfigurasi_a", "konfigurasi_b", "selisih_mean", "ci95_bawah", "ci95_atas",
                        "bermakna_95", "p_utama", "p_holm", "triple_concordance",
                        "bermakna_setelah_holm"])
            for r, (kunci, p, adj, tolak) in zip(rows, hasil):
                w.writerow([r.get("konfigurasi_a"), r.get("konfigurasi_b"), r.get("selisih_mean"),
                            r.get("ci95_bawah"), r.get("ci95_atas"), r.get("bermakna_95"),
                            "" if p is None else f"{p:.6g}",
                            "" if adj is None else f"{adj:.6g}",
                            triple_concordance(r),
                            bool(triple_concordance(r) and adj is not None and adj < ALFA)])
        gugur = sebelum - sesudah
        baris.append(f"## {nama}")
        baris.append("")
        baris.append(f"- pasangan: {len(rows)}")
        baris.append(f"- triple concordance tanpa koreksi: {sebelum}")
        baris.append(f"- triple concordance setelah Holm: {sesudah}")
        baris.append(f"- gugur karena koreksi: {gugur}")
        baris.append("")

    baris += ["## Ringkasan", "", "| keluarga uji | pasangan | bermakna | setelah Holm |",
              "|---|---|---|---|"]
    for nama, n, sebelum, sesudah in ringkas:
        baris.append(f"| {nama} | {n} | {sebelum} | {sesudah} |")

    teks = "\n".join(baris) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(teks)
        print(f"ditulis {args.out}")
    else:
        print(teks)


if __name__ == "__main__":
    main()
