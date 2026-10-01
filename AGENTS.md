# Instruksi Proyek: JCCE-First Revision

Folder ini adalah bundel rerun eksperimen untuk manuscript JCCE-10619 yang menerima major
revision. Tugas agen adalah menjalankan ulang seluruh eksperimen dan menghasilkan angka baru.

## Tindakan pertama

Baca `PROTOKOL_RERUN.md` dari awal sampai akhir sebelum menjalankan perintah apa pun. Dokumen itu
memuat 11 langkah kerja, perintah konkret, patch kode, dan gerbang pemeriksaan. Dokumen ini hanya
ringkasan; protokol yang berlaku.

Sebelum setiap peluncuran panjang dan setelah setiap proses selesai, ikuti `RUNBOOK_OPERASIONAL.md`.
Dokumen itu mengatur ritme kerja: daftar periksa pra-peluncuran, cara memantau, cara mengarsipkan
hasil satu tahap sebelum tahap berikutnya, dan prompt siap tempel untuk melanjutkan agen.

Setelah membacanya, jalankan pemeriksaan kesiapan:

```
python scripts/preflight.py
```

Jangan memulai langkah mana pun sebelum pemeriksaan itu tidak lagi melaporkan kegagalan.

## Aturan yang tidak boleh dilanggar

1. **Jangan menyunting manuscript.** Tugas agen hanya menjalankan eksperimen dan menyusun tabel
   angka. Penulisan naskah dilakukan manusia.
2. **Jangan mengarang angka.** Setiap angka harus berasal dari berkas yang benar-benar dihasilkan
   perintah, dan sebutkan jalur berkasnya.
3. **Jangan melewati gerbang pemeriksaan.** Setiap langkah punya pemeriksaan. Bila gagal,
   hentikan langkah itu, laporkan, dan jangan lanjut.
4. **Jangan menyentuh berkas referensi.** Folder `*_splits` tanpa akhiran `_v2`,
   `evaluation_result`, `model_results_dir`, dan seluruh isi `DOKUMEN_PENDUKUNG` bersifat
   referensi pembanding. Jangan diubah dan jangan dihapus.
5. **Jangan mengubah hal pada bagian 18 protokol**, termasuk model, kuantisasi, parameter dekode,
   dan template prompt.
6. **Catat setiap langkah di `RUN_LOG.md`**: perintah, waktu mulai dan selesai, keluaran penting,
   dan status.
7. **Bila gagal, jangan menambal dengan perkiraan.** Laporkan perintah, pesan galat, dan berkas
   yang terlibat.

## Cara bekerja di editor ini

- **Jangan membaca seluruh folder hasil ke dalam konteks.** Folder `evaluation_result` dan
  `model_results_dir` memuat ratusan berkas CSV berisi ribuan baris. Pakai script di `scripts/`
  yang sudah meringkasnya, dan hanya buka berkas tertentu bila perlu.
- **Jalankan tugas panjang lewat `scripts/launch_detached.py`, bukan lewat perintah shell.** Generasi
  per korpus memerlukan 4 sampai 15 jam, jadi prosesnya harus hidup terlepas dari giliran agen.

  ```bash
  python scripts/launch_detached.py --nama aaker_step6 --cwd ../fewshot_aaker -- python main.py
  python scripts/launch_detached.py --status --nama aaker_step6
  ```

  Peluncur itu memisahkan stdout dan stderr ke dua berkas, melepaskan proses dari sesi ini, mencatat
  PID dan SHA-256 berkas config ke `LOGS/detached_<nama>.json`, lalu menunggu beberapa detik dan
  memverifikasi bahwa prosesnya benar-benar hidup dan lognya sudah bertambah. Bila verifikasi gagal,
  ia mencetak isi stderr dan keluar dengan kode bukan nol.

  Alasannya penting: pola `Start-Process -RedirectStandardOutput/-RedirectStandardError` pada
  PowerShell di mesin ini pernah gagal tanpa jejak. Proses mati seketika, kedua berkas log tetap
  0 byte, tidak ada berkas hasil, dan tidak ada pesan galat yang bisa dibaca. Jangan memakai pola
  itu.

  Catat PID ke `RUN_LOG.md`. Periksa daftar proses sebelum meluncurkan yang baru, karena dua
  proses generasi di satu GPU akan kehabisan memori dan keduanya batal.
- **Saat proses panjang berjalan, jawab pertanyaan agen dengan instruksi ringan.** Proses
  generasi terpisah dari giliran agen, sehingga pesan baru tidak mematikannya. Tetapi pesan baru
  memang menghentikan giliran agen yang sedang berjalan. Jadi jangan minta agen mengubah
  konfigurasi, meluncurkan proses lain, atau menjalankan langkah berikutnya selama generasi
  berjalan. Mintalah agen mencatat keputusan ke `RUN_LOG.md` lalu kembali memantau log.
- **Untuk memeriksa keadaan tanpa menyentuh giliran agen**, jalankan `python scripts/status.py`
  dari terminal biasa. Script itu menampilkan keadaan konfigurasi kedua repo, ukuran dan ekor log
  terbaru, serta daftar proses Python yang hidup.
- **Satu langkah, satu laporan.** Setelah setiap langkah selesai, perbarui `RUN_LOG.md` sebelum
  melanjutkan.
- **Perhatikan waktu, ukur dulu jangan menebak.** Konfigurasi pertama selalu paling lambat karena
  memuat model dan membangun indeks retrieval; laju stabil baru terlihat sejak konfigurasi kedua.
  Pada mesin ini laju stabil sekitar 3,3 detik per sampel untuk korpus Aaker dan 2,2 detik per
  sampel untuk korpus formality. Struktur yang dipakai adalah satu seed (42), sehingga sisa
  pekerjaan setelah proses formality dihentikan sekitar 16 jam. Bandingkan dengan
  `RUNBOOK_OPERASIONAL.md` bagian 6.
- **Satu seed, jadi ukuran ketidakpastian adalah bootstrap atas butir uji.** Jangan menulis di
  naskah bahwa setiap konfigurasi diulang beberapa seed. Saat mengevaluasi dan menghitung statistik,
  pakai `--patterns "*_seed42*"` atau `--only-seed 42` supaya seed lain tidak tercampur.

## Perintah yang paling sering dipakai

| Kebutuhan | Perintah |
|---|---|
| Pemeriksaan kesiapan | `python scripts/preflight.py` |
| Keadaan pekerjaan | `python scripts/status.py` |
| Luncurkan tugas panjang | `python scripts/launch_detached.py --nama <nama> --cwd <repo> -- python <script>` |
| Periksa run terlepas | `python scripts/launch_detached.py --status --nama <nama>` |
| Verifikasi split | `python scripts/verify_splits.py --dir <folder> --gate` |
| Gerbang hasil uji jalur | `python scripts/check_smoke_output.py --dir <folder hasil>` |
| Evaluasi lengkap | `python scripts/evaluate_results.py --help` |
| Statistik ringkas | `python scripts/report_metrics.py --dir <folder> --only-seed 42 --out <csv>` |
| Uji signifikansi | `python scripts/bootstrap_significance.py --dir <folder> --only-seed 42 --metric <kolom>` |
| Metrik replikasi templat | `python scripts/replication_metric.py --dir <folder> --only-seed 42 --from-column` |
| Pemilihan alpha | `python scripts/select_alpha_dev.py --dir <folder alpha_dev>` |
| Kalibrasi classifier | `python scripts/calibrate_classifier.py --help` |

## Hasil akhir yang diharapkan

Tiga hal, semuanya di akar folder ini:

1. Folder `HASIL/` berisi tabel CSV, manifes, dan keluaran generasi per sampel, sesuai bagian 14
   protokol.
2. `LAPORAN_AKHIR.md` dengan dua belas bagian sesuai bagian 16 protokol.
3. `RUN_LOG.md` yang sudah terisi lengkap.

## Konteks yang tidak perlu digali ulang

Folder `DOKUMEN_PENDUKUNG/` sudah memuat seluruh analisis yang mendasari protokol ini: protokol
split kedua korpus, audit perbandingan klaim manuscript dengan implementasi, spesifikasi lengkap,
pemetaan 38 butir komentar reviewer ke kategori dan effort, serta tabel bukti temuan. Baca bila
butuh memahami alasan sebuah langkah, tetapi jangan mengubahnya dan jangan mengulang analisisnya.
