# Rencana Perbaikan JCCE-10619 (1st Round)

Manuscript: *The Impact of Hybrid Semantic and Stylistic Embedding Retrieval Strategies on
Indonesian Text Style Transfer using Large Language Model*

Dokumen ini disusun dari tiga sumber: komentar reviewer, kode aktual di dua repo
(`TST_fewshot_formality_hf_ref` dan `TST_fewshot_aaker - Copy`), dan pengukuran langsung atas
data split, cache embedding, serta berkas hasil eksperimen. Seluruh angka di sini dihitung ulang
oleh `build_plan_excel.py` dan tersedia di sheet `Bukti Temuan`.

---

## 1. Temuan yang mengubah urutan kerja

Empat hal ini bukan sekadar butir revisi. Masing-masing mengubah keputusan yang lebih besar, jadi
harus ditetapkan lebih dulu.

### 1.1 Klaim anti-kebocoran pada naskah hanya berlaku untuk satu dari dua korpus

Naskah menyatakan, pada bagian partisi data:

> "Test Set (10%): The untouched texts that the LLM is tasked with modifying. This test set is not
> leaked to retrieval or classifier train set."

Pengukuran atas berkas split:

| Pemeriksaan | STIF (formality) | Aaker (brand) |
|---|---|---|
| Teks identik antara test set dan retrieval pool | 4 kalimat | **629 kalimat** |
| Teks identik antara train classifier dan retrieval pool | 9 kalimat | **1.715 kalimat** |
| Duplikat teks di dalam test set | 0 baris | **703 baris** |
| Duplikat di dalam retrieval index per kelas | 0,0% | **21,3%** (excitement), 13,7% (competence) |
| Baris test dari thread yang juga ada di pool | tidak berlaku | **27,5%** |
| Akun unik di seluruh korpus | tidak berlaku | 24 |

Korpus STIF bersih, dan mekanisme penguncian `pair_id` yang dijelaskan di naskah memang bekerja di
sana. Korpus Aaker tidak memakai mekanisme itu: split-nya hanya stratifikasi lima persona, tanpa
deduplikasi dan tanpa pengelompokan percakapan. Jadi pernyataan "not leaked" benar untuk STIF dan
tidak benar untuk Aaker sebagaimana diimplementasikan.

Butir reviewer yang terkait: R1 (grouped data splits), R2-06, R2-18, R2-20.

### 1.2 Duplikat di pool menarik centroid ke satu template, dan LLM menyalinnya

Ini temuan yang paling menentukan. Retrieval index Aaker mengandung satu teks Telkom yang terulang
**414 kali** dalam kelas competence, dan 1.316 dari 5.965 teks pool competence (22,1%) menyebut
"Sobat BRI". Karena centroid adalah rata-rata embedding pool, ia tertarik ke template yang paling
banyak terulang.

Akibatnya, lima eksemplar teratas metode centroid pada kelas competence memuat hanya **3 teks yang
berbeda**, dan semuanya boilerplate permintaan maaf layanan pelanggan. Eksemplar ini identik untuk
setiap kalimat sumber, sesuai temuan Reviewer 2 bahwa metode centroid bersifat query-independent.
Pada kelas STIF, kelima eksemplar berbeda dan tidak ada pola template.

Lalu diukur overlap 8-gram antara output generasi dan eksemplar yang diambil:

| Korpus | Metode centroid | Metode dense |
|---|---|---|
| Aaker (brand) | **76,6% output** mengandung 8-gram dari eksemplar | 0,4% |
| STIF (formality) | 1,2% | 0,0% |

Pada korpus Aaker, gradasi terhadap alpha bersifat monoton dan searah dengan skor gaya:

| alpha (hybrid early fusion) | output dengan overlap | median style strength |
|---|---|---|
| 0,1 | 72,4% | 0,99999 |
| 0,3 | 38,8% | 0,99999 |
| 0,5 | 12,2% | 0,99997 |
| 0,7 | 2,2% | 0,00008 |
| 0,9 | 0,4% | 0,00004 |

Selama output menyalin eksemplar, classifier memberi 0,9999. Begitu penyalinan berhenti (alpha 0,7
ke atas), skor gaya jatuh ke 0,0001. Ini menunjukkan bahwa pada korpus Aaker, skor gaya tinggi
metode centroid dan hybrid alpha rendah berasal dari penyalinan verbatim eksemplar, bukan dari
transfer gaya. Kritik Reviewer 2 pada butir 3 dan 9 terkonfirmasi oleh data pemilik naskah sendiri,
dan penjelasannya bertumpu pada duplikat pool, bukan pada sifat centroid semata.

Butir reviewer yang terkait: R2-03, R2-09, R2-10, R3-W3.

### 1.3 Encoder retrieval identik dengan encoder evaluasi

`fewshot_config.json` dan `main.py` memakai `LazarusNLP/simcse-indobert-base` sebagai
`sentence_model`, yaitu model yang mengubah query dan pool menjadi embedding retrieval. `eval.py`
memakai model yang sama di `ContentPreservationEvaluator`. Jadi kekhawatiran sirkularitas pada butir
R2-08 bukan potensi, melainkan keadaan aktual.

Perbaikannya tidak menuntut regenerasi: cukup encode ulang seluruh output yang sudah tersimpan
dengan encoder lain.

### 1.4 Degradasi PPL berasal dari segelintir output dan mudah diselesaikan

Angka pada naskah sama persis dengan kolom mean di `summary_average_metrics.csv`, sehingga masalahnya
murni pelaporan statistik:

| Korpus | Output dengan PPL > 1000 | Rasio mean terhadap median (kasus terburuk) |
|---|---|---|
| STIF | 49 dari 8.000 (0,61%) | 2,6x |
| Aaker | 441 dari 8.000 (5,51%) | 3.774.807x (dense, Excitement) |

Satu output dengan PPL sekitar 6,9 x 10^10 muncul pada tiga konfigurasi sekaligus dan menarik
seluruh rata-rata. Berkas per sampel sudah tersedia untuk seluruh 48 konfigurasi, jadi perbaikan ini
dapat dikerjakan tanpa GPU.

Butir reviewer terkait: R2-21, R3-W5, R2-18.

### 1.5 Protokol split dapat direproduksi, tetapi penguncian pasangan tidak diterapkan

Script pembuat split tidak berada di dalam repo eksperimen. Untuk korpus Aaker script-nya ada di
luar repo (`Downloads/brand_personality_classification - Copy/main.py`), untuk korpus STIF tidak
ditemukan. Meski begitu, `verify_split_protocol.py` menunjukkan bahwa **kedelapan berkas split
dapat direproduksi persis** dari berkas sumber dengan satu protokol yang sama:

```python
rest_df, test_df            = train_test_split(df, test_size=0.10, random_state=42, stratify=df['label'])
classifier_df, retrieval_df = train_test_split(rest_df, test_size=(1/3), random_state=42, stratify=rest_df['label'])
train_df, val_df            = train_test_split(classifier_df, test_size=(1/6), random_state=42, stratify=classifier_df['label'])
```

Rasio akhir 50% train classifier, 10% validation, 30% retrieval pool, 10% test, distratifikasi pada
kolom label gaya, `random_state=42`, tanpa deduplikasi dan tanpa pengelompokan. Rinciannya ada di
`PROTOKOL_SPLIT_JCCE-10619.md`.

Yang penting: naskah menyatakan bahwa pada korpus STIF pasangan paralel dikunci dengan `pair_id`
sebelum splitting. Pemeriksaan atas berkas split yang benar-benar dipakai menunjukkan penguncian itu
tidak diterapkan. Hanya **35,7%** pasangan berada di split yang sama, berhimpit dengan **36,0%**
ekspektasi bila tidak ada penguncian sama sekali. Karena `stif_formal.txt` dan `stif_informal.txt`
sejajar baris demi baris, penguncian itu seharusnya mudah diterapkan dan seharusnya menghasilkan
angka mendekati 100%.

Dampaknya per arah transfer:

| Arah transfer | Sumber uji | Pasangan targetnya di retrieval pool | Di train/val classifier |
|---|---|---|---|
| target FORMAL (sumber = kalimat informal di test) | 246 | 77 (31,3%) | 141 (57,3%) |
| target INFORMAL (sumber = kalimat formal di test) | 244 | 66 (27,0%) | 150 (61,5%) |

Jadi untuk sekitar 27% sampai 31% kalimat uji, teks target yang seharusnya dihasilkan sudah berada di
dalam indeks retrieval. Karena pasangan formal dan informal berbagi sebagian besar kata, BM25 dan
dense berpotensi mengambilnya sebagai eksemplar. Ini kebocoran yang berbeda dari duplikasi verbatim,
karena teksnya memang tidak identik, sehingga tidak terdeteksi oleh pemeriksaan duplikat pada
bagian 1.1.

---

## 2. Konsekuensi terhadap strategi revisi

1. **Korpus Aaker harus diregenerasi.** Setelah duplikat dibuang, centroid berubah, sehingga seluruh
   tabel hasil Aaker berubah. Hasil Aaker yang sekarang tidak dapat dipertahankan dengan split yang
   sama.
2. **Kedua korpus perlu split baru, koreksi atas versi pertama dokumen ini.** Pada versi pertama saya
   menyatakan korpus STIF tidak perlu diregenerasi penuh karena pool-nya nol duplikat dan tidak ada
   replikasi template. Kedua alasan itu tetap benar, tetapi keduanya tidak menangkap kebocoran
   pasangan paralel. Karena sekitar 27% sampai 31% kalimat uji memiliki teks targetnya di dalam
   indeks retrieval, pool STIF harus dibersihkan dan eksperimen STIF perlu dijalankan ulang. Beban
   komputasinya tetap kecil, sekitar 8,5 menit per konfigurasi atau 4,5 jam untuk 32 konfigurasi.
3. **Klaim inti perlu digeser.** Klaim "centroid menyandikan gaya" tidak didukung data. Yang didukung
   data adalah temuan mekanistik yang justru lebih menarik: retrieval berbasis centroid mengalami
   degenerasi menjadi prompt statis, dan pada korpus dengan template berulang, degenerasi itu
   menghasilkan penyalinan eksemplar yang diberi nilai tinggi oleh classifier. Ini menjawab R2-01,
   R2-03, R2-09 sekaligus, dan metrik replikasi yang sudah dihitung di sini menjadi bukti barunya.
4. **Pemilihan alpha harus pindah ke development set.** Saat ini kelima nilai alpha dijalankan pada
   test set yang sama, lalu yang "optimal" dipilih dari hasil test set itu.

---

## 3. Alur perbaikan yang disarankan

Rincian tiap langkah, prasyarat, dan estimasi ada di sheet `Alur Perbaikan`. Ringkasannya:

### FASE 0: tetapkan fakta dan protokol (1 sampai 2 hari, tanpa GPU)

Langkah 0.1 sampai 0.3 sudah selesai, hasilnya ada di sheet `Bukti Temuan`. Yang tersisa adalah 0.4,
yaitu menulis protokol eksperimen ulang sepanjang satu sampai dua halaman sebelum menyentuh kode:
skema split Aaker, definisi development set untuk pemilihan alpha, jumlah ulangan, dan apakah
evaluasi manusia dijalankan. Protokol ini yang mencegah pengerjaan dua kali. Langkah 0.5 memilih
encoder evaluasi pengganti.

### FASE 1: perbaikan data (2 sampai 3 hari, tanpa GPU)

Bangun ulang split kedua korpus. Untuk Aaker: hapus duplikat teks, kelompokkan per
`conversation_id_str`, stratifikasi lima persona. Untuk STIF: terapkan penguncian pasangan paralel
(`pair_id`) yang sudah diklaim naskah padahal belum diterapkan. Keduanya prasyarat mutlak sebelum
rerun. Pada fase ini juga ditambahkan dua hal kecil yang
berdampak besar: pencatatan eksemplar dan prompt per sampel (sekarang tidak disimpan, padahal
dibutuhkan untuk metrik replikasi dan untuk materi suplemen), dan penguncian seed generasi (sekarang
seed 42 hanya dipakai untuk sampling partisi, bukan untuk generasi).

Catatan yang perlu ditulis di naskah: pengelompokan per akun tidak dapat dilakukan pada korpus ini
karena hanya ada 24 akun brand, sehingga alternatifnya adalah pengelompokan per percakapan ditambah
deduplikasi. Ini jawaban yang jujur dan dapat dipertahankan untuk permintaan grouped split
Reviewer 1.

### FASE 2: re-analisis artefak lama (1 sampai 2 hari, tanpa GPU)

Fase ini menutup banyak butir reviewer tanpa biaya GPU: encode ulang content preservation dengan
encoder independen (R2-08), ganti statistik fluency ke median dan trimmed mean (R2-21, R3-W5),
kalibrasi classifier pada `val_set` yang sudah bertanda label (R2-10, R3-W3), bootstrap interval
keyakinan dan uji signifikansi antar metode (R2-07), metrik replikasi template sebagai metrik baru
(R2-03, R2-09), protokol sampling analisis error yang konsisten (R2-22, R3-W4), dan penyusunan materi
suplemen (R2-18).

Kerjakan fase ini sebelum rerun, agar evaluasi tidak dijalankan dua kali dan agar hipotesis bisa diuji
lebih dulu tanpa biaya GPU.

### FASE 3: rerun eksperimen (sekitar 3 sampai 5 hari GPU)

Urutannya: regenerasi Aaker dengan split bersih (3.1), tambahkan baseline random-k dan zero-shot
(3.2, fungsi `retrieve_random` sudah ada di `retrieval_utils.py` tetapi belum pernah dijalankan),
pemilihan alpha pada development set (3.3), ulangan generasi tiga kali dengan seed terkunci untuk
pelaporan varians (3.4), serta regenerasi STIF dengan pool yang sudah dikunci pasangannya (3.6).
Terakhir, jalankan ulang pipeline evaluasi pada semua output baru (3.7).

Anggaran waktu dari timestamp run asli: median 8,5 menit per konfigurasi untuk STIF dan 27,7 menit
untuk Aaker. Satu kali ulang penuh Aaker sekitar 7,4 jam, dengan tiga ulangan sekitar 22 jam.

### FASE 4: evaluasi manusia (opsional, dapat berjalan paralel)

Butir R2-11 menuntut evaluasi manusia. Infrastrukturnya sudah dimiliki: rubrik penilaian dan tiga
penilai pernah dipakai untuk studi validitas dataset n=385, dan berkas 40 sampel per konfigurasi sudah
terekspor sebagai `*_HUMAN_EVAL.csv` (tanpa kolom penilaian). Jadi yang belum ada hanyalah penilaian
atas output generasi. Sampel 40 per konfigurasi terlalu banyak untuk dinilai seluruhnya; cukup pilih
sekitar 100 sampel tetap. Bila tidak dijalankan, nyatakan ketiadaan evaluasi manusia sebagai limitasi
secara eksplisit.

### FASE 5: penulisan, reframing, sitasi, reproducibility (setelah angka final)

Reframing klaim inti dan posisi terhadap Rocchio serta pseudo-relevance feedback (R2-01, R2-03,
R2-09), kualifikasi angka abstrak per korpus (R2-05), statistik deskriptif dan nilai p masuk tabel
(R2-06, R2-07), atribusi dataset STIF kepada Wibowo et al. (2020) dan sitasi model card Sahabat-AI
(R2-16, R2-19), notasi split dan terminologi BM25+ (R2-13, R2-14), renomori gambar dan tabel
menyeluruh (R2-24, R2-25, R2-28, R3-W1), language edit dan perbaikan encoding (R2-26, R2-27),
reproducibility dan rilis artefak (R2-15, R2-17, R2-18), lalu response letter (5.10).

---

## 4. Yang sebaiknya tidak dikerjakan lebih dulu

1. **Jangan perbaiki penomoran tabel, gambar, dan abstrak sekarang.** Angka pada Tabel 6, 7, 8 dan
   abstrak akan berubah setelah korpus Aaker diregenerasi.
2. **Jangan rerun Aaker sebelum split dibersihkan.** Selama duplikat pool ada, centroid tetap
   tertarik ke template yang sama dan hasilnya akan terulang.
3. **Jangan rerun sebelum pencatatan eksemplar ditambahkan.** Tanpa itu, metrik replikasi template
   tidak dapat dihitung dan klaim analisis error tetap tidak dapat diverifikasi reviewer.
4. **Jangan menulis ulang klaim zero-leakage sebelum split diperbaiki**, dan jangan mempertahankan
   pernyataan "not leaked" untuk korpus Aaker dalam bentuk apa pun.
5. **Jangan mempertahankan klaim penguncian pasangan (pair_id) pada korpus STIF.** Pengukuran
   menunjukkan penguncian itu tidak diterapkan, dan sekitar 27% sampai 31% kalimat uji memiliki teks
   targetnya di dalam indeks retrieval.
6. **Jawab butir lintas reviewer satu kali.** R2-10 sama dengan R3-W3, R2-12 sama dengan R3-W2, R2-21
   sama dengan R3-W5, R2-22 sama dengan R3-W4, dan R2-24, R2-25, R2-28 sama dengan R3-W1.

---

## 5. Berkas dalam folder ini

| Berkas | Fungsi |
|---|---|
| `JCCE-10619_Alur_Perbaikan_v1.xlsx` | Rencana kerja berurutan, peringatan urutan, bukti temuan, statistik dataset, anggaran komputasi |
| `build_plan_excel.py` | Pembuat workbook di atas. Semua angka bukti dihitung ulang dari repo, tidak ada yang disalin manual |
| `JCCE-10619_Mapping_Reviewer_Comments_v1.xlsx` | Pemetaan 38 butir komentar ke kategori (writing, rerun, dan lima kategori tambahan) |
| `build_mapping_excel.py` | Pembuat workbook pemetaan |
| `verify_split_protocol.py` | Mereproduksi protokol split kedua korpus dan menguji klaim penguncian pasangan paralel STIF |
| `PROTOKOL_SPLIT_JCCE-10619.md` | Dokumentasi protokol split, hasil verifikasi reproduksi, dan temuan penguncian pasangan |
| `KLAIM_VS_IMPLEMENTASI_PREPROCESSING.md` | Perbandingan klaim sub-bab Data Preprocessing pada naskah dengan implementasinya, plus draf pengganti untuk sub-bab tersebut |
| `verify_mapping.py` | Verifikasi independen bahwa setiap kutipan di workbook pemetaan benar-benar berasal dari docx |
| `README_mapping.md` | Dokumentasi workbook pemetaan |
| `RENCANA_PERBAIKAN_JCCE-10619.md` | Dokumen ini |

Menjalankan ulang:

```bash
python build_mapping_excel.py
python verify_mapping.py
python build_plan_excel.py
python verify_split_protocol.py
```

Keempat skrip bersifat read-only terhadap repo kode dan naskah. `build_plan_excel.py` membaca
`data/*/retrieval_pool.csv`, `outputs/cache/*.npy`, `evaluation_result/**/evaluated_*.csv`, serta
`Downloads/stif_formal.txt` dan `Downloads/stif_informal.txt`, jadi angkanya akan otomatis mengikuti
bila eksperimen dijalankan ulang.

---

## 6. Catatan

- Seluruh angka pada sheet `Bukti Temuan` dihasilkan skrip, bukan disalin dari percakapan. Bila
  dijalankan setelah rerun, angkanya akan berubah dan itu memang tujuannya.
- Estimasi komputasi memakai jumlah konfigurasi dan jumlah sampel yang sama dengan run asli.
  Penambahan baseline dan ulangan menambah waktu secara proporsional.
- Dua angka mudah salah dibaca: duplikat pool sebaiknya selalu dihitung per kelas (karena indeks
  retrieval dibangun per kelas), dan jumlah eksemplar berbeda pada kelas competence adalah 3 dari 5,
  bukan 4 dari 5 (empat eksemplar tampak sama pada 170 karakter pertama, tetapi berbeda pada teks
  lengkapnya).
