# Runbook Operasional

Panduan langkah demi langkah untuk manusia yang mengawal agen. Protokol teknis ada di
`PROTOKOL_RERUN.md`; dokumen ini mengatur ritme kerja: kapan meluncurkan, kapan memeriksa, dan apa
yang dilakukan setelah satu proses selesai.

Semua perintah ditulis satu baris agar aman dijalankan pada PowerShell maupun shell POSIX.

---

## 1. Siklus kerja

Setiap tahap panjang mengikuti pola yang sama:

```
SEBELUM   periksa konfigurasi dan proses   -> pastikan tidak ada yang tertinggal
SELAMA    jangan kirim instruksi berat     -> pantau dengan status.py
SESUDAH   arsipkan, catat, pulihkan config -> baru boleh lanjut ke tahap berikutnya
```

Kesalahan yang paling mahal bukan pada kode, melainkan pada peralihan antar tahap: konfigurasi
tertinggal dalam keadaan uji, hasil satu tahap tertimpa tahap berikutnya, atau proses lama masih
hidup sehingga dua generasi berebut GPU.

---

## 1.5 Setelan lingkungan wajib di mesin ini

Fakta berikut sudah ditemukan dan diverifikasi pada mesin remote. Nilainya harus ada sebelum setiap
peluncuran, karena kegagalannya baru terlihat saat proses berjalan, bukan saat mulai.

| Setelan | Nilai | Akibat bila tidak ada |
|---|---|---|
| `PYTHONIOENCODING` | `utf-8` | `UnicodeEncodeError: 'charmap' codec can't encode character` ketika keluaran model memuat emoji dan stdout dialihkan ke berkas |
| `PYTHONUTF8` | `1` | sama, mengaktifkan mode UTF-8 untuk seluruh pembukaan berkas |
| `HF_HUB_DISABLE_SYMLINKS` | `1` | `OSError: [WinError 1314] A required privilege is not held by the client` saat unduhan model, karena mesin ini tidak mengizinkan symlink cache |
| `HF_TOKEN` | token akun pemilik | unduhan model gagal. `setx` baru berlaku pada proses yang dibuat setelah Zed di-restart |

Batas versi pustaka yang sudah terbukti bermasalah di mesin ini:

- `transformers` 5.8.0 menolak kwarg `generate(generator=...)` yang masih diterima pada 4.x, sehingga
  kedua pipeline memakai `torch.manual_seed(seed)` tepat sebelum `generate()`. Determinisme sudah
  diverifikasi: seed sama menghasilkan teks identik, seed berbeda menghasilkan teks berbeda.
- `rank_bm25` tidak menyediakan `__version__`, sehingga `preflight.py` memakai
  `importlib.metadata.version` sebagai cadangan.
- Keluaran emoji membuat stdout yang dialihkan ke berkas gagal pada codec cp1252.

Ketiga variabel itu kini disetel otomatis oleh `scripts/launch_detached.py` pada proses anak, dan
nilainya dicatat di `LOGS/detached_<nama>.json`, sehingga peluncuran tidak lagi bergantung pada sesi
yang sudah menyetelnya. Nilai yang sudah ada di lingkungan pemanggil tidak ditimpa.

Kartu grafis mesin ini 12,0 GB, sedangkan protokol mensyaratkan 16 GB. Penyimpangan ini disetujui
manusia dan harus dilaporkan pada bagian Kendala laporan akhir.

Bila evaluasi langkah 8 kehabisan memori, jalankan dua tahap. Tahap pertama evaluasi penuh dengan
`--skip-fluency`, tahap kedua menghitung fluency saja dengan `--only-fluency` pada folder hasil tahap
pertama, sehingga puncak pemakaian memori tahap kedua hanya berasal dari model fluency. Tahap kedua
aman diulang karena berkas yang sudah lengkap dilewati. Jangan memakai `--legacy-eval-dir` untuk
menyalin PPL lama, karena berkas lama tidak memuat penanda seed sehingga jumlah barisnya berbeda.

---

## 2. Sebelum setiap peluncuran panjang

Jalankan dari terminal biasa, bukan dari panel agen:

```powershell
cd "D:\FILEMAHASISWA\Fikri Hasani Folder\JCCE-First Revision"
python scripts\status.py
```

Yang harus bersih sebelum lanjut:

- [ ] Tidak ada peringatan pada bagian KONFIGURASI. Peringatan yang mungkin muncul:
      `split_dir` tidak memuat `_v2` berarti masih memakai split lama yang bocor,
      `split_dir` memuat `dev` berarti masih dalam keadaan pemilihan alpha,
      `num_samples` bukan nilai penuh, metode `random` atau `zero_shot` belum ada,
      `run_seeds` belum ada.
- [ ] Tidak ada proses Python lain yang masih hidup. Dua generasi di satu GPU akan kehabisan memori
      dan keduanya batal.
- [ ] Direktori hasil yang terbaca dari config sudah benar. Ini penting karena sapuan alpha-dev dan
      run utama dapat memakai direktori berbeda, atau bertabrakan bila direktori dan namanya sama.
- [ ] `skip_existing` disetel `true` bila melanjutkan pekerjaan yang pernah terhenti, supaya
      konfigurasi yang sudah selesai tidak dihitung ulang.
- [ ] GPU dalam keadaan lega. Tutup aplikasi lain yang memakai VRAM.
- [ ] Peluncuran memakai `python scripts/launch_detached.py`, bukan perintah shell biasa. Peluncur
      itu memverifikasi sendiri bahwa prosesnya hidup dan lognya sudah bertambah, lalu mencatat PID
      dan SHA-256 berkas config ke `LOGS/detached_<nama>.json`.

---

## 3. Saat proses berjalan

- [ ] Jangan mengirim instruksi berat ke agen. Instruksi ringan seperti mencatat ke `RUN_LOG.md`
      aman, tetapi mengubah konfigurasi, meluncurkan proses lain, atau memulai langkah berikutnya
      tidak.
- [ ] Pantau dengan `python scripts\status.py` dari terminal biasa, bukan dari panel agen.
- [ ] Ukuran berkas log harus bertambah antar pemanggilan. Bila diam lebih dari 10 menit sementara
      GPU juga diam, periksa PID dan CPU-nya.
- [ ] Berkas hasil baru muncul setiap satu konfigurasi selesai. Jumlahnya adalah penanda kemajuan
      yang paling andal, karena pipeline menulis hasil per konfigurasi, bukan per sampel.
- [ ] Pola nama berkas: target mendahului seed, jadi pola `*_seed42_informal*` tidak akan cocok.
      Bentuk namanya `STIF_<target>_fewshot_<metode>[_alpha<a>]_<k>_seed42_results.csv` untuk
      formality dan `AAKER_<target>_fewshot_<metode>[_alpha<a>]_<k>_seed42_results.csv` untuk Aaker.
      Pakai `*informal*seed42*results.csv` untuk informal, dan `*seed42*results.csv` untuk menghitung
      seluruh berkas satu korpus.
- [ ] Agen di panel editor bekerja per giliran, sehingga ia tidak dapat memantau sendiri selama
      berjam-jam. Setiap laporan membutuhkan pesan baru dari manusia. Karena proses generasinya
      terlepas, tidak ada pekerjaan yang hilang, tetapi GPU menganggur selama jeda itu. Karena itu
      satukan beberapa langkah pendek dalam satu pesan supaya jumlah jeda berkurang.
- [ ] Perkiraan waktu perlu memperhitungkan bahwa `zero_shot` berjalan hampir dua kali lebih lambat
      daripada konfigurasi lain, karena tanpa contoh keluaran model cenderung lebih panjang.

---

## 4. Setelah proses selesai

Urutannya seperti ini. Jangan melompati langkah 1 sampai 3.

### Langkah 1. Pastikan benar-benar selesai, bukan berhenti di tengah

```powershell
cd "D:\FILEMAHASISWA\Fikri Hasani Folder\JCCE-First Revision"
python scripts\status.py
```

Tiga tanda selesai:

- Jumlah berkas hasil bertambah sesuai jumlah konfigurasi yang diharapkan. Sapuan alpha-dev korpus
  Aaker adalah 10 konfigurasi, yaitu 5 nilai alpha dikali 2 target.
- Baris terakhir log internal berisi `ALL FEW-SHOT EXPERIMENTS COMPLETED`. Log internal ada di
  `fewshot_aaker\outputs\fewshot_logs\google_gemma-3-4b-it\`, berkas dengan tanggal terbaru.
- Tidak ada lagi proses Python yang hidup di bagian PROSES PYTHON.

Bila proses berhenti di tengah, jumlah berkas hasil lebih kecil dari yang diharapkan. Jangan
meluncurkan ulang dengan `skip_existing` bernilai `false`, karena konfigurasi yang sudah selesai
akan dihitung ulang dari nol.

### Langkah 2. Arsipkan hasil tahap ini sebelum tahap berikutnya menyentuhnya

Ini langkah yang paling mudah terlupa dan akibatnya paling merugikan. Nama berkas hasil tidak
memuat penanda split, sehingga hasil sapuan alpha-dev dan hasil run utama dapat bertabrakan bila
berada di direktori yang sama. Arsipkan dulu:

```powershell
New-Item -ItemType Directory -Force -Path "ARSIP\alphadev_aaker" | Out-Null
Copy-Item "fewshot_aaker\model_results_dir\google_gemma-3-4b-it\*_results.csv" "ARSIP\alphadev_aaker\" -Force
Copy-Item "fewshot_aaker\outputs\fewshot_logs\google_gemma-3-4b-it\*.log" "ARSIP\alphadev_aaker\" -Force
Copy-Item "fewshot_aaker\fewshot_config.json" "ARSIP\alphadev_aaker\config_saat_alphadev.json" -Force
Get-ChildItem "ARSIP\alphadev_aaker" | Measure-Object
```

Direktori sumber pada perintah di atas harus disesuaikan bila config menunjuk direktori hasil yang
berbeda. Bagian BERKAS HASIL pada `status.py` menyebutkan direktori yang sedang dipakai.

### Langkah 3. Catat ke `RUN_LOG.md`

Isi yang perlu tercatat: perintah yang dijalankan, PID, waktu mulai dan selesai, durasi nyata per
konfigurasi, laju detik per sampel, jumlah konfigurasi yang selesai, dan jumlah `retrieval_fallback`
serta keluaran `ERROR`. Laju detik per sampel itu penting, karena seluruh anggaran waktu di protokol
harus disesuaikan dengan angka nyata dari mesin ini.

### Langkah 4. Evaluasi hasil sapuan alpha-dev, tanpa fluency

Kriteria pemilihan alpha hanya memakai akurasi gaya dan content preservation, sehingga fluency
tidak perlu dihitung pada tahap ini. Melewatinya menghemat beberapa jam:

```powershell
python scripts\evaluate_results.py --results ../fewshot_aaker/model_results_dir/google_gemma-3-4b-it --classifier ../fewshot_aaker/style_classifier --out ../fewshot_aaker/evaluation_result_alphadev/google_gemma-3-4b-it --calibration ../fewshot_aaker/style_classifier/calibration.json --encoder LaBSE=sentence-transformers/LaBSE --skip-fluency
```

Lalu pilih alpha:

```powershell
python scripts\select_alpha_dev.py --dir ../fewshot_aaker/evaluation_result_alphadev/google_gemma-3-4b-it --content-col content_preservation_LaBSE --out ../fewshot_aaker/alpha_star.json
```

### Langkah 5. Periksa keputusan alpha sebelum menyetujuinya

Yang perlu kamu lihat pada keluaran `select_alpha_dev.py`: apakah selisih kriteria antara alpha
teratas dan alpha kedua cukup besar untuk disebut terpilih, atau hanya berbeda di digit terakhir.
Bila selisihnya kecil, jangan biarkan agen menulis "optimal" tanpa kualifikasi. Minta ia menyajikan
kurva lengkap dan menyatakan bahwa rentang itu tidak terbedakan, lalu menyerahkan keputusan akhir
ke uji signifikansi berpasangan pada langkah 9.

### Langkah 6. Pulihkan konfigurasi ke keadaan penuh, lalu jalankan gate

```powershell
python scripts\status.py
```

Bagian KONFIGURASI harus bersih dari peringatan sebelum run utama diluncurkan. Setelah itu perintahkan
agen menempelkan isi `fewshot_config.json` yang akan dipakai run utama, dan setujui peluncuran hanya
setelah kamu melihat sendiri bahwa `split_dir` menunjuk `_v2` tanpa kata `dev`, dan
`retrieval_methods` sudah memuat `random` serta `zero_shot`.

### Langkah 7. Luncurkan run utama, satu korpus pada satu waktu

Jangan menjalankan korpus Aaker dan korpus formality secara bersamaan. Satu GPU, satu proses.

---

## 5. Prompt siap tempel

**Melanjutkan agen setelah proses selesai:**

```
Proses sebelumnya sudah selesai. Sebelum melakukan apa pun, laporkan dulu: jumlah berkas hasil
yang dihasilkan, apakah baris terakhir log internal berbunyi ALL FEW-SHOT EXPERIMENTS COMPLETED,
dan apakah masih ada proses python yang hidup.

Setelah itu lakukan berurutan dan berhenti setelah tiap langkah untuk melapor:
1. Catat ke RUN_LOG.md: perintah, PID, waktu mulai dan selesai, durasi per konfigurasi, laju detik
   per sampel, jumlah fallback, jumlah keluaran ERROR.
2. Jalankan evaluate_results.py pada hasil alphadev dengan --skip-fluency, karena kriteria
   pemilihan alpha tidak memakai fluency.
3. Jalankan select_alpha_dev.py dengan --content-col content_preservation_LaBSE.
4. Laporkan kurva sapuan lengkap dan alpha terpilih untuk setiap target.

Jangan meluncurkan generasi baru, jangan mengubah konfigurasi, dan jangan mulai langkah 6 sebelum
aku menyetujui hasil pemilihan alpha.

Ada satu hal yang harus kamu lakukan lebih dulu: arsipkan seluruh berkas hasil tahap ini ke folder
ARSIP\alphadev_aaker beserta log internal dan salinan fewshot_config.json, karena nama berkas hasil
tidak memuat penanda split sehingga run utama dapat menimpanya.
```

**Menyetujui peluncuran run utama:**

```
Setujui peluncuran run utama, dengan syarat berikut sudah kamu penuhi dan laporkan buktinya:
1. Isi fewshot_config.json ditempel di laporan, dengan split_dir menunjuk _v2 tanpa kata dev,
   retrieval_methods memuat random dan zero_shot, dan run_seeds berisi [42] saja.
2. Tidak ada proses python lain yang hidup.
3. Perintah peluncuran memakai scripts/launch_detached.py, mencetak PID, dan PID itu langsung
   dicatat ke RUN_LOG.md bersama SHA-256 config dari manifest.
4. skip_existing bernilai true bila melanjutkan pekerjaan yang pernah terhenti.
```

**Menjawab pertanyaan alpha:**

```
Setuju memakai LaBSE sebagai kolom kriteria, dan pakai LaBSE juga untuk korpus lain agar
kriterianya konsisten. Bila selisih kriteria antar alpha kecil, jangan sebut alpha terpilih sebagai
optimal tanpa kualifikasi: sajikan kurva lengkap, nyatakan bahwa rentang tersebut tidak terbedakan
pada target itu, dan bahwa pemilihan mengikuti kriteria yang ditetapkan lebih dahulu. Uji
signifikansi berpasangan pada langkah 9 yang menentukan. Catat keputusan ini dan alasan penggantian
kolom kriteria di RUN_LOG.md, karena itu harus diungkapkan di manuscript.
```

---

## 6. Anggaran waktu berdasarkan laju terukur

Laju pada mesin ini tidak seragam. Konfigurasi pertama selalu paling lambat, karena memuat model dan
membangun indeks retrieval sekali di awal, lalu laju stabil. Karena itu jangan menyimpulkan anggaran
dari konfigurasi pertama saja.

Pengukuran dari sapuan alpha Aaker, 26 September 2026, 5.000 generasi dalam 4 jam 58 menit 37 detik:

| Konfigurasi | Durasi | Laju |
|---|---|---|
| competence alpha 0,1 | 43:16 | 5,19 detik per sampel |
| competence alpha 0,3 | 37:04 | 4,45 |
| competence alpha 0,5 | 28:16 | 3,39 |
| competence alpha 0,7 | 24:14 | 2,91 |
| competence alpha 0,9 | 23:42 | 2,84 |
| excitement, kelima alpha | 27:13 sampai 30:20 | 3,27 sampai 3,64 |

Laju stabil sekitar 3,3 detik per sampel, setara dengan 3,79 detik per sampel pada run Juni. Jadi
mesin ini tidak lebih lambat dari mesin run asli, dan estimasi awal yang mengalikan seluruh protokol
dengan 1,7 kali terlalu tinggi. Rata-rata keseluruhan 3,58 detik per sampel.

Laju korpus formality dari sapuan alpha 25 September: 2,06 detik per sampel pada konfigurasi 250
sampel.

Perkiraan sisa pekerjaan untuk struktur yang dipakai, yaitu satu seed (42) saja:

| Tahap | Berkas | Generasi | Laju | Perkiraan |
|---|---|---|---|---|
| formality, target informal saja (target formal sudah selesai) | 19 | 4.750 | 2,2 detik | 2,9 jam |
| Aaker, 10 konfigurasi per target, dua target | 20 | 10.000 | 3,3 detik | 9,7 jam |
| Evaluasi 58 berkas termasuk fluency | | 19.500 baris | | 1 sampai 1,5 jam |
| Statistik, sampel manusia, pengepakan | | | | 2 jam |
| **Sisa setelah proses formality dihentikan** | | | | **sekitar 16 jam** |

Catatan tentang pilihan seed. Satu seed dipilih karena waktu. Konsekuensinya harus diungkapkan di
naskah dan di surat balasan: varians antar-jalan tidak diukur, sehingga ukuran ketidakpastian yang
dilaporkan adalah bootstrap berpasangan atas butir uji, bukan simpangan baku antar-seed. Pernyataan
bahwa setiap konfigurasi diulang beberapa seed harus dihapus dari naskah. Kelebihan struktur ini:
selisih pada klaim utama jauh melampaui derau butir, sehingga kesimpulannya tidak bergantung pada
jumlah seed.

Bila suatu saat varians antar-jalan diminta kembali, berkas seed 43 dan 44 yang sudah dihasilkan
masih tersimpan di `ARSIP/seed43_44_formality`, dan evaluasi serta statistiknya dapat dijalankan
tanpa membangkitkan ulang teksnya.

Bila waktu menjadi kendala, pemotongan berikutnya adalah metode `random` pada k lebih dari satu,
lalu sensitivity k. Pemotongan ulangan seed tidak lagi berlaku karena strukturnya sudah satu seed.
Setiap pemotongan harus dicatat di `RUN_LOG.md` dan diungkapkan sebagai limitasi.

Penyaring seed wajib dipakai sejak tahap evaluasi. `evaluate_results.py` menerima `--patterns`,
sedangkan `report_metrics.py`, `bootstrap_significance.py`, dan `replication_metric.py` menerima
`--only-seed`. Bila penyaring tidak dipakai sedangkan berkas dari beberapa seed berada di folder yang
sama, ketiga skrip terakhir memberi peringatan bahwa statistiknya mencampur seed.

---

## 7. Yang tidak boleh dilakukan

1. Meluncurkan dua proses generasi sekaligus pada satu GPU.
2. Mengirim instruksi yang mengubah konfigurasi atau memulai langkah baru saat proses panjang
   berjalan.
3. Meluncurkan tahap berikutnya sebelum hasil tahap sebelumnya diarsipkan.
4. Meluncurkan run utama tanpa memeriksa `status.py` terlebih dahulu.
5. Melanjutkan pekerjaan yang terhenti tanpa menyetel `skip_existing` menjadi `true`.
6. Melaporkan angka sebelum berkas hasilnya ada.
7. Menutup sesi Zed ketika agen sedang memantau proses. Prosesnya tetap hidup, tetapi kamu
   kehilangan visibilitas dan harus mengarahkan agen dari awal.
