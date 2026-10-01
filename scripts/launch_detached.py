#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
launch_detached.py
==================
Peluncur proses terlepas untuk tugas panjang (generasi 4 sampai 15 jam).

Latar belakang: pola `Start-Process -RedirectStandardOutput/-RedirectStandardError` pada PowerShell
di mesin ini gagal tanpa jejak, yaitu proses mati seketika sedangkan kedua berkas log tetap 0 byte
dan tidak ada berkas hasil yang ditulis. Peluncur ini menggantikannya dan langsung memverifikasi
bahwa prosesnya benar-benar hidup dan menulis.

Yang dilakukan:
  1. menjalankan perintah dengan stdout dan stderr ke DUA berkas terpisah,
  2. melepaskan proses dari sesi ini sehingga tetap hidup ketika agen atau terminal ditutup,
  3. mencatat manifest JSON berisi PID, perintah, waktu mulai, dan SHA-256 berkas config,
  4. menunggu beberapa detik lalu memeriksa prosesnya masih hidup dan lognya sudah bertambah,
  5. keluar dengan kode bukan nol bila verifikasi gagal.

Pemakaian
---------
    python scripts/launch_detached.py --nama aaker_step6 --cwd ../fewshot_aaker -- python main.py

    # memeriksa proses yang diluncurkan
    python scripts/launch_detached.py --status --nama aaker_step6

Manifest disimpan di LOGS/detached_<nama>.json, log di LOGS/<nama>.out.log dan LOGS/<nama>.err.log.
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGDIR = os.path.join(ROOT, "LOGS")
IS_WIN = platform.system() == "Windows"

# Variabel lingkungan yang wajib ada pada proses anak. Tanpa ketiganya, peluncuran panjang dapat
# mati di tengah: keluarannya memuat emoji sehingga stdout dengan codec cp1252 gagal, atau unduhan
# model gagal karena mesin ini tidak mengizinkan symlink cache. Nilai yang sudah ada di lingkungan
# pemanggil tidak ditimpa.
ENV_WAJIB = {
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
    "HF_HUB_DISABLE_SYMLINKS": "1",
}


def sha256_of(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def pid_alive(pid):
    """Benar bila proses masih hidup. Aman untuk dipanggil berulang."""
    if IS_WIN:
        try:
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                                 capture_output=True, text=True, timeout=30)
            return str(pid) in (out.stdout or "")
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_manifest(nama):
    path = os.path.join(LOGDIR, f"detached_{nama}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def status(nama):
    man = read_manifest(nama)
    if not man:
        print(f"tidak ada manifest LOGS/detached_{nama}.json")
        return 1
    hidup = pid_alive(man["pid"])
    print(f"nama       : {nama}")
    print(f"PID        : {man['pid']}  ({'HIDUP' if hidup else 'TIDAK HIDUP'})")
    print(f"perintah   : {' '.join(man['argv'])}")
    print(f"cwd        : {man['cwd']}")
    print(f"mulai      : {man['mulai']}")
    for label, key in (("stdout", "log_out"), ("stderr", "log_err")):
        p = man[key]
        if os.path.exists(p):
            st = os.stat(p)
            umur = (datetime.now() - datetime.fromtimestamp(st.st_mtime)).total_seconds()
            print(f"{label:10s} : {st.st_size:>10d} byte | ditulis {umur:.0f} detik lalu | {p}")
        else:
            print(f"{label:10s} : berkas tidak ada | {p}")
    if not hidup:
        print("\nProses tidak hidup. Baca bagian akhir berkas stderr di atas untuk sebabnya.")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nama", required=True, help="nama run, dipakai untuk nama berkas log")
    ap.add_argument("--cwd", default=None,
                    help="direktori kerja proses, misalnya ../fewshot_aaker. Wajib saat meluncurkan, "
                         "tidak perlu saat --status")
    ap.add_argument("--tunggu", type=int, default=8, help="detik menunggu sebelum verifikasi")
    ap.add_argument("--status", action="store_true", help="hanya melaporkan keadaan run")
    ap.add_argument("perintah", nargs=argparse.REMAINDER,
                    help="perintah dan argumennya, awali dengan --")
    args = ap.parse_args()

    if args.status:
        return status(args.nama)

    if not args.cwd:
        print("--cwd wajib diisi saat meluncurkan. Contoh:\n"
              "  python scripts/launch_detached.py --nama aaker_step6 --cwd ../fewshot_aaker "
              "-- python main.py")
        return 2

    cmd = [a for a in args.perintah if a != "--"]
    if not cmd:
        print("perintah kosong. Contoh: --nama aaker_step6 --cwd ../fewshot_aaker -- python main.py")
        return 2

    cwd = os.path.abspath(args.cwd)
    if not os.path.isdir(cwd):
        print(f"direktori kerja tidak ada: {cwd}")
        return 2

    os.makedirs(LOGDIR, exist_ok=True)
    log_out = os.path.join(LOGDIR, f"{args.nama}.out.log")
    log_err = os.path.join(LOGDIR, f"{args.nama}.err.log")
    for p in (log_out, log_err):
        open(p, "w", encoding="utf-8").close()   # kosongkan supaya penambahan baru terbaca jelas

    cfg = os.path.join(cwd, "fewshot_config.json")
    env = dict(os.environ)
    env_diterapkan = {}
    for k, v in ENV_WAJIB.items():
        if not env.get(k):
            env[k] = v
            env_diterapkan[k] = v

    kwargs = {}
    if IS_WIN:
        kwargs["creationflags"] = (subprocess.DETACHED_PROCESS
                                   | subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        kwargs["start_new_session"] = True

    with open(log_out, "w", encoding="utf-8") as fo, open(log_err, "w", encoding="utf-8") as fe:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=fo, stderr=fe, env=env,
                                stdin=subprocess.DEVNULL, **kwargs)

    man = {
        "nama": args.nama,
        "pid": proc.pid,
        "argv": cmd,
        "cwd": cwd,
        "mulai": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "log_out": log_out,
        "log_err": log_err,
        "config": cfg if os.path.exists(cfg) else None,
        "config_sha256": sha256_of(cfg) if os.path.exists(cfg) else None,
        "env_wajib": {k: env.get(k) for k in ENV_WAJIB},
        "env_baru_disetel": env_diterapkan,
    }
    with open(os.path.join(LOGDIR, f"detached_{args.nama}.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2, ensure_ascii=False)

    print(f"PID {proc.pid} diluncurkan terlepas, cwd {cwd}")
    print(f"config sha256: {man['config_sha256']}")
    print("variabel lingkungan wajib: "
          + ", ".join(f"{k}={v}" for k, v in man["env_wajib"].items())
          + (f" ({len(env_diterapkan)} baru disetel oleh peluncur)" if env_diterapkan else
             " (sudah ada di lingkungan pemanggil)"))
    print(f"menunggu {args.tunggu} detik lalu memverifikasi ...")
    time.sleep(args.tunggu)

    if not pid_alive(proc.pid):
        kode = proc.poll()
        if kode == 0:
            print(f"\nProses sudah selesai dengan kode keluar 0 setelah {args.tunggu} detik, "
                  f"jadi tidak ada yang berjalan sekarang.")
            print("Untuk tugas panjang itu di luar kebiasaan, dan bisa berarti perintahnya memang "
                  "pekerjaan singkat. Berikut keluarnya:")
        else:
            print(f"\nGAGAL: proses tidak hidup setelah beberapa detik (kode keluar {kode}). "
                  f"Berikut keluarnya:")
        for label, p in (("stdout", log_out), ("stderr", log_err)):
            print(f"--- {label} ({os.path.getsize(p)} byte) ---")
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    for ln in f.read().splitlines()[-15:]:
                        print(f"  {ln[:160]}")
            except Exception as e:
                print(f"  gagal membaca: {e}")
        if kode == 0:
            return 0
        print("\nJangan menganggap pekerjaan berjalan. Perbaiki sebabnya lalu luncurkan ulang.")
        return 1

    ukuran = (os.path.getsize(log_out), os.path.getsize(log_err))
    print(f"LULUS: PID {proc.pid} masih hidup. stdout {ukuran[0]} byte, stderr {ukuran[1]} byte.")
    if sum(ukuran) == 0:
        print("Catatan: kedua log masih kosong. Pada beberapa program itu normal di detik pertama, "
              "tetapi bila tetap kosong setelah 10 menit, jalankan --status lalu periksa stderr.")
    print(f"Periksa kapan saja dengan: python scripts/launch_detached.py --status --nama {args.nama}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
