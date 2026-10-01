# Perubahan Naskah JCCE-10619 setelah Rerun

Daftar komponen yang harus ditulis ke manuskrip untuk revisi, per bagian, beserta butir reviewer yang
ditutup. Disusun agar dapat dikerjakan berurutan setelah rerun selesai.

Pasangan dokumen: `SPESIFIKASI_RERUN.md` untuk perubahan kode yang mendahuluinya.

Aturan urutan: **jangan menyentuh penomoran tabel, gambar, abstrak, dan angka mana pun di naskah
sebelum rerun selesai.** Angka akan berubah, sehingga pengerjaan lebih awal akan terbuang.

---

## 1. Tingkat prioritas

| Prioritas | Bagian | Alasan |
|---|---|---|
| P0 | Sec. 3.2 partisi data, Sec. 3.3 premis centroid, Sec. 3.5 metrik | Memuat klaim yang tidak didukung data atau kode. Risiko paling tinggi |
| P1 | Sec. 3.1 dataset, Sec. 3.4 setup, Sec. 4 seluruh tabel, Sec. 5 diskusi | Berubah total karena rerun |
| P2 | Judul, abstrak, kesimpulan, daftar referensi | Perbaikan terarah |
| P3 | Penomoran tabel dan gambar, cross-reference, bahasa, encoding | Dikerjakan paling akhir |

---

## 2. Perubahan per bagian

### Judul

Perbaikan gramatikal, butir R2-04. Menjadi: *"Retrieval Strategies **for** Indonesian Text Style
Transfer using **a** Large Language Model"* (dan hilangkan klaim kebaruan dari judul bila ada).

### Abstrak

| Yang diubah | Butir |
|---|---|
| Angka `median style strength < 0.001` harus menyebut korpus dan target, karena angka itu hanya berlaku untuk korpus Aaker. Untuk STIF, target formal berada pada 0,014 dan target informal di atas 0,99 | R2-05 |
| Semua angka diperbarui dari hasil rerun | R2-05, R2-07 |
| Klaim kebaruan dilunakkan menjadi "to our knowledge" | R2-02 |
| Tambahkan satu kalimat hasil mekanistik baru: retrieval centroid mengalami degenerasi menjadi prompt statis, dan pada korpus dengan templat berulang hal itu menghasilkan penyalinan eksemplar | R2-01, R2-03, R2-09 |

### Sec. 2 Related Work

| Yang ditambahkan | Butir |
|---|---|
| Sub-bab atau paragraf tentang query-centroid interpolation, Rocchio-style query modification, dan centroid-based pseudo-relevance feedback. Posisikan kebaruan pada penerapan untuk pemilihan eksemplar berbasis gaya, bukan pada mekanisme interpolasinya | R2-01 |
| Atribusi STIF-Indonesia kepada Wibowo et al. (2020), IALP. Perbaiki Sec. 2.2 yang menyatakan Irnawan et al. "membangun" dataset paralel, padahal mereka memakainya | R2-16 |
| Sitasi yang benar-benar menjustifikasi k=5, atau gantikan dengan hasil sensitivity analysis | R2-12, R3-W2 |

### Sec. 3.1 Dataset

| Yang ditambahkan | Butir |
|---|---|
| Tabel statistik dataset: jumlah baris per split per korpus, distribusi kelas lima persona, panjang teks, dan **jumlah baris setelah deduplikasi** untuk korpus Aaker (75.756 menjadi 62.052) | R2-06 |
| Verifikasi pelabelan Tabel 1. Dua baris pertama berlabel "formal" memuat penanda informal; jelaskan bahwa penulisan ulang formal pada korpus ini masih mempertahankan pronomina kolokial, atau perbaiki baris contohnya | R2-20 |
| Satu kalimat pemeriksaan kestabilan: label pada `v1 - With Human Validation` identik dengan `v0`, sehingga pilihan berkas tidak mengubah hasil | K4 di spesifikasi rerun |

### Sec. 3.2 Data Preprocessing dan partisi data (P0)

Ini bagian yang paling banyak berubah. Tiga kalimat berikut harus diganti, bukan hanya dilunakkan.

**Kalimat yang harus dihapus atau diganti:**

> "This test set is not leaked to retrieval or classifier train set."

> "However, to maintain integrity, parallel sentences were locked via a pair_id before splitting. If
> a formal sentence was assigned to the Test Set, its informal counterpart was explicitly restricted
> from entering the Retrieval Pool or Classifier Train Set."

> "Because the classifier never encountered the retrieved few-shot examples nor the test sentences
> during its training phase, any evaluated style strength accurately reflects the LLM's true
> generalization capabilities."

Alasannya terdokumentasi di `KLAIM_VS_IMPLEMENTASI_PREPROCESSING.md`: pada split yang dipakai
eksperimen, korpus Aaker memiliki 629 teks test identik dengan pool, 1.715 teks train identik dengan
pool, dan 24 dari 24 akun muncul di train sekaligus test; penguncian pasangan STIF tidak pernah
ditulis di kode (nol kemunculan `pair_id`); dan dari lima eksemplar centroid yang benar-benar diambil,
empat di antaranya ada di classifier train set.

**Yang ditulis sebagai gantinya**, memakai angka hasil split baru:

1. Protokol split dinyatakan lengkap: tiga tahap `train_test_split`, rasio 50/10/30/10, stratifikasi,
   `random_state=42`, dan fakta bahwa split dapat direproduksi persis dari berkas sumber.
2. Untuk STIF: penguncian pasangan dijelaskan sebagai pelaksanaan pada split baru, dengan menyebut
   bahwa setiap pasangan berada utuh dalam satu split dan kolom `pair_id` disertakan pada berkas split.
3. Untuk Aaker: deduplikasi teks sebelum split (13.704 baris dibuang, 18,1%), pengelompokan per
   percakapan sehingga setiap thread utuh dalam satu split, dan hasilnya: nol teks identik dan nol
   percakapan bersama antar split. Sebutkan juga bahwa pengelompokan per akun tidak dapat dilakukan
   karena seluruh korpus berasal dari 24 akun brand, sehingga menahan akun akan menghapus gaya brand
   tertentu dari indeks retrieval.
4. Klaim independensi diganti dengan pengukuran, bukan pernyataan. Contoh kalimat:
   *"After deduplication and thread-level grouping, no test text occurs in the retrieval index or in
   the classifier training set, and no conversation identifier is shared across splits."*
5. Notasi split diperbaiki: 50% dan 10% dinyatakan sebagai bagian dari total korpus, bukan "internal
   50:10 di dalam set 60%" | R2-13.
6. Ukuran indeks retrieval efektif per target ditambahkan, karena indeks difilter per kelas target.
7. Untuk korpus Aaker, jumlah kalimat uji yang benar-benar dievaluasi dinyatakan (500 per target),
   bukan ukuran test set (6.205 setelah dedup) | R2-06.
8. Diungkapkan bahwa laporan performa classifier gaya diukur pada `test_set.csv` yang sama dengan
   test set eksperimen.

Butir reviewer yang ditutup: R1-01 (grouped data splits), R2-06, R2-13, dan dasar kredibilitas untuk
R2-07 serta R2-09.

### Sec. 3.3 Retrieval (P0)

| Yang diubah | Butir |
|---|---|
| Nyatakan eksplisit bahwa metode centroid bersifat query-independent, sehingga set eksemplar identik untuk setiap kalimat sumber, dan bahwa sebagai akibatnya metode ini setara dengan prompt statis. Tambahkan bahwa hybrid hanya bergantung pada query melalui suku `q`, sehingga mengalami degenerasi ketika alpha menuju 0 | R2-03 |
| Hilangkan klaim bahwa centroid "will contain the most stylistic information" tanpa justifikasi, atau gantikan dengan argumen yang benar | R2-09 |
| Perbaiki kalimat "After vector h is generated for each document" menjadi "per query" | R2-03 |
| Perbaiki terminologi BM25+: bukan metode embedding, melainkan fungsi skor atas statistik term | R2-14 |
| Tambahkan ukuran indeks per target dan jelaskan konsekuensinya: seluruh eksemplar selalu bergaya target | R2-06 |

### Sec. 3.4 Generation Setup

| Yang ditambahkan | Butir |
|---|---|
| Hardware dan komputasi: tipe GPU, VRAM, framework inferensi, jenis kuantisasi, versi pustaka | R2-15 |
| Skema seed generasi dan alasan mengapa generasi dapat direproduksi, atau pernyataan jujur bila tidak | R2-07 |
| Prosedur pemilihan alpha: sapuan pada alpha-dev, kriteria pemilihan yang ditetapkan lebih dulu, dan kurva sapuannya | R1-01 |
| Jumlah ulangan, himpunan sampel uji per target, dan fakta bahwa indeks sampel sama di seluruh metode | R2-07 |

### Sec. 3.5 Evaluation Protocol

| Yang ditambahkan | Butir |
|---|---|
| Encoder content preservation independen dari encoder retrieval, beserta alasan pemilihannya. Sertakan hasil encoder lama sebagai pembanding agar besarnya perbedaan dapat dilihat | R2-08 |
| Kalibrasi classifier: metode, suhu hasil kalibrasi, dan probabilitas terkalibrasi berdampingan dengan probabilitas mentah. Laporkan pula akurasi transfer biner | R2-10, R3-W3 |
| Statistik fluency: median dan trimmed mean, proporsi output degenerate per metode, dan kriteria penyaringan | R2-21, R3-W5 |
| Uji signifikansi berpasangan dan interval keyakinan bootstrap antar metode | R2-07 |
| Definisi metrik replikasi template: proporsi n-gram (n=8) output yang muncul pada eksemplar yang diambil untuk sampel tersebut | R2-03, R2-09 |
| Evaluasi manusia bila dijalankan: jumlah sampel, jumlah penilai, rubrik, dan kesepakatan antar penilai. Bila tidak dijalankan, nyatakan ketiadaannya sebagai limitasi eksplisit | R2-11 |

### Sec. 4 Results (seluruh tabel diganti)

| Yang dikerjakan | Butir |
|---|---|
| Seluruh tabel dihitung ulang dari hasil rerun | R1-01 |
| Kolom mean fluency diganti median atau trimmed mean, dan jumlah output degenerate dilaporkan berdampingan | R2-21, R3-W5 |
| Style strength dilaporkan bersama akurasi biner dan probabilitas terkalibrasi | R2-10 |
| Interval keyakinan dan nilai p ditambahkan pada perbandingan antar metode | R2-07 |
| Tabel baru: statistik dataset | R2-06 |
| Tabel baru: size indeks per target | R2-06 |
| Tabel baru: hasil sensitivity `k` bila dijalankan | R2-12, R3-W2 |
| Gambar baru: kurva trade-off gaya dan konten pada alpha-dev, dengan alpha* ditandai | R1-01 |
| Gambar baru: laju replikasi template per metode, yang memperlihatkan pemisahan tajam antara centroid dan dense pada korpus Aaker | R2-03, R2-09 |
| Angka pada klaim "hybrid alpha=0.5 at 0.794 vs dense at 0.796" hanya boleh dipertahankan bila uji signifikansi mendukungnya. Bila tidak, ubah menjadi pernyataan bahwa keduanya setara secara statistik | R2-07 |

### Sec. 4.3 Error Analysis

| Yang dikerjakan | Butir |
|---|---|
| Tetapkan satu protokol pemilihan sampel, terapkan konsisten, dan tulis kriterianya secara eksplisit beserta jumlah sampel. Kriteria sekarang saling bertentangan antara teks dan keterangan tabel | R2-22, R3-W4 |
| Sertakan tabel contoh error untuk target formal yang sekarang tidak ada | R2-25 |
| Hubungkan temuan replikasi template dengan penjelasan mekanistik: centroida tertarik ke templat yang paling banyak terulang dalam pool, lalu LLM menyalinnya, lalu classifier gaya memberi skor tinggi | R2-09 |
| Pisahkan pembahasan per korpus, karena fenomena replikasi hanya terjadi pada korpus Aaker | R2-09 |

### Sec. 5 Discussion

Bagian ini perlu ditulis ulang sebagian, bukan hanya ditambahi. Isi yang disarankan:

1. Mekanisme degenerasi: karena centroid tidak bergantung pada query, retrieval kehilangan sifat
   per-query dan menjadi prompt statis. Ini menjelaskan mengapa kegagalan template replication
   muncul pada korpus dengan templat berulang dan tidak muncul pada korpus formality.
2. Mengapa hasilnya berbeda antar korpus: STIF memiliki pool tanpa duplikat dan tanpa templat
   berulang, sedangkan pool Aaker memiliki 18,1% duplikat sebelum deduplikasi.
3. Interpretasi ulang temuan utama: yang bertahan adalah trade-off gaya dan konten serta kegagalan
   asimetris informal ke formal. Yang perlu dibatasi adalah klaim bahwa centroid menyandikan gaya.
4. Limitasi: satu model 4-bit, satu bahasa, sampel uji Aaker 500 per target, dan bila relevan,
   keandalan label korpus.
5. Bila temuan pilot validitas diungkapkan: sebutkan bahwa pada sampel pilot n=100 yang diseimbangkan
   20 per kelas, penilai manusia sepakat satu sama lain pada 81% kasus tetapi hanya selaras dengan
   label dataset pada sekitar 37% kasus, dan jelaskan implikasinya terhadap penggunaan classifier
   dataset sebagai metrik gaya.

### Sec. 6 Conclusion

| Yang dikerjakan | Butir |
|---|---|
| Tulis ulang kalimat "this study doesn't warrant a single metric that generally choose the best method" | R2-23 |
| Perbarui temuan utama sesuai hasil rerun | R1-01 |
| Tambahkan pernyataan limitasi yang eksplisit | R2-11 |

### Daftar referensi

| Yang dikerjakan | Butir |
|---|---|
| Tambahkan Wibowo et al. (2020), IALP sebagai sumber dataset STIF | R2-16 |
| Ganti sitasi model perplexity Sahabat-AI dengan model card atau technical report resminya, bukan paper aplikasi chatbot ginjal | R2-19 |
| Tambahkan rujukan query-centroid interpolation dan pseudo-relevance feedback | R2-01 |
| Perbaiki entri referensi [8] yang memuat label ganda | R2-28 |
| Pastikan penulisan "et al." konsisten | R2-26 |

### Data Availability dan materi suplemen

| Yang dikerjakan | Butir |
|---|---|
| Rilis repositori kode: script split, pipeline generasi, script evaluasi, seluruh prompt, indeks retrieval, checkpoint classifier, dan suhu kalibrasi. Gunakan DOI | R2-17 |
| Materi suplemen: output generasi per sampel beserta seluruh skor metrik per sampel, termasuk eksemplar yang diambil | R2-18 |
| Perbarui Data Availability Statement dengan tautan repositori | R2-17 |

### Penomoran dan bahasa (dikerjakan paling akhir)

| Yang dikerjakan | Butir |
|---|---|
| Renomori seluruh gambar. Sekarang ada dua gambar berlabel "Figure 1" dan teks merujuk "Figure 3" untuk gambar yang berlabel "Figure 2" | R2-24 |
| Renomori seluruh tabel. Sekarang melompat dari Tabel 2 ke Tabel 5, dan rujukan di Sec. 4.3.1 serta 4.3.2 tidak cocok dengan isi tabelnya | R2-25 |
| Perbarui rujukan "Tables 5 and 6" di pembuka Sec. 4.1 setelah renomori | R2-28 |
| Language editing menyeluruh, termasuk daftar contoh kesalahan yang disebut reviewer | R2-26 |
| Perbaiki artefak encoding UTF-8 pada tabel, dan pastikan pemrosesan teks sendiri tidak menimbulkan artefak yang kemudian dikaitkan dengan output model | R2-27 |

---

## 3. Tabel dan gambar: keadaan akhir yang disarankan

Angka pasti menyesuaikan hasil, tetapi komposisinya sebaiknya seperti ini.

| Nomor | Isi | Status |
|---|---|---|
| Tabel 1 | Contoh data dan label per korpus (diperbaiki pelabelannya) | lama, diperbaiki |
| Tabel 2 | Statistik dataset per split per korpus | baru |
| Tabel 3 | Protokol split dan ukuran indeks efektif per target | baru |
| Tabel 4 | Hasil utama korpus formality (median dan trimmed, dengan interval keyakinan) | lama, dihitung ulang |
| Tabel 5 | Hasil utama korpus brand personality | lama, dihitung ulang |
| Tabel 6 | Hasil dengan probabilitas terkalibrasi dan akurasi biner | baru |
| Tabel 7 | Fluency: median, trimmed, proporsi degenerate | lama, diganti isinya |
| Tabel 8 | Uji signifikansi berpasangan dan interval keyakinan | baru |
| Tabel 9 | Sensitivity analysis k (bila dijalankan) | baru |
| Tabel 10 | Hasil evaluasi manusia (bila dijalankan) | baru |
| Tabel 11-12 | Contoh error target informal dan target formal (konsisten kriteria) | lama, diperbaiki |
| Gambar 1 | Ikhtisar metodologi | lama |
| Gambar 2 | Ilustrasi retrieval centroid | lama |
| Gambar 3 | Ilustrasi hybrid early fusion | lama |
| Gambar 4 | Kurva trade-off gaya dan konten pada alpha-dev | baru |
| Gambar 5 | Laju replikasi template per metode per korpus | baru |

---

## 4. Kalimat yang tidak boleh dipertahankan dalam bentuk apa pun

1. Bahwa test set tidak bocor ke retrieval pool atau classifier train set, untuk korpus Aaker, tanpa
   angka hasil split baru.
2. Bahwa pasangan paralel dikunci dengan `pair_id` pada eksperimen yang sudah berjalan.
3. Bahwa classifier tidak pernah menemui eksemplar few-shot yang diambil.
4. Bahwa centroid berisi informasi gaya paling banyak, tanpa argumen yang benar.
5. Bahwa perbedaan beberapa perseratus antar metode bermakna, tanpa uji signifikansi.
6. Adanya studi validitas manusia n=385. Berkasnya ada tetapi kolom penilaiannya kosong.
7. Bahwa test set korpus Aaker berisi 7.576 teks yang dimodifikasi. Yang benar adalah 500 per target.

---

## 5. Butir reviewer yang tidak menuntut perubahan naskah

Empat butir kekuatan dari Reviewer 3 (R3-S1 sampai R3-S4) tidak menuntut revisi. Kutip keempatnya di
response letter sebagai hal yang dipertahankan, dan sebutkan bahwa analisis error tetap
dipertahankan meski protokol pemilihan sampelnya diperbaiki.

Butir yang ditutup oleh pekerjaan yang sama di dua reviewer, sehingga cukup dijawab sekali:
R2-10 sama dengan R3-W3, R2-12 sama dengan R3-W2, R2-21 sama dengan R3-W5, R2-22 sama dengan R3-W4,
serta R2-24, R2-25, dan R2-28 sama dengan R3-W1.
