# JCCE-First Revision

Bundel kerja untuk menjalankan ulang seluruh eksperimen few-shot text style transfer pada
manuscript JCCE-10619 setelah reviewer meminta major revision.

Disusun agar dapat diserahkan langsung kepada agen LLM yang akan menjalankan eksperimen di
remote PC.

---

## Cara memulai

1. Jalankan `pip install -r requirements.txt`, lalu `python scripts/preflight.py` dan pastikan tidak
   ada kegagalan. Pemeriksaan ini mencakup versi pustaka, GPU, `HF_TOKEN`, kelengkapan berkas, dan
   kebocoran split.
2. Baca `PROTOKOL_RERUN.md` dari atas sampai bawah sebelum menjalankan perintah lain.
3. Perbarui `RUN_LOG.md` setiap kali satu langkah selesai.
4. Jalankan langkah 1 sampai 11 sesuai urutan pada protokol.
5. Tulis `LAPORAN_AKHIR.md` dengan format pada bagian 16 protokol.

### Membuka di Zed

Folder ini sudah memuat berkas instruksi proyek, sehingga agen membaca aturannya tanpa perlu
diberi tahu.

| Berkas | Dibaca oleh |
|---|---|
| `.rules` | Agen Zed. Ini berkas prioritas pertama pada urutan yang dipakai Zed |
| `AGENTS.md` | Agen eksternal, CLI, dan agen Zed pada pemuatan berikutnya bila `.rules` tidak ada |
| `PROTOKOL_RERUN.md` | Rujukan utama, disebut oleh kedua berkas di atas sebagai tindakan pertama |

Menurut dokumentasi Zed, berkas instruksi proyek dipilih dari yang pertama cocok pada urutan
`.rules`, lalu `.github/copilot-instructions.md`, lalu `AGENTS.md`. Karena `.rules` sudah ada, agen
Zed memakainya. `AGENTS.md` isinya identik dan disediakan sebagai cadangan bila agen dijalankan di
luar Zed atau sebagai CLI, karena agen semacam itu biasanya membaca berkas instruksinya sendiri.

Langkah praktisnya: buka folder ini di Zed, buka Agent Panel, lalu minta agen membaca
`PROTOKOL_RERUN.md` dan mengikuti instruksi proyek. Bila panel agen tidak memuat aturan secara
otomatis, sebut berkasnya secara eksplisit dengan sintaks `@` pada panel, misalnya `@PROTOKOL_RERUN.md`
dan `@.rules`.

---

## Isi folder

| Item | Isi |
|---|---|
| `PROTOKOL_RERUN.md` | Instruksi kerja lengkap: 11 langkah, perintah, patch kode, gerbang pemeriksaan, kriteria penerimaan |
| `.rules` dan `AGENTS.md` | Aturan proyek yang dibaca agen secara otomatis, berisi larangan dan tindakan pertama |
| `requirements.txt` | Dependensi dengan batas versi minimum |
| `RUN_LOG_TEMPLATE.md` | Template catatan kerja, salinan yang siap dipakai ada di `RUN_LOG.md` |
| `scripts/` | Sebelas script yang dijalankan, semuanya CLI |
| `DOKUMEN_PENDUKUNG/` | Protokol split, audit klaim, spesifikasi, pemetaan butir reviewer, dan bukti temuan |
| `classifier_formality/` | Script pelatihan classifier gaya korpus STIF beserta data dan split |
| `classifier_brand/` | Script pelatihan classifier gaya korpus Aaker beserta data dan split |
| `fewshot_formality/` | Pipeline generasi dan evaluasi korpus STIF |
| `fewshot_aaker/` | Pipeline generasi dan evaluasi korpus Aaker |

Nama folder sudah diberi nama baru agar mudah dirujuk. Padanan dengan nama aslinya:

| Nama di bundel ini | Nama asli di `C:\Devs\Code\Python` |
|---|---|
| `classifier_formality` | `formality_cls - Copy` |
| `classifier_brand` | `brand_personality_classification - Copy` |
| `fewshot_formality` | `TST_fewshot_formality_hf_ref` |
| `fewshot_aaker` | `TST_fewshot_aaker - Copy` |

---

## Script di `scripts/`

Seluruhnya dapat dipanggil dengan `--help`. Dikelompokkan menurut perannya.

**Kesiapan dan gerbang penerimaan**

| Script | Fungsi | Status uji |
|---|---|---|
| `preflight.py` | Memeriksa lingkungan, paket, GPU, token, kelengkapan berkas, dan kebocoran split dalam satu perintah. Keluar kode 1 bila ada kegagalan | sudah diuji, melaporkan 42 dari 47 pemeriksaan lulus pada mesin tanpa GPU |
| `check_smoke_output.py` | Gerbang untuk langkah 3: memeriksa kolom baru terisi, tidak ada fallback, eksemplar centroid identik, dan `sample_index` seragam antar metode | sudah diuji, benar menolak hasil lama yang belum dipatch |

**Pembuat dan pemeriksa split**

| Script | Fungsi | Status uji |
|---|---|---|
| `make_splits_formality.py` | Split korpus STIF pada pasangan paralel sehingga penguncian berlaku | sudah diuji pada data asli |
| `make_splits_brand.py` | Deduplikasi teks lalu split berstrata dan bergrup per percakapan | sudah diuji pada data asli |
| `verify_splits.py` | Memeriksa kebocoran antar split, dapat dipakai sebagai gerbang | sudah diuji pada data asli |

**Evaluator dan statistik**

| Script | Fungsi | Status uji |
|---|---|---|
| `evaluate_results.py` | Evaluator baru: encoder independen, kalibrasi, diagnostik degenerasi, laju replikasi | belum diuji, memerlukan GPU dan model |
| `report_metrics.py` | Statistik ringkas: median, trimmed mean, proporsi degenerate | sudah diuji pada hasil lama |
| `bootstrap_significance.py` | Interval keyakinan bootstrap dan uji berpasangan antar metode | sudah diuji pada hasil lama |
| `replication_metric.py` | Laju replikasi templat, dari kolom eksemplar atau rekonstruksi cache | sudah diuji pada hasil lama |

**Pemilihan alpha dan kalibrasi**

| Script | Fungsi | Status uji |
|---|---|---|
| `select_alpha_dev.py` | Memilih alpha pada development set dengan kriteria yang ditetapkan lebih dulu | sudah diuji pada hasil lama |
| `calibrate_classifier.py` | Temperature scaling pada validation set | belum diuji, memerlukan GPU dan model |

Script yang belum diuji sudah lulus pemeriksaan sintaks. Keduanya memerlukan model yang tidak
tersedia saat bundel ini disusun, sehingga pengujiannya dilakukan pada remote PC. Jalankan
keduanya dengan `--limit` lebih dulu bila ingin memeriksa jalurnya sebelum proses penuh.

---

## Berkas bobot model tidak disertakan

Folder bundel ini sengaja tidak memuat `model.safetensors`, `optimizer.pt`, dan checkpoint
pelatihan, karena ukurannya mencapai beberapa GB. Konsekuensinya classifier gaya **harus dilatih
ulang**, dan itu memang bagian dari protokol karena split berubah. Yang disertakan untuk setiap
classifier hanya `config.json`, tokenizer, dan laporan klasifikasi lama sebagai pembanding.

---

## Split lama dan split baru

Keduanya ada di bundel ini dan tidak saling menimpa:

| Folder | Isi | Sikap |
|---|---|---|
| `data/*_splits/` | Split yang dipakai eksperimen lama | Jangan diubah. Referensi pembanding |
| `data/*_splits_v2/` | Split baru, sudah dibuat dan terverifikasi | Dipakai seluruh eksperimen baru |

Split baru sudah lulus pemeriksaan kebocoran saat bundel ini disusun:
korpus Aaker turun dari 75.756 menjadi 62.052 baris setelah deduplikasi 18,1%, dan setelah split
tidak ada lagi teks identik maupun percakapan bersama antar split. Korpus STIF mempertahankan
ukuran yang sama (2.498 / 500 / 1.500 / 500) dengan setiap pasangan paralel utuh dalam satu split.

Setiap folder split baru memuat `split_manifest.json` yang mencatat seed, ukuran, hash berkas
sumber, dan versi pustaka.

---

## Angka pembanding dari eksperimen lama

Angka ini dipakai untuk memeriksa apakah hasil baru masuk akal. Semuanya dihitung ulang oleh
script di bundel ini pada hasil lama, dan juga tersedia di
`DOKUMEN_PENDUKUNG/Alur_Perbaikan_dan_Bukti_Temuan.xlsx` pada sheet `Bukti Temuan`.

| Temuan pada eksperimen lama | Nilai |
|---|---|
| Teks test korpus Aaker yang identik dengan retrieval pool | 629 |
| Teks train classifier yang identik dengan retrieval pool | 1.715 |
| Akun yang muncul di train sekaligus test | 24 dari 24 |
| Baris test dari percakapan yang juga ada di train | 33,5% |
| Duplikat di dalam retrieval index korpus Aaker | 21,3% (excitement), 13,7% (competence) |
| Pengulangan satu teks dalam satu index | 414 kali |
| Output metode centroid yang menyalin eksemplar, korpus Aaker | 76,6% |
| Output metode dense yang menyalin eksemplar, korpus Aaker | 0,4% |
| Pasangan paralel STIF yang berada di split yang sama | 35,7% (ekspektasi tanpa penguncian 36,0%) |
| Sampel uji yang pasangan targetnya ada di retrieval pool, STIF | 77 dari 246 dan 66 dari 244 |
| Output degenerate, PPL di atas 1000 | 0,61% korpus STIF, 5,51% korpus Aaker |

---

## Hal yang perlu diketahui sebelum menilai hasil baru

Empat hal berikut menjelaskan mengapa hasil baru akan berbeda dari yang lama, dan semuanya perlu
dilaporkan apa adanya.

1. **Penguncian pasangan mengubah keanggotaan split STIF**, bukan ukurannya. Sebagian kalimat uji
   bergeser, sehingga angka per konfigurasi akan berubah walau model dan prompt tidak berubah.
2. **Deduplikasi mengubah arah centroid korpus Aaker.** Setelah 13.704 baris duplikat dibuang,
   centroid tidak lagi tertarik ke satu templat boilerplate. Laju replikasi templat diharapkan
   turun, dan bila tidak turun, itu temuan yang perlu dilaporkan.
3. **Encoder content preservation berubah.** Kolom lama tetap dihitung agar besarnya perbedaan
   dapat dilihat. Jangan menyajikan kolom lama sebagai hasil utama.
4. **Classifier gaya dilatih ulang** pada split baru, sehingga skor gaya tidak dapat dibandingkan
   langsung dengan angka pada manuscript versi lama.

---

## Berkas pendukung di `DOKUMEN_PENDUKUNG/`

| Berkas | Isi |
|---|---|
| `PROTOKOL_SPLIT_JCCE-10619.md` | Protokol split kedua korpus, hasil verifikasi reproduksi, dan temuan penguncian pasangan |
| `KLAIM_VS_IMPLEMENTASI_PREPROCESSING.md` | Perbandingan klaim manuscript dengan implementasi, plus draf pengganti sub-bab tersebut |
| `SPESIFIKASI_RERUN.md` | Spesifikasi lengkap perubahan kode, urutan eksekusi, dan anggaran waktu |
| `PERUBAHAN_NASKAH.md` | Daftar perubahan manuscript per bagian, dipetakan ke butir reviewer |
| `RENCANA_PERBAIKAN_JCCE-10619.md` | Rencana perbaikan bertahap beserta temuan yang mendasarinya |
| `Pemetaan_Butir_Reviewer.xlsx` | 38 butir komentar reviewer dengan kategori, effort, dan tindakan yang diperlukan |
| `Alur_Perbaikan_dan_Bukti_Temuan.xlsx` | Rencana kerja, peringatan urutan, bukti temuan, statistik dataset, protokol split, dan daftar perubahan |

---

## Isi repositori dan berkas bobot yang tidak disertakan

Repositori ini memuat bahan yang dipakai untuk menjawab revisi manuscript JCCE-10619: data dan split
kedua korpus, skrip pelatihan dan evaluasi, hasil evaluasi per sampel, tabel uji statistik, berkas
sampel penilaian manusia, serta catatan pelaksanaan (`PROTOKOL_RERUN.md`, `RUNBOOK_OPERASIONAL.md`,
`RUN_LOG.md`, `LAPORAN_AKHIR.md`).

Empat berkas bobot classifier hasil fine-tuning (`model.safetensors`, masing-masing sekitar 475 MB,
total sekitar 1,9 GB) tidak disertakan karena ukurannya, begitu pula `training_args.bin` di dalam
folder yang sama:

| Berkas | Peran |
|---|---|
| `classifier_formality/model_results_dir/formality_model_roberta/model.safetensors` | classifier formality dua kelas |
| `classifier_brand/model_results_dir/brand_model_roberta/model.safetensors` | classifier brand personality lima kelas |
| `fewshot_formality/style_classifier/model.safetensors` | salinan yang dipakai tahap few-shot korpus formality |
| `fewshot_aaker/style_classifier/model.safetensors` | salinan yang dipakai tahap few-shot korpus brand personality |

Berkas konfigurasi dan tokenizer di folder yang sama tetap disertakan. Untuk membangun ulang
checkpoint, latih classifier dengan `classifier_formality/main.py` dan `classifier_brand/main.py`
mengikuti langkah pada `PROTOKOL_RERUN.md`; data dan split yang dibutuhkan sudah ada di repositori.

