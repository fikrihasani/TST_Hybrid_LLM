"""Menyalin seluruh berkas terkait naskah revisi JCCE-10619 ke vault Obsidian.

Sumber:
  G:\\My Drive\\...\\1st Round Review        pemetaan reviewer, perencanaan, audit, naskah
  C:\\Devs\\Code\\Python\\JCCE-First Revision-From Remote   bundel hasil rerun

Tujuan:
  C:\\Obsidian\\Notes\\S3\\JCCE

Skrip ini hanya menyalin. Tidak ada berkas sumber yang diubah atau dihapus. Aman dijalankan ulang:
berkas tujuan ditimpa dengan salinan terbaru dari sumbernya.

Yang sengaja TIDAK disalin, karena besar dan sudah terwakili:
  - folder model dan data mentah tiap repo (2,4 GB)
  - ARSIP/ (cadangan hasil generasi, 62 MB)
  - HASIL/keluaran_generasi/ (keluaran generasi mentah, 23 MB)
  - log peluncuran berukuran besar (12,4 MB) dan __pycache__

Contoh:
    python arsipkan_ke_vault.py
    python arsipkan_ke_vault.py --tujuan "C:/Obsidian/Notes/S3/JCCE" --kering
"""
import argparse
import os
import shutil
import sys

G = "G:/My Drive/Documents/Perkuliahan S3/Untuk SHP/Paper 2 Jurnal/1st Round Review"
REMOTE = "C:/Devs/Code/Python/JCCE-First Revision-From Remote"

# (berkas tujuan, folder tujuan, sumber)
RENCANA = [
    # 01 naskah
    ("JCCE-10619-Revision.docx", "01_Naskah", f"{G}/JCCE-10619-Revision.docx"),
    ("10619 1st round reviewer comments.docx", "01_Naskah",
     f"{G}/10619 1st round reviewer comments.docx"),
    # 02 pemetaan reviewer
    ("JCCE-10619_Mapping_Reviewer_Comments_v1.xlsx", "02_Pemetaan_Reviewer",
     f"{G}/JCCE-10619_Mapping_Reviewer_Comments_v1.xlsx"),
    ("JCCE-10619_Alur_Perbaikan_v1.xlsx", "02_Pemetaan_Reviewer",
     f"{G}/JCCE-10619_Alur_Perbaikan_v1.xlsx"),
    ("JCCE-10619_Kerangka_Surat_Balasan.xlsx", "02_Pemetaan_Reviewer",
     f"{G}/JCCE-10619_Kerangka_Surat_Balasan.xlsx"),
    ("README_mapping.md", "02_Pemetaan_Reviewer", f"{G}/README_mapping.md"),
    ("README_kerangka_respon.md", "02_Pemetaan_Reviewer", f"{G}/README_kerangka_respon.md"),
    ("build_mapping_excel.py", "02_Pemetaan_Reviewer", f"{G}/build_mapping_excel.py"),
    ("build_plan_excel.py", "02_Pemetaan_Reviewer", f"{G}/build_plan_excel.py"),
    ("build_response_skeleton.py", "02_Pemetaan_Reviewer", f"{G}/build_response_skeleton.py"),
    ("verify_mapping.py", "02_Pemetaan_Reviewer", f"{G}/verify_mapping.py"),
    ("verify_split_protocol.py", "02_Pemetaan_Reviewer", f"{G}/verify_split_protocol.py"),
    # 03 perencanaan
    ("RENCANA_PERBAIKAN_JCCE-10619.md", "03_Perencanaan",
     f"{G}/RENCANA_PERBAIKAN_JCCE-10619.md"),
    ("PROTOKOL_SPLIT_JCCE-10619.md", "03_Perencanaan", f"{G}/PROTOKOL_SPLIT_JCCE-10619.md"),
    ("SPESIFIKASI_RERUN.md", "03_Perencanaan", f"{G}/SPESIFIKASI_RERUN.md"),
    ("KLAIM_VS_IMPLEMENTASI_PREPROCESSING.md", "03_Perencanaan",
     f"{G}/KLAIM_VS_IMPLEMENTASI_PREPROCESSING.md"),
    ("PERUBAHAN_NASKAH.md", "03_Perencanaan", f"{G}/PERUBAHAN_NASKAH.md"),
    ("AUDIT_SITASI_R2-16_dan_R2-19.md", "03_Perencanaan",
     f"{G}/AUDIT_SITASI_R2-16_dan_R2-19.md"),
    # 04 dokumen rerun
    ("LAPORAN_AKHIR.md", "04_Rerun_Dokumen", f"{REMOTE}/LAPORAN_AKHIR.md"),
    ("PROTOKOL_RERUN.md", "04_Rerun_Dokumen", f"{REMOTE}/PROTOKOL_RERUN.md"),
    ("RUNBOOK_OPERASIONAL.md", "04_Rerun_Dokumen", f"{REMOTE}/RUNBOOK_OPERASIONAL.md"),
    ("RUN_LOG.md", "04_Rerun_Dokumen", f"{REMOTE}/RUN_LOG.md"),
    ("RUN_LOG_TEMPLATE.md", "04_Rerun_Dokumen", f"{REMOTE}/RUN_LOG_TEMPLATE.md"),
    ("README_bundel.md", "04_Rerun_Dokumen", f"{REMOTE}/README.md"),
    ("rules_agen_zed.txt", "04_Rerun_Dokumen", f"{REMOTE}/.rules"),
    ("AGENTS.md", "04_Rerun_Dokumen", f"{REMOTE}/AGENTS.md"),
    ("requirements.txt", "04_Rerun_Dokumen", f"{REMOTE}/requirements.txt"),
    ("preflight.json", "04_Rerun_Dokumen", f"{REMOTE}/preflight.json"),
    ("smoke_formality.json", "04_Rerun_Dokumen", f"{REMOTE}/smoke_formality.json"),
    ("smoke_aaker.json", "04_Rerun_Dokumen", f"{REMOTE}/smoke_aaker.json"),
    # 05 tabel dan pendukung
    ("Pendukung/alpha_star_formality.json", "05_Rerun_Tabel",
     f"{REMOTE}/HASIL/alpha_star_formality.json"),
    ("Pendukung/alpha_star_aaker.json", "05_Rerun_Tabel",
     f"{REMOTE}/HASIL/alpha_star_aaker.json"),
    ("Pendukung/alpha_star_formality_legacy_content.json", "05_Rerun_Tabel",
     f"{REMOTE}/HASIL/alpha_star_formality_legacy_content.json"),
    ("Pendukung/calibration_formality.json", "05_Rerun_Tabel",
     f"{REMOTE}/HASIL/calibration_formality.json"),
    ("Pendukung/calibration_aaker.json", "05_Rerun_Tabel",
     f"{REMOTE}/HASIL/calibration_aaker.json"),
    ("Pendukung/split_manifest_formality.json", "05_Rerun_Tabel",
     f"{REMOTE}/HASIL/split_manifest_formality.json"),
    ("Pendukung/split_manifest_aaker.json", "05_Rerun_Tabel",
     f"{REMOTE}/HASIL/split_manifest_aaker.json"),
    # 08 laporan revisi
    ("SURAT_BALASAN_REVIEWER.md", "08_Laporan_Revisi",
     f"{REMOTE}/LAPORAN_REVISI/SURAT_BALASAN_REVIEWER.md"),
    ("LAPORAN_PERBAIKAN_REVISI.md", "08_Laporan_Revisi",
     f"{REMOTE}/LAPORAN_REVISI/LAPORAN_PERBAIKAN_REVISI.md"),
    ("TABEL_STATUS_BUTIR.md", "08_Laporan_Revisi",
     f"{REMOTE}/LAPORAN_REVISI/TABEL_STATUS_BUTIR.md"),
    ("VERIFIKASI_ANGKA.md", "08_Laporan_Revisi",
     f"{REMOTE}/LAPORAN_REVISI/VERIFIKASI_ANGKA.md"),
    ("README.md", "08_Laporan_Revisi", f"{REMOTE}/LAPORAN_REVISI/README.md"),
    ("Skrip/verifikasi_angka.py", "08_Laporan_Revisi",
     f"{REMOTE}/LAPORAN_REVISI/verifikasi_angka.py"),
    ("Skrip/build_dokumen.py", "08_Laporan_Revisi",
     f"{REMOTE}/LAPORAN_REVISI/build_dokumen.py"),
    ("Skrip/jawaban_en.py", "08_Laporan_Revisi",
     f"{REMOTE}/LAPORAN_REVISI/jawaban_en.py"),
    ("sumber/JCCE-10619_Mapping_Reviewer_Comments_v1.xlsx", "08_Laporan_Revisi",
     f"{REMOTE}/LAPORAN_REVISI/sumber/JCCE-10619_Mapping_Reviewer_Comments_v1.xlsx"),
]

PETA_README = """# JCCE-10619 — Berkas Revisi Pertama

Arsip berkas yang terkait naskah *Retrieval Strategies for Indonesian Text Style Transfer using a
Large Language Model* (JCCE-10619, putaran revisi pertama).

Disalin pada {tanggal} dari `G:\\My Drive\\...\\1st Round Review` dan
`C:\\Devs\\Code\\Python\\JCCE-First Revision-From Remote`.

## Peta isi

| Folder | Isi |
|---|---|
| `01_Naskah` | naskah versi pertama yang direview dan berkas komentar reviewer |
| `02_Pemetaan_Reviewer` | ketiga workbook pemetaan, kode pembuatnya, dan skrip pemeriksanya |
| `03_Perencanaan` | rencana perbaikan, protokol split, spesifikasi rerun, catatan klaim versus implementasi, perubahan naskah, audit sitasi |
| `04_Rerun_Dokumen` | protokol rerun, runbook operasional, run log, laporan akhir 12 bagian, aturan agen, requirements |
| `05_Rerun_Tabel` | 18 tabel hasil, sampel evaluasi manusia, berkas pendukung (alpha, kalibrasi, manifes split), dan keluaran per sampel |
| `06_Rerun_Skrip` | 18 skrip pelaksana rerun |
| `07_Rerun_Log` | log pelatihan, uji skala kecil, sapuan alpha, evaluasi, dan manifes peluncuran |
| `08_Laporan_Revisi` | surat balasan reviewer, laporan perbaikan, tabel status butir, hasil verifikasi angka, beserta skripnya |

## Angka kunci hasil rerun

| Hal | Nilai |
|---|---|
| Split STIF baru | 2.498 / 500 / 1.500 / 500, pasangan utuh 100% (sebelumnya 35,7%) |
| Split Aaker baru | 62.052 baris setelah membuang 13.704 duplikat (18,1%); 24.820 / 6.205 / 18.617 / 6.205 |
| Gerbang kebocoran | split lama gagal (duplikat lintas split sampai 503), split baru lulus tanpa duplikat |
| Akurasi gaya STIF informal | 0,904 sampai 0,988 pada seluruh metode retrieval |
| Akurasi gaya STIF formal | 0,048 sampai 0,252, di bawah aras acak |
| Pemertahanan isi | seluruh metode retrieval mengalahkan zero-shot pada kedua arah |
| Kalibrasi classifier Aaker | suhu 2,6779; ECE 0,0739 turun ke 0,0437 |
| Alpha terpilih | informal 0,7; competence 0,3; excitement 0,5; formal tidak ditetapkan |
| Median PPL STIF | 191,45 (formal) dan 226,18 (informal), sedangkan rerata 1.436 dan 1.081 |
| Proporsi keluaran degenerate | 12,80% dan 14,74% untuk STIF, 5,86% untuk Aaker |
| Uji signifikansi | 342 pasangan sebanding STIF dan 90 Aaker, selang bootstrap berpasangan 95% |
| Kepekaan k | gaya bermakna pada 1 dari 18 pasangan, isi pada 10 dari 18 |

## Keadaan pekerjaan

| Status | Jumlah butir |
|---|---|
| Selesai dengan bukti | 17 |
| Menunggu penyuntingan naskah | 17 |
| Tanpa tindakan | 4 |

Surat balasan menyatakan perubahan yang harus benar-benar ada pada naskah, jadi belum boleh dikirim
sebelum 17 butir yang menunggu penyuntingan selesai. Rinciannya di `08_Laporan_Revisi`.

## Yang tidak disalin ke arsip ini

Berkas besar tetap di `C:\\Devs\\Code\\Python\\JCCE-First Revision-From Remote`:

| Item | Ukuran | Alasan |
|---|---|---|
| Folder model dan data tiap repo | 2,4 GB | bukan dokumen, dan dapat dibangun ulang dari split |
| `ARSIP/` | 62 MB | cadangan hasil generasi yang sama dengan yang sudah diarsipkan |
| `HASIL/keluaran_generasi/` | 23 MB | keluaran generasi mentah, sudah diringkas pada berkas per sampel |
| Log peluncuran berukuran besar | 12 MB | hanya bilah kemajuan, bukan isi hasil |
| `__pycache__` | kecil | berkas sementara Python |

Keluaran per sampel yang menjadi materi suplemen (58 berkas, 19.500 baris, 24 MB) **disalin** ke
`05_Rerun_Tabel/Per_Sampel/` karena setiap angka pada naskah dan surat balasan dapat dilacak ke sana.
"""


def salin(daftar, tujuan, kering=False):
    hasil = []
    for nama, folder, sumber in daftar:
        if not os.path.exists(sumber):
            hasil.append(("HILANG", nama, sumber, 0))
            continue
        p = os.path.join(tujuan, folder, nama)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not kering:
            try:
                shutil.copy2(sumber, p)
            except PermissionError:
                # biasanya karena berkas tujuan sedang dibuka aplikasi lain
                hasil.append(("TERKUNCI", os.path.join(folder, nama), sumber,
                              os.path.getsize(sumber)))
                continue
        hasil.append(("ok", os.path.join(folder, nama), sumber, os.path.getsize(sumber)))
    return hasil


def daftar_berpola():
    """Tabel hasil, skrip rerun, dan log: diambil dengan pola, bukan satu per satu."""
    d = []
    for f in sorted(os.listdir(REMOTE)):
        if f.startswith("TABEL_") and f.endswith(".csv"):
            d.append((f, "05_Rerun_Tabel", os.path.join(REMOTE, f)))
        elif f.startswith("EVAL_MANUSIA_") and f.endswith(".csv"):
            d.append((f, "05_Rerun_Tabel", os.path.join(REMOTE, f)))
    for f in sorted(os.listdir(f"{REMOTE}/scripts")):
        if f.endswith(".py"):
            d.append((f, "06_Rerun_Skrip", f"{REMOTE}/scripts/{f}"))
    for f in sorted(os.listdir(REMOTE)):
        if f.endswith(".log") or f.endswith(".err"):
            d.append((f, "07_Rerun_Log", os.path.join(REMOTE, f)))
    for f in sorted(os.listdir(f"{REMOTE}/LOGS")):
        if f.endswith(".json") or (f.endswith(".log") and os.path.getsize(
                os.path.join(REMOTE, "LOGS", f)) < 1_000_000):
            d.append((f, "07_Rerun_Log", f"{REMOTE}/LOGS/{f}"))
    # keluaran per sampel
    for korpus, folder in [("STIF", "fewshot_formality"), ("AAKER", "fewshot_aaker")]:
        p = f"{REMOTE}/{folder}/evaluation_result_v2/google_gemma-3-4b-it"
        for f in sorted(os.listdir(p)):
            if f.startswith("evaluated_v2_") and f.endswith("_seed42_results.csv"):
                d.append((f, "05_Rerun_Tabel/Per_Sampel", os.path.join(p, f)))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tujuan", default="C:/Obsidian/Notes/S3/JCCE")
    ap.add_argument("--kering", action="store_true", help="hanya tampilkan rencana salinan")
    args = ap.parse_args()

    if not os.path.isdir(args.tujuan):
        os.makedirs(args.tujuan, exist_ok=True)
    daftar = RENCANA + daftar_berpola()
    hasil = salin(daftar, args.tujuan, args.kering)

    hilang = [h for h in hasil if h[0] == "HILANG"]
    terkunci = [h for h in hasil if h[0] == "TERKUNCI"]
    ok = [h for h in hasil if h[0] == "ok"]
    total = sum(h[3] for h in ok)

    per_folder = {}
    for _, nama, _, ukuran in ok:
        f = nama.split(os.sep)[0]
        a, b = per_folder.get(f, (0, 0))
        per_folder[f] = (a + 1, b + ukuran)
    print(f"{'folder':<26} {'berkas':>7} {'MB':>9}")
    for f in sorted(per_folder):
        n, s = per_folder[f]
        print(f"{f:<26} {n:>7} {s/1e6:>9.2f}")
    print(f"\ntotal {len(ok)} berkas, {total/1e6:.1f} MB")
    if hilang:
        print(f"\n{len(hilang)} berkas sumber tidak ditemukan:")
        for _, nama, sumber, _ in hilang:
            print(f"   {nama}  <-  {sumber}")
    if terkunci:
        print(f"\n{len(terkunci)} berkas tidak dapat diperbarui karena sedang dipakai aplikasi lain:")
        for _, nama, _, _ in terkunci:
            print(f"   {nama}")
        print("   tutup aplikasi yang memakainya lalu jalankan ulang skrip ini")

    if not args.kering:
        import datetime
        readme = PETA_README.format(tanggal=datetime.date.today().isoformat())
        with open(os.path.join(args.tujuan, "README.md"), "w", encoding="utf-8") as fh:
            fh.write(readme)
        print(f"\nREADME.md ditulis di {args.tujuan}")
    else:
        print("\nmode kering: tidak ada berkas yang disalin")
    return 1 if hilang else 0


if __name__ == "__main__":
    sys.exit(main())
