#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import glob
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent.parent
MIN_PY = (3, 10)
PACKAGES = [
    ("numpy", "1.24", None),
    ("pandas", "1.5", None),
    ("sklearn", "0.24", "scikit-learn"),
    ("torch", "2.0", None),
    ("transformers", "4.40", None),
    ("sentence_transformers", "2.2", "sentence-transformers"),
    ("rank_bm25", "0.2", "rank-bm25"),
    ("tqdm", "4.60", None),
]
OPTIONAL = [("scipy", "1.7", "scipy")]
REQUIRED_FILES = [
    "PROTOKOL_RERUN.md",
    "README.md",
    "scripts/make_splits_formality.py",
    "scripts/make_splits_brand.py",
    "scripts/verify_splits.py",
    "scripts/evaluate_results.py",
    "scripts/report_metrics.py",
    "scripts/bootstrap_significance.py",
    "scripts/replication_metric.py",
    "scripts/select_alpha_dev.py",
    "scripts/calibrate_classifier.py",
    "classifier_formality/main.py",
    "classifier_formality/data/combined_stif.csv",
    "classifier_formality/data/stif_formal.txt",
    "classifier_formality/data/stif_informal.txt",
    "classifier_brand/main.py",
    "classifier_brand/data/Combined Aaker Brand Personality - Cleaned v0.csv",
    "fewshot_formality/fewshot_formality.py",
    "fewshot_formality/eval.py",
    "fewshot_formality/retrieval_utils.py",
    "fewshot_formality/prompts/fewshot_generation_prompt.txt",
    "fewshot_aaker/main.py",
    "fewshot_aaker/eval.py",
    "fewshot_aaker/retrieval_utils.py",
    "fewshot_aaker/prompts/fewshot_generation_prompt.txt",
]
CONFIG_CANDIDATES = ["fewshot_config.json"]
SPLIT_CHECKS = [
    ("Aaker, split lama (diharapkan GAGAL)", "fewshot_aaker/data/brand_splits", 0, False),
    ("Aaker, split baru (diharapkan LOLOS)", "fewshot_aaker/data/brand_splits_v2", 0, True),
    ("STIF, split lama (diharapkan GAGAL)", "fewshot_formality/data/formality_splits", 0, False),
    ("STIF, split baru (diharapkan LOLOS)", "fewshot_formality/data/formality_splits_v2", 5, True),
]

results = []

def record(category, item, ok, detail=""):
    results.append({"kategori": category, "item": item, "lulus": bool(ok), "keterangan": detail})

def version_tuple(s):
    out = []
    for part in str(s).split("."):
        num = "".join(c for c in part if c.isdigit())
        out.append(int(num) if num else 0)
    return tuple(out)

def check_env():
    ok = sys.version_info[:2] >= MIN_PY
    record("lingkungan", f"Python >= {MIN_PY[0]}.{MIN_PY[1]}", ok,
           f"terdeteksi {platform.python_version()}")
    record("lingkungan", "sistem operasi", True, platform.platform())

    for mod, minv, pipname in PACKAGES:
        try:
            m = importlib.import_module(mod)
            v = getattr(m, "__version__", None)
            if v is None:
                try:
                    v = importlib.metadata.version(pipname or mod)
                except importlib.metadata.PackageNotFoundError:
                    v = "0"
            good = version_tuple(v) >= version_tuple(minv)
            record("paket", f"{mod} >= {minv}", good, f"terdeteksi {v}")
        except ImportError:
            record("paket", f"{mod} >= {minv}", False,
                   f"BELUM TERPASANG, jalankan: pip install {pipname or mod}")

    for mod, minv, pipname in OPTIONAL:
        try:
            m = importlib.import_module(mod)
            record("paket opsional", f"{mod} >= {minv}", True,
                   f"terdeteksi {getattr(m, '__version__', '0')}, uji Wilcoxon tersedia")
        except ImportError:
            record("paket opsional", f"{mod} >= {minv}", False,
                   f"tidak ada, uji permutasi tanda akan dipakai. pip install {pipname}")

    try:
        from sklearn.model_selection import StratifiedGroupKFold
        record("paket", "StratifiedGroupKFold tersedia", True)
    except Exception as e:
        record("paket", "StratifiedGroupKFold tersedia", False, str(e))

    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            record("perangkat", "GPU CUDA", total >= 15.0,
                   f"{name}, {total:.1f} GB VRAM (syarat minimal 16 GB, toleransi 15)")
        else:
            record("perangkat", "GPU CUDA", False, "tidak ada GPU terdeteksi, jalankan di mesin ber-GPU")
    except Exception as e:
        record("perangkat", "GPU CUDA", False, str(e))

    tok = os.environ.get("HF_TOKEN")
    record("token", "variabel lingkungan HF_TOKEN", bool(tok),
           "terpasang" if tok else "BELUM terpasang, unduhan model akan gagal dengan 401")

def check_files():
    for rel in REQUIRED_FILES:
        p = BUNDLE / rel
        record("berkas", rel, p.exists(), "" if p.exists() else "TIDAK DITEMUKAN")
    for repo in ["fewshot_formality", "fewshot_aaker"]:
        found = [c for c in CONFIG_CANDIDATES if (BUNDLE / repo / c).exists()]
        record("berkas", f"{repo}/fewshot_config.json", bool(found),
               "" if found else "TIDAK DITEMUKAN")
    for rel in ["fewshot_formality/style_classifier/config.json",
                "fewshot_aaker/style_classifier/config.json"]:
        p = BUNDLE / rel
        record("berkas", rel, p.exists(),
               "" if p.exists() else "TIDAK DITEMUKAN (bobot model memang tidak disertakan)")

def check_splits():
    import pandas as pd

    def normalize(s):
        return " ".join(str(s).lower().split())

    for label, rel, tolerance, expect_pass in SPLIT_CHECKS:
        d = BUNDLE / rel
        if not d.is_dir():
            record("split", label, False, f"folder tidak ada: {rel}")
            continue
        try:
            frames = {}
            for name in ["train_set", "val_set", "retrieval_pool", "test_set"]:
                f = d / f"{name}.csv"
                if not f.exists():
                    raise FileNotFoundError(f)
                frames[name] = pd.read_csv(f)
            tcol = "cleaned_text" if "cleaned_text" in frames["test_set"].columns else "text"
            scol = "personality" if "personality" in frames["test_set"].columns else "formality"
            dup = 0
            for cls in frames["test_set"][scol].unique():
                sets = {k: set(v[v[scol] == cls][tcol].map(normalize)) for k, v in frames.items()}
                names = list(sets)
                for i, a in enumerate(names):
                    for b in names[i + 1:]:
                        dup = max(dup, len(sets[a] & sets[b]))

            gcol = ("conversation_id_str"
                    if "conversation_id_str" in frames["test_set"].columns else None)
            groups_shared = False
            if gcol:
                g = {k: set(v[gcol].dropna()) for k, v in frames.items()}
                names = list(g)
                for i, a in enumerate(names):
                    for b in names[i + 1:]:
                        if g[a] & g[b]:
                            groups_shared = True

            passed = (dup <= tolerance) and not groups_shared
            detail = f"duplikat lintas split maks {dup} (toleransi {tolerance})"
            if gcol:
                detail += ", ada percakapan bersama" if groups_shared else ", tidak ada percakapan bersama"
            ok = (passed == expect_pass)
            record("split", label, ok,
                   detail + ("; sesuai harapan" if ok else
                             f"; TIDAK sesuai harapan (diharapkan "
                             f"{'LOLOS' if expect_pass else 'GAGAL'})"))
        except Exception as e:
            record("split", label, False, f"gagal dibaca: {e}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="simpan hasil ke berkas JSON")
    args = ap.parse_args()

    print(f"Pemeriksaan kesiapan untuk {BUNDLE}\n" + "=" * 78)
    check_env()
    check_files()
    check_splits()

    failures, warnings = [], []
    for cat in ["lingkungan", "paket", "perangkat", "token", "berkas", "split"]:
        rows = [r for r in results if r["kategori"] == cat]
        if not rows:
            continue
        print(f"\n[{cat.upper()}]")
        for r in rows:
            mark = "OK  " if r["lulus"] else "GAGAL"
            print(f"  {mark} {r['item']:58s} {r['keterangan']}")
            if not r["lulus"]:
                (warnings if cat in ("paket opsional",) else failures).append(r)

    print("\n" + "=" * 78)
    n_ok = sum(1 for r in results if r["lulus"])
    print(f"{n_ok} dari {len(results)} pemeriksaan lulus")
    for label, group in [("KEGAGALAN", failures), ("PERINGATAN", warnings)]:
        if not group:
            continue
        print(f"\n{label}:")
        for r in group:
            print(f"  - [{r['kategori']}] {r['item']}: {r['keterangan']}")

    if failures:
        print("\nJANGAN mulai protokol sebelum seluruh kegagalan diselesaikan.")
    else:
        print("\nLingkungan siap. Lanjutkan ke langkah 1 PROTOKOL_RERUN.md.")
        print("Periksa juga daftar pemotongan pada bagian 10 protokol bila waktu GPU terbatas.")

    if args.json:
        Path(args.json).write_text(
            json.dumps({"bundle": str(BUNDLE), "checks": results}, indent=2), encoding="utf-8")
        print(f"\nHasil disimpan: {args.json}")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
