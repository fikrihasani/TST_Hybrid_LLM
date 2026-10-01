# Protokol Split Data JCCE-10619

Dokumen ini menjelaskan bagaimana pembagian data (split) pada kedua korpus eksperimen
dilakukan, di mana kodenya berada, dan apa yang terbukti ketika direproduksi ulang.
Seluruh angka di sini dihasilkan oleh `verify_split_protocol.py`.

---

## 1. Di mana kode split berada

| Korpus | Script pembuat split | Status |
|---|---|---|
| Aaker (brand personality) | `C:\Devs\Code\Python\brand_personality_classification - Copy\main.py` baris 49 sampai 51 dan 54 sampai 57 | Ada, lengkap |
| STIF (formality) | `C:\Devs\Code\Python\formality_cls - Copy\main.py` baris 46 sampai 53 dan 57 sampai 60 | Ada, lengkap |

Catatan penting: script pembuat split **tidak berada di dalam repo eksperimen**
(`TST_fewshot_formality_hf_ref` dan `TST_fewshot_aaker - Copy`). Kedua repo itu hanya
membaca berkas hasil split dari `data/formality_splits/` dan `data/brand_splits/`.
Komentar di dalam kode eksperimen menyebut hal ini: "Pastikan script klasifikasi
formality sudah selesai dieksekusi terlebih dahulu".

Kedua script itu adalah script pelatihan classifier gaya, dan sekaligus pembuat split.
Buktinya: berkas split di `formality_cls - Copy/data/formality_splits/` identik byte per byte
dengan berkas yang dipakai repo eksperimen, sehingga asal-usul berkas split dapat dipastikan.

Seluruh berkas split juga **dapat direproduksi persis** dari berkas sumber dengan protokol yang
sama, sehingga protokolnya dapat dinyatakan secara lengkap di naskah.

---

## 2. Protokolnya

Tiga baris ini adalah inti seluruh protokol, persis seperti tertulis di
`brand_personality_classification - Copy/main.py` baris 49 sampai 51:

```python
rest_df, test_df          = train_test_split(df, test_size=0.10, random_state=42, stratify=df['label'])
classifier_df, retrieval_df = train_test_split(rest_df, test_size=(1/3), random_state=42, stratify=rest_df['label'])
train_df, val_df          = train_test_split(classifier_df, test_size=(1/6), random_state=42, stratify=classifier_df['label'])
```

Karakteristiknya:

| Aspek | Nilai |
|---|---|
| Rasio akhir | 50% train classifier, 10% validation classifier, 30% retrieval pool, 10% test |
| Metode | Tiga tahap `train_test_split` berurutan, bukan satu pemanggilan |
| Stratifikasi | Ya, pada kolom label gaya di setiap tahap |
| Seed | `random_state=42` pada ketiga tahap |
| Deduplikasi | Tidak ada |
| Pengelompokan (grouping) | Tidak ada |
| Penguncian pasangan paralel | Tidak diterapkan (lihat bagian 4) |
| Keluaran | Empat CSV ditulis ke folder split |

Urutan tahapnya: test diambil 10% lebih dulu, lalu dari sisa 90% diambil sepertiga sebagai
retrieval pool (30% dari total), lalu dari 60% sisanya diambil seperenam sebagai validation
(10% dari total), sehingga train classifier tinggal 50%.

### Berkas sumber dan berkas keluaran

| Korpus | Berkas sumber | Folder keluaran |
|---|---|---|
| Aaker | `brand_personality_classification - Copy\data\Combined Aaker Brand Personality - Cleaned v0.csv` (75.756 baris) | `TST_fewshot_aaker - Copy\data\brand_splits\` |
| STIF | `TST_fewshot_formality_hf_ref\data\combined_stif.csv` (4.998 baris) | `TST_fewshot_formality_hf_ref\data\formality_splits\` |

Berkas STIF itu sendiri dirakit dari `Downloads\stif_formal.txt` (2.499 baris) dan
`Downloads\stif_informal.txt` (2.499 baris), dengan urutan baris yang dipertahankan persis
untuk kedua blok.

Perlu dicatat: korpus Aaker diambil dari berkas **v0**, bukan dari berkas
`Cleaned v1 - With Human Validation.csv` yang sudah melewati validasi manusia (n=385, tiga
penilai). Jadi indeks retrieval dan classifier gaya untuk korpus Aaker dibangun di atas label
sebelum validasi.

### Ukuran hasil per split

| Korpus | Train (50%) | Validation (10%) | Retrieval pool (30%) | Test (10%) | Total |
|---|---|---|---|---|---|
| STIF | 2.498 | 500 | 1.500 | 500 | 4.998 |
| Aaker | 37.877 | 7.576 | 22.727 | 7.576 | 75.756 |

Distribusi kelas seimbang di setiap split. STIF: 1.249 formal dan 1.249 informal di train,
250 dan 250 di validation, 750 dan 750 di pool, 250 dan 250 di test. Aaker mengikuti proporsi
lima persona (competence, excitement, ruggedness, sincerity, sophistication) dengan stratifikasi
di setiap tahap.

---

## 3. Hasil verifikasi reproduksi

`verify_split_protocol.py` menjalankan ulang protokol di atas pada berkas sumber, lalu
membandingkan hasilnya dengan berkas split yang benar-benar dipakai eksperimen:

| Korpus | train | val | pool | test |
|---|---|---|---|---|
| Aaker | identik | identik | identik | identik |
| STIF | identik | identik | identik | identik |

Kedelapan berkas cocok persis. Artinya protokol split dapat dinyatakan secara lengkap di naskah
dan dapat direproduksi oleh reviewer dari berkas sumber. Untuk korpus STIF, hasil ini sekaligus
menunjukkan bahwa split-nya memang dihasilkan protokol tiga tahap yang sama, tanpa langkah
tambahan apa pun.

Perbandingan dilakukan pada nilai teks ternormalisasi, bukan pada indeks baris, karena berkas
split tidak menyimpan identifier sumber sehingga duplikat teks membuat pencocokan indeks ambigu.

---

## 4. Temuan yang bertentangan dengan naskah

Naskah menyatakan, pada bagian partisi data:

> "For the formality dataset (STIF), which natively consists of parallel pairs
> (formal-informal), we flattened the structure into a single corpus for unsupervised
> generation. However, to maintain integrity, parallel sentences were locked via a pair_id
> before splitting. If a formal sentence was assigned to the Test Set, its informal
> counterpart was explicitly restricted from entering the Retrieval Pool or Classifier Train
> Set."

Pemeriksaan atas berkas split yang benar-benar dipakai menunjukkan penguncian itu **tidak
diterapkan**, dan pada tingkat kode penguncian itu **tidak pernah ditulis**:

| Pemeriksaan | Hasil |
|---|---|
| String `pair_id` di seluruh kode | tidak ada satu pun kemunculan di seluruh `*.py` pada `C:\Devs\Code\Python` |
| Langkah pada `formality_cls - Copy/main.py` | hanya langkah A (test 10%), B (retrieval pool), dan C (train/val), tanpa langkah penguncian |
| Pasangan paralel yang kedua sisinya berada di split yang sama | 893 dari 2.499 (35,7%) |
| Ekspektasi bila tidak ada penguncian (independen) | 36,0% |
| Kesesuaian berkas split tersimpan dengan tiga langkah `train_test_split` | cocok persis, sehingga tidak ada koreksi pasca-proses |

Bila penguncian benar-benar diterapkan, angka ketiga seharusnya mendekati 100%. Karena berkas
split tersimpan cocok persis dengan hasil tiga langkah tanpa penguncian, dapat dipastikan tidak
ada penyuntingan manual setelah split dijalankan. Dengan demikian kalimat pada naskah
menggambarkan protokol yang direncanakan, bukan protokol yang dijalankan.

Dampak praktisnya terhadap indeks retrieval, dihitung per arah transfer:

| Arah transfer | Sumber uji | Pasangan targetnya berada di retrieval pool | Berada di train/val classifier |
|---|---|---|---|
| target FORMAL (sumber = kalimat informal di test, indeks = pool formal) | 246 | 77 (31,3%) | 141 (57,3%) |
| target INFORMAL (sumber = kalimat formal di test, indeks = pool informal) | 244 | 66 (27,0%) | 150 (61,5%) |

Maksudnya: untuk sekitar 27% sampai 31% kalimat uji, teks target yang seharusnya dihasilkan
sudah berada di dalam indeks retrieval. Karena pasangan formal dan informal sebuah kalimat
berbagi sebagian besar kata, metode BM25 dan dense berpotensi besar mengambil teks itu sebagai
eksemplar. Ini adalah bentuk kebocoran yang berbeda dari duplikasi verbatim, karena teksnya
memang tidak identik. Metode centroid tidak terpengaruh karena indeksnya tidak bergantung pada
query.

Jumlah sumber uji tertulis 246 dan 244, bukan 250 dan 250, karena beberapa kalimat test set
memiliki teks yang identik dengan kalimat di split lain sehingga penetapan split-nya menjadi
ambigu. Selisih ini tidak mengubah kesimpulan.

---

## 5. Catatan tentang consumer berkas split

Kode eksperimen hanya membaca dua dari empat berkas split:

- `fewshot_formality.py` dan `main.py` membaca `retrieval_pool.csv` dan `test_set.csv`.
- `train_set.csv` dan `val_set.csv` dipakai oleh script pelatihan classifier gaya, yaitu
  `formality_cls - Copy/main.py` dan `brand_personality_classification - Copy/main.py`. Kedua script
  itu juga yang menulis keempat berkas split, lalu melatih classifier dan menyimpan hasilnya sebagai
  `style_classifier/` di masing-masing repo eksperimen.
- `formality_cls - Copy/main.py` tidak menetapkan seed secara eksplisit, sehingga reproduksibilitas
  pelatihan classifier bergantung pada nilai default `TrainingArguments`. Skrip Aaker menetapkan
  `set_seed(42)`. Perbedaan ini sebaiknya diseragamkan dan dinyatakan di naskah.

Satu hal yang perlu dinyatakan di naskah: laporan klasifikasi classifier gaya
(`style_classifier/classification_report_test.txt` dan `style_classifier/test_report.txt`)
diukur pada `test_set.csv` yang sama dengan test set eksperimen TST. Untuk STIF support-nya 500
dan akurasinya 0,9220, untuk Aaker support-nya 7.576 dan akurasinya 0,93. Jadi himpunan yang
dipakai untuk mengklaim performa metrik adalah himpunan yang sama dengan yang dinilai metrik
tersebut. Ini bukan kebocoran ke indeks retrieval, tetapi perlu disebut sebagai keterbukaan
protokol karena reviewer kemungkinan menanyakannya.

---

## 6. Konsekuensi untuk revisi

Kedua korpus memerlukan perbaikan split sebelum regenerasi:

1. **Aaker**: hapus duplikat teks, lalu kelompokkan per `conversation_id_str`, tetap
   stratifikasi lima persona. Pengelompokan per akun tidak dapat dilakukan karena hanya ada
   24 akun brand di seluruh korpus.
2. **STIF**: terapkan penguncian pasangan paralel seperti yang sudah diklaim naskah. Karena
   berkas `stif_formal.txt` dan `stif_informal.txt` sejajar baris demi baris, `pair_id` dapat
   direkonstruksi tanpa data tambahan.

Catatan koreksi: pada rencana perbaikan versi pertama saya menyatakan korpus STIF tidak perlu
diregenerasi penuh, dengan alasan pool-nya nol duplikat dan output-nya tidak memuat replikasi
template. Kedua alasan itu tetap benar, tetapi keduanya tidak menangkap kebocoran pasangan
paralel. Karena sekitar 27% sampai 31% kalimat uji memiliki teks targetnya di dalam indeks
retrieval, pool STIF harus dibersihkan dan eksperimen STIF perlu dijalankan ulang. Beban
komputasinya tetap kecil: sekitar 8,5 menit per konfigurasi, jadi sekitar 4,5 jam untuk 32
konfigurasi.

---

## 7. Cara menjalankan ulang verifikasi

```bash
python verify_split_protocol.py
```

Exit code 0 berarti seluruh split dapat direproduksi persis dan pengukuran kebocoran pasangan
selesai. Skrip bersifat read-only.
