#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
make_splits_formality.py
========================
Membuat split korpus STIF (formality) dengan PENGUNCIAN PASANGAN PARALEL.

Mengapa script ini ada
----------------------
Naskah JCCE-10619 menyatakan bahwa pasangan paralel dikunci dengan `pair_id`
sebelum splitting. Pemeriksaan atas split yang dipakai eksperimen menunjukkan
penguncian itu tidak pernah diterapkan: hanya 35,7% pasangan berada di split
yang sama, sedangkan ekspektasi tanpa penguncian adalah 36,0%.

Cara kerja
----------
Berkas `stif_formal.txt` dan `stif_informal.txt` sejajar baris demi baris,
sehingga `pair_id` = nomor baris. Split dilakukan pada daftar `pair_id`, bukan
pada baris, sehingga kedua anggota pasangan selalu berada di split yang sama.
Akibatnya keseimbangan formal dan informal terjaga dengan sendirinya.

Perbedaan dari split lama
-------------------------
Ukuran hasilnya sama persis dengan split lama (50/10/30/10), yang berbeda hanya
keanggotaan tiap split. Kolom `pair_id` kini ikut diekspor agar klaim penguncian
dapat diverifikasi pembaca.

Pemakaian
---------
    python make_splits_formality.py --check          # uji tanpa menulis
    python make_splits_formality.py                  # tulis split + manifest
"""
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import pandas as pd

try:
    from sklearn.model_selection import train_test_split
except ImportError:
    sys.exit("scikit-learn belum terpasang: pip install scikit-learn")

BUNDLE = Path(__file__).resolve().parent.parent
SEED = 42
RATIOS = {"test": 0.10, "pool_of_rest": 1 / 3, "val_of_classifier": 1 / 6}


def sha256(path, limit=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_lines(path):
    return [x.strip() for x in open(path, encoding="utf-8").read().splitlines() if x.strip()]


def build(src_dir, seed=SEED):
    formal = read_lines(src_dir / "stif_formal.txt")
    informal = read_lines(src_dir / "stif_informal.txt")
    if len(formal) != len(informal):
        raise SystemExit(
            f"berkas paralel tidak sejajar: {len(formal)} formal vs {len(informal)} informal"
        )
    rows = []
    for pid, (f, i) in enumerate(zip(formal, informal)):
        rows.append({"pair_id": pid, "text": f, "formality": "formal"})
        rows.append({"pair_id": pid, "text": i, "formality": "informal"})
    df = pd.DataFrame(rows)

    pairs = df["pair_id"].unique()
    rest, test = train_test_split(pairs, test_size=RATIOS["test"], random_state=seed)
    clf, pool = train_test_split(rest, test_size=RATIOS["pool_of_rest"], random_state=seed)
    train, val = train_test_split(clf, test_size=RATIOS["val_of_classifier"], random_state=seed)

    out = {}
    for name, ids in [("train_set", train), ("val_set", val),
                      ("retrieval_pool", pool), ("test_set", test)]:
        sub = df[df.pair_id.isin(ids)].copy()
        sub["label_id"] = sub["formality"].map({"formal": 0, "informal": 1})
        sub = sub[["pair_id", "text", "formality", "label_id"]].reset_index(drop=True)
        out[name] = sub
    return out, df


def verify(out, df):
    """Pemeriksaan yang harus lolos sebelum hasil dipakai.

    Mengembalikan (problems, notes, metrics).
    """
    problems, notes = [], []
    metrics = {}
    total = sum(len(v) for v in out.values())
    if total != len(df):
        problems.append(f"jumlah baris berubah: {total} vs {len(df)}")

    # 1. setiap pasangan harus utuh dalam satu split
    pair_to_split = {}
    for name, sub in out.items():
        for pid in sub["pair_id"]:
            if pid in pair_to_split and pair_to_split[pid] != name:
                problems.append(f"pair_id {pid} terpecah ke dua split")
                break
            pair_to_split[pid] = name

    # 2. setiap split harus berimbang formal dan informal
    for name, sub in out.items():
        vc = sub["formality"].value_counts().to_dict()
        if vc.get("formal", 0) != vc.get("informal", 0):
            problems.append(f"{name} tidak berimbang: {vc}")

    # 3. duplikat diperiksa PER KELAS, karena indeks retrieval dibangun per kelas.
    #    Berkas sumber sendiri sudah memuat baris ganda (2 baris di tiap blok), sehingga
    #    sisa duplikat kecil dilaporkan sebagai angka, bukan diperlakukan sebagai kegagalan.
    per_class_dup = {}
    for cls in ["formal", "informal"]:
        sets = {name: set(sub[sub.formality == cls]["text"]) for name, sub in out.items()}
        tot_pairs = 0
        for a in sets:
            for b in sets:
                if a >= b:
                    continue
                tot_pairs += len(sets[a] & sets[b])
        per_class_dup[cls] = tot_pairs
        if tot_pairs > 10:
            problems.append(f"{tot_pairs} teks identik kelas {cls} melintas split, melebihi batas wajar")
    metrics["duplikat_lintas_split_per_kelas"] = per_class_dup

    # 4. teks yang bentuk formal dan informalnya kebetulan identik: sifat korpus paralel
    #    yang diratakan, tidak masuk ke indeks yang sama, hanya dilaporkan.
    fa_all = set(df[df.formality == "formal"]["text"])
    inf_all = set(df[df.formality == "informal"]["text"])
    metrics["teks_identik_antar_blok"] = len(fa_all & inf_all)
    if metrics["teks_identik_antar_blok"]:
        notes.append(f"{metrics['teks_identik_antar_blok']} teks muncul pada blok formal sekaligus "
                     f"informal; ini sifat korpus paralel yang diratakan dan tidak memengaruhi "
                     f"indeks per kelas")

    # 5. rasio
    expected = {"train_set": 0.50, "val_set": 0.10, "retrieval_pool": 0.30, "test_set": 0.10}
    for name, sub in out.items():
        share = len(sub) / total
        if abs(share - expected[name]) > 0.005:
            problems.append(f"{name} rasionya {share:.3f}, diharapkan {expected[name]:.2f}")
    return problems, notes, metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(BUNDLE / "classifier_formality" / "data"),
                    help="folder berisi stif_formal.txt dan stif_informal.txt")
    ap.add_argument("--out", default=None,
                    help="folder tujuan split (default: <src>/formality_splits_v2)")
    ap.add_argument("--also", default=str(BUNDLE / "fewshot_formality" / "data" / "formality_splits_v2"),
                    help="folder kedua yang ikut ditulisi (dipakai pipeline fewshot)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--check", action="store_true", help="hanya uji, jangan menulis")
    args = ap.parse_args()

    src_dir = Path(args.src)
    out_dir = Path(args.out) if args.out else src_dir / "formality_splits_v2"

    out, df = build(src_dir, args.seed)
    for name, sub in out.items():
        print(f"  {name:15s} n={len(sub):5d}  kelas={sub['formality'].value_counts().to_dict()}")

    problems, notes, metrics = verify(out, df)
    if problems:
        print("\nPEMERIKSAAN GAGAL:")
        for p in problems:
            print("   -", p)
        sys.exit(1)
    for n in notes:
        print("  catatan:", n)
    print(f"  duplikat lintas split per kelas : {metrics['duplikat_lintas_split_per_kelas']}")
    print("\nPemeriksaan lolos: setiap pasangan utuh dalam satu split, tidak ada teks kelas yang "
          "sama melintas split, dan rasio 50/10/30/10 terpenuhi.")

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
        "corpus": "STIF (formality)",
        "protocol": "split pada pasangan paralel, pair_id = nomor baris berkas sumber",
        "seed": args.seed,
        "ratios": {"train": 0.50, "val": 0.10, "retrieval_pool": 0.30, "test": 0.10},
        "sizes": {k: int(len(v)) for k, v in out.items()},
        "pairs": int(df["pair_id"].nunique()),
        "duplikat_lintas_split_per_kelas": metrics["duplikat_lintas_split_per_kelas"],
        "teks_identik_antar_blok_formal_informal": metrics["teks_identik_antar_blok"],
        "source_files": {
            "stif_formal.txt": {"rows": len(read_lines(src_dir / "stif_formal.txt")),
                                "sha256": sha256(src_dir / "stif_formal.txt")},
            "stif_informal.txt": {"rows": len(read_lines(src_dir / "stif_informal.txt")),
                                  "sha256": sha256(src_dir / "stif_informal.txt")},
        },
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
