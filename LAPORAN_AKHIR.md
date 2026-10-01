# LAPORAN AKHIR RERUN EKSPERIMEN — JCCE-10619 First Revision

Bundel: `D:\FILEMAHASISWA\Fikri Hasani Folder\JCCE-First Revision`
Tanggal laporan: 2026-09-28
Rujukan prosedur: `PROTOKOL_RERUN.md` bagian 0 sampai 18, `RUNBOOK_OPERASIONAL.md`

Seluruh angka pada laporan ini diambil dari berkas yang benar-benar dihasilkan perintah, dan
setiap angka disertai jalur berkas sumbernya. Tidak ada angka perkiraan. Tidak ada berkas di
folder referensi (`*_splits` lama, `evaluation_result`, `model_results_dir`, `DOKUMEN_PENDUKUNG`)
yang diubah atau dihapus. Naskah tidak disentuh.

---

## 1. Ringkasan eksekusi

Seluruh sebelas langkah protokol dijalankan. Dua bagian dinyatakan tidak dijalankan, dan alasannya
diuraikan pada bagiannya masing-masing:

| Langkah | Status | Catatan |
|---|---|---|
| 0 Prasyarat | dijalankan | 46/47 lulus; satu penyimpangan VRAM (bagian 11) |
| 1 Verifikasi split | dijalankan | kedua split baru LOLOS gerbang |
| 2 Patch konfigurasi dan pipeline | dijalankan | enam berkas, `py_compile` lulus |
| 3 Uji jalur sampel kecil | dijalankan | kedua korpus, gerbang 154 lulus / 0 gagal |
| 4 Latih classifier dan kalibrasi | dijalankan | kedua korpus |
| 5 Sapuan alpha dev set | dijalankan | formality + Aaker |
| 6 Run utama test set | dijalankan | seed 42 |
| 7 Ulangan untuk varians | **tidak dijalankan** | lihat bagian 7 |
| 8 Evaluasi lengkap | dijalankan | kedua korpus, 27 kolom |
| 9 Statistik dan metrik baru | dijalankan | kedua belas tabel uji dihitung ulang dengan skrip versi baru |
| 10 Sampel evaluasi manusia | dijalankan sebagian | hanya ekspor sampel, penilaian **tidak** dijalankan (bagian 10) |
| 11 Pengepakan keluaran | dijalankan | `HASIL/` dan laporan ini |

Waktu dinding keseluruhan: 2026-09-25 15:57 sampai 2026-09-28 (sekitar tiga hari kerja), dengan
rincian yang tercatat presisi sebagai berikut.

| Tahap | Waktu nyata | Sumber |
|---|---|---|
| Prasyarat selesai | 2026-09-25 15:57:46 | `preflight.json`; `RUN_LOG.md` bagian Prasyarat |
| Langkah 1 selesai | 2026-09-25 16:00:22 | `RUN_LOG.md` Langkah 1 |
| Langkah 2 selesai | 2026-09-25 21:20:58 | `RUN_LOG.md` Langkah 2 |
| Langkah 3 mulai | 2026-09-25 21:26:08 | `run_smoke_formality.log`, `run_smoke_aaker.log` |
| Langkah 4 mulai sampai selesai | 2026-09-25 21:54:26 → 22:08:22 (13 menit 56 detik) | `run_train_formality.log`, `run_train_brand.log` |
| Langkah 5 mulai | 2026-09-25 22:26:17 (formality), Aaker menyusul | `run_alphadev_formality.log`, `run_alphadev_aaker.log` |
| Langkah 6 (formality) | 2026-09-26 21:24:47 → 2026-09-27 09:06:55 (11 jam 42 menit dinding; generasi bersih 5 jam 48 menit) | `LOGS/formality_s42*.err.log`, log internal |
| Langkah 7 (Aaker) | 2026-09-27 10:19:48 → 20:43 (10 jam 23 menit) | `LOGS/aaker_s42.err.log` |
| Langkah 8 (Aaker) | 2026-09-27 21:03:31 → 21:57:39 (54 menit) | `LOGS/eval_v2_aaker.err.log` |
| Langkah 8 (formality) | 2026-09-27 21:58:40 → 22:38 (40 menit) | `LOGS/eval_v2_formality.err.log` |
| Langkah 9 | 2026-09-27 dan 2026-09-28 | `LOGS/uji_v2_recompute.log` |
| Langkah 10 dan 11 | 2026-09-28 | laporan ini |

Total generasi: 38 konfigurasi formality (9.500 sampel) + 20 konfigurasi Aaker (10.000 sampel)
= 19.500 sampel. Laju stabil 2,06 detik per sampel (formality) dan 3,3 detik per sampel (Aaker).

---

## 2. Lingkungan

| Item | Nilai |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 Ti |
| VRAM | 12.282 MiB (12,0 GB) total, 10.498 MiB bebas, driver 560.94 |
| Python | 3.14.4 |
| torch | 2.11.0+cu126 |
| transformers | 5.8.0 |
| sentence-transformers | 5.4.1 |
| scikit-learn / pandas / numpy | 1.8.0 / 3.0.2 / 2.4.4 |
| tqdm / rank-bm25 / scipy | 4.67.3 / 0.2.2 / 1.17.1 |
| accelerate / bitsandbytes / huggingface_hub | 1.13.0 / 0.49.2 / 1.13.0 |
| Model generasi | `google/gemma-3-4b-it` |
| Kuantisasi | 4-bit nf4, double quantization |
| Parameter dekode | temperature 0.7, top_p 0.9, max_new_tokens 1500, do_sample True |
| Model fluency | `Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct` (kedua korpus) |
| Encoder isi | `sentence-transformers/LaBSE`, `intfloat/multilingual-e5-base`, `LazarusNLP/simcse-indobert-base` |
| Variabel lingkungan wajib | `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1`, `HF_HUB_DISABLE_SYMLINKS=1`, `HF_TOKEN` |

Sumber: `RUN_LOG.md` bagian Lingkungan dan manifes peluncuran di `LOGS/detached_*.json`.

Setelan kuantisasi dan parameter dekode tidak diubah sepanjang eksperimen (bagian 18 protokol).

---

## 3. Split baru

### 3.1 Ukuran split

| Korpus | train | val | retrieval_pool | test | jumlah | sumber |
|---|---|---|---|---|---|---|
| formality (v2) | 2.498 | 500 | 1.500 | 500 | 4.998 | `fewshot_formality/data/formality_splits_v2/split_manifest.json` |
| Aaker (v2) | 24.820 | 6.205 | 18.617 | 6.205 (test) + 6.205 (alpha_dev) | 62.052 | `fewshot_aaker/data/brand_splits_v2/split_manifest.json` |

Pembanding split lama:

| Korpus | train | val | retrieval_pool | test | jumlah |
|---|---|---|---|---|---|
| formality (lama) | 2.498 | 500 | 1.500 | 500 | 4.998 |
| Aaker (lama) | 37.877 | 7.576 | 22.727 | 7.576 | 75.756 |

Ukuran split formality tidak berubah; proses split ulang mengganti pembagian keanggotaan, bukan
jumlah baris. Korpus Aaker turun dari 75.756 menjadi 62.052 baris, yaitu 13.704 baris (18,1%)
dibuang oleh deduplikasi teks ternormalisasi, seperti tercatat pada
`fewshot_aaker/data/brand_splits_v2/split_manifest.json` (`rows_raw` 75.756, `rows_after_dedup`
62.052, `rows_dropped` 13.704).

### 3.2 Hasil gerbang kebocoran

Dijalankan lewat `scripts/verify_splits.py --gate` (Langkah 1, `RUN_LOG.md`):

| Pemeriksaan | Hasil |
|---|---|
| Aaker split lama | GAGAL (exit 1): duplikat lintas split maksimum 503 (sophistication, retrieval_pool vs train_set); percakapan bersama pada keenam pasangan split, mis. test_set vs train_set 1.908 percakapan |
| Aaker split baru | LOLOS (exit 0): nol duplikat di kelima kelas, nol percakapan bersama |
| STIF split lama | GAGAL (exit 1): kelas formal train_set vs val_set 1; kelas informal retrieval_pool vs test_set 1 dan test_set vs train_set 1 |
| STIF split baru | LOLOS (exit 0, toleransi 5): kelas formal nol; kelas informal retrieval_pool vs train_set 1 |

Catatan duplikat korpus Aaker: selain 13.704 baris duplikat yang dibuang, pemisahan percakapan
di level `conversation_id_str` juga menghapus kebocoran lintas split. Pengelompokan di level akun
tidak mungkin karena korpus hanya memuat 24 akun dan setiap akun muncul di lebih dari satu split
(tercatat sebagai `catatan` pada manifest). Untuk korpus STIF, sisa satu duplikat pada split baru
berasal dari baris kembar di berkas sumber, bukan kebocoran; karena itu toleransi 5 dipakai.
Terdapat pula 34 teks identik antara blok formal dan informal (manifest formality), yang bukan
kebocoran karena kedua blok memang pasangan paralel.

---

## 4. Classifier dan kalibrasi

### 4.1 F1 per kelas pada test set baru

Classifier formality (`classifier_formality/model_results_dir/formality_model_roberta/classification_report_test.txt`,
test 500 baris):

| Kelas | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| formal | 0,8981 | 0,9520 | 0,9243 | 250 |
| informal | 0,9489 | 0,8920 | 0,9196 | 250 |
| akurasi | | | 0,9220 | 500 |
| macro avg | 0,9235 | 0,9220 | 0,9219 | 500 |

Classifier Aaker (`classifier_brand/model_results_dir/brand_model_roberta/test_report.txt`,
test 6.205 baris):

| Kelas | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| competence | 0,97 | 0,97 | 0,97 | 1.611 |
| excitement | 0,88 | 0,88 | 0,88 | 1.123 |
| ruggedness | 0,84 | 0,84 | 0,84 | 999 |
| sincerity | 0,90 | 0,90 | 0,90 | 1.013 |
| sophistication | 0,93 | 0,94 | 0,93 | 1.459 |
| akurasi | | | 0,91 | 6.205 |
| macro avg | 0,90 | 0,90 | 0,9043 | 6.205 |

Pembanding lama (tidak boleh dipakai sebagai angka utama): formality
`classification_report_test_LAMA_20260611.txt` akurasi 0,9220 dengan F1 per kelas 0,9225 / 0,9215;
Aaker `test_report_LAMA_20260611.txt` akurasi 0,93 dengan F1 0,98 / 0,92 / 0,86 / 0,92 / 0,95 pada
support 7.576. Seluruh kelas Aaker turun tipis pada split v2, konsisten dengan deduplikasi dan
pemisahan percakapan.

### 4.2 Suhu, NLL, dan ECE sebelum dan sesudah kalibrasi

Formality (`fewshot_formality/style_classifier/calibration.json`, n_val 500):

| Besaran | Sebelum | Sesudah |
|---|---|---|
| Suhu T | — | 0,9805 |
| NLL | 0,1578 | 0,1578 |
| ECE | 0,0131 | 0,0132 |
| Keyakinan rata-rata | 0,9434 | 0,9451 |
| Median probabilitas kelas target | 0,97317 | 0,97497 |
| Persentil 5–95 probabilitas kelas target | [0,42981; 0,99844] | [0,42843; 0,99863] |
| Akurasi validasi | 0,9440 | 0,9440 |

Aaker (`fewshot_aaker/style_classifier/calibration.json`, n_val 6.205):

| Besaran | Sebelum | Sesudah |
|---|---|---|
| Suhu T | — | 2,6779 |
| NLL | 0,6087 | **0,3013** |
| ECE | 0,0739 | **0,0437** |
| Keyakinan rata-rata | 0,9905 | 0,9304 |
| Median probabilitas kelas target | 0,99998 | 0,95789 |
| Persentil 5–95 probabilitas kelas target | [0,00158; 0,99998] | [0,07136; 0,96225] |
| Akurasi validasi | 0,9168 | 0,9168 |

Tafsiran: classifier formality sudah terkalibrasi baik sejak awal (ECE 0,0131) sehingga suhu
mendekati 1 dan kalibrasi nyaris tidak mengubah apa pun; classifier Aaker sangat melampaui
keyakinan (ECE 0,0739, keyakinan rata-rata 0,9905 pada akurasi 0,9168) sehingga suhu 2,6779
memotong NLL dan ECE sekitar separuh. Sebaran probabilitas kelas target Aaker menyempit dari
median 0,99998 menjadi 0,95789, persis yang diminta reviewer: nilai mentah tidak lagi menumpuk di
ekstrem, sehingga `style_strength_calibrated` dapat menjadi ukuran bertingkat.

Dipakai oleh evaluasi melalui `--calibration`; berkas hasilnya ada di `HASIL/calibration_formality.json`
dan `HASIL/calibration_aaker.json`.

---

## 5. Pemilihan alpha

Kriteria ditetapkan lebih dahulu: `criterion = harmonic`, `accuracy_column = style_accuracy`,
`content_column = content_preservation_LaBSE` (`fewshot_formality/alpha_star.json` dan
`fewshot_aaker/alpha_star.json`). Kolom kriteria adalah LaBSE, sesuai keputusan manusia agar
konsisten antar korpus dan tidak memakai encoder lama. Sapuan dijalankan pada development set
(Aaker: `alpha_dev`, n = 500 per konfigurasi; formality: `val_set_v2`, n = 250 per konfigurasi),
bukan pada test set.

### 5.1 Kurva sapuan formality

| alpha | formal akurasi | formal LaBSE | formal H | informal akurasi | informal LaBSE | informal H |
|---|---|---|---|---|---|---|
| 0,1 | 0,136 | 0,69427 | 0,22745 | 0,968 | 0,77595 | 0,86140 |
| 0,3 | 0,116 | 0,72953 | 0,20017 | 0,980 | 0,77451 | 0,86522 |
| 0,5 | 0,120 | 0,74094 | 0,20655 | 0,948 | 0,79047 | 0,86210 |
| 0,7 | 0,128 | 0,74233 | 0,21835 | 0,968 | 0,78369 | **0,86615** |
| 0,9 | 0,108 | 0,75980 | 0,18912 | 0,960 | 0,77535 | 0,85785 |

Keputusan: **informal α = 0,7**, **formal α tidak ditetapkan**.

Alasan yang harus dipatuhi saat menulis naskah: α = 0,7 menang tipis atas α = 0,3 (jarak H
0,00093) sehingga tidak boleh disebut optimal tanpa kualifikasi; pada n = 250 galat baku proporsi
sekitar 0,02, jadi rentang 0,3 sampai 0,7 tidak terbedakan pada target informal. Untuk target
formal, akurasi gaya hanya 0,108 sampai 0,136 dengan sebaran 0,028 (sekitar 1,4 kali galat baku),
yaitu aras derau; pada data lama α = 0,5 terpilih dengan kriteria yang sama, sehingga pilihan itu
berubah hanya karena derau. Untuk tabel naskah dipakai satu alpha per korpus dari target yang
kriterianya informatif (informal), dan kurva target formal disajikan sebagai bukti ketidakpekaan.

Catatan: `alpha_star_formality.json` pada disk memuat `picks.formal.alpha = 0.1` sebagai hasil
aritmetika kriteria; sesuai keputusan manusia, angka itu **tidak** dipakai sebagai alpha formal.
Berkas pembanding `alpha_star_formality_legacy_content.json` (kolom encoder lama) disertakan
sebagai bukti kepekaan terhadap pilihan kolom kriteria.

### 5.2 Kurva sapuan Aaker

| alpha | competence akurasi | competence LaBSE | competence H | excitement akurasi | excitement LaBSE | excitement H |
|---|---|---|---|---|---|---|
| 0,1 | 0,872 | 0,41163 | 0,55926 | 0,318 | 0,70443 | 0,43819 |
| 0,3 | 0,838 | 0,49807 | **0,62479** | 0,326 | 0,71801 | 0,44841 |
| 0,5 | 0,452 | 0,65587 | 0,53518 | 0,336 | 0,73569 | **0,46131** |
| 0,7 | 0,226 | 0,71637 | 0,34360 | 0,310 | 0,74856 | 0,43843 |
| 0,9 | 0,152 | 0,71818 | 0,25090 | 0,260 | 0,74773 | 0,38584 |

Keputusan: **competence α = 0,3** (jarak H 0,06551, cukup terbedakan) dan **excitement α = 0,5**
(jarak H hanya 0,01290, tidak boleh disebut optimal tanpa kualifikasi). Aras acak korpus Aaker
adalah 0,20 karena lima kelas; competence pada α 0,1–0,3 berada sekitar 4,2–4,4 kali aras acak,
sedangkan excitement 0,318–0,336 sekitar 1,6 kali aras acak, dengan sebaran antar alpha hanya 0,018
(di bawah satu galat baku). Karena itu untuk tabel naskah dipilih α = 0,3 dari competence, dan
kurva excitement disajikan sebagai pendamping.

---

## 6. Hasil utama

Sumber untuk subbagian ini: `TABEL_ringkasan_formality.csv` dan `TABEL_ringkasan_aaker.csv`
(di `HASIL/`), yang diturunkan dari berkas per sampel `evaluated_v2_*` di
`fewshot_formality/evaluation_result_v2/google_gemma-3-4b-it` dan
`fewshot_aaker/evaluation_result_v2/google_gemma-3-4b-it`. Aras acak: 0,50 (formality, biner) dan
0,20 (Aaker, lima kelas).

### 6.1 Formality, konfigurasi hybrid_early k = 5 (kurva alpha pada test set, n = 250 per titik)

| alpha | akurasi (formal) | kekuatan terkalibrasi | isi (lama) | isi LaBSE | isi mE5 | median PPL | trimmed PPL |
|---|---|---|---|---|---|---|---|
| 0,1 | 0,192 | 0,1967 | 0,7498 | 0,6950 | 0,9080 | 142,3 | 191,7 |
| 0,3 | 0,176 | 0,1957 | 0,7729 | 0,7210 | 0,9194 | 169,7 | 221,8 |
| 0,5 | 0,112 | 0,1499 | 0,7950 | 0,7463 | 0,9261 | 190,8 | 289,8 |
| 0,7 | 0,152 | 0,1790 | 0,7908 | 0,7495 | 0,9231 | 192,1 | 298,0 |
| 0,9 | 0,120 | 0,1589 | 0,7975 | 0,7584 | 0,9260 | 197,4 | 294,8 |

| alpha | akurasi (informal) | kekuatan terkalibrasi | isi (lama) | isi LaBSE | isi mE5 | median PPL | trimmed PPL |
|---|---|---|---|---|---|---|---|
| 0,1 | 0,960 | 0,9317 | 0,7532 | 0,7677 | 0,9251 | 151,0 | 206,2 |
| 0,3 | 0,984 | 0,9606 | 0,7735 | 0,7702 | 0,9305 | 239,7 | 337,0 |
| 0,5 | 0,968 | 0,9466 | 0,7773 | 0,7763 | 0,9312 | 243,9 | 332,7 |
| 0,7 | 0,936 | 0,9346 | 0,7813 | 0,7784 | 0,9314 | 257,1 | 367,9 |
| 0,9 | 0,960 | 0,9444 | 0,7903 | 0,7858 | 0,9327 | 225,0 | 374,0 |

Rentang seluruh konfigurasi pada test set (metode dan alpha): target formal akurasi 0,048–0,780
(batas atas 0,780 adalah `zero_shot`; seluruh konfigurasi retrieval 0,048–0,252), LaBSE
0,559–0,794; target informal akurasi 0,136–0,988 (seluruh konfigurasi retrieval 0,904–0,988), LaBSE
0,587–0,803.

PPL keseluruhan korpus formality (9.500 baris), dari `TABEL_ppl_formality_per_target.csv`:

| Target | n | median | trimmed10 | rata-rata | sd | maks |
|---|---|---|---|---|---|---|
| formal | 4.750 | 191,45 | 287,38 | 1.436,45 | 36.680,95 | 2.399.765,85 |
| informal | 4.750 | 226,18 | 342,27 | 1.081,08 | 11.974,31 | 755.942,67 |

Proporsi degenerate formality (ambang PPL > 1000): formal 608/4.750 = 12,80%; informal
700/4.750 = 14,74%. Per metode: bm25 17,00 / 17,00%; centroid 7,60 / 8,60%; dense 16,40 / 15,40%;
hybrid_early 13,28 / 16,56%; random 12,80 / 15,60%; zero_shot 2,80 / 1,20% (formal / informal).

### 6.2 Aaker, konfigurasi hybrid_early k = 5 (n = 500 per titik)

| alpha | akurasi (competence) | kekuatan terkalibrasi | isi (lama) | isi LaBSE | isi mE5 | median PPL | trimmed PPL |
|---|---|---|---|---|---|---|---|
| 0,1 | 0,864 | 0,8344 | 0,3951 | 0,4209 | 0,8538 | 34,7 | 41,5 |
| 0,3 | 0,842 | 0,8109 | 0,4879 | 0,4974 | 0,8714 | 48,4 | 64,1 |
| 0,5 | 0,514 | 0,4981 | 0,6510 | 0,6657 | 0,9069 | 74,1 | 122,9 |
| 0,7 | 0,244 | 0,2416 | 0,7111 | 0,7138 | 0,9179 | 73,6 | 147,8 |
| 0,9 | 0,200 | 0,1986 | 0,7172 | 0,7189 | 0,9195 | 83,7 | 163,2 |

| alpha | akurasi (excitement) | kekuatan terkalibrasi | isi (lama) | isi LaBSE | isi mE5 | median PPL | trimmed PPL |
|---|---|---|---|---|---|---|---|
| 0,1 | 0,330 | 0,3225 | 0,6349 | 0,6877 | 0,9130 | 77,0 | 92,0 |
| 0,3 | 0,340 | 0,3362 | 0,6793 | 0,7186 | 0,9201 | 86,5 | 112,0 |
| 0,5 | 0,300 | 0,2956 | 0,7131 | 0,7390 | 0,9253 | 83,7 | 124,9 |
| 0,7 | 0,310 | 0,3032 | 0,7349 | 0,7417 | 0,9266 | 72,9 | 122,8 |
| 0,9 | 0,272 | 0,2695 | 0,7485 | 0,7581 | 0,9304 | 72,7 | 129,1 |

Rentang seluruh konfigurasi: competence akurasi 0,162–0,864, LaBSE 0,391–0,719; excitement akurasi
0,058–0,340, LaBSE 0,531–0,758. Proporsi degenerate Aaker (10.000 baris, ambang PPL > 1000):
keseluruhan 586/10.000 = 5,86%; per target competence 255/5.000 = 5,10% dan excitement
331/5.000 = 6,62%; per metode pada kedua target: bm25 4,40/9,20%, centroid 0,20/1,00%, dense
10,20/9,80%, hybrid_early 6,16/7,32%, random 2,00/7,00%, zero_shot 3,40/2,60%.

### 6.3 Pola penting yang harus diungkapkan

1. **Target informal formality tercapai, target formal tidak.** Pada target informal, metode
   retrieval berada di 0,920–0,988 (jauh di atas aras acak 0,50) dengan isi sekitar 0,79. Pada
   target formal, seluruh konfigurasi retrieval 0,048–0,252, yaitu di bawah aras acak 0,50;
   classifier memprediksi kelas informal untuk sekitar 88% keluaran bertarget formal.
2. **Tukar-menukar gaya-isi pada Aaker competence sangat tajam.** alpha kecil menaikkan gaya
   (0,864 pada α 0,1) tetapi menjatuhkan isi (0,395); alpha besar sebaliknya (0,200 / 0,717).
3. **`zero_shot` menyimpang.** Pada target formal formality akurasi gayanya 0,780 (tertinggi) dan
   PPL mediannya 39,82 (terendah), tetapi `content_preservation`-nya paling buruk (0,5166 / LaBSE
   0,5593); pada target informal akurasinya justru 0,136 (terendah). Pola ini dilaporkan apa adanya
   dan **tidak** boleh dipakai untuk menyimpulkan keunggulan `zero_shot`.

---

## 7. Varians

**Tidak diukur.** Eksperimen memakai **satu seed (42)**. Ulangan generasi pada Langkah 7
(sebagaimana diuraikan protokol bagian 10) tidak dijalankan karena struktur tiga seed dibatalkan
atas keputusan manusia 2026-09-27: loop menyusun target di lapisan luar dan seed di lapisan dalam,
sehingga menyelesaikan "formal untuk tiga seed" tidak berarti formality selesai dan target
informal belum tersentuh sama sekali. Berkas generasi seed 43 dan 44 dari peluncuran pertama yang
terhenti disimpan di `ARSIP/seed43_44_formality` (76 berkas, tidak dihapus), sehingga bila varians
antar-jalan diminta lagi hanya evaluasi yang perlu diulang, bukan pembangkitan.

**Naskah tidak boleh menyatakan bahwa setiap konfigurasi diulang beberapa seed.** Ukuran
ketidakpastian yang dilaporkan adalah **bootstrap berpasangan atas butir uji**: interval keyakinan
95% dihitung dengan 10.000 resample atas 250 pasangan (formality) atau 500 pasangan (Aaker) per
perbandingan, memakai mata uji yang sama lintas metode sehingga perbandingannya berpasangan
(`scripts/bootstrap_significance.py`). Karena hanya satu seed, tidak ada komponen varians
antar-generasi di dalam interval tersebut, dan keterbatasan ini harus disebut apa adanya.

---

## 8. Uji signifikansi

Skrip: `scripts/bootstrap_significance.py` versi baru (SHA-256
`5c4603662007133cc52954f10faf0faddfd94c8aa0be2e872e2eba1528ed9472`, 10.553 byte). Skrip ini
memasangkan hanya konfigurasi di dalam target yang sama, memasukkan `k` ke dalam label konfigurasi,
memberi peringatan bila label bertabrakan, dan melewati pasangan lintas target sambil melaporkan
penghitungnya. Seluruh dua belas tabel dihitung ulang dengan `--only-seed 42`.

Cakupan dan penyaring:

| Korpus | Konfigurasi | Pasangan sebanding | Pasangan lintas target dilewati |
|---|---|---|---|
| formality | 38 (19 per target; k = 5 dan k = 10 terpisah) | 342 | 361 |
| Aaker | 20 (10 per target; hanya k = 5) | 90 | 100 |

Jumlah pasangan dengan interval keyakinan 95% yang tidak memuat nol:

| Metrik | formality | Aaker |
|---|---|---|
| style_accuracy | 128/342 | 66/90 |
| style_strength_calibrated | 157/342 | 70/90 |
| content_preservation | 230/342 | 80/90 |
| content_preservation_LaBSE | 189/342 | 73/90 |
| content_preservation_mE5 | 193/342 | 74/90 |
| replication_rate_8 | 28/342 | 61/90 |

Pasangan yang **berbeda bermakna** (contoh utama, dari `TABEL_uji_*.csv`):

- `zero_shot` vs setiap metode retrieval, formality: 36/36 pasangan bermakna. Arah berbalik menurut
  target — formal, retrieval lebih rendah `d = −0,732…−0,528`; informal, retrieval lebih tinggi
  `d = +0,768…+0,852`. Pada `content_preservation`: 36/36 bermakna, formal `d = +0,210…+0,311`,
  informal `d = +0,165…+0,233`.
- Aaker competence, `hybrid_early` α 0,3 vs α 0,5: `d = +0,328` CI [+0,282; +0,374] (akurasi gaya);
  vs α 0,9 pada isi: `d = −0,229` CI [−0,250; −0,209].
- Aaker excitement, `hybrid_early` α 0,3 vs α 0,5: `d = +0,040` CI [−0,004; +0,084]
  (**tidak** bermakna); α 0,5 vs `zero_shot`: `d = +0,242` CI [+0,196; +0,286] (bermakna).

Pasangan yang **tidak berbeda bermakna** (penting untuk tidak mengklaim keunggulan):

- Aaker competence, tiga teratas setara: `hybrid_early` α 0,1 vs α 0,3 `d = +0,022`
  CI [−0,004; +0,050]; `centroid` vs α 0,3 `d = +0,008` CI [−0,022; +0,038].
- Formality informal, α 0,3 vs α 0,7 pada kolom kriteria `content_preservation_LaBSE`:
  `d = −0,008` CI [−0,023; +0,007]; pada `style_accuracy` justru α 0,7 lebih rendah
  (`d = +0,048` CI [+0,016; +0,080]).
- Formality informal, mayoritas pasangan antar metode retrieval: 59/171 bermakna.

### 8.1 Kepekaan k (R2-12 dan R3-W2)

Tabel `TABEL_kepekaan_k_formality.csv` (dihasilkan `scripts/k_sensitivity.py`), 18 pasangan
k10-vs-k5 per metrik (9 konfigurasi × 2 target, 250 baris per pasangan). Yang bermakna:
`style_accuracy` 1/18, `style_strength_calibrated` 4/18, `content_preservation` 10/18,
`content_preservation_LaBSE` 3/18, `content_preservation_mE5` 9/18, `replication_rate_8` 2/18.

Pola: k memengaruhi **isi** lebih daripada **gaya**. Pada target formal, `content_preservation`
(encoder lama) naik dari k=5 ke k=10 pada 7 dari 9 konfigurasi (bm25 +0,032; centroid +0,044;
hybrid α 0,1 +0,018; α 0,3 +0,020; α 0,7 +0,015; α 0,9 +0,016; random +0,015). Pada kolom kriteria
LaBSE efeknya lebih kecil (hanya formal bm25 +0,023, formal centroid +0,019, formal hybrid α 0,1
+0,024). Gaya nyaris tidak bergerak: satu-satunya perbedaan bermakna adalah formal `centroid`
`k10 − k5 = −0,148`, yaitu k=10 justru **lebih rendah**. Perbandingan ini sebelumnya tidak dapat
dihitung karena label konfigurasi tidak memuat k.

---

## 9. Replikasi templat

Sumber: `TABEL_replikasi_formality.csv` dan `TABEL_replikasi_aaker.csv` (skrip
`scripts/replication_metric.py`, `--only-seed 42 --from-column`, sumber eksemplar = kolom
`retrieved_exemplars`, ukuran tumpang tindih 8-gram).

| Korpus / target | overlap8 rata-rata | rentang | output ber-overlap tinggi |
|---|---|---|---|
| formality formal | 0,0037 | 0,0000–0,0142 | 0,48% |
| formality informal | 0,0079 | 0,0000–0,0194 | 1,05% |
| Aaker competence | 0,0911 | 0,0000–0,3393 | 15,17% |
| Aaker excitement | 0,0235 | 0,0000–0,0426 | 3,82% |

Menurut konfigurasi, `replication_rate_8` tertinggi ada pada alpha kecil korpus Aaker:
competence α 0,1 = 0,3386, α 0,3 = 0,2200, centroid = 0,1880; excitement seluruhnya di bawah 0,037;
formality seluruhnya di bawah 0,011. Jadi klaim penyalinan eksemplar kuat hanya pada competence
alpha kecil (mendukung hipotesis panjang keluaran untuk R2-09), lemah pada excitement, dan tidak
didukung pada korpus formality. Hipotesis panjang keluaran diuji terpisah: pada competence,
`output_tokens` menurun monoton dari 58,69 (α 0,1) ke 31,61 (α 0,9); pada excitement rasio panjang
keluaran terhadap asli mendekati 1,0 di semua alpha, sehingga keluarannya nyaris sekadar parafrase
dan gaya tidak berpindah — itu menjelaskan mengapa akurasinya bertahan di sekitar 0,33.

---

## 10. Evaluasi manusia

**Tidak dijalankan.** Hanya ekspor sampel yang dikerjakan (Langkah 10). Tidak ada penilai yang
mengisi lembar penilaian, sehingga tidak ada angka kesepakatan antar penilai maupun korelasinya
dengan metrik otomatis. Bagian ini harus dibaca sebagai "tidak ada hasil", bukan "hasil kosong".

Berkas sampel yang dihasilkan (skrip `scripts/export_human_eval.py`, memakai 25 `sample_index`
terkecil yang sama lintas metode dari empat metode utama dense, centroid, bm25, hybrid_early):

| Berkas | Baris | Kalimat sumber | Berkas metode |
|---|---|---|---|
| `EVAL_MANUSIA_formality.csv` | 400 | 25 | 16 |
| `EVAL_MANUSIA_aaker.csv` | 200 | 25 | 8 |

Kolom: `sample_index`, `original_message`, `paraphrased_message`, `method_file`. Rubrik penilaian
sudah tersedia di `fewshot_aaker/data/Aaker Brand Personality - Human Validity Rubric.md`; lembar
penilaian dirancang dengan tiga kolom per penilai (kekuatan gaya, pemeliharaan konten, kelancaran,
skala 1–5) dan tiga penilai terpisah.

Catatan penting yang harus dilaporkan apa adanya: studi validitas label n = 385 pada repo ini
**belum terisi** kolom penilaiannya; hanya pilot n = 100 yang terisi. Jangan menyatakan adanya
studi n = 385 dalam laporan mana pun.

---

## 11. Kendala

Seluruh butir berikut tercatat di `RUN_LOG.md` (bagian *Catatan per langkah* dan tabel *Kendala
dan keputusan*) beserta jalur log dan berkas yang terlibat.

### 11.1 Penyimpangan yang disetujui manusia

1. **VRAM 12,0 GB di bawah syarat 16 GB.** Lanjut di mesin ini dengan mitigasi bagian 17. Tidak
   pernah terjadi OOM, sehingga jalur dua tahap (`--skip-fluency` lalu PPL terpisah) tidak
   diperlukan. Ini penyimpangan yang harus disebut pada bagian Kendala naskah.
2. **Struktur seed diubah menjadi satu seed (42).** Alasan pada bagian 7. Akibatnya Langkah 7
   tidak dijalankan.
3. **Model fluency diseragamkan.** Pipeline asli tidak seragam: `fewshot_aaker/eval.py` memakai
   `gemma2-9b-cpt-sahabatai-v1-instruct` sedangkan `fewshot_formality/eval.py` memakai
   `llama3-8b-cpt-sahabatai-v1-instruct`, sementara naskah hanya menyebut satu model. Revisi ini
   memakai `gemma2-9b` pada **kedua** korpus. Konsekuensinya proporsi degenerate formality naik dari
   0,61% (README, model lama) menjadi 12,80–14,74%, sedangkan Aaker hampir tidak bergerak (5,51%
   menjadi 5,86%). **Kedua angka tidak sebanding karena modelnya berbeda; lonjakan ini adalah akibat
   pergantian model fluency, bukan penurunan mutu keluaran, dan angka 0,61% tidak boleh dipakai
   sebagai pembanding.** Bukti model yang benar-benar dimuat: log memuat pemuatan 464 tensor, cocok
   dengan indeks cache `gemma2-9b` (464 tensor), bukan `llama3-8b` (291 tensor).

### 11.2 Kegagalan dan perbaikan

4. **`rank_bm25` negatif palsu pada `preflight.py`.** Paket tidak menyediakan `__version__`;
   patch satu baris mengambil versi dari `importlib.metadata.version`.
5. **Symlink cache Hugging Face gagal** (`OSError: [WinError 1314]`) saat mengunduh
   `intfloat/multilingual-e5-base`; diselesaikan dengan `HF_HUB_DISABLE_SYMLINKS=1` (mode salin).
6. **`generate(generator=...)` tidak didukung transformers 5.8.0** sehingga 30 generasi pertama
   gagal; diganti `torch.manual_seed(seed)` tepat sebelum `generate()`, tanpa mengubah parameter
   dekode bagian 18.
7. **`UnicodeEncodeError` cp1252** karena emoji pada keluaran model; diselesaikan dengan
   `PYTHONIOENCODING=utf-8` dan `PYTHONUTF8=1`.
8. **Pola `Start-Process -RedirectStandardOutput` mati tanpa jejak** (log 0 byte, tidak ada berkas
   hasil, tidak ada galat). Diganti peluncur teruji `scripts/launch_detached.py` yang memisahkan
   stdout dan stderr, melepaskan proses, serta mencatat PID, SHA-256 config, dan `env_wajib`.
9. **Cache embedding retrieval berasal dari split lama**; keempat pasang berkas dinetralkan dengan
   sufiks `.split_lama_20260611` (tidak dihapus) dan cache dibangun ulang dari pool v2.
10. **Bug `args.pattern` vs `--patterns`** pada `evaluate_results.py`; dua rujukan diperbaiki
    menjadi `args.patterns`.
11. **Dua cacat `bootstrap_significance.py`** (pasangan lintas target tidak dipisah; `k` tidak masuk
    label sehingga berkas k=10 dan k=5 saling menimpa tanpa peringatan). Skrip versi baru dipakai dan
    kedua belas tabel uji dihitung ulang. Sebelum koreksi, tabel formality hanya memuat 10 konfigurasi
    per target (bukan 19) dan tabel Aaker memuat 100 pasangan lintas target.
12. **Perkiraan waktu Aaker meleset sekitar satu jam** karena `zero_shot` memakan sekitar 1,8–1,9
    kali waktu normal.

### 11.3 Catatan interpretasi yang harus dibawa ke naskah

13. **Definisi `eos_reached` berbeda antar berkas.** Pada berkas hasil generasi, `eos_reached`
    mengikuti bagian 5.4 (perbandingan dengan `tokenizer.eos_token_id` = 1) sehingga selalu `False`
    untuk Gemma 3 yang mengakhiri turn dengan `<end_of_turn>` (id 106). Pada berkas `evaluated_v2_*`,
    `evaluate_results.py` menimpanya dengan heuristik tanda baca `[.!?"]$`. Interpretasi truncation
    harus memakai `output_tokens` dibanding `max_new_tokens`, bukan `eos_reached`.
14. **Bobot kelas classifier Aaker** dihitung dari frekuensi korpus gabungan penuh, bukan dari train
    split v2. Dibiarkan agar satu-satunya yang berubah dibanding run lama adalah split; ini
    keterbatasan yang harus disebut.
15. **`sampling_seed`** ada di kedua config tetapi tidak dikonsumsi skrip mana pun.
16. **Penghentian mendadak** pada peluncuran formality pertama tidak meninggalkan berkas terpotong
    (38 berkas seed 42 diperiksa, semuanya tepat 250 baris).
17. **Berkas `*_HUMAN_EVAL.csv` berisi 25 baris**, bukan 250; itu benar sesuai `human_eval_samples`
    = 25, bukan kerusakan.

---

## 12. Berkas keluaran

Semua di bawah `HASIL/`, kecuali skrip dan log yang tetap di tempat asalnya. `HASIL/` memuat 87
berkas dan `HASIL/keluaran_generasi/` memuat 116 berkas; seluruhnya berpenanda `_seed42` atau
turunannya, sehingga materi pendukung hanya memuat satu eksperimen.

### 12.1 Tabel di `HASIL/`

| Berkas | Isi |
|---|---|
| `TABEL_ringkasan_formality.csv` | 38 baris, statistik per konfigurasi (median, trimmed, proporsi degenerate) |
| `TABEL_ringkasan_aaker.csv` | 20 baris |
| `TABEL_uji_formality_<metrik>.csv` | 6 berkas, masing-masing 342 pasangan sebanding |
| `TABEL_uji_aaker_<metrik>.csv` | 6 berkas, masing-masing 90 pasangan sebanding |
| `TABEL_replikasi_formality.csv` | 38 baris |
| `TABEL_replikasi_aaker.csv` | 20 baris |
| `TABEL_ppl_formality_per_target.csv` | median dan trimmed PPL per target dan per metode |
| `TABEL_kepekaan_k_formality.csv` | 108 baris, kepekaan k10-vs-k5 (R2-12, R3-W2) |

`<metrik>` = `style_accuracy`, `style_strength_calibrated`, `content_preservation`,
`content_preservation_LaBSE`, `content_preservation_mE5`, `replication_rate_8`.

### 12.2 Berkas pendukung di `HASIL/`

| Berkas | Isi |
|---|---|
| `alpha_star_formality.json` | alpha terpilih dan kurva sapuan lengkap formality |
| `alpha_star_aaker.json` | alpha terpilih dan kurva sapuan lengkap Aaker |
| `alpha_star_formality_legacy_content.json` | pembanding kolom kriteria encoder lama |
| `calibration_formality.json` | suhu dan metrik kalibrasi formality |
| `calibration_aaker.json` | suhu dan metrik kalibrasi Aaker |
| `split_manifest_formality.json` | manifes split v2 formality |
| `split_manifest_aaker.json` | manifes split v2 Aaker |
| `EVAL_MANUSIA_formality.csv` | 400 baris sampel evaluasi manusia |
| `EVAL_MANUSIA_aaker.csv` | 200 baris sampel evaluasi manusia |
| `evaluated_v2_*_seed42_results.csv` | 58 berkas hasil evaluasi per sampel (38 formality + 20 Aaker) |
| `RUN_LOG.md` | catatan seluruh langkah |
| `LAPORAN_AKHIR.md` | laporan ini |

### 12.3 `HASIL/keluaran_generasi/`

116 berkas, hanya yang berpenanda `_seed42`: 38 `*_results.csv` dan 38 `*_HUMAN_EVAL.csv` formality,
ditambah 20 `*_results.csv` dan 20 `*_HUMAN_EVAL.csv` Aaker. Berkas run lama tanpa penanda seed
(64 berkas formality dan 32 berkas Aaker) **tidak** disalin ke `HASIL/`, agar materi pendukung
naskah hanya memuat satu eksperimen.

### 12.4 Skrip

Protokol dan bundel:

| Berkas | Peran |
|---|---|
| `scripts/preflight.py` | pemeriksaan kesiapan |
| `scripts/verify_splits.py` | gerbang kebocoran split |
| `scripts/launch_detached.py` | peluncur tugas panjang (PID, SHA-256 config, `env_wajib`) |
| `scripts/evaluate_results.py` | evaluasi lengkap 27 kolom |
| `scripts/calibrate_classifier.py` | temperature scaling |
| `scripts/select_alpha_dev.py` | pemilihan alpha pada development set |
| `scripts/report_metrics.py` | statistik ringkas per konfigurasi |
| `scripts/bootstrap_significance.py` | uji berpasangan dan interval keyakinan (versi baru) |
| `scripts/replication_metric.py` | laju replikasi templat |

Skrip bantu yang ditambahkan pada revisi ini:

| Berkas | Peran | SHA-256 | Ukuran |
|---|---|---|---|
| `scripts/k_sensitivity.py` | menghasilkan `TABEL_kepekaan_k_formality.csv` | `ee2e2e7cd99fa1b34730be09871d305165caec8f8adaa703b11156d813724a5d` | 3.562 byte |
| `scripts/ppl_per_target.py` | menghasilkan `TABEL_ppl_formality_per_target.csv` | `4904c4cc84ee09d69fa00c6110dd30307cdf9dc7ad36c41495421a4178826536` | 4.104 byte |
| `scripts/export_human_eval.py` | Langkah 10: ekspor sampel evaluasi manusia | `6a32098c099d8f124b0ab30a6aacad5fde8dc5daf7666a192207926f4b96778e` | 2.390 byte |

### 12.5 Arsip dan log

`ARSIP/` memuat cadangan, bukan pemindahan: `formality_s42`, `aaker_s42`, `seed43_44_formality`
(76 berkas), `peluncuran_pertama_formality`, dan `rusak` (kosong). Log perhitungan ada di
`LOGS/` (`uji_v2_recompute.log`, `detached_*.json`, `eval_v2_*.err.log`, `formality_s42*.err.log`,
`aaker_s42.err.log`).

### 12.6 Daftar periksa penerimaan (bagian 15 protokol)

- Split baru kedua korpus lolos `verify_splits.py --gate` — **ya** (bagian 3.2).
- Ukuran split formality tetap 2.498 / 500 / 1.500 / 500 — **ya**.
- Korpus Aaker turun dari 75.756 menjadi 62.052 baris — **ya**.
- `retrieved_exemplars` terisi pada seluruh berkas hasil — **ya**.
- `retrieval_fallback` nol — **ya**, pada kedua korpus.
- Tidak ada keluaran yang diawali `ERROR:` — **ya**, 0 pada kedua korpus.
- Jumlah sampel per konfigurasi sesuai (250 formality, 500 Aaker) — **ya**.
- Himpunan `sample_index` sama di seluruh metode per konfigurasi — **ya** (dipakai sebagai kunci
  pemasangan berpasangan).
- Himpunan eksemplar identik antar ulangan — **tidak berlaku** (hanya satu seed).
- `calibration.json` ada untuk kedua korpus — **ya**.
- Kolom content preservation dari ketiga encoder ada — **ya**.
- Laju replikasi templat terhitung untuk seluruh berkas — **ya**.
- Uji signifikansi dijalankan pada seluruh metrik yang dilaporkan — **ya** (enam metrik).
- Proporsi output degenerate dilaporkan per metode — **ya** (bagian 6).
- `LAPORAN_AKHIR.md` memuat seluruh angka dengan jalur berkas sumbernya — **ya**.
- Setiap kegagalan atau bagian yang dipotong tercatat, tanpa angka perkiraan — **ya** (bagian 11).
