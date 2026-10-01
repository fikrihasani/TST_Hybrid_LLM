# RUN_LOG

Catatan kerja saat menjalankan `PROTOKOL_RERUN.md`. Salin berkas ini menjadi `RUN_LOG.md` lalu
perbarui setiap kali satu langkah selesai.

---

## Lingkungan

| Item | Nilai |
|---|---|
| Tanggal mulai | 2026-09-25 |
| Tanggal selesai | 2026-09-28 |
| GPU dan VRAM | NVIDIA GeForce RTX 4070 Ti, 12.282 MiB total (12,0 GB), 10.498 MiB bebas, driver 560.94 |
| Python | 3.14.4 |
| torch / transformers / sentence-transformers | 2.11.0+cu126 / 5.8.0 / 5.4.1 |
| scikit-learn / pandas / numpy | 1.8.0 / 3.0.2 / 2.4.4 |
| tqdm / rank-bm25 / scipy | 4.67.3 / 0.2.2 / 1.17.1 |
| accelerate / bitsandbytes / huggingface_hub | 1.13.0 / 0.49.2 / 1.13.0 |
| `HF_TOKEN` terpasang | ya, variabel user (di-set 2026-09-25, 37 karakter) |
| Catatan VRAM | 12,0 GB di bawah syarat 16 GB pada bagian 1 protokol. Disetujui manusia untuk lanjut di mesin ini dengan mitigasi bagian 17, dicatat sebagai penyimpangan |
| Catatan versi | pandas 3.0.2 dan transformers 5.8.0 jauh di atas versi uji bundel. `preflight.py` hanya memeriksa batas minimum, jadi ketidakcocokan API baru akan terlihat pada langkah 2 dan 3 |

---

## Catatan per langkah

Format untuk setiap langkah: perintah yang dijalankan, waktu mulai dan selesai, keluaran penting,
status.

### Prasyarat. Pemeriksaan kesiapan (`preflight.py`)

```
perintah: & 'C:\Ana3\envs\fikri_hasani\python.exe' scripts/preflight.py   (dijalankan di akar bundel)
mulai  : 2026-09-25, sesi yang sama dengan penyusunan laporan prakerja
selesai: 2026-09-25 15:57:46 (stempel waktu berkas preflight.json)
hasil  :
  run 1, sebelum patch preflight.py        : 44/47 lulus, exit 1
      gagal: rank_bm25 (negatif palsu), GPU 12,0 GB, HF_TOKEN kosong
  run 2, sesudah patch preflight.py        : 45/47 lulus, exit 1
      gagal: GPU 12,0 GB, HF_TOKEN (env sesi agen belum diperbarui setelah setx)
  run 3, HF_TOKEN disuntikkan ke proses    : 46/47 lulus, exit 1
      gagal: GPU 12,0 GB saja
berkas keluaran: preflight.json (keluaran run terakhir)
gerbang split : keempat pemeriksaan sesuai harapan
  Aaker split lama   GAGAL  : duplikat lintas split maks 503, ada percakapan bersama
  Aaker split baru   LOLOS  : duplikat 0, tidak ada percakapan bersama
  STIF  split lama   GAGAL  : duplikat lintas split maks 1 (toleransi 0)
  STIF  split baru   LOLOS  : duplikat lintas split maks 1 (toleransi 5, dari baris ganda di sumber)
berkas wajib   : 29 dari 29 ditemukan, termasuk fewshot_config.json dan style_classifier/config.json
                 pada kedua repo
status : lulus dengan satu penyimpangan yang disetujui manusia (VRAM 12,0 GB < syarat 16 GB)
```

### Langkah 1. Verifikasi split baru

```
perintah:
  cd scripts
  python verify_splits.py --dir ../fewshot_aaker/data/brand_splits    --gate
  python verify_splits.py --dir ../fewshot_aaker/data/brand_splits_v2 --gate
  python verify_splits.py --dir ../fewshot_formality/data/formality_splits    --gate
  python verify_splits.py --dir ../fewshot_formality/data/formality_splits_v2 --gate --tolerance 5
  Keempatnya dijalankan lewat pembungkus Python (subprocess, cwd=scripts) yang menangkap kode
  keluar, karena PowerShell tidak memiliki padanan langsung untuk echo "exit=$?". Argumen dan
  direktori kerja sama persis dengan bagian 4 protokol.
mulai  : 2026-09-25 (sesi yang sama; stempel presisi hanya tercatat untuk waktu selesai)
selesai: 2026-09-25 16:00:22
hasil  :
  1a Aaker split lama   exit 1  GAGAL  : duplikat maks 503 (kelas sophistication, retrieval_pool
      vs train_set) dan duplikat pada keempat kelas lain; percakapan bersama pada keenam pasangan
      split (mis. test_set vs train_set: 1.908 percakapan, 15,0% baris train_set); akun 24 dari 24
  1b Aaker split baru   exit 0  LOLOS  : nol duplikat di kelima kelas, nol percakapan bersama
  1c STIF  split lama   exit 1  GAGAL  : kelas formal train_set vs val_set 1; kelas informal
      retrieval_pool vs test_set 1 dan test_set vs train_set 1
  1d STIF  split baru   exit 0  LOLOS  : kelas formal nol; kelas informal retrieval_pool vs
      train_set 1, masih dalam toleransi 5
  Ukuran STIF v2 tetap: train 2.498 / val 500 / retrieval_pool 1.500 / test 500 = 4.998
  Ukuran Aaker v2 turun: 75.756 -> 62.052 baris (deduplikasi 13.704 baris, 18,1%)
  Catatan kualitatif: korpus Aaker hanya memuat 24 akun dan pada split v2 pun setiap akun muncul
  di lebih dari satu split (mis. alpha_dev sekaligus retrieval_pool: 24 dari 24). Pengelompokan
  level akun karena itu tidak mungkin; split v2 mengandalkan pengelompokan level percakapan
  (conversation_id_str), yang pada split baru sudah bersih sepenuhnya
status : lulus. Gerbang lanjut bagian 4 terpenuhi: kedua split baru lolos
```

### Langkah 2. Patch konfigurasi dan pipeline

```
perintah:
  patch manual pada enam berkas sesuai bagian 5.1 sampai 5.7, lalu pemeriksaan bagian 5.8:
  cd fewshot_formality && python -m py_compile fewshot_formality.py retrieval_utils.py
  cd fewshot_aaker     && python -m py_compile main.py retrieval_utils.py
  python -c "import json;print(json.load(open('fewshot_config.json'))['split_dir'])"
  py_compile dan pembacaan config dijalankan lewat pembungkus Python (subprocess) agar kode keluar
  dan nilai config dari kedua repo tercatat sekaligus
mulai  : 2026-09-25
selesai: 2026-09-25 21:20:58
berkas yang diubah:
  fewshot_formality/fewshot_config.json   split_dir, retrieval_methods, run_seeds, sampling_seed,
                                          human_eval_samples
  fewshot_aaker/fewshot_config.json       sama, num_examples_range tetap [5]
  fewshot_formality/retrieval_utils.py    retrieve_random diberi parameter seed
  fewshot_aaker/retrieval_utils.py        sama
  fewshot_formality/fewshot_formality.py  get_style_examples, robust_chat_completion,
                                          generate_paraphrases_sequential, blok results_df,
                                          loop run_seeds, lewati zero_shot untuk k>1,
                                          sufiks _seed{run_seed}, --only-seed, import sys
  fewshot_aaker/main.py                   sama; sistem prompt tetap tanpa keterangan formality
hasil py_compile:
  fewshot_formality -> exit 0 | fewshot_aaker -> exit 0
hasil config:
  formality: split_dir data/formality_splits_v2, metode 6, k [5, 10], alpha 5, run_seeds [42, 43, 44],
             human_eval_samples 25, sampling_seed 42
  aaker    : split_dir data/brand_splits_v2, metode 6, k [5], alpha 5, run_seeds [42, 43, 44],
             human_eval_samples 25, sampling_seed 42
pemeriksaan tambahan di luar bagian 5.8:
  - cabang zero-shot: setelah blok contoh referensi dihapus, placeholder {style_examples_str} dan
    judul CONTOH REFERENSI tidak tersisa pada kedua template prompt, teks sumber tetap ada
  - retrieve_random: seed sama menghasilkan sampel identik, seed berbeda berbeda, tanpa seed tetap jalan
  - tidak ada lagi rujukan ke variabel lama paraphrased_messages
  - hf_token di config masih VALID (akun fikrihasani); initialize_models memakai ENV HF_TOKEN lebih dulu
status : lulus
```

Catatan penafsiran yang dipakai saat patch:

1. Protokol 5.7.1 menempatkan pemeriksaan `zero_shot` di awal iterasi `num_examples`, padahal
   variabel `method` baru ada di loop dalam. Pemeriksaan diletakkan di awal loop `method`; efeknya
   sama, yaitu `zero_shot` hanya dijalankan pada k terkecil (5).
2. `--only-seed` ditempatkan di `main()` tepat setelah `load_config()`, sesuai bagian 5.7.3.
3. Loop `run_seeds` membungkus loop `num_examples` di dalam loop `personality`, sehingga model dan
   indeks retrieval tidak dimuat ulang per seed.
4. `sampling_seed` ditambahkan ke config karena diminta bagian 5.1, tetapi belum dibaca script mana pun;
   tidak ada pemakaian baru yang dikarang untuknya.
5. `DEFAULT_CONFIG` di dalam kedua script masih berisi nilai lama dan hanya dipakai `ensure_setup()`
   bila `fewshot_config.json` tidak ada (baris 86). Config JSON yang ada sekarang yang menentukan
   seluruh nilai, jadi tidak ada perubahan di sana sesuai bagian 18.

### Langkah 3. Uji jalur dengan sampel kecil

```
perintah:
  config sementara formality: num_samples 5, num_examples_range [5],
      retrieval_methods [dense, centroid, zero_shot], run_seeds [42], hybrid_alphas []
  python fewshot_formality.py   (latar belakang, log run_smoke_formality.log)
  config penuh kedua repo dicadangkan lebih dulu ke %TEMP%\jcce_backup_*.json
mulai  : 2026-09-25 21:26:08
selesai: 2026-09-25 21:27:20 (30 generasi, masing-masing gagal seketika)
hasil  :
  Muat model: BERHASIL. Tidak ada pesan 'Gagal memuat model', jadi google/gemma-3-4b-it 4-bit
  dapat dimuat pada GPU 12 GB. Deviasi VRAM tidak menghalangi pemuatan model.
  Generasi: GAGAL seluruhnya. Pesan yang sama muncul 30 kali (sekali per sampel):
    ERROR - Hugging Face generation failed: The following `model_kwargs` are not used by the
    model: ['generator'] (note: typos in the generate arguments will also show up in this list)
  Kolom baru dari patch bagian 5.6 tetap terbentuk dan terisi, tetapi kolom paraphrased_message
  berisi 'ERROR: Gagal memproses hasil.' pada semua baris. Gerbang check_smoke_output.py tidak
  dijalankan karena pasti gagal pada pemeriksaan 'tidak ada keluaran ERROR'.
  Catatan: uji jalur ini memakai cache embedding retrieval lama yang masih ada di outputs/cache,
  sehingga indeks retrieval yang dipakai berasal dari split lama, bukan split v2.
berkas yang terlibat:
  fewshot_formality/fewshot_formality.py  -> robust_chat_completion (bagian 5.4 protokol)
  keluaran tidak valid: 12 berkas *_seed42_*.csv di
  fewshot_formality/model_results_dir/google_gemma-3-4b-it (6 results + 6 HUMAN_EVAL)
  config kedua repo sudah dipulihkan ke nilai penuh dari cadangan
status : GAGAL pada percobaan pertama. Langkah dihentikan menurut aturan 3 dan gerbang bagian 6.

Percobaan kedua sesudah perbaikan:
  yang diperbaiki lebih dulu:
    - robust_chat_completion: kwarg generator diganti torch.manual_seed(int(seed)) pada kedua pipeline
    - cache embedding retrieval lama dinetralkan dengan penggantian nama (lihat tabel keputusan)
    - proses dijalankan dengan PYTHONIOENCODING=utf-8 dan PYTHONUTF8=1
    - 12 berkas keluaran percobaan pertama yang tidak valid dipindahkan ke smoke_output_dir/
  perintah:
    config smoke formality, lalu python fewshot_formality.py     (log run_smoke_formality.log)
    config smoke aaker, lalu python main.py                      (log run_smoke_aaker.log)
    python check_smoke_output.py --dir ../fewshot_formality/smoke_output_dir/google_gemma-3-4b-it --num-examples 5 --json ../smoke_formality.json
    python check_smoke_output.py --dir ../fewshot_aaker/smoke_output_dir/google_gemma-3-4b-it --num-examples 5 --json ../smoke_aaker.json
  mulai  : 2026-09-25 21:35:05 (formality), aaker menyusul 21:39
  selesai: 2026-09-25 21:47:54
  hasil  :
    formality: 'ALL FEW-SHOT EXPERIMENTS COMPLETED', 0 keluaran ERROR, 0 generation gagal,
               0 UnicodeEncodeError, 12 berkas keluaran (2 target x 3 metode, results + HUMAN_EVAL)
    aaker    : sama, 12 berkas keluaran, 0 ERROR
    gerbang formality: 154 lulus, 0 gagal, exit 0
    gerbang aaker    : 154 lulus, 0 gagal, exit 0
    fallback retrieval: 0 pada seluruh berkas kedua korpus
    eksemplar centroid: tepat satu himpunan per target (query-independent) dan 5 teks berbeda
      dari 5 eksemplar pada keempat berkas centroid, jadi tidak ada eksemplar kembar
    cache retrieval: dibangun ulang dari pool v2, terverifikasi identik dengan
      formality_splits_v2 dan brand_splits_v2
    himpunan sample_index: sama di seluruh metode pada setiap target kedua korpus
  berkas keluaran: smoke_formality.json, smoke_aaker.json, run_smoke_formality.log, run_smoke_aaker.log
  Catatan: gerbang dijalankan terhadap smoke_output_dir, bukan model_results_dir, karena folder hasil
  masih memuat 96 berkas lama tanpa kolom baru sehingga gerbang akan gagal pada berkas lama itu
  (lihat baris keputusan tentang pola berkas untuk Langkah 8)
status : LOLOS. Gerbang lanjut bagian 6 terpenuhi untuk kedua korpus.
```

### Langkah 4. Latih ulang classifier dan kalibrasi

```
perintah:
  patch main.py kedua classifier: hapus blok split, baca berkas split v2, tambahkan set_seed(42)
    (set_seed sudah ada di classifier_brand/main.py, ditambahkan di classifier_formality/main.py)
  cd classifier_formality && python main.py     (log run_train_formality.log)
  cd classifier_brand     && python main.py     (log run_train_brand.log)
  penyalinan isi folder model ke style_classifier (checkpoint tidak disalin)
  cd scripts
  python calibrate_classifier.py --classifier ../fewshot_formality/style_classifier --val ../fewshot_formality/data/formality_splits_v2/val_set.csv --text-col text --style-col formality
  python calibrate_classifier.py --classifier ../fewshot_aaker/style_classifier --val ../fewshot_aaker/data/brand_splits_v2/val_set.csv --text-col cleaned_text --style-col personality
mulai  : 2026-09-25 21:54:26
selesai: 2026-09-25 22:08:22
hasil  :
  Ukuran data latih dari split v2:
    formality: train 2.498 / val 500 / test 500
    Aaker    : train 24.820 / val 6.205 / test 6.205 (retrieval_pool 18.617; 62.052 baris = keempat
               split ini + alpha_dev 6.205)
  classifier formality, test set 500 baris, 1.570 langkah (10 epoch x 157):
    akurasi 0,9220 | macro avg F1 0,9219 | formal P 0,8981 R 0,9520 F1 0,9243 | informal P 0,9489 R 0,8920 F1 0,9196
    pembanding lama (classification_report_test_LAMA_20260611.txt, support 500): akurasi 0,9220,
    formal F1 0,9225, informal F1 0,9215. Angka total kebetulan sama, angka per kelas berbeda,
    sehingga terbukti pelatihan memakai split v2 (bukan salinan laporan lama)
  classifier Aaker, test set 6.205 baris, 7.760 langkah (10 epoch x 776):
    Macro-F1 0,9043 | akurasi 0,91 | F1 competence 0,97, excitement 0,88, ruggedness 0,84,
    sincerity 0,90, sophistication 0,93
    pembanding lama (test_report_LAMA_20260611.txt, support 7.576): akurasi 0,93; F1 competence 0,98,
    excitement 0,92, ruggedness 0,86, sincerity 0,92, sophistication 0,95. Seluruh kelas turun tipis,
    konsisten dengan deduplikasi dan pemisahan percakapan pada split v2
  kalibrasi formality (fewshot_formality/style_classifier/calibration.json, n_val 500):
    T 0,9805 | akurasi 0,9440 | NLL 0,1578 -> 0,1578 | ECE 0,0131 -> 0,0132
    keyakinan rata-rata 0,9434 -> 0,9451
    median prob kelas target 0,97317 -> 0,97497, persentil 5-95 [0,42981, 0,99844] -> [0,42843, 0,99863]
  kalibrasi Aaker (fewshot_aaker/style_classifier/calibration.json, n_val 6.205):
    T 2,6779 | akurasi 0,9168 | NLL 0,6087 -> 0,3013 | ECE 0,0739 -> 0,0437
    keyakinan rata-rata 0,9905 -> 0,9304
    median prob kelas target 0,99998 -> 0,95789, persentil 5-95 [0,00158, 0,99998] -> [0,07136, 0,96225]
  Gerbang bagian 7: calibration.json terbentuk di kedua style_classifier; bobot model.safetensors
  (498,6 MB) ada di kedua style_classifier sehingga evaluate_results.py dan calibrate_classifier.py
  dapat memuatnya
berkas keluaran:
  fewshot_formality/style_classifier/{model.safetensors, config.json, tokenizer.json, tokenizer_config.json,
    calibration.json, classification_report_test.txt}
  fewshot_aaker/style_classifier/{model.safetensors, config.json, tokenizer.json, tokenizer_config.json,
    calibration.json, test_report.txt}
  laporan lama diamankan (tidak dihapus): classification_report_test_LAMA_20260611.txt pada
    classifier_formality/model_results_dir/formality_model_roberta dan fewshot_formality/style_classifier;
    test_report_LAMA_20260611.txt pada classifier_brand/model_results_dir/brand_model_roberta dan
    fewshot_aaker/style_classifier
  log: run_train_formality.log, run_train_brand.log
status : lulus
```

### Langkah 5. Sapuan alpha pada development set

```
perintah (masih berjalan, blok ini dilengkapi bila langkah selesai):
  langkah persiapan sesuai tiga usulan yang disetujui manusia:
    1. folder dev set dibuat tanpa menyentuh folder v2:
         fewshot_formality/data/formality_splits_v2_alphadev/  (pool v2 + test_set.csv dari val_set.csv)
         fewshot_aaker/data/brand_splits_v2_alphadev/          (pool v2 + test_set.csv dari alpha_dev.csv)
       retrieval_pool.csv pada kedua folder dev terverifikasi identik dengan pool v2 (md5 sama)
    2. fewshot_config.json ditukar sementara karena load_config() tidak menerima nama berkas lain
       (fewshot_config_alphadev.json tidak akan terbaca)
    3. output_dirs.results diarahkan ke model_results_dir_alphadev agar tidak menimpa hasil Langkah 6
  config formality: split_dir data/formality_splits_v2_alphadev, num_samples all, k [5],
      retrieval_methods [hybrid_early], run_seeds [42], hybrid_alphas [0.1, 0.3, 0.5, 0.7, 0.9]
  python fewshot_formality.py     (latar belakang, log run_alphadev_formality.log)
mulai  : 2026-09-25 22:26:17
kemajuan yang sudah diperiksa:
  konfigurasi selesai: 3 dari 10 pada 22:41 | keluaran ERROR 0 | generation gagal 0
  berkas terverifikasi: STIF_formal_fewshot_hybrid_early_alpha0.1_5_seed42_results.csv berisi 250 baris
    dengan kolom alpha 0,1 dan run_seed 42, dan berkas _HUMAN_EVAL memuat 25 baris
  laju: sekitar 2,1 detik per sampel, jadi 10 konfigurasi (2 target x 5 alpha) diperkirakan 35 sampai 50 menit
status : langkah (c), (d), dan (e) SELESAI; config sudah dipulihkan; menunggu persetujuan manusia sebelum Langkah 6

Langkah (c) evaluasi sapuan alpha-dev Aaker, tanpa fluency:
  perintah: python scripts/evaluate_results.py --results ../fewshot_aaker/model_results_dir_alphadev/google_gemma-3-4b-it --classifier ../fewshot_aaker/style_classifier --out ../fewshot_aaker/evaluation_result_alphadev/google_gemma-3-4b-it --calibration ../fewshot_aaker/style_classifier/calibration.json --encoder LaBSE=sentence-transformers/LaBSE --skip-fluency
  hasil: exit 0, durasi 61,7 detik, 10 berkas evaluated_v2_* tertulis di
    fewshot_aaker/evaluation_result_alphadev/google_gemma-3-4b-it, T = 2,6779 dibaca dari calibration.json
  catatan: peluncuran pertama lewat Start-Process dengan pengalihan stdout dan stderr mati seketika tanpa
    keluaran sama sekali (kedua berkas log 0 byte, PID hilang, tidak ada berkas hasil). Perintah yang sama
    dijalankan ulang di depan dengan penangkapan keluaran dan berhasil. Peluncuran berikutnya memakai
    peluncur Python detached dengan DUA berkas terpisah untuk stdout dan stderr

Langkah (d) pemilihan alpha Aaker (kriteria rata-rata harmonik, kolom isi content_preservation_LaBSE):
  perintah: python select_alpha_dev.py --dir ../fewshot_aaker/evaluation_result_alphadev/google_gemma-3-4b-it --content-col content_preservation_LaBSE --out ../fewshot_aaker/alpha_star.json

    target competence
      alpha 0,1 -> akurasi 0,872 | konten 0,41163 | H 0,55926
      alpha 0,3 -> akurasi 0,838 | konten 0,49807 | H 0,62479   <- terpilih
      alpha 0,5 -> akurasi 0,452 | konten 0,65587 | H 0,53518
      alpha 0,7 -> akurasi 0,226 | konten 0,71637 | H 0,34360
      alpha 0,9 -> akurasi 0,152 | konten 0,71818 | H 0,25090
      jarak H peringkat pertama ke kedua: 0,06551
    target excitement
      alpha 0,1 -> akurasi 0,318 | konten 0,70443 | H 0,43819
      alpha 0,3 -> akurasi 0,326 | konten 0,71801 | H 0,44841
      alpha 0,5 -> akurasi 0,336 | konten 0,73569 | H 0,46131   <- terpilih menurut kriteria
      alpha 0,7 -> akurasi 0,310 | konten 0,74856 | H 0,43843
      alpha 0,9 -> akurasi 0,260 | konten 0,74773 | H 0,38584
      jarak H peringkat pertama ke kedua: 0,01290
  kualifikasi: pada competence jarak 0,06551 cukup terbedakan. Pada excitement jarak hanya 0,01290,
    sehingga menurut runbook bagian 4 langkah 5 alpha 0,5 TIDAK boleh disebut optimal tanpa kualifikasi;
    keputusan akhir diserahkan ke uji signifikansi berpasangan Langkah 9. Akurasi target excitement adalah
    0,318 sampai 0,336 pada alpha 0,1 sampai 0,5 dan 0,260 sampai 0,310 pada alpha 0,7 sampai 0,9.
    KOREKSI 2026-09-26: aras acak korpus Aaker adalah 0,20 karena korpus ini punya lima kelas
    kepribadian, bukan 0,50 seperti pada tugas biner. Jadi angka itu sekitar 1,6 kali aras acak, bukan
    berada dekat aras acak. Sebaran antar alpha hanya 0,018 sehingga tetap di bawah satu galat baku,
    jadi kesimpulan kualifikasi tidak berubah. Sebagai pembanding, akurasi competence pada alpha 0,1
    sampai 0,3 (0,838 sampai 0,872) adalah sekitar 4,2 sampai 4,4 kali aras acak
  berkas: fewshot_aaker/alpha_star.json

Langkah (e) dan analisis tambahan output_tokens (sepuluh berkas hasil sapuan):
  rata-rata output_tokens (median), rata-rata karakter keluaran, rata-rata karakter teks asli:
    competence α=0,1  58,69 (63)  214,94  106,87
    competence α=0,3  49,75 (49)  188,42  106,87
    competence α=0,5  37,73 (38)  142,70  106,87
    competence α=0,7  32,60 (32)  121,45  106,87
    competence α=0,9  31,61 (30)  116,02  106,87
    excitement α=0,1  40,88 (40,5) 145,08  144,20
    excitement α=0,3  38,36 (38)   138,83  144,20
    excitement α=0,5  37,66 (37)   137,57  144,20
    excitement α=0,7  36,42 (35)   134,25  144,20
    excitement α=0,9  36,56 (35)   135,72  144,20
  rasio panjang keluaran terhadap teks asli: competence 2,011 / 1,763 / 1,335 / 1,136 / 1,086 dan
    excitement 1,006 / 0,963 / 0,954 / 0,931 / 0,941
  kesimpulan: hipotesis "alpha kecil menghasilkan keluaran lebih panjang" DIDUKUNG KUAT pada target
    competence (monoton turun 58,69 menjadi 31,61 token, rasio 2,011 menjadi 1,086) tetapi LEMAH pada
    target excitement (40,88 menjadi 36,56 token, rasio 1,006 menjadi 0,941, dan nilai terpendek ada di
    α=0,7 bukan α=0,9). Dilaporkan apa adanya: dukungan bukti untuk R2-09 hanya kuat pada competence
  Penafsiran tambahan: pada target excitement rasio panjang keluaran terhadap teks asli mendekati 1,0
    di semua alpha (0,941 sampai 1,006), sehingga keluarannya nyaris sekadar parafrase dan gaya tidak
    berpindah. Itu menjelaskan mengapa akurasi target excitement bertahan di sekitar 0,33

Pemulihan konfigurasi sebelum Langkah 6 (dua syarat manusia) beserta bukti:
  1. split_dir = data/brand_splits_v2, tanpa kata dev, memuat _v2
  2. output_dirs.results = model_results_dir
  Keadaan penuh lain: num_samples 500, num_examples_range [5], enam metode termasuk random dan zero_shot,
    run_seeds [42, 43, 44], hybrid_alphas lima nilai, skip_existing false
  Bukti dari python scripts/status.py pukul 16:21:03:
    KONFIGURASI formality dan aaker bersih TANPA satu pun peringatan
    BERKAS HASIL: kedua repo membaca model_results_dir, tanpa peringatan direktori hasil berbeda
    PROSES PYTHON: kosong, tidak ada proses yang hidup

Sapuan alpha Aaker, generasi:
  perintah : python main.py dengan config split_dir data/brand_splits_v2_alphadev, num_samples 500,
             num_examples_range [5], retrieval_methods [hybrid_early], run_seeds [42],
             hybrid_alphas [0.1, 0.3, 0.5, 0.7, 0.9], output_dirs.results model_results_dir_alphadev
  PID : 10008 | mulai 2026-09-26 10:15:27 | selesai 2026-09-26 15:14:04 (4 jam 58 menit 37 detik)
  log peluncuran: run_alphadev_aaker.log
  log internal : fewshot_aaker/outputs/fewshot_logs/google_gemma-3-4b-it/fewshot_experiment_20260926-101533.log
                 baris pertama 10:15:33,222 | baris terakhir '2026-09-26 15:14:04,436 - INFO - ALL
                 FEW-SHOT EXPERIMENTS COMPLETED.' | 0 baris ERROR, 0 baris WARNING pada log internal
  durasi dan laju per konfigurasi (masing-masing 500 sampel):
    competence α=0.1  43 menit 16 detik  5,19 detik/sampel
    competence α=0.3  37 menit  4 detik  4,45 detik/sampel
    competence α=0.5  28 menit 16 detik  3,39 detik/sampel
    competence α=0.7  24 menit 14 detik  2,91 detik/sampel
    competence α=0.9  23 menit 42 detik  2,84 detik/sampel
    excitement α=0.1  30 menit 20 detik  3,64 detik/sampel
    excitement α=0.3  28 menit 36 detik  3,43 detik/sampel
    excitement α=0.5  28 menit  7 detik  3,37 detik/sampel
    excitement α=0.7  27 menit 13 detik  3,27 detik/sampel
    excitement α=0.9  27 menit 16 detik  3,27 detik/sampel
  total 4 jam 58 menit untuk 5.000 generasi = 3,58 detik/sampel rata-rata. Konfigurasi pertama paling
    lambat (5,19 detik/sampel) lalu stabil di sekitar 2,8 sampai 3,6 detik/sampel. Laju stabil ini
    setara dengan 3,3 detik/sampel yang dicatat runbook untuk mesin asli, jadi anggaran waktu bagian 6
    runbook (55 sampai 60 jam) cenderung terlalu konservatif; perkiraan berbasis laju stabil ada di
    catatan waktu langkah ini
  jumlah retrieval_fallback: 0 pada kesepuluh berkas
  jumlah keluaran ERROR    : 0 pada kesepuluh berkas

Pemeriksaan kelengkapan sesuai tiga syarat tambahan manusia:
  1. daftar nama *_results.csv setelah diurutkan (10 berkas, dua target x lima alpha, tanpa pengulangan):
       AAKER_competence_fewshot_hybrid_early_alpha0.1_5_seed42_results.csv
       AAKER_competence_fewshot_hybrid_early_alpha0.3_5_seed42_results.csv
       AAKER_competence_fewshot_hybrid_early_alpha0.5_5_seed42_results.csv
       AAKER_competence_fewshot_hybrid_early_alpha0.7_5_seed42_results.csv
       AAKER_competence_fewshot_hybrid_early_alpha0.9_5_seed42_results.csv
       AAKER_excitement_fewshot_hybrid_early_alpha0.1_5_seed42_results.csv
       AAKER_excitement_fewshot_hybrid_early_alpha0.3_5_seed42_results.csv
       AAKER_excitement_fewshot_hybrid_early_alpha0.5_5_seed42_results.csv
       AAKER_excitement_fewshot_hybrid_early_alpha0.7_5_seed42_results.csv
       AAKER_excitement_fewshot_hybrid_early_alpha0.9_5_seed42_results.csv
     pasangan (target, alpha) unik = 10, target {competence, excitement}, alpha {0.1, 0.3, 0.5, 0.7, 0.9}
  2. setiap berkas *_results.csv berisi tepat 500 baris: terpenuhi untuk kesepuluhnya
  3. jumlah retrieval_fallback 0 dan keluaran ERROR 0 pada kesepuluh berkas, konsisten dengan 0 baris
     ERROR dan 0 baris WARNING pada log internal
  Selain itu terdapat 10 berkas *_HUMAN_EVAL.csv, sehingga total 20 berkas hasil di direktori itu

Langkah (a) arsip cadangan:
  tujuan ARSIP/alphadev_aaker, 23 berkas = 20 berkas hasil (salin, bukan pindah) + config_saat_alphadev.json
  + log_internal_alphadev_aaker.log + log_peluncuran_alphadev_aaker.log
  Berkas asli tetap ada di fewshot_aaker/model_results_dir_alphadev/google_gemma-3-4b-it (20 berkas),
  terverifikasi sesudah penyalinan. Sumber arsip memakai model_results_dir_alphadev, bukan
  model_results_dir seperti contoh perintah pada runbook, karena config sapuan memang menunjuk ke sana

Hasil formality:
  generasi: 22:26:22 -> 23:51:20 (1 jam 25 menit) untuk 2.500 generasi, 10 konfigurasi,
    0 keluaran ERROR, 0 generation gagal, setiap berkas 250 baris dan 25 baris HUMAN_EVAL
  evaluasi: 10 dari 10 berkas, fluency terhitung, 0 galat, 0 OOM; median PPL berkisar 41,55 sampai
    64,53 dengan 1 sampai 6 keluaran degenerate per 250 baris (ambang PPL 1000)
    keluaran: fewshot_formality/evaluation_result_alphadev/google_gemma-3-4b-it/evaluated_v2_*.csv
    log: run_eval_alphadev_formality.log
  pemilihan alpha (rata-rata harmonik akurasi gaya dan content preservation):

    target formal (kolom isi = content_preservation_LaBSE)
      alpha 0,1 -> akurasi 0,136 | konten 0,69427 | H 0,22745
      alpha 0,3 -> akurasi 0,116 | konten 0,72953 | H 0,20017
      alpha 0,5 -> akurasi 0,120 | konten 0,74094 | H 0,20655
      alpha 0,7 -> akurasi 0,128 | konten 0,74233 | H 0,21835
      alpha 0,9 -> akurasi 0,108 | konten 0,75980 | H 0,18912
      alpha terpilih: 0,1 (H 0,22745)
    target informal (kolom isi = content_preservation_LaBSE)
      alpha 0,1 -> akurasi 0,968 | konten 0,77595 | H 0,86140
      alpha 0,3 -> akurasi 0,980 | konten 0,77451 | H 0,86522
      alpha 0,5 -> akurasi 0,948 | konten 0,79047 | H 0,86210
      alpha 0,7 -> akurasi 0,968 | konten 0,78369 | H 0,86615
      alpha 0,9 -> akurasi 0,960 | konten 0,77535 | H 0,85785
      alpha terpilih: 0,7 (H 0,86615), hanya 0,00093 di atas alpha 0,3
    dengan kolom isi encoder LAMA (content_preservation, pembanding): formal -> 0,1 (H 0,22969) dan
      informal -> 0,3 (H 0,86862)
  KEPUTUSAN MANUSIA atas hasil ini:
    1. kolom kriteria pemilihan alpha untuk kedua korpus adalah content_preservation_LaBSE
    2. target informal: alpha 0,7 dipakai TETAPI tidak disebut optimal tanpa kualifikasi; selisih
       0,00093 terhadap alpha 0,3 tidak terbedakan (galat baku proporsi sekitar 0,02 pada n = 250),
       kurva lengkap disajikan, keputusan akhir diserahkan ke uji signifikansi Langkah 9
    3. target formal: alpha TIDAK ditetapkan; akurasi 0,108 sampai 0,136 (rentang 0,028 sekitar
       1,4 kali galat baku) berada di aras derau, sehingga dilaporkan bahwa gaya formal tidak
       tercapai pada semua alpha dan pemilihan alpha pada target itu tidak bermakna. Kurva target
       formal disajikan sebagai bukti ketidakpekaan
    4. evaluasi sapuan alpha-dev Aaker dijalankan dengan --skip-fluency
  berkas alpha: fewshot_formality/alpha_star.json (kriteria LaBSE) dan
    fewshot_formality/alpha_star_legacy_content.json (kriteria encoder lama, pembanding)
  Catatan temuan: akurasi gaya target formal sangat rendah (0,108 sampai 0,136) sedangkan target
    informal sangat tinggi (0,948 sampai 0,980). Ini keadaan yang dilaporkan apa adanya, bukan
    kegagalan langkah, dan selaras dengan laporan naskah lama bahwa kekuatan gaya berada di ekstrem
```

### Langkah 6 dan 7. Run utama: tiga seed untuk seluruh konfigurasi

```
Rencana yang disetujui manusia: 6 peluncuran, satu proses pada satu waktu, konfigurasi identik
pada keenam peluncuran, urutan formality lalu Aaker untuk setiap seed.
  formality_s42  python fewshot_formality.py
  aaker_s42      python main.py
  formality_s43  python fewshot_formality.py --only-seed 43
  aaker_s43      python main.py --only-seed 43
  formality_s44  python fewshot_formality.py --only-seed 44
  aaker_s44      python main.py --only-seed 44
Berkas per peluncuran: formality 38 berkas (19 konfigurasi x 2 target, 250 sampel per konfigurasi),
  Aaker 20 berkas (10 konfigurasi x 2 target, 500 sampel per konfigurasi).
Perkiraan: formality 5,4 jam per seed, Aaker 9,2 jam per seed, total generasi 43,8 jam (laju 2,06
  detik per sampel formality dan 3,3 detik per sampel Aaker).
Laporan progres hanya pada enam titik, yaitu setiap satu peluncuran selesai.

Keadaan konfigurasi yang dipakai (identik untuk keenam peluncuran):
  fewshot_formality/fewshot_config.json sha256 d0dd22b736ed4134fb0a5e1864d7c0c8562bfddf067a2a4ecc4d7358aed89973
    split_dir data/formality_splits_v2 | num_samples all | k [5, 10] | 6 metode | 5 alpha
    | run_seeds [42, 43, 44] | human_eval_samples 25 | skip_existing true | results model_results_dir
  fewshot_aaker/fewshot_config.json sha256 ae4113f8b907b32d7692633a74781d63e67b7d5d9b9619d02b7ffb6dcd8dfbd5
    split_dir data/brand_splits_v2 | num_samples 500 | k [5] | 6 metode | 5 alpha
    | run_seeds [42, 43, 44] | human_eval_samples 25 | skip_existing true | results model_results_dir
  Perubahan dari keadaan sebelum Langkah 6: hanya skip_existing false menjadi true pada kedua berkas.
  SHA-256 itu akan dicatat ulang pada setiap manifes peluncuran; bila berbeda, pekerjaan dihentikan
  dan dilaporkan, bukan dilanjutkan.

Peluncuran 1 dari 6, formality seed 42:
  perintah : python scripts/launch_detached.py --nama formality_s42 --cwd fewshot_formality -- python fewshot_formality.py
  PID      : 24824 | mulai 2026-09-26 21:24:47 | manifest LOGS/detached_formality_s42.json
  log      : LOGS/formality_s42.out.log (stdout) dan LOGS/formality_s42.err.log (stderr)
  verifikasi peluncur: LULUS, proses hidup 8 detik setelah diluncurkan
  manifest env_wajib: PYTHONIOENCODING=utf-8, PYTHONUTF8=1, HF_HUB_DISABLE_SYMLINKS=1, ketiganya
    tercatat sebagai disetel baru oleh peluncur (env_baru_disetel) karena sesi pemanggil belum memilikinya
  manifest config_sha256: d0dd22b736ed4134fb0a5e1864d7c0c8562bfddf067a2a4ecc4d7358aed89973 (cocok)
  pemeriksaan kesehatan pada +4 menit: PID masih hidup, stderr bertambah sampai 66.645 byte dan
    terus ditulis, stdout masih 0 byte (keluaran print tertahan buffer, sedangkan bilah tqdm dan
    StreamHandler logging menulis ke stderr), belum ada berkas hasil karena konfigurasi pertama
    baru selesai sekitar 5,5 menit sesudah pemuatan model dan pembangunan indeks
PENYIMPANGAN PADA PELUNCURAN PERTAMA (ditemukan 2026-09-27 05:25):
  Perintah peluncuran pertama dijalankan TANPA `--only-seed 42`, sedangkan konfigurasi memuat
  `run_seeds [42, 43, 44]`. Akibatnya proses ini menjalankan ketiga seed secara berurutan dalam satu
  proses, bukan hanya seed 42 seperti yang direncanakan. Ini kekeliruan penyusunan perintah oleh agen,
  bukan perubahan konfigurasi dan bukan kegagalan pipeline.
  Bukti keadaan pukul 05:26:27:
    104 berkas ber_seed di fewshot_formality/model_results_dir/google_gemma-3-4b-it, SELURUHNYA target
      formal: seed42 19 results + 19 HUMAN_EVAL, seed43 19 + 19, seed44 14 + 14. Berkas target informal: 0
    konfigurasi yang sedang berjalan: Target formal | hybrid_early (α=0,3) | seed=44 pada 19% (47/250),
      laju 2,12 detik per sampel
    kata 'informal' belum pernah muncul di LOGS/formality_s42.err.log, karena loop menyusun personality
      di lapisan luar dan seed di lapisan dalam, sehingga informal baru dimulai setelah formal seed 44 usai
  Dampak: proses ini akan menghasilkan seluruh 114 konfigurasi formality (228 berkas) untuk ketiga seed,
    setara dengan tiga peluncuran formality yang direncanakan. Peluncuran formality_s43 dan formality_s44
    nanti tidak akan menghasilkan apa pun karena `skip_existing` true akan melewati seluruh konfigurasi.
  Keabsahan hasil tidak terganggu: setiap sampel tetap memakai seed sendiri (sample_seed = run_seed x
    100000 + i), nama berkas memuat seed sehingga tidak ada yang saling menimpa, dan tidak ada berkas
    lama maupun hasil sapuan alpha-dev yang tersentuh.
  Keputusan yang menunggu manusia: (a) biarkan proses ini menuntaskan ketiga seed formality, lalu hanya
    menjalankan bagian Aaker; atau (b) tetap menjalankan formality_s43 dan formality_s44 sebagai
    peluncuran kosong untuk kelengkapan administrasi.
Penghentian proses dan keputusan satu seed (2026-09-27):
  PID 24824 dihentikan 2026-09-27 06:09:49 atas perintah manusia. Konfirmasi: PID tidak lagi hidup dan
  tidak ada proses Python lain yang hidup.
  Pemeriksaan keutuhan berkas seed 42 (38 berkas): 19 results berisi tepat 250 baris dan 19 HUMAN_EVAL
  berisi tepat 25 baris (angka 25 memang benar untuk berkas HUMAN_EVAL, bukan kerusakan), semuanya
  memuat kolom run_seed dan output_tokens dengan run_seed = 42. Berkas bermasalah: 0, sehingga
  ARSIP/rusak kosong dan tidak ada berkas terpotong akibat penghentian mendadak.
  Berkas seed 43 dan 44 dipindahkan (bukan dihapus) ke ARSIP/seed43_44_formality: 76 berkas
  (seed43 38 + seed44 38), bukan 66 seperti perkiraan manusia. Sebabnya: pada 05:26 seed 44 baru
  menyelesaikan 14 dari 19 konfigurasi formal, dan pada saat penghentian 06:09 ia sudah menuntaskan
  seluruh 19, sehingga bertambah 5 konfigurasi = 10 berkas.
  Folder sumber sesudah pemindahan: 102 berkas = 38 berkas seed 42 + 64 berkas lama tanpa penanda seed,
  dan tidak ada lagi penanda seed 43 maupun seed 44.
  Keputusan manusia: hanya seed 42 yang dipakai. Struktur tiga seed dibatalkan karena (a) target
  informal belum dikerjakan sama sekali, karena loop menyusun target di lapisan luar dan seed di
  lapisan dalam sehingga selesainya formal untuk tiga seed TIDAK berarti formality selesai, dan
  (b) dengan satu seed tidak ada konfigurasi yang perlu dipilih untuk diulang. Ukuran ketidakpastian
  yang dilaporkan adalah bootstrap berpasangan atas butir uji, dan naskah TIDAK boleh menyatakan
  setiap konfigurasi diulang beberapa seed.
  run_seeds diubah menjadi [42] pada kedua config, tidak lagi bergantung pada --only-seed:
    fewshot_formality/fewshot_config.json sha256 29974d6b182e7873544a091f498b28b1cadb33ac96d85a85fc430b5207b77521
    fewshot_aaker/fewshot_config.json     sha256 cbd6dd95ce1b64306ccb04ca0dc0886bc8784461e747093fe06e57b1b6a74ba8
  Rencana peluncuran berikutnya: formality dengan run_seeds [42]; skip_existing true akan melewati 19
  konfigurasi formal seed 42 sehingga hanya 19 konfigurasi informal yang dikerjakan (4.750 generasi,
  sekitar 2,9 jam). Lalu Aaker dengan run_seeds [42] (10 konfigurasi x 2 target x 500 = 10.000
  generasi, sekitar 9,7 jam).
  Verifikasi hash tiga skrip statistik versi baru:
    scripts/report_metrics.py          91209163e0ce36d0  COCOK
    scripts/bootstrap_significance.py  387a9fbed6f78bdf  COCOK
    scripts/replication_metric.py      TIDAK COCOK. sha256 di disk b3bc0872ebec977d..., diharapkan
      b3bc872ebec977d3... Perbedaannya hanya satu karakter: '0' setelah 'b3bc' tidak ada pada nilai
      yang diharapkan dan ada '3' tambahan di ujungnya.
    Ketiganya menerima --only-seed (terbukti dari --help, exit 0). Berkas replication_metric.py di disk
    berukuran 8.116 byte sedangkan versi lama 6.736 byte, jadi tanda-tandanya memang versi baru, tetapi
    hash-nya TIDAK dapat saya nyatakan cocok.
  Karena aturan manusia "verifikasi hash sebelum dipakai" tidak terpenuhi untuk satu berkas, langkah 6
  (peluncuran formality) BELUM dijalankan dan menunggu konfirmasi.
Langkah 6 dijalankan (2026-09-27):
  Ketiga hash skrip statistik diverifikasi ulang memakai hash LENGKAP 64 aksara dengan Get-FileHash,
  dan ketiganya COCOK dengan salinan kanonik manusia:
    report_metrics.py         91209163e0ce36d0af0427abb914536b702dd0269c8c2e7bec888291ed915d7a
    bootstrap_significance.py 387a9fbed6f78bdfaf2dc9dd27434135055c6a1a893b44a23931136d112d72b2
    replication_metric.py     b3bc0872ebec977db99a7a2dd5c261d60362b0d64ceb280db5a13bc558f8c214
  Hash 16 aksara tidak dipakai lagi pada pemeriksaan berikutnya, supaya tidak ada ruang salah ketik.
  Log dan manifest peluncuran pertama diamankan ke ARSIP/peluncuran_pertama_formality:
    log_pertama.err.log 6.260.113 byte, log_pertama.out.log 91.187 byte, manifest_pertama.json
  Peluncuran: python scripts/launch_detached.py --nama formality_s42_informal --cwd fewshot_formality -- python fewshot_formality.py
    PID 8800 | mulai 2026-09-27 06:13:43 | manifest LOGS/detached_formality_s42_informal.json
    config sha256 29974d6b182e7873544a091f498b28b1cadb33ac96d85a85fc430b5207b77521 (cocok)
    env_wajib pada manifest: PYTHONIOENCODING=utf-8, PYTHONUTF8=1, HF_HUB_DISABLE_SYMLINKS=1, ketiganya
      disetel baru oleh peluncur
    Nama run sengaja baru agar manifest dan log peluncuran pertama tidak tertimpa.
  Verifikasi penyaring skip_existing pada +5,7 menit (06:19:27): 0 baris kemajuan "Target: formal" pada
    stderr, artinya 19 konfigurasi formal benar-benar dilewati; generasi berjalan pada
    "Target: informal | dense | seed=42" 58% (144/250) dengan laju 2,13 detik per sampel; berkas informal
    belum ada karena konfigurasi pertama belum selesai
  Perkiraan selesai: 19 konfigurasi informal x 250 sampel x sekitar 2,05 detik ditambah overhead
    sekitar 2,7 jam, jadi sekitar 08:55 sampai 09:00
Langkah 6 tamat dan langkah 7 diluncurkan (2026-09-27):
  Formality SELESAI. Bukti:
    log internal fewshot_formality/outputs/fewshot_logs/google_gemma-3-4b-it/fewshot_experiment_20260926-212504.log
      berakhir dengan "2026-09-27 09:06:55,472 - INFO - ALL FEW-SHOT EXPERIMENTS COMPLETED."
    19 berkas *_seed42_results.csv bertarget informal, masing-masing tepat 250 baris, memuat kolom run_seed
      bernilai 42 dan output_tokens; ditambah 19 berkas *_HUMAN_EVAL.csv
    0 keluaran ERROR dan 0 retrieval_fallback pada kesembilan belas berkas
    proses berakhir sendiri; setelahnya tidak ada proses Python yang hidup, karena itu GPU terlihat bebas
    durasi: peluncuran 06:13:43 -> selesai 09:06:55 = 2 jam 53 menit untuk 19 konfigurasi informal
  Laju nyata per konfigurasi formality informal (250 sampel per konfigurasi, dari konfigurasi ketiga):
    17 konfigurasi selesai dalam 8,2 sampai 9,0 menit, yaitu 1,97 sampai 2,16 detik per sampel
    dua pencilan: zero_shot k=5 memakan 16,4 menit (3,94 detik per sampel) dan hybrid_early alpha0.5 k=10
      memakan 10,1 menit. Pencilan zero_shot konsisten dengan pengamatan sebelumnya: tanpa eksemplar,
      keluaran cenderung lebih panjang sehingga generasi memakan waktu hampir dua kali
  Ketiga syarat manusia untuk meluncurkan Aaker DIPENUHI dan diperiksa:
    1. 19 berkas informal masing-masing 250 baris: ya
    2. 0 keluaran ERROR dan 0 retrieval_fallback pada kesembilan belas berkas: ya
    3. tidak ada proses Python lain yang hidup; config Aaker run_seeds [42] dengan sha256
       cbd6dd95ce1b64306ccb04ca0dc0886bc8784461e747093fe06e57b1b6a74ba8: ya
  Langkah 7 diluncurkan tanpa menunggu, sesuai persetujuan manusia:
    perintah: python scripts/launch_detached.py --nama aaker_s42 --cwd fewshot_aaker -- python main.py
    PID 26228 | mulai 2026-09-27 10:19:48 | manifest LOGS/detached_aaker_s42.json
    config sha256 cbd6dd95ce1b64306ccb04ca0dc0886bc8784461e747093fe06e57b1b6a74ba8 (cocok)
    env_wajib pada manifest: ketiganya disetel baru oleh peluncur
    verifikasi peluncur: LULUS, stderr sudah 3.369 byte saat diverifikasi
    cakupan: 10 konfigurasi x 2 target x 500 sampel = 10.000 generasi, sekitar 9,2 sampai 9,7 jam
Langkah 7 tamat dan pemeriksaan kelengkapan (2026-09-27):
  20 berkas *_seed42_results.csv di fewshot_aaker/model_results_dir/google_gemma-3-4b-it, semuanya 500 baris,
    himpunan (target, metode, alpha) tepat 20 kombinasi: competence dan excitement x {dense, centroid,
    bm25, random, zero_shot} ditambah hybrid_early pada lima nilai alpha
  0 keluaran ERROR dan 0 retrieval_fallback pada keseluruhan berkas; ditambah 20 berkas *_HUMAN_EVAL.csv
  Durasi Aaker: 10:19:48 sampai sekitar 20:43 = 10 jam 23 menit untuk 20 konfigurasi
Koreksi perkiraan waktu memakai laju nyata:
  Aaker: laju stabil 2,73 sampai 3,70 detik per sampel (sekitar 3,3 pada median), sesuai asumsi.
    Perkiraan awal 9,2 sampai 9,7 jam, nyata 10 jam 23 menit, jadi meleset sekitar satu jam.
  Sebab utamanya zero_shot: 49,1 menit untuk 500 sampel = 5,89 detik per sampel, yaitu 1,8 kali laju
    normal sekitar 27,5 menit. hybrid_early alpha kecil juga lebih lambat (42,6 dan 37,8 menit).
  Formality: zero_shot 16,4 menit untuk 250 sampel = 3,94 detik per sampel, yaitu 1,9 kali laju normal
    8,5 sampai 9,0 menit. Jadi anggaran waktu tiap korpus harus memakai laju normal ditambah sekitar
    1,8 sampai 1,9 kali untuk zero_shot dan alpha kecil.
  Laju formality fase seed 42: formal 21:24:47->00:19:23 (2 jam 55 menit) dan informal 06:13:43->09:06:55
    (2 jam 53 menit); total 5 jam 48 menit untuk 38 konfigurasi, sekitar 9,2 menit per konfigurasi.
    Ini mendekati perkiraan 5,4 jam; selisihnya berasal dari konfigurasi zero_shot.
Arsip kedua korpus (cadangan, bukan pemindahan; berkas lama tanpa penanda seed TIDAK diarsipkan):
  ARSIP/formality_s42: 85 berkas = 76 berkas _seed42 (38 results + 38 HUMAN_EVAL) + 2 log internal
    (fewshot_experiment_20260926-212504.log, fewshot_experiment_20260927-061408.log) + 6 log/manifes
    peluncuran + config_saat_run.json
  ARSIP/aaker_s42: 45 berkas = 40 berkas _seed42 (20 results + 20 HUMAN_EVAL) + 1 log internal
    (fewshot_experiment_20260927-101954.log) + 3 log/manifes peluncuran + config_saat_run.json
  Catatan angka: manusia menyebut 38 berkas formality dan 20 berkas Aaker, keduanya hitungan berkas
    *_results.csv. Arsip memuat juga berkas _HUMAN_EVAL berpenanda sama, sehingga totalnya 76 dan 40.
    Berkas asli tetap utuh di model_results_dir (formality 76 berkas _seed42, Aaker 40).
Uji cepat sebelum evaluasi penuh (langkah 4):
  perintah sama seperti evaluasi penuh dengan tambahan --limit 20 dan --out evaluation_result_v2_uji pada
  korpus Aaker. Exit 0 dalam 193,1 detik, 20 berkas keluaran masing-masing 20 baris, 27 kolom.
  Kolom penting yang terbentuk: style_strength_calibrated, style_predicted, style_accuracy,
    content_preservation (encoder lama), content_preservation_LaBSE, content_preservation_mE5 (dua encoder
    independen yang menjawab R2-08), fluency_ppl, ppl_degenerate, replication_rate_8
  Folder uji sudah dihapus dan terverifikasi tidak ada.
Evaluasi langkah 8 dimulai (langkah 5 dan 6):
  perintah: python scripts/launch_detached.py --nama eval_v2_aaker --cwd scripts -- python evaluate_results.py
    --results ../fewshot_aaker/model_results_dir/google_gemma-3-4b-it --classifier ../fewshot_aaker/style_classifier
    --out ../fewshot_aaker/evaluation_result_v2/google_gemma-3-4b-it
    --calibration ../fewshot_aaker/style_classifier/calibration.json
    --encoder LaBSE=sentence-transformers/LaBSE --encoder mE5=intfloat/multilingual-e5-base
    --legacy-encoder LazarusNLP/simcse-indobert-base
    --fluency-model Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct --patterns *_seed42*results.csv
  PID 25932 | mulai 2026-09-27 21:03:31 | log LOGS/eval_v2_aaker.out.log dan LOGS/eval_v2_aaker.err.log
  manifest: config_sha256 null karena evaluasi dijalankan dari scripts/ dan tidak memakai fewshot_config.json;
    env_wajib ketiganya disetel peluncur
  Bukti model fluency yang BENAR-BENAR dimuat: skrip tidak mencetak nama model di keluarannya, jadi buktinya
    diambil dari jumlah entri pemuatan bobot. Log memuat pemuatan 464 entri untuk model terbesar, sedangkan
    indeks cache Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct memuat tepat 464 tensor dan
    Sahabat-AI/llama3-8b-cpt-sahabatai-v1-instruct hanya 291 tensor. Jadi yang dimuat adalah gemma2-9b.
  Peringatan tidak berbahaya pada log: "The following generation flags are not valid and may be ignored:
    ['cache_implementation']" berasal dari generation_config model fluency, bukan dari opsi kita.
Evaluasi langkah 8 selesai untuk kedua korpus (2026-09-27):
  Aaker: PID 25932, 21:03:31 -> 21:57:39 (54 menit), 0 galat atau OOM pada log
    20 berkas evaluated_v2_*, semuanya 500 baris (10.000 baris), 27 kolom
    0 NaN pada content_preservation_LaBSE, content_preservation_mE5, dan fluency_ppl
    keluaran degenerate (PPL > 1000): 586 dari 10.000 baris = 5,86 persen, berdekatan dengan angka
      lama pada README (5,51 persen korpus Aaker)
  Formality: PID 28568, 21:58:40 -> sekitar 22:38 (40 menit), 0 galat atau OOM pada log
    38 berkas evaluated_v2_*, semuanya 250 baris (9.500 baris), 27 kolom
    0 NaN pada ketiga kolom yang sama
    keluaran degenerate (PPL > 1000): 1.308 dari 9.500 baris = 13,77 persen, JAUH di atas angka lama
      pada README (0,61 persen korpus STIF). Dilaporkan apa adanya; rincian per metode akan dihitung
      pada Langkah 9, dan perbedaan ini harus diungkapkan di LAPORAN_AKHIR
  Bukti model fluency pada KEDUA log: entri pemuatan terbesar 464 pada log Aaker maupun formality,
    cocok dengan 464 tensor indeks cache gemma2-9b-cpt-sahabatai-v1-instruct, sedangkan
    llama3-8b-cpt-sahabatai-v1-instruct hanya 291 tensor. Jadi kedua korpus memakai gemma2-9b
  Kedua output ada di evaluation_result_v2/google_gemma-3-4b-it pada repo masing-masing, terpisah dari
    32 dan 16 berkas evaluasi lama tanpa penanda seed
  Langkah 9 BELUM dijalankan dan menunggu persetujuan manusia atas hasil evaluasi ini
status : langkah 1 sampai 8 selesai; menunggu persetujuan sebelum Langkah 9
```

### Langkah 7. Ulangan kedua dan ketiga

```
TIDAK DIJALANKAN. Struktur tiga seed dibatalkan atas keputusan manusia 2026-09-27 (lihat blok
"Langkah 6 dan 7" di atas): hanya seed 42 yang dipakai. Tidak ada seed 43 maupun 44 yang dijalankan
pada run utama, sehingga tidak ada ulangan yang dimulai maupun bagian yang dipotong. Berkas
generasi seed 43 dan 44 dari peluncuran pertama yang terhenti disimpan di ARSIP/seed43_44_formality
(76 berkas, tidak dihapus) agar evaluasi dapat diulang tanpa membangkitkan ulang bila varians
antar-jalan diminta. Ukuran ketidakpastian yang dilaporkan adalah bootstrap berpasangan atas butir
uji, bukan varians antar-seed.
status  : dilewati atas keputusan manusia.
```

### Langkah 8. Evaluasi lengkap

```
perintah:
mulai:
selesai:
fluency dihitung ulang atau disalin:
status:
```

### Langkah 9. Statistik dan metrik baru

```
perintah (semuanya memakai penyaring seed; <korpus> = formality atau aaker):
  ringkasan : & 'C:\Ana3\envs\fikri_hasani\python.exe' scripts\report_metrics.py --dir
              fewshot_<korpus>\evaluation_result_v2 --only-seed 42 --degenerate-threshold 1000
              --out TABEL_ringkasan_<korpus>.csv
  uji       : python scripts\bootstrap_significance.py --dir
              fewshot_<korpus>\evaluation_result_v2\google_gemma-3-4b-it
              --only-seed 42 --metric <kolom> --out TABEL_uji_<korpus>_<metrik>.csv
              (skrip versi baru membaca glob evaluated_*.csv di dalam --dir, bukan rekursif)
  kepekaan k: python scripts\k_sensitivity.py --dir . --corpus formality
              --out TABEL_kepekaan_k_formality.csv
  replikasi : python scripts\replication_metric.py --dir fewshot_<korpus>\evaluation_result_v2
              --only-seed 42 --from-column --out TABEL_replikasi_<korpus>.csv
  PPL/target: python scripts\ppl_per_target.py --dir fewshot_formality\evaluation_result_v2
              --threshold 1000 --out TABEL_ppl_formality_per_target.csv
  <metrik> = style_accuracy, style_strength_calibrated, content_preservation,
             content_preservation_LaBSE, content_preservation_mE5, replication_rate_8
mulai   : 2026-09-27, sesudah hasil evaluasi Langkah 8 disetujui manusia
selesai : 2026-09-27 (ringkasan, replikasi, PPL per target) dan 2026-09-28 (kedua belas tabel uji
          dihitung ulang dengan skrip uji versi baru, lihat butir g)
berkas yang dihasilkan: 18 berkas TABEL_* di akar bundel
  TABEL_ringkasan_formality.csv   38 baris (satu per berkas hasil)
  TABEL_ringkasan_aaker.csv       20 baris
  TABEL_uji_formality_<metrik>.csv   6 berkas x 342 pasangan sebanding (38 konfigurasi)
  TABEL_uji_aaker_<metrik>.csv       6 berkas x  90 pasangan sebanding (20 konfigurasi)
  TABEL_replikasi_formality.csv   38 baris
  TABEL_replikasi_aaker.csv       20 baris
  TABEL_ppl_formality_per_target.csv  14 baris data + kepala (2 ringkasan target + 12 target x metode)
  TABEL_kepekaan_k_formality.csv      108 baris data + kepala (6 metrik x 18 pasangan k10-vs-k5)
Dua skrip bantu read-only ditambahkan di scripts/: ppl_per_target.py (menghasilkan TABEL_ppl_*) dan
k_sensitivity.py (menghasilkan TABEL_kepekaan_k_formality.csv). Log perhitungan ulang tabel uji ada
di LOGS/uji_v2_recompute.log.
CATATAN PENTING: kedua belas TABEL_uji_* di atas adalah hasil HITUNG ULANG dengan
bootstrap_significance.py versi baru (lihat butir g), bukan berkas lama. Angka pada butir (c) sudah
memakai tabel baru itu; angka uji yang dilaporkan sebelum 2026-09-28 TIDAK sah.
Tidak ada berkas di evaluation_result_v2 yang diubah, dipindahkan, atau dihapus.

(a) DEGENERASI KORPUS FORMALITY, ambang PPL > 1000, dari 9.500 baris (38 berkas x 250 sampel):
  per target : formal 608/4.750 = 12,80 persen ; informal 700/4.750 = 14,74 persen
  per metode (formal / informal):
    bm25          85/500   = 17,00 persen / 85/500   = 17,00 persen
    centroid      38/500   =  7,60 persen / 43/500   =  8,60 persen
    dense         82/500   = 16,40 persen / 77/500   = 15,40 persen
    hybrid_early 332/2.500 = 13,28 persen / 414/2.500 = 16,56 persen
    random        64/500   = 12,80 persen / 78/500   = 15,60 persen
    zero_shot      7/250   =  2,80 persen /  3/250   =  1,20 persen
  Angka itu jauh di atas 0,61 persen pada README, tetapi sebabnya adalah pergantian model fluency
  (llama3-8b -> gemma2-9b) pada revisi ini, bukan penurunan mutu keluaran; lihat blok Langkah 8 dan
  baris koreksi pada tabel Kendala. Angka 0,61 persen TIDAK dipakai sebagai pembanding. Aaker tetap
  5,86 persen (586/10.000), berdekatan dengan angka lama 5,51 persen, karena modelnya tidak berubah.

(b) MEDIAN DAN TRIMMED10 PPL KORPUS FORMALITY PER TARGET (dihitung langsung dari kolom per sampel
    fluency_ppl pada 38 berkas evaluated_v2_*, BUKAN median dari median antar berkas):
    target formal   n 4.750 : median 191,45 | trimmed10 287,38 | rata-rata 1.436,45 | sd 36.680,95
                              | min 1,23 | maks 2.399.765,85
    target informal n 4.750 : median 226,18 | trimmed10 342,27 | rata-rata 1.081,08 | sd 11.974,31
                              | min 1,14 | maks   755.942,67
  Rata-rata jauh di atas median karena satu ekor sangat panjang; trimmed10 menunjukkan pemusatan yang
  sesungguhnya. Median dan trimmed inilah angka yang sebaiknya dipakai untuk menyatakan besar PPL
  korpus ini, bukan rata-rata.

(c) SELANG KEPERCAYAAN BERPASANGAN (bootstrap atas butir uji; skrip versi baru melewati pasangan
    lintas target karena membandingkan dua target gaya berbeda tidak bermakna):
  pasangan sebanding per korpus:
    formality : 38 konfigurasi (19 per target, k=5 dan k=10 kini terpisah) -> 342 pasangan sebanding,
                361 pasangan lintas target dilewati
    aaker     : 20 konfigurasi (10 per target, hanya k=5) -> 90 pasangan sebanding,
                100 pasangan lintas target dilewati
  jumlah pasangan bermakna 95 persen (seluruhnya pasangan sebanding):
    formality: style_accuracy 128/342 | style_strength_calibrated 157/342 |
               content_preservation 230/342 | LaBSE 189/342 | mE5 193/342 | replication_rate_8 28/342
    aaker    : style_accuracy  66/90  | style_strength_calibrated  70/90  |
               content_preservation  80/90 | LaBSE 73/90 | mE5 74/90 | replication_rate_8 61/90
  formality / style_accuracy:
    zero_shot berbeda bermakna dari SEMUA metode retrieval (36/36), arahnya berbalik menurut target:
      formal  : 18/18 bermakna, d = -0,732 sampai -0,528 (retrieval LEBIH RENDAH)
      informal: 18/18 bermakna, d = +0,768 sampai +0,852 (retrieval LEBIH TINGGI)
    di antara metode retrieval, banyak selisih kecil dan sering tidak bermakna
      (formal 69/171 bermakna, informal 59/171 bermakna)
  formality / content_preservation:
    zero_shot vs retrieval: 36/36 bermakna
      formal  : d = +0,210 sampai +0,311 ; informal: d = +0,165 sampai +0,233
  aaker / style_accuracy (66/90 bermakna; competence 37/45, excitement 29/45):
    competence: tiga teratas setara secara statistik - hybrid_early a0,1 0,864, centroid 0,850,
      hybrid_early a0,3 0,842 (a0,1 - a0,3 d +0,022 CI [-0,004; +0,050], TIDAK bermakna; centroid -
      a0,3 d +0,008, TIDAK bermakna). a0,3 - a0,5 d +0,328 CI [+0,282; +0,374] bermakna.
    excitement: puncak hybrid_early a0,3 0,340; a0,3 - a0,5 d +0,040 CI [-0,004; +0,084] TIDAK
      bermakna; hybrid_early a0,5 - zero_shot d +0,242 CI [+0,196; +0,286] bermakna.
  aaker / content_preservation (80/90 bermakna; competence 40/45, excitement 40/45):
    competence: berlawanan arah dengan akurasi gaya - terbaik pada alpha BESAR (hybrid a0,9 0,717)
      dan terburuk pada alpha kecil (a0,3 0,488; a0,1 0,395). a0,3 - a0,5 d -0,163
      CI [-0,184; -0,142] dan a0,3 - a0,9 d -0,229 CI [-0,250; -0,209], keduanya bermakna
      (pola tukar-menukar gaya-isi).
    excitement: dense 0,749 dan hybrid a0,9 0,749 terbaik; zero_shot 0,420 terburuk. hybrid a0,5 -
      zero_shot d +0,293 CI [+0,272; +0,314] bermakna.

(d) VERIFIKASI KEPUTUSAN ALPHA PADA DATA UJI:
    informal: alpha 0,7 melawan 0,3 pada content_preservation_LaBSE d -0,008 CI [-0,023; +0,007]
      TIDAK bermakna, sedangkan pada style_accuracy a0,7 justru lebih rendah (d +0,048 CI
      [+0,016; +0,080], bermakna). Jadi 0,7 tetap dilaporkan sebagai hasil kriteria yang ditetapkan
      lebih dahulu dan TIDAK disebut optimal; kurva lengkap kelima alpha disajikan.
    formal: gaya tidak tercapai pada semua alpha (0,056-0,178). Pada kolom kriteria LaBSE, pasangan
      a0,1 dan a0,3 terhadap alpha lain sebagian bermakna, sedangkan a0,5, a0,7, a0,9 saling tidak
      berbeda - konsisten dengan kesimpulan bahwa pemilihan alpha pada target ini tidak bermakna.
    Aaker competence alpha 0,3: unggul bermakna atas a0,5 (d +0,328) tetapi setara dengan a0,1 dan
      centroid; jarak isi a0,3 - a0,5 (-0,163) menunjukkan a0,3 sudah menukar sebagian isi demi gaya,
      sehingga kurva lengkap tetap diperlukan.
    Aaker excitement alpha 0,5: tidak berbeda bermakna dari a0,3, a0,7, a0,9, maupun centroid.

(e) REPLIKASI (TABEL_replikasi_*; sumber eksemplar = kolom retrieved_exemplars, overlap 8-gram):
  formality formal   : overlap8 rata-rata 0,0037 (0,0000-0,0142), output ber-overlap tinggi 0,48 persen
  formality informal : overlap8 rata-rata 0,0079 (0,0000-0,0194), output ber-overlap tinggi 1,05 persen
  aaker competence   : overlap8 rata-rata 0,0911 (0,0000-0,3393), output ber-overlap tinggi 15,17 persen
  aaker excitement   : overlap8 rata-rata 0,0235 (0,0000-0,0426), output ber-overlap tinggi 3,82 persen
  replication_rate_8 tertinggi ada pada alpha kecil korpus Aaker: competence a0,1 0,3386, a0,3 0,2200,
  centroid 0,1880; excitement semuanya di bawah 0,037; formality seluruhnya di bawah 0,011. Jadi
  klaim penyalinan eksemplar kuat hanya pada competence alpha kecil (mendukung hipotesis R2-09),
  lemah pada excitement dan tidak didukung pada korpus formality.

(f) FAKTA YANG HARUS MASUK LAPORAN AKHIR (ditemukan pada Langkah 9):
  zero_shot punya pola menyimpang. Pada target formal formality akurasi gayanya 0,780 (tertinggi,
  jauh di atas rata-rata per metode retrieval 0,056-0,178 dan di atas maksimum per berkas 0,252)
  dan PPL mediannya paling rendah (39,82); pada target
  informal akurasinya justru 0,136 (terendah), sedangkan content_preservation-nya paling buruk
  (0,517 formal; 0,562 informal). Artinya keluaran zero_shot adalah teks yang fasih dan bagi
  classifier condong ke kelas formal, tetapi paling lemah mempertahankan isi. Dilaporkan apa adanya
  dan tidak boleh dipakai untuk menyimpulkan keunggulan zero_shot.

(g) KOREKSI SKRIP UJI (2026-09-28). bootstrap_significance.py versi lama punya dua cacat:
      (i) tidak memasangkan hanya di dalam target yang sama, sehingga tabel Aaker versi lama memuat
          sekitar 100 pasangan lintas target (mis. competence|bm25 melawan excitement|zero_shot);
          membandingkan dua target gaya berbeda tidak bermakna. Bukti ketidakkonsistenan: tabel Aaker
          lama 190 baris = C(20,2), sedangkan tabel formality lama 90 baris hanya berisi pasangan
          dalam target, jadi kedua tabel lama bahkan tidak konsisten satu sama lain.
      (ii) label konfigurasi tidak memuat k, dan berkas hasil tidak memuat kolom k, sehingga berkas
          k=10 dan k=5 bertabrakan pada label yang sama dan salah satunya tertimpa diam-diam.
          Akibatnya tabel formality lama hanya memuat 10 konfigurasi per target, bukan 19, dan
          analisis kepekaan k tidak mungkin dilakukan.
    Skrip versi baru (SHA-256 5c4603662007133cc52954f10faf0faddfd94c8aa0be2e872e2eba1528ed9472,
    ukuran 10.553 byte, terverifikasi) membaca k dari nama berkas dan memasukkannya ke label, memberi
    PERINGATAN bila label bertabrakan, dan melewati pasangan lintas target sambil melaporkan
    penghitungnya. Kedua belas tabel uji dihitung ulang dengan --only-seed 42; log lengkap ada di
    LOGS/uji_v2_recompute.log.
    Hasil pemeriksaan koreksi: 0 peringatan label bertabrakan, 0 berkas terlewat, dan pada kedua
    korpus seluruh berkas memuat kolom sample_index sehingga kunci pemasangan eksplisit (tidak ada
    peringatan kunci posisi).

  KEPEKAAN k (k10 - k5 pada target dan metode yang sama; hanya korpus formality, karena Aaker hanya
  k=5). Tabel: TABEL_kepekaan_k_formality.csv. 18 pasangan per metrik (9 konfigurasi x 2 target),
  masing-masing 250 baris. Jumlah yang bermakna 95 persen:
    style_accuracy 1/18 | style_strength_calibrated 4/18 | content_preservation 10/18 |
    content_preservation_LaBSE 3/18 | content_preservation_mE5 9/18 | replication_rate_8 2/18
  Pola: k memengaruhi ISI lebih daripada GAYA.
    - target formal, content_preservation (encoder lama): k=10 lebih tinggi dari k=5 pada 7 dari 9
      konfigurasi (bm25 +0,032; centroid +0,044; hybrid a0,1 +0,018; a0,3 +0,020; a0,7 +0,015;
      a0,9 +0,016; random +0,015); dense (+0,008) dan hybrid a0,5 (+0,012) tidak bermakna
    - target informal, content_preservation encoder lama: hanya tiga yang bermakna, semuanya
      hybrid_early (a0,3 +0,013; a0,5 +0,013; a0,7 +0,014)
    - pada content_preservation_LaBSE (kolom kriteria) efeknya lebih kecil: hanya formal bm25
      (+0,023), formal centroid (+0,019), dan formal hybrid a0,1 (+0,024) yang bermakna
    - gaya hampir tidak berubah: style_accuracy hanya 1 dari 18 bermakna, yaitu formal centroid
      k10 - k5 = -0,148 (k=10 justru LEBIH RENDAH)
  Kesimpulan kepekaan k: menambah contoh dari 5 menjadi 10 tidak memperbaiki gaya secara umum, dan
  keuntungannya terutama pada pemertahanan isi target formal; pengecualian arah berlawanan pada
  centroid harus disebut apa adanya. Sebelum koreksi ini, perbandingan tersebut tidak dapat dihitung.

status  : Langkah 9 selesai (dengan tabel uji hasil hitung ulang). Seluruh angka berasal dari 18
          berkas TABEL_* di akar bundel yang diturunkan dari berkas evaluated_v2_* di kedua
          evaluation_result_v2.
```

### Langkah 10. Sampel evaluasi manusia

```
perintah: python scripts\export_human_eval.py   (skrip baru, transkripsi bagian 13 protokol; dijalankan
dari akar bundel, tanpa GPU karena hanya membaca CSV hasil)
  Sumber: fewshot_{formality,aaker}/model_results_dir/google_gemma-3-4b-it
  Penyaring: berkas berpenanda _seed42, hanya metode utama (dense, centroid, bm25, hybrid_early);
  random dan zero_shot dikecualikan sesuai daftar empat metode utama pada protokol
  Kunci: 25 sample_index terkecil dipatok dari berkas pertama yang lolos penyaring, lalu dipakai
  sama untuk seluruh berkas berikutnya supaya penilaian dapat dibandingkan lintas metode
mulai  : 2026-09-28
selesai: 2026-09-28 (kurang dari satu menit)
jumlah sampel:
  EVAL_MANUSIA_formality.csv : 400 baris, 25 kalimat sumber, 16 berkas metode (target informal)
  EVAL_MANUSIA_aaker.csv     : 200 baris, 25 kalimat sumber,  8 berkas metode (target competence)
  kolom: sample_index, original_message, paraphrased_message, method_file
jumlah penilai: 0. Evaluasi manusia TIDAK dijalankan; hanya ekspor sampel. Tidak ada lembar
  penilaian yang diisi, sehingga tidak ada kesepakatan antar penilai maupun korelasinya dengan
  metrik otomatis. Bagian 10 LAPORAN_AKHIR.md menyatakan hal ini secara eksplisit
catatan wajib: studi validitas label n=385 pada repo ini belum terisi kolom penilaiannya; hanya
  pilot n=100 yang terisi. Jangan menyatakan adanya studi n=385 pada laporan mana pun
status : lulus sebagai ekspor. Penilaian manusia tidak dijalankan atas keputusan manusia
```

### Langkah 11. Pengepakan keluaran

```
perintah: penyalinan berbasis daftar (Get-ChildItem + Copy-Item) dari akar bundel ke HASIL/
berkas di HASIL/ (87 berkas, seluruhnya berpenanda atau turunan seed 42):
  18 TABEL_*.csv : ringkasan (2), uji (12), replikasi (2), TABEL_ppl_formality_per_target.csv,
    TABEL_kepekaan_k_formality.csv
  2 EVAL_MANUSIA_*.csv
  58 evaluated_v2_*_seed42_results.csv (38 formality + 20 Aaker)
  3 alpha_star : alpha_star_formality.json, alpha_star_aaker.json,
    alpha_star_formality_legacy_content.json
  2 calibration : calibration_formality.json, calibration_aaker.json
  2 split_manifest : split_manifest_formality.json, split_manifest_aaker.json
  RUN_LOG.md dan LAPORAN_AKHIR.md
berkas di HASIL/keluaran_generasi/ (116 berkas), hanya penanda _seed42:
  38 *_seed42_results.csv + 38 *_seed42_HUMAN_EVAL.csv formality (76)
  20 *_seed42_results.csv + 20 *_seed42_HUMAN_EVAL.csv Aaker (40)
  Berkas run lama tanpa penanda seed (64 berkas formality dan 32 berkas Aaker) TIDAK disalin ke
  HASIL/ sesuai permintaan manusia, agar materi pendukung naskah hanya memuat satu eksperimen
SHA-256 skrip bantu baru, diminta dicatat supaya dua tabel dapat direproduksi:
  scripts/k_sensitivity.py    ee2e2e7cd99fa1b34730be09871d305165caec8f8adaa703b11156d813724a5d
                              (3.562 byte) -> TABEL_kepekaan_k_formality.csv
  scripts/ppl_per_target.py   4904c4cc84ee09d69fa00c6110dd30307cdf9dc7ad36c41495421a4178826536
                              (4.104 byte) -> TABEL_ppl_formality_per_target.csv
  scripts/export_human_eval.py 6a32098c099d8f124b0ab30a6aacad5fde8dc5daf7666a192207926f4b96778e
                              (2.390 byte) -> EVAL_MANUSIA_*.csv
LAPORAN_AKHIR.md disusun dengan 12 bagian sesuai bagian 16 protokol, memuat jalur berkas untuk
  setiap angka. Bagian 7 ditulis sebagai varians tidak diukur (satu seed) dan ketidakpastian
  dilaporkan lewat bootstrap berpasangan atas butir uji. Bagian 4 memuat F1 per kelas pada test set
  baru, suhu kalibrasi, serta NLL dan ECE sebelum dan sesudah. Bagian 12 mencantumkan seluruh
  berkas termasuk ketiga skrip bantu di atas. Bagian 10 menyatakan evaluasi manusia tidak dijalankan
status : selesai
```

---

## Kendala dan keputusan

Catat setiap kegagalan, peringatan, dan keputusan yang diambil di luar protokol. Sertakan pesan
galat apa adanya.

| Waktu | Langkah | Gejala | Tindakan | Alasan |
|---|---|---|---|---|
| 2026-09-25 | Prasyarat | `preflight.py` melaporkan `rank_bm25` GAGAL dengan "terdeteksi 0" padahal `importlib.metadata.version('rank-bm25')` = 0.2.2 dan `BM25Okapi` berfungsi | Patch satu baris pada `scripts/preflight.py`: bila atribut `__version__` tidak ada, versi diambil dari `importlib.metadata.version(pipname or mod)` | Disetujui manusia. Paket `rank_bm25` memang tidak menyediakan `__version__`; pemeriksaan lain pada skrip tidak diubah |
| 2026-09-25 | Prasyarat | GPU terdeteksi 12.282 MiB (12,0 GB), syarat bagian 1 minimal 16 GB dengan toleransi preflight 15 GB | Lanjut di mesin ini; bila OOM, mitigasi bagian 17 (`--skip-fluency` lalu PPL pada proses terpisah, atau turunkan batch) | Disetujui manusia. Penyimpangan ini harus dilaporkan pada bagian Kendala di `LAPORAN_AKHIR.md` |
| 2026-09-25 | Prasyarat | `HF_TOKEN` belum ada sebagai variabel lingkungan | `setx HF_TOKEN` dijalankan memakai token login yang sudah tersimpan di `~/.cache/huggingface/token` (diverifikasi valid, akun `fikrihasani`); nilai tidak dicetak ke log | Disetujui manusia. Token login itu sendiri sudah cukup untuk unduhan karena `huggingface_hub` membacanya otomatis |
| 2026-09-25 | Prasyarat | Sesi terminal agen masih memakai env lama setelah `setx`, sehingga pemeriksaan `HF_TOKEN` tetap GAGAL pada run 2 | Perlu restart Zed agar proses baru mewarisi nilai itu; sementara itu preflight dijalankan dengan nilai disuntikkan ke proses | `setx` hanya memengaruhi proses yang dibuat setelahnya, sedangkan env diteruskan dari proses Zed yang sudah berjalan |
| 2026-09-25 | Prasyarat | Encoder `sentence-transformers/LaBSE` dan `intfloat/multilingual-e5-base` belum ada di cache Hugging Face (yang ada hanya `multilingual-e5-large`) | Diunduh di latar belakang sejak 2026-09-25 16:00 (PID 10400, log `unduhan_encoder.log`) memakai `snapshot_download` dengan pola TF, Flax, dan ONNX diabaikan | Disetujui manusia. Bagian 8 dan 11 memerlukan keduanya; ruang disk C: 717 GB dan D: 1.833 GB bebas |
| 2026-09-25 | Prasyarat | LaBSE selesai 16/16 berkas (1.883,7 MB `model.safetensors`, tidak ada berkas kosong), lalu unduhan `intfloat/multilingual-e5-base` berhenti dengan `OSError: [WinError 1314] A required privilege is not held by the client` pada `_create_symlink` (`huggingface_hub/file_download.py` baris 664) | Snapshot e5-base dilanjutkan dengan menjalankan ulang `snapshot_download` sambil memaksa mode salin lewat `HF_HUB_DISABLE_SYMLINKS=1`; selesai 13/13 berkas | Mesin ini memang tidak mendukung symlink cache, dibuktikan langsung: `os.symlink` pada folder sementara gagal dengan WinError 1314. `HF_HUB_DISABLE_SYMLINKS` adalah sakelar resmi pustaka (`constants.py` baris 254, dipatuhi di `file_download.py` baris 98), sehingga jalur symlink tidak lagi ditempuh |
| 2026-09-25 | Prasyarat | Dugaan penyebab kegagalan di atas: `are_symlinks_supported()` menyimpan `True` ke cache per folder (`file_download.py` baris 103) sebelum tes symlink selesai, sedangkan unduhan pertama memakai `max_workers=4`; thread lain dapat membaca `True` yang belum diverifikasi lalu menempuh jalur symlink | Tidak ada kode pustaka yang diubah. Cukup pakai `HF_HUB_DISABLE_SYMLINKS=1` pada proses unduh; belum diusulkan untuk dijadikan variabel lingkungan tetap | Reproduksi buatan dengan `os.symlink` diperlambat: thread kedua mengembalikan `True` sementara thread pertama mengembalikan `False`. Ini inferensi berbasis reproduksi buatan, bukan bukti langsung dari log run pertama |
| 2026-09-25 | Prasyarat | Verifikasi kedua encoder setelah unduhan | Dimuat dengan `SentenceTransformer` dan dipakai `encode` pada dua kalimat uji | Hasil: LaBSE dan `intfloat/multilingual-e5-base` sama-sama menghasilkan vektor dimensi 768 tanpa galat. Snapshot lengkap: LaBSE 16 berkas, e5-base 18 berkas, nol berkas kosong |
| 2026-09-25 | Prasyarat | Kategori `paket opsional` (scipy) ikut dihitung dalam total pemeriksaan tetapi tidak dicetak, karena daftar kategori pada `scripts/preflight.py` tidak memuatnya | Tidak diubah; status scipy diverifikasi manual (1.17.1 terpasang) | Perbaikan yang diminta hanya untuk deteksi versi `rank_bm25` |
| 2026-09-25 | Prasyarat | `HF_HUB_DISABLE_SYMLINKS=1` dijadikan variabel lingkungan user lewat `setx` | Berlaku untuk proses yang dibuat setelah Zed di-restart; proses unduh/model yang sudah berjalan tanpa variabel ini rentan pada galat symlink yang sama | Disetujui manusia. Perubahan hanya memengaruhi cara cache Hugging Face menyimpan berkas (salin, bukan tautan), sehingga kebutuhan disk sedikit lebih besar |
| 2026-09-25 | Langkah 2 | Protokol 5.7.1 memakai variabel `method` di awal loop `num_examples`, padahal variabel itu baru ada di loop dalam | Pemeriksaan `zero_shot` diletakkan di awal loop `method` | Efek yang diminta tetap tercapai: `zero_shot` hanya dijalankan pada k terkecil. Alternatif lain akan menyebabkan `NameError` |
| 2026-09-25 | Langkah 2 | `sampling_seed` diminta ada pada bagian 5.1 tetapi tidak dijelaskan pemakaiannya | Ditambahkan ke kedua `fewshot_config.json`, tidak dikonsumsi script mana pun | Tidak mengarang perilaku baru. Bila seed ini dimaksudkan untuk pemilihan sampel evaluasi manusia, perlu keputusan manusia |
| 2026-09-25 | Langkah 2 | `hf_token` tersimpan dalam bentuk teks biasa pada kedua `fewshot_config.json` dan pada `DEFAULT_CONFIG` di dalam script | Tidak diubah sesuai bagian 18; diverifikasi masih valid (akun `fikrihasani`) | Risiko kredensial perlu ditangani di luar protokol ini, misalnya rotasi token setelah seluruh eksperimen selesai |
| 2026-09-25 | Langkah 3 | Cache embedding retrieval di `outputs/cache` tidak memuat penanda versi split (`texts_{personality}_pool.json`, `embeddings_{personality}_pool.npy`), dan isinya terbukti berasal dari split LAMA: keempat entri identik dan seurutan dengan pool split lama, sementara irisan dengan pool v2 hanya 22-30%. Cache competence memuat 5.965 teks dengan 5.151 unik (814 duplikat, 13,7%), persis angka duplikasi index lama pada README | Disetujui manusia: keempat pasang berkas dinetralkan dengan sufiks `.split_lama_20260611` (tidak ada yang dihapus). Cache dibangun ulang oleh uji jalur dan terverifikasi identik dengan pool `formality_splits_v2` dan `brand_splits_v2` | Tanpa tindakan ini seluruh hasil v2 akan dihitung di atas indeks retrieval split lama, yaitu cacat yang justru ingin diperbaiki revisi ini |
| 2026-09-25 | Langkah 3 | Seluruh 30 generasi gagal: `Hugging Face generation failed: The following model_kwargs are not used by the model: ['generator']` | Disetujui manusia: `gen_kwargs['generator'] = torch.Generator(...)` diganti `torch.manual_seed(int(seed))` tepat sebelum `generate()` pada kedua pipeline. Diverifikasi: seed sama dua kali menghasilkan teks identik, seed berbeda menghasilkan teks berbeda, tanpa ERROR | Terverifikasi pada pustaka terpasang: `generate()` transformers 5.8.0 tidak memiliki parameter `generator`, dan `_validate_model_kwargs` kini `raise ValueError` untuk kwarg tak terpakai (pada transformers 4.x hanya peringatan). Parameter dekode bagian 18 tidak berubah |
| 2026-09-25 | Langkah 3 | Percobaan kedua gagal dengan `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f64f'` pada `print_debug_samples_from_df`, karena keluaran model memuat emoji dan stdout yang dialihkan ke berkas memakai cp1252 | `setx PYTHONIOENCODING utf-8` dan `setx PYTHONUTF8 1`; proses generasi dijalankan dengan kedua variabel itu disuntikkan ke lingkungan proses | Pola `tee` yang disarankan protokol mengalami galat yang sama di Windows. Ini setelan lingkungan, bukan perubahan kode, sehingga bagian 18 tidak tersentuh |
| 2026-09-25 | Langkah 3 | Kolom `eos_reached` selalu bernilai False pada uji determinisme, padahal generasi berhenti normal | Tidak ada perubahan kode. Dilaporkan sebagai sifat model: `generation_config.eos_token_id` Gemma 3 adalah `[1, 106]`, sedangkan `tokenizer.eos_token_id` adalah 1. Turn berakhir pada token `<end_of_turn>` (106), sehingga perbandingan dengan id 1 memberi False | Definisi kolom mengikuti bagian 5.4 protokol. Interpretasi truncation harus memakai kolom `output_tokens` dibanding `max_new_tokens`, bukan `eos_reached`; dicatat untuk LAPORAN_AKHIR |
| 2026-09-25 | Langkah 3 | Folder `model_results_dir/google_gemma-3-4b-it` masih memuat 96 berkas hasil lama, sehingga gerbang `check_smoke_output.py --dir` dan `evaluate_results.py --results` akan mencampur berkas lama tanpa kolom baru | Gerbang dijalankan terhadap `smoke_output_dir/google_gemma-3-4b-it`. Untuk Langkah 8, `evaluate_results.py` harus dipanggil dengan `--patterns "*_seed*_results.csv"` agar hanya berkas v2 yang dibaca | `evaluate_results.py` memilih berkas dengan `glob` dan sudah menyediakan opsi `--patterns`; berkas lama tidak memuat `_seed` sehingga pola itu memisahkannya dengan bersih |
| 2026-09-25 | Langkah 4 | Berkas split `brand_splits_v2/*.csv` tidak memuat kolom `label`, sedangkan `brand_splits_v2` tetap dibutuhkan oleh `Dataset.from_pandas` di `classifier_brand/main.py` | Ditambahkan pemetaan `label` dari kolom `personality` memakai `label2id` yang sama dengan yang dibangun dari korpus gabungan, lalu dicetak jumlah label tak terpetakan (hasil: 0) | Bagian 7 protokol hanya menyebut pengarahan `split_dir` dan penghapusan blok split, tanpa membahas kolom label. Pemetaan ini diperlukan agar script berjalan tanpa mengubah definisi label |
| 2026-09-25 | Langkah 4 | Bobot kelas (`class_weights`) pada `classifier_brand/main.py` tetap dihitung dari korpus gabungan penuh (75.756 baris), bukan dari train split v2 (24.820 baris) | Dibiarkan seperti semula | Bobot kelas adalah frekuensi agregat, bukan kebocoran teks, dan membiarkannya menjaga perbandingan dengan run lama sehingga satu-satunya yang berubah adalah split. Dicatat sebagai keterbatasan di LAPORAN_AKHIR |
| 2026-09-25 | Langkah 4 | Pelatihan menimpa `classification_report_test.txt` (formality) dan `test_report.txt` (Aaker) yang merupakan laporan run lama | Salinan laporan lama dibuat lebih dulu dengan akhiran `_LAMA_20260611` di folder pelatihan maupun di `style_classifier`, sehingga keduanya tetap ada untuk pembanding | Laporan lama dipakai sebagai angka pembanding pada laporan akhir dan tidak boleh hilang |
| 2026-09-25 | Langkah 4 | Protokol memakai `cp -r model_results_dir/<model>_roberta ../<repo>/style_classifier`; pada PowerShell/bash, penyalinan ke folder yang sudah ada akan membuat subfolder bersarang, sehingga `--classifier style_classifier` tidak akan menemukan bobot | Isi folder model (config, bobot, tokenizer, laporan) disalin ke dalam `style_classifier`, sedangkan checkpoint tidak disalin | `calibrate_classifier.py` dan `evaluate_results.py` memanggil `from_pretrained(args.classifier)`, jadi folder itulah yang harus memuat bobot |
| 2026-09-26 | Langkah 5 | Bug pada script bundel `scripts/evaluate_results.py`: argparse mendefinisikan opsi `--patterns` (baris 166) tetapi kode membaca `args.pattern` (baris 177 dan 180), sehingga evaluasi pertama gagal seketika dengan `AttributeError: 'Namespace' object has no attribute 'pattern'` | Dua rujukan itu diperbaiki menjadi `args.patterns`; pemeriksaan lain tidak diubah dan `py_compile` lulus. Evaluasi dijalankan ulang dan selesai tanpa galat | Tanpa perbaikan ini Langkah 8 tidak dapat berjalan sama sekali. Perbaikan hanya membuat script berjalan sesuai antarmukanya sendiri, tidak mengubah perhitungan |
| 2026-09-26 | Langkah 5 | `select_alpha_dev.py` memakai `--content-col content_preservation` sebagai bawaan, yaitu kolom **encoder lama** (`simcse-indobert`), sedangkan bagian 11 protokol menyatakan kolom lama tidak boleh dijadikan acuan utama | Pemilihan alpha dijalankan dua kali: `alpha_star.json` memakai `content_preservation_LaBSE`, dan `alpha_star_legacy_content.json` memakai kolom lama sebagai pembanding. Kedua kurva dilaporkan | Keputusan manusia kemudian menetapkan LaBSE sebagai kolom kriteria untuk kedua korpus, jadi kolom isi yang dipakai pada Langkah 6 dan 7 adalah `content_preservation_LaBSE` |
| 2026-09-26 | Langkah 5 | Ketika fluency dihitung, `evaluate_results.py` menimpa kolom `output_tokens` dan `eos_reached` dengan definisi lain (`eos_reached` menjadi heuristik tanda baca `[.!?"]$`) | Dibiarkan; dilaporkan apa adanya | Berkas hasil generasi tetap memakai definisi bagian 5.4, sedangkan berkas `evaluated_v2_*` memakai definisi tanda baca. Perbedaan ini harus disebut di LAPORAN_AKHIR agar tidak salah tafsir |
| 2026-09-26 | Langkah 5 | Kolom isi mana yang dipakai sebagai dasar kriteria pemilihan alpha | Keputusan manusia: `content_preservation_LaBSE` dipakai sebagai kolom kriteria untuk KEDUA korpus | Konsistensi antar korpus lebih penting daripada kecocokan dengan run lama; bagian 11 juga menyatakan kolom encoder lama bukan acuan utama |
| 2026-09-26 | Langkah 5 | Target informal: alpha 0,7 menang tipis atas 0,3 (H 0,86615 vs 0,86522, selisih 0,00093) | Keputusan manusia: pakai alpha 0,7 tetapi TIDAK boleh disebut optimal tanpa kualifikasi. Kurva lengkap kelima alpha disajikan, pemilihan dinyatakan mengikuti kriteria yang ditetapkan lebih dahulu, dan keputusan akhir diserahkan pada uji signifikansi berpasangan di Langkah 9 | Pada n = 250 galat baku proporsi sekitar 0,02, sehingga rentang 0,3 sampai 0,7 tidak terbedakan pada target ini |
| 2026-09-26 | Langkah 5 | Target formal: akurasi gaya hanya 0,108 sampai 0,136 pada seluruh alpha, rentang 0,028 yaitu sekitar 1,4 kali galat baku | Keputusan manusia: alpha TIDAK ditetapkan untuk target formal. Laporan harus menyatakan gaya formal tidak tercapai pada semua alpha dan pemilihan alpha pada target itu tidak bermakna. Untuk tabel naskah dipakai satu alpha per korpus yang diambil dari target informatif (informal), dan kurva target formal disajikan sebagai bukti ketidakpekaan | Angka berada di aras derau sehingga alpha yang menang hanya menang karena keberuntungan. Pada data lama alpha 0,5 terpilih dengan kriteria yang sama, jadi pilihan itu berubah hanya karena derau |
| 2026-09-26 | Langkah 5 | Evaluasi sapuan alpha-dev Aaker akan memakan 2 sampai 3 jam tambahan bila fluency dihitung | Keputusan manusia: evaluasi dijalankan dengan `--skip-fluency` | Kriteria pemilihan alpha tidak memakai fluency, jadi perhitungan itu tidak diperlukan untuk keputusan ini |
| 2026-09-26 | Langkah 5 | Bukti pendukung untuk keputusan "alpha target formal tidak ditetapkan": `scripts/audit_style_accuracy.py` (read-only) dijalankan saat sapuan Aaker masih berjalan | Hasilnya dicatat apa adanya di bawah | Menjawab pertanyaan apakah akurasi gaya rendah pada target formal adalah regresi patch revisi atau sifat yang sudah ada |
| 2026-09-26 | Langkah 5 | Peluncuran langkah (c) lewat `Start-Process` dengan `-RedirectStandardOutput` dan `-RedirectStandardError` mati seketika tanpa keluaran: kedua berkas log 0 byte, PID hilang, tidak ada berkas hasil | Perintah yang sama dijalankan ulang di depan dengan penangkapan keluaran dan berhasil (exit 0, 61,7 detik). Peluncuran panjang berikutnya memakai peluncur Python detached dengan dua berkas terpisah untuk stdout dan stderr | Sebabnya tidak dapat dipastikan dari bukti yang ada; yang penting adalah stdout dan stderr tetap dialihkan ke berkas terpisah dan PID dicatat, hanya mekanisme peluncurnya yang berbeda |
| 2026-09-26 | Langkah 5 | Pemilihan alpha Aaker: `excitement` menang dengan jarak H hanya 0,01290 dari peringkat kedua | Alpha 0,5 dilaporkan sebagai hasil kriteria, tetapi tidak disebut optimal tanpa kualifikasi; keputusan akhir diserahkan ke uji signifikansi Langkah 9. Pada `competence` jarak 0,06551 sehingga alpha 0,3 dapat disebut terpilih | Aturan runbook bagian 4 langkah 5: bila selisih hanya di digit terakhir, jangan menulis "optimal" tanpa kualifikasi |
| 2026-09-26 | Langkah 5 | Analisis tambahan hipotesis panjang keluaran: "alpha kecil menghasilkan keluaran lebih panjang karena menyalin lebih banyak eksemplar" | Dihitung dari kesepuluh berkas hasil sapuan, dilaporkan apa adanya | Didukung kuat pada competence (monoton 58,69 menjadi 31,61 token), lemah pada excitement (40,88 menjadi 36,56 dengan nilai terpendek di α=0,7). Bukti untuk R2-09 hanya kuat pada satu target |
| 2026-09-26 | Langkah 5 | KOREKSI manusia: aras acak korpus Aaker adalah 0,20 (lima kelas kepribadian), bukan 0,50 seperti pada tugas biner | Dua pernyataan di `RUN_LOG.md` diperbaiki: blok (d) tentang akurasi excitement dan blok hasil audit tentang akurasi run lama korpus Aaker | Angka yang benar: excitement 0,318-0,336 adalah sekitar 1,6 kali aras acak (bukan dekat aras acak); competence pada alpha 0,1-0,3 sekitar 4,2-4,4 kali aras acak; run lama 0,5250 dan 0,5025 sekitar 2,6 dan 2,5 kali aras acak |
| 2026-09-26 | Langkah 6 | Runbook bagian 5 (daftar periksa persetujuan run utama) masih menyebut `run_seeds` berisi `[42]`, sedangkan rencana yang disetujui manusia memakai `run_seeds [42, 43, 44]` dengan `--only-seed` agar konfigurasi identik pada keenam peluncuran | Diikuti rencana yang disetujui manusia: `run_seeds [42, 43, 44]` pada berkas, satu seed per peluncuran lewat `--only-seed`. SHA-256 config dicatat pada setiap manifes sebagai bukti konfigurasi tidak berubah | Konfigurasi identik membuat SHA-256 sama di keenam manifes, sehingga setiap perubahan config setelah peluncuran pertama langsung terdeteksi. Ini juga yang membuat `skip_existing` benar-benar melanjutkan dan bukan menghitung ulang |
| 2026-09-26 | Langkah 6 | Sesi agen belum mewarisi variabel lingkungan hasil `setx` (Zed belum di-restart), padahal pipeline dapat mati karena emoji pada stdout dengan codec cp1252 | Peluncur versi baru menyetel `PYTHONIOENCODING`, `PYTHONUTF8`, dan `HF_HUB_DISABLE_SYMLINKS` pada proses anak tanpa menimpa nilai yang ada, lalu mencatatnya pada manifest sebagai `env_wajib` dan `env_baru_disetel` | Terbukti pada peluncuran formality_s42: ketiganya tercatat disetel baru oleh peluncur, sehingga peluncuran tidak lagi bergantung pada sesi yang sudah menyetelnya |
| 2026-09-27 | Langkah 6 | Peluncuran pertama dijalankan tanpa `--only-seed 42` sehingga proses menjalankan ketiga seed dalam satu proses, bukan satu seed seperti rencana | Proses TIDAK diinterupsi sesuai perintah manusia saat itu. Penyimpangan dicatat di blok Langkah 6 dan 7 beserta bukti keadaan berkas | Kekeliruan penyusunan perintah oleh agen. Hasil tidak terpengaruh karena setiap sampel memakai seed sendiri dan nama berkas memuat penanda seed, sehingga tidak ada berkas yang tertimpa. Yang berubah hanya pembagian pekerjaan antar peluncuran |
| 2026-09-27 | Langkah 6 | Proses formality dihentikan di tengah karena struktur tiga seed bertabrakan dengan urutan loop: target di lapisan luar, seed di lapisan dalam, sehingga selesainya formal untuk tiga seed tidak berarti formality selesai dan target informal belum tersentuh sama sekali | PID 24824 dihentikan 06:09:49; berkas seed 43 dan 44 dipindahkan ke `ARSIP/seed43_44_formality` (76 berkas, tidak ada yang dihapus); `run_seeds` disetel `[42]` pada kedua config; formality akan diluncurkan ulang untuk mengisi 19 konfigurasi informal | Dengan satu seed, tidak ada konfigurasi yang perlu dipilih untuk diulang, dan peluncuran ulang tidak perlu bergantung pada flag `--only-seed` yang pernah terlewat. Berkas seed 43/44 disimpan agar bila varians antar-jalan diminta lagi hanya evaluasi yang perlu diulang, bukan pembangkitan |
| 2026-09-27 | Langkah 6 | Hash 16 aksara `scripts/replication_metric.py` tidak cocok dengan yang dikirim manusia (`b3bc0872ebec977d` di disk vs `b3bc872ebec977d3` diharapkan), sehingga langkah 6 sempat ditahan | Manusia mengonfirmasi salah ketik dan memberi hash kanonik. Verifikasi diulang dengan hash 64 aksara: `b3bc0872ebec977db99a7a2dd5c261d60362b0d64ceb280db5a13bc558f8c214` COCOK, ukuran 8.116 byte. Langkah 6 lalu dijalankan | Aturan manusia: verifikasi hash sebelum dipakai. Untuk seterusnya setiap pemeriksaan memakai hash lengkap 64 aksara lewat `Get-FileHash`, supaya tidak ada lagi ruang salah ketik 16 aksara |
| 2026-09-27 | Langkah 6 | Konfigurasi `zero_shot` memakan waktu hampir dua kali konfigurasi lain (16,4 menit vs 8,2-9,0 menit untuk 250 sampel) | Tidak ada perubahan konfigurasi; dicatat sebagai sifat metode dan dipakai untuk memperkirakan waktu langkah 6 dan 7 lebih akurat | Tanpa eksemplar, prompt lebih pendek dan model cenderung menghasilkan teks lebih panjang, sehingga biaya per sampel naik |
| 2026-09-27 | Langkah 8 (persiapan) | Model fluency tidak seragam pada pipeline asli: `fewshot_aaker/eval.py` memakai `Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct` sedangkan `fewshot_formality/eval.py` memakai `Sahabat-AI/llama3-8b-cpt-sahabatai-v1-instruct`, sementara naskah hanya menyebut satu model | Koreksi manusia: rerun memakai `Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct` pada KEDUA korpus dan disebut eksplisit lewat opsi saat memanggil `evaluate_results.py`. Skrip versi baru sudah memakai nilai bawaan itu; hash 64 aksara `9653910ee965d66b25b333dbc6fd684fb5ac40f8cb94124881e4ba2426841b60` dan ukuran 12.702 byte terverifikasi cocok | Nilai PPL dari sapuan alpha Langkah 5 TIDAK dipakai untuk memilih alpha, sehingga tidak ada yang perlu dibangkitkan ulang; yang wajib memakai model benar hanya evaluasi Langkah 8. Saat Langkah 8 dijalankan, nama model fluency yang benar-benar dimuat akan dilaporkan dari log, bukan hanya nilai bawaan opsi |
| 2026-09-27 | Langkah 7 | Perkiraan waktu Aaker meleset sekitar satu jam (perkiraan 9,2 sampai 9,7 jam, nyata 10 jam 23 menit) | Perkiraan dikoreksi memakai laju nyata; anggaran tiap korpus memakai laju normal ditambah sekitar 1,8 sampai 1,9 kali untuk `zero_shot` dan `hybrid_early` alpha kecil | `zero_shot` memakan 5,89 detik per sampel vs 3,3 pada konfigurasi normal (Aaker 1,8 kali; formality 3,94 vs 2,06, yaitu 1,9 kali) |
| 2026-09-27 | Langkah 8 | `evaluate_results.py` tidak mencetak nama model fluency pada keluarannya, padahal manusia meminta pelaporan model yang benar-benar dimuat | Dibuktikan dari jumlah entri pemuatan bobot pada log: 464 entri pada kedua log, dan indeks cache `gemma2-9b-cpt-sahabatai-v1-instruct` memuat tepat 464 tensor sedangkan `llama3-8b-cpt-sahabatai-v1-instruct` 291 tensor | Tanpa bukti ini pernyataan "model fluency yang benar sudah dipakai" tidak dapat dipertanggungjawabkan dari berkas hasil |
| 2026-09-27 | Langkah 8 | Proporsi keluaran degenerate korpus formality 13,77 persen tampak jauh di atas angka lama pada README (0,61 persen korpus STIF) | Manusia menemukan sebabnya di mesin ini: skrip evaluasi LAMA untuk formality memakai `Sahabat-AI/llama3-8b-cpt-sahabatai-v1-instruct` sedangkan skrip lama untuk Aaker memakai `gemma2-9b`, dan revisi ini memakai `gemma2-9b` untuk KEDUA korpus. Jadi korpus yang model fluency-nya berubah melonjak (formality) sedangkan yang modelnya tetap hampir tidak bergerak (Aaker 5,51 menjadi 5,86 persen). Angka 0,61 persen TIDAK dipakai sebagai pembanding, dan lonjakan itu TIDAK boleh ditulis sebagai penurunan mutu keluaran | Ambangnya sama di kedua angka (PPL di atas 1000) sehingga angkanya tetap sebanding sebagai angka, tetapi sebab perubahannya adalah model fluency, bukan mutu keluaran. Ini harus diungkapkan di LAPORAN_AKHIR |
| 2026-09-27 | Langkah 9 | `report_metrics.py` menyimpan statistik per berkas, sehingga tidak langsung memberi median dan trimmed PPL per target seperti yang diminta manusia | Dibuat skrip bantu read-only `scripts/ppl_per_target.py` yang menghitung statistik langsung dari kolom per sampel `fluency_ppl` pada 38 berkas korpus formality, lalu menulis `TABEL_ppl_formality_per_target.csv` di akar bundel | Median dari median antar berkas bukan median sebenarnya; cara langsung dari 9.500 nilai per sampel itulah yang sah. Skrip tidak menulis apa pun ke `evaluation_result_v2` |
| 2026-09-27 | Langkah 9 | `zero_shot` menyimpang dari seluruh metode retrieval: pada target formal formality akurasi gayanya 0,780 (tertinggi) dan PPL mediannya 39,82 (terendah), tetapi `content_preservation`-nya paling buruk (0,517 formal; 0,562 informal); pada target informal akurasinya justru 0,136 (terendah) | Dilaporkan apa adanya, dengan CI berpasangan: `zero_shot` berbeda bermakna dari semua retrieval pada kedua target, dan arah selisihnya berbalik menurut target | Keluaran `zero_shot` adalah teks yang fasih dan bagi classifier condong ke kelas formal, tetapi paling lemah mempertahankan isi. Tidak boleh dipakai untuk menyimpulkan keunggulan `zero_shot`; harus diungkapkan di LAPORAN_AKHIR |
| 2026-09-27 | Langkah 9 | Keputusan alpha informal 0,7 diverifikasi pada data uji: terhadap alpha 0,3, `content_preservation_LaBSE` TIDAK berbeda bermakna (d -0,008; CI [-0,023; +0,007]), sedangkan `style_accuracy` justru lebih rendah pada 0,7 (d +0,048; CI [+0,016; +0,080]; bermakna) | Alpha 0,7 tetap dilaporkan sebagai hasil kriteria yang ditetapkan lebih dahulu dan TIDAK disebut optimal; kurva lengkap kelima alpha disajikan | Konsisten dengan keputusan manusia 2026-09-26: rentang 0,3 sampai 0,7 tidak terbedakan pada target informal, sehingga pemilihan tidak boleh diklaim sebagai keunggulan |
| 2026-09-27 | Langkah 9 | Korpus Aaker target competence menunjukkan pola tukar-menukar gaya-isi yang tajam: alpha kecil unggul gaya (a0,1 0,864; a0,3 0,842) tetapi terburuk mempertahankan isi (a0,1 0,395; a0,3 0,488), sedangkan alpha besar sebaliknya (a0,9 gaya 0,200; isi 0,717) | Dilaporkan apa adanya; kurva lengkap kedua sumbu per alpha diwajibkan pada LAPORAN_AKHIR | Alpha 0,3 untuk tabel naskah dipilih dari kriteria `content_preservation_LaBSE` pada dev set (jarak H 0,06551), dan uji berpasangan menunjukkan a0,1 serta centroid tidak berbeda bermakna darinya pada akurasi gaya, jadi ketiganya setara |
| 2026-09-28 | Langkah 9 | `bootstrap_significance.py` versi lama memiliki dua cacat: tidak memisahkan target sehingga 190 pasangan Aaker memuat sekitar 100 pasangan lintas target, dan label konfigurasi tidak memuat `k` sehingga berkas k=10 dan k=5 bertabrakan dan salah satunya tertimpa tanpa peringatan | Skrip versi baru dipakai (SHA-256 `5c4603662007133cc52954f10faf0faddfd94c8aa0be2e872e2eba1528ed9472`, 10.553 byte, terverifikasi), kedua belas tabel uji dihitung ulang dengan `--only-seed 42` dan nama berkas yang sama, dan satu tabel tambahan dibuat: `TABEL_kepekaan_k_formality.csv` | Angka uji yang dilaporkan sebelumnya tidak sah: pasangan lintas target tidak bermakna dan k yang tertimpa membuat tabel formality hanya memuat 10 konfigurasi per target, bukan 19. Sesudah koreksi: formality 38 konfigurasi / 342 pasangan sebanding / 361 dilewati; Aaker 20 / 90 / 100; nol peringatan label bertabrakan |
| 2026-09-28 | Langkah 9 | Kepekaan k baru dapat dihitung setelah label memuat `k` | Dilaporkan sebagai tabel `TABEL_kepekaan_k_formality.csv`: dari 18 pasangan k10-vs-k5 per metrik, hanya 1/18 bermakna pada `style_accuracy` sedangkan `content_preservation` 10/18 | Menjawab R2-12 dan R3-W2: menambah contoh dari 5 ke 10 tidak memperbaiki gaya secara umum, keuntungannya terutama pada pemertahanan isi target formal. Pengecualian: formal centroid justru turun 0,148 pada akurasi gaya |
| 2026-09-28 | Langkah 10 | Protokol menyebut langkah ini "sampel untuk evaluasi manusia", dan keputusan manusia adalah hanya mengekspor sampel tanpa menjalankan penilaian | Ekspor dijalankan lewat skrip baru `scripts/export_human_eval.py`: 400 baris formality (16 berkas metode) dan 200 baris Aaker (8 berkas metode), masing-masing 25 kalimat sumber | Bagian 10 LAPORAN_AKHIR.md menyatakan evaluasi manusia TIDAK dijalankan, sehingga tidak ada angka kesepakatan antar penilai. `random` dan `zero_shot` dikecualikan karena protokol menyebut "empat metode utama" |
| 2026-09-28 | Langkah 11 | `HASIL/keluaran_generasi/` berisiko memuat 96 berkas run lama tanpa penanda seed sehingga materi naskah memuat dua eksperimen | Penyalinan dibatasi pada penanda `_seed42`: 116 berkas (76 formality + 40 Aaker). Berkas lama (64 formality + 32 Aaker) tidak disalinkan | Permintaan manusia. `HASIL/` memuat 87 berkas dan seluruhnya berpenanda atau turunan seed 42 |
| 2026-09-28 | Langkah 11 | Dua tabel Langkah 9 dihasilkan skrip bantu di luar protokol, sehingga reprodusibilitasnya perlu dijamin | SHA-256 dicatat: `k_sensitivity.py` `ee2e2e7cd99fa1b34730be09871d305165caec8f8adaa703b11156d813724a5d` (3.562 byte); `ppl_per_target.py` `4904c4cc84ee09d69fa00c6110dd30307cdf9dc7ad36c41495421a4178826536` (4.104 byte); `export_human_eval.py` `6a32098c099d8f124b0ab30a6aacad5fde8dc5daf7666a192207926f4b96778e` (2.390 byte) | Diminta manusia. Ketiganya read-only: hanya membaca berkas hasil yang sudah ada dan tidak menyentuh `evaluation_result_v2` |
| 2026-09-28 | Luar protokol | Bundel 19,10 GB memberatkan untuk dikirim; 16,76 GB di antaranya checkpoint pelatihan classifier (`classifier_brand/model_results_dir/brand_model_roberta/checkpoint-*` 13,97 GB = 10 folder, `classifier_formality/model_results_dir/formality_model_roberta/checkpoint-*` 2,79 GB = 2 folder) | Disetujui manusia opsi A (non-destruktif): dibuat salinan transfer **tanpa menghapus apa pun** ke `D:\kirim\JCCE-First Revision` memakai `robocopy /E /XD` dengan kedua belas nama folder checkpoint. Hasil: 1.126 berkas, 2,35 GB, 0 gagal, 0 folder checkpoint pada salinan | Checkpoint adalah state antara Trainer (salinan `model.safetensors` + `optimizer.pt` 951,2 MB + scheduler/rng/scaler) dan tidak dibaca oleh `evaluate_results.py` maupun `calibrate_classifier.py`, yang memuat `fewshot_*/style_classifier` tanpa subfolder checkpoint. Sumber tetap utuh (19,10 GB, kedua belas folder checkpoint masih ada), sehingga aturan 4 tidak dilanggar |

Hasil `audit_style_accuracy.py` (read-only, dijalankan 2026-09-26 11:16):

```
formality, RUN LAMA (evaluation_result, 32 berkas, 8.000 baris):
  target formal   : n 4.000, rata-rata style_accuracy 0,1662 (min 0, maks 1)
  target informal : n 4.000, rata-rata style_accuracy 0,9742
  sebaran style_predicted target formal  : informal 3.335, formal 665
  sebaran style_predicted target informal: informal 3.897, formal 103
formality, SAPUAN ALPHA-DEV BARU (10 berkas, 2.500 baris):
  target formal   : n 1.250, rata-rata 0,1216
  target informal : n 1.250, rata-rata 0,9648
  sebaran style_predicted target formal  : informal 1.098, formal 152
  sebaran style_predicted target informal: informal 1.206, formal 44
aaker, RUN LAMA (16 berkas, 8.000 baris):
  target competence: n 4.000, rata-rata 0,5250
  target excitement: n 4.000, rata-rata 0,5025
  sebaran style_predicted scattered di kelima kelas
aaker, SAPUAN ALPHA-DEV: belum ada berkas evaluasi karena baru akan dievaluasi pada langkah (c)
```

Kesimpulan dari angka di atas: akurasi gaya rendah pada target formal **sudah ada pada run lama**
(0,1662) dan sedikit lebih rendah pada sapuan baru (0,1216). Jadi ini bukan regresi yang diperkenalkan
patch revisi, melainkan sifat pipeline dan model pada korpus STIF: keluaran untuk target formal
berakhir di kelas informal pada 83% baris run lama dan 88% baris sapuan baru. Untuk korpus Aaker, aras acak adalah 0,20 karena korpus ini punya lima kelas kepribadian. Dengan
demikian 0,5250 dan 0,5025 pada run lama adalah sekitar 2,6 dan 2,5 kali aras acak, bukan dekat aras
acak, dan prediksinya tersebar di kelima kelas. Kalimat sebelumnya pada blok ini menyebut aras acak 0,50;
itu keliru untuk korpus lima kelas dan dikoreksi pada 2026-09-26.

---

## Ringkasan waktu

| Langkah | Estimasi protokol | Waktu nyata |
|---|---|---|
| 0 Prasyarat | 10 menit | sekitar 15 menit; selesai 2026-09-25 15:57:46 |
| 1 Verifikasi split | 5 menit | sekitar 3 menit; selesai 2026-09-25 16:00:22 |
| 2 Patch konfigurasi | 1 jam | sekitar 5 jam 20 menit termasuk penulisan patch manual; selesai 2026-09-25 21:20:58 |
| 3 Uji jalur | 30 menit | 19 menit; 21:26:08 -> 21:45:15 (dua korpus, setelah dua kali perbaikan) |
| 4 Latih dan kalibrasi | 2 jam | 14 menit; 21:54:26 -> 22:08:22 |
| 5 Sapuan alpha | 2 jam | sapuan formality 1 jam 25 menit (22:26:17 -> 23:51:20), eval dev 09-26 10:06:56; sapuan Aaker selesai 09-26 15:14:04, eval dev 16:15:23. Jeda antar tahap termasuk waktu menunggu persetujuan manusia |
| 6 Generasi formality | 15 jam | generasi bersih 5 jam 48 menit (2 jam 55 menit formal + 2 jam 53 menit informal); dinding 09-26 21:24:47 -> 09-27 09:06:55 termasuk penghentian dan peluncuran ulang |
| 7 Generasi Aaker | 15 jam | 10 jam 23 menit; 09-27 10:19:48 -> 20:43 |
| 8 Evaluasi lengkap | 5 jam | 1 jam 34 menit; Aaker 54 menit (21:03:31 -> 21:57:39), formality 40 menit (21:58:40 -> 22:38) |
| 9 Statistik | 1 jam | tidak diukur presisi; perhitungan ulang dua belas tabel uji pada 09-28 berlangsung beberapa menit tanpa GPU |
| 10 Ekspor sampel manusia | 1 jam | kurang dari 1 menit |
| 11 Pengepakan keluaran | 1 jam | sekitar 1 jam |

Catatan: angka dinding pada Langkah 5 sampai 9 memuat jeda menunggu persetujuan manusia, sehingga
tidak sama dengan waktu komputasi. Waktu komputasi yang terukur dicantumkan pada baris masing-masing.
Satu berkas log dev set, `run_eval_alphadev_aaker.log`, berukuran 0 byte karena pola pengalihan log
lama; hasil evaluasinya tetap terbentuk (`evaluation_result_alphadev`, 10 berkas) dan sudah
diverifikasi berjumlah 500 baris per berkas.
