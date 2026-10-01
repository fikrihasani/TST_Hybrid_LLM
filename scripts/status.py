#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
status.py
=========
Menampilkan keadaan pekerjaan tanpa mengganggu proses yang sedang berjalan.
Jalankan dari terminal terpisah, bukan lewat panel agen, supaya tidak menghentikan
giliran agen yang sedang memantau.

Yang ditampilkan
----------------
1. Keadaan `fewshot_config.json` kedua repo: split yang dipakai, daftar metode,
   rentang k, alpha, dan seed. Berguna untuk memastikan konfigurasi tidak tertinggal
   dalam keadaan uji atau keadaan alphadev.
2. Berkas log terbaru per repo: nama, ukuran, waktu perubahan terakhir, dan 10 baris
   terakhir. Ukuran yang bertambah antar pemanggilan berarti pekerjaan masih berjalan.
3. Proses Python yang sedang hidup beserta PID, waktu mulai, dan waktu CPU.
4. Jumlah berkas hasil per repo.

Pemakaian
---------
    python status.py
    python status.py --watch 60      # tampilkan ulang setiap 60 detik
"""
import argparse
import glob
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent.parent
REPOS = [("formality", BUNDLE / "fewshot_formality"),
         ("aaker", BUNDLE / "fewshot_aaker")]
KEYS = ["split_dir", "retrieval_methods", "num_examples_range", "hybrid_alphas",
        "run_seeds", "num_samples", "skip_existing"]


def human_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def show_configs():
    print("\nKONFIGURASI")
    print("-" * 78)
    for tag, repo in REPOS:
        p = repo / "fewshot_config.json"
        print(f"\n  {tag}  ({p.relative_to(BUNDLE)})")
        if not p.exists():
            print("    TIDAK ADA")
            continue
        cfg = json.loads(p.read_text(encoding="utf-8"))
        for k in KEYS:
            if k in cfg:
                print(f"    {k:20s} {cfg[k]}")
        warn = []
        split = str(cfg.get("split_dir", ""))
        if "_v2" not in split:
            warn.append("split_dir TIDAK menunjuk ke split baru. Hasilnya akan memakai split lama "
                        "yang masih bocor, dan seluruh pekerjaan menjadi tidak sah")
        if "dev" in split.lower():
            warn.append("split_dir masih menunjuk ke split dev. Ini keadaan untuk pemilihan alpha, "
                        "bukan untuk run utama")
        expect_ns = "all" if tag == "formality" else 500
        if cfg.get("num_samples") != expect_ns:
            warn.append(f"num_samples = {cfg.get('num_samples')!r}, sedangkan nilai penuh untuk "
                        f"{tag} adalah {expect_ns!r}. Ini nilai uji")
        methods = cfg.get("retrieval_methods", [])
        for necessity in ("random", "zero_shot"):
            if necessity not in methods:
                warn.append(f"metode {necessity} belum ada di retrieval_methods. Diperlukan untuk "
                            f"memenuhi permintaan baseline pada langkah 6")
        if not cfg.get("run_seeds"):
            warn.append("run_seeds belum ada. Diperlukan untuk ulangan pada langkah 7")
        for w in warn:
            print(f"    ! {w}")


def find_logs(repo):
    """Cari berkas log di mana pun di dalam repo, termasuk lokasi tak terduga."""
    found = []
    for pat in ("*.log", "*.err"):
        found += glob.glob(str(repo / pat))
        found += glob.glob(str(repo / "outputs" / "fewshot_logs" / "*" / pat))
        try:
            found += [str(p) for p in repo.rglob(pat)]
        except Exception:
            pass
    return sorted(set(found), key=os.path.getmtime)


def render_log(path, ringkas=False):
    """Tampilkan satu berkas log: ukuran, waktu tulis terakhir, dan beberapa baris terakhir.

    Untuk berkas stderr peluncur terlepas, baris terakhir berisi bilah kemajuan tqdm dengan hitungan
    sampel, sehingga baris itu sekaligus menjadi penunjuk kemajuan per sampel.
    """
    st = os.stat(path)
    age = (datetime.now() - datetime.fromtimestamp(st.st_mtime)).total_seconds()
    print(f"\n  {path}")
    print(f"    ukuran {human_size(st.st_size)} | "
          f"terakhir ditulis {age:.0f} detik lalu "
          f"({datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M:%S})")
    # Log internal pipeline ditulis satu baris per blok target, bukan per konfigurasi.
    # Pada korpus Aaker satu blok target berarti lima nilai alpha kali 500 sampel, yaitu
    # sekitar 3,7 jam. Basis waktu untuk log internal karena itu jauh lebih longgar.
    internal = "fewshot_experiment_" in os.path.basename(path)
    if internal:
        if age > 150 * 60:
            print("    PERHATIAN: log internal diam lebih dari 150 menit, sedangkan satu blok "
                  "target biasanya selesai dalam sekitar 3,7 jam")
        elif age > 600:
            print("    (log internal menulis satu baris per blok target; diam sampai sekitar "
                  "3,7 jam itu normal. Pantau berkas hasil, bukan berkas ini)")
    elif age > 600:
        print("    PERHATIAN: tidak ada penulisan baru lebih dari 10 menit")
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        for line in lines[-8:]:
            print(f"      | {line[:140]}")
    except Exception as e:
        print(f"    gagal membaca: {e}")


def show_logs(running):
    print("\nLOG TERBARU")
    print("-" * 78)
    any_log = False

    # Log peluncur terlepas ditulis di LOGS/ pada akar bundel, bukan di dalam repo. Berkas stderr di
    # situ memuat bilah kemajuan tqdm, yaitu satu-satunya sumber kemajuan per sampel.
    pl = sorted(glob.glob(str(BUNDLE / "LOGS" / "*.log")), key=os.path.getmtime)
    if pl:
        any_log = True
        print("\n  LOG PELUNCUR TERLEPAS (LOGS/ di akar bundel)")
        for path in pl[-2:]:
            render_log(path)
        err = [p for p in pl if p.endswith(".err.log")]
        if err:
            print(f"\n  Berkas stderr di atas memuat bilah kemajuan tqdm. Baris terakhirnya "
                  f"menunjukkan hitungan sampel yang sedang dikerjakan, jadi ukuran berkas itu "
                  f"bertambah terus meski belum ada konfigurasi yang selesai.")

    for tag, repo in REPOS:
        files = find_logs(repo)
        if not files:
            print(f"\n  {tag}: TIDAK ADA berkas log sama sekali di dalam {repo.name}")
            if running:
                print("    PERHATIAN BESAR: ada proses Python yang hidup tetapi keluarannya "
                      "tidak dialihkan ke berkas.")
                print("    Artinya kemajuan hanya terlihat dari sesi agen. Prosesnya sendiri tetap")
                print("    berjalan, dan hasil tiap konfigurasi tetap ditulis saat konfigurasi itu")
                print("    selesai, tetapi persentase per sampel tidak dapat dipantau dari berkas.")
            continue
        any_log = True
        for path in files[-3:]:
            render_log(path)
    return any_log


def list_processes():
    """Daftar proses Python lain, tanpa proses sementara milik status.py sendiri."""
    print("\nPROSES PYTHON")
    print("-" * 78)
    system = platform.system()
    me = os.getpid()
    rows = []
    try:
        if system == "Windows":
            ps = ("Get-Process python*,pythonw* -ErrorAction SilentlyContinue | "
                  "Select-Object Id,ProcessName,"
                  "@{n='CPUsec';e={[math]::Round($_.CPU,1)}},"
                  "@{n='Mulai';e={$_.StartTime.ToString('yyyy-MM-dd HH:mm:ss')}} | "
                  "ConvertTo-Csv -NoTypeInformation")
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                                 capture_output=True, text=True, timeout=30)
            for line in (out.stdout or "").splitlines()[1:]:
                parts = [p.strip().strip('"') for p in line.split(",")]
                if len(parts) < 4 or not parts[0].isdigit():
                    continue
                pid = int(parts[0])
                try:
                    cpu = float(parts[2])
                except ValueError:
                    cpu = 0.0
                try:
                    started = datetime.strptime(parts[3], "%Y-%m-%d %H:%M:%S")
                    age = (datetime.now() - started).total_seconds()
                except ValueError:
                    age = 9999.0
                rows.append({"pid": pid, "nama": parts[1], "cpu": cpu, "umur": age})
        else:
            out = subprocess.run(["ps", "-eo", "pid,etime,pcpu,cmd"],
                                 capture_output=True, text=True, timeout=30)
            for line in (out.stdout or "").splitlines()[1:]:
                parts = line.split(None, 3)
                if len(parts) < 4 or "python" not in parts[3] or "status.py" in parts[3]:
                    continue
                rows.append({"pid": int(parts[0]), "nama": parts[3][:60],
                             "cpu": float(parts[2]), "umur": 9999.0})
    except Exception as e:
        print(f"  gagal membaca daftar proses: {e}")
        return 0

    def sementara(r):
        # Proses pembungkus status.py sendiri: baru dibuat dan CPU-nya mendekati nol.
        return r["umur"] < 120 and r["cpu"] < 1.0

    sementara_rows = [r for r in rows if r["pid"] == me or sementara(r)]
    nyata = [r for r in rows if not (r["pid"] == me or sementara(r))]

    if nyata:
        print(f"  {'PID':>8}  {'CPU (detik)':>11}  {'berjalan':>10}  nama")
        for r in nyata:
            umur = f"{r['umur']/3600:.1f} jam" if r["umur"] < 9999 else "-"
            print(f"  {r['pid']:>8}  {r['cpu']:>11.1f}  {umur:>10}  {r['nama'][:40]}")
    else:
        print("  tidak ada proses Python lain yang berjalan")
    if sementara_rows:
        print(f"  (proses sementara, termasuk status.py sendiri: "
              f"{len(sementara_rows)} baris, tidak dihitung)")
    if len(nyata) > 1:
        print("  PERHATIAN: lebih dari satu proses Python berjalan. Sebelum meluncurkan generasi "
              "baru, pastikan tidak ada yang sedang memakai GPU.")
    return len(nyata)


def configured_results_dir(repo):
    """Direktori hasil dibaca dari config, karena bisa berbeda antara run alphadev dan run utama."""
    p = repo / "fewshot_config.json"
    if p.exists():
        try:
            cfg = json.loads(p.read_text(encoding="utf-8"))
            rel = cfg.get("output_dirs", {}).get("results", "model_results_dir")
            return repo / rel
        except Exception:
            pass
    return repo / "model_results_dir"


def show_outputs():
    print("\nBERKAS HASIL")
    print("-" * 78)
    for tag, repo in REPOS:
        cfg_dir = configured_results_dir(repo)
        gen = [f for f in glob.glob(str(cfg_dir / "*" / "*_results.csv"))
               if not f.endswith("_HUMAN_EVAL.csv")]
        any_dir = glob.glob(str(repo / "model_results_dir" / "*" / "*_results.csv"))
        any_dir = [f for f in any_dir if not f.endswith("_HUMAN_EVAL.csv")]
        ev = glob.glob(str(repo / "evaluation_result" / "*" / "evaluated_*.csv"))
        ev2 = glob.glob(str(repo / "evaluation_result_v2" / "*" / "evaluated_v2_*.csv"))
        print(f"\n  {tag:10s} direktori hasil dari config: {cfg_dir.relative_to(repo)}")
        print(f"  {'':10s} keluaran generasi di situ={len(gen):3d}"
              + (f" | total di model_results_dir={len(any_dir):3d}" if len(any_dir) != len(gen) else "")
              + f" | evaluasi lama={len(ev):3d} | evaluasi baru={len(ev2):3d}")
        if cfg_dir != repo / "model_results_dir":
            print(f"  {'':10s} PERHATIAN: direktori hasil berbeda dari model_results_dir. Hasil "
                  f"sapuan alphadev dan run utama bisa berada di folder berbeda, atau bisa juga "
                  f"bertabrakan bila namanya sama")
        files = sorted(gen, key=os.path.getmtime)
        if files:
            print(f"  {'':10s} 3 berkas terbaru:")
            for f in files[-3:]:
                age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(f))).total_seconds()
                print(f"  {'':12s} {os.path.basename(f)[:62]:64s} {age/60:8.1f} menit lalu")


def once():
    print(f"\nKeadaan pekerjaan JCCE-First Revision  |  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"Folder: {BUNDLE}")
    show_configs()
    n_proc = list_processes()
    show_logs(n_proc > 0)
    show_outputs()
    print("\n" + "=" * 78)
    print("Ukuran log yang bertambah antar pemanggilan berarti pekerjaan masih berjalan.")
    print("Bila ukurannya diam padahal seharusnya jalan, periksa PID pada daftar proses di atas.")
    print("Jalankan script ini dari terminal biasa, bukan lewat panel agen, agar giliran agen")
    print("yang sedang memantau tidak terhenti.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", type=int, default=0,
                    help="tampilkan ulang setiap N detik (0 = sekali saja)")
    args = ap.parse_args()
    if args.watch <= 0:
        once()
        return
    try:
        while True:
            os.system("cls" if platform.system() == "Windows" else "clear")
            once()
            time.sleep(args.watch)
    except KeyboardInterrupt:
        print("\nberhenti")


if __name__ == "__main__":
    main()
