# Laporan Perbaikan Revisi: JCCE-10619

Naskah: *The Impact of Hybrid Semantic and Stylistic Embedding Retrieval Strategies on Indonesian
Text Style Transfer using Large Language Model* (judul revisi: *Retrieval Strategies for Indonesian
Text Style Transfer using a Large Language Model*)

Putaran: revisi pertama. Tanggal penyusunan laporan: 2026-09-28.

Bundel hasil: `C:\Devs\Code\Python\JCCE-First Revision-From Remote`
Berkas terkait di folder ini: `SURAT_BALASAN_REVIEWER.md`, `TABEL_STATUS_BUTIR.md`,
`VERIFIKASI_ANGKA.md`, `verifikasi_angka.py`, `build_dokumen.py`, `jawaban_en.py`.

---

## 1. Ringkasan eksekusi

Seluruh sebelas langkah protokol rerun dijalankan dalam tiga hari di satu mesin ber-GPU RTX 4070 Ti
12 GB. Total 19.500 keluaran dibangkitkan: 38 konfigurasi STIF (9.500 sampel, 250 per konfigurasi)
dan 20 konfigurasi korpus brand personality (10.000 sampel, 500 per konfigurasi).

| Tahap | Hasil | Waktu nyata |
|---|---|---|
| Split ulang dan gerbang kebocoran | kedua korpus LOLOS; split lama GAGAL | 2026-09-25 |
| Latih ulang dan kalibrasi classifier | kedua korpus | 14 menit |
| Sapuan alpha pada development set | kedua korpus | 2026-09-25 sampai 09-26 |
| Run utama test set, seed 42 | 19.500 sampel | 16 jam 11 menit |
| Evaluasi lengkap 27 kolom | kedua korpus | 94 menit |
| Statistik, uji signifikansi, kepekaan k | 19 tabel | 2026-09-27 sampai 09-28 |

Dua hal **tidak** dijalankan dan alasannya dinyatakan di naskah: ulangan generasi untuk varians
(dipotong menjadi satu seed atas keputusan sadar) dan penilaian manusia (dinyatakan sebagai
limitasi). Keduanya dijelaskan pada bagian 4.

---

## 2. Verifikasi angka

Sebelum angka apa pun dipakai, seluruh 130 angka pada laporan agen diperiksa langsung terhadap
berkas per sampel `evaluated_v2_*_seed42_results.csv`, bukan terhadap tabel ringkasan. Skrip dan
hasilnya ada di `verifikasi_angka.py` dan `VERIFIKASI_ANGKA.md`.

| Hasil | Jumlah |
|---|---|
| Periksa dijalankan | 130 |
| Cocok dengan data per sampel | 128 |
| Selisih karena perbedaan konvensi rata-rata | 2 |

Empat hal yang ditemukan dan cara memperlakukannya:

1. **Porsi keluaran formal yang diprediksi informal adalah 82,8%, bukan 88%.** Angka 88% pada
   laporan agen terlalu tinggi. Untuk naskah dipakai 82,8% (3.934 dari 4.750 baris).
2. **Tabel replikasi dan kolom per sampel memakai dua konvensi rata-rata yang berbeda.** Tabel
   merata-ratakan tanpa baris yang keluarannya lebih pendek dari 8 kata, sedangkan kolom per sampel
   memberi nilai 0 pada baris itu. Akibatnya nilai tingkat target pada laporan (0,0037 dan 0,0079 untuk
   STIF) berasal dari tabel, sedangkan nilai per konfigurasi pada laporan (0,3386 untuk competence
   alpha 0,1) berasal dari kolom. Selisihnya sampai 0,015. Untuk naskah dipakai **tabel replikasi
   sebagai sumber tunggal**, dengan definisi dan jumlah baris yang dikeluarkan dinyatakan pada
   keterangan tabel.
3. **Angka panjang keluaran 58,69 dan 31,61 berasal dari sapuan alpha pada development set**, bukan
   dari test set. Pada test set nilainya 54,09 dan 28,52. Arah temuan tidak berubah, yaitu menurun
   monoton, tetapi untuk naskah dipakai angka test set agar sumbernya seragam di dalam satu bagian.
4. **Satu angka pada pesan diskusi sebelumnya, 0,562, sebenarnya milik kolom encoder lama**, bukan
   LaBSE. Nilai LaBSE untuk konfigurasi itu 0,5873. Laporan agen sendiri tidak memuat kekeliruan ini.

Kesimpulan: laporan agen dapat dipercaya, dengan tiga angka yang harus diperbaiki sumber atau
nilainya seperti di atas.

---

## 3. Temuan yang mengubah klaim naskah

Rerun ini tidak hanya memperbarui angka. Empat temuan mengubah cara hasil harus ditulis, dan
semuanya sudah tercermin pada surat balasan.

### 3.1 Klaim gaya harus dibatasi per arah

Pada target **informal**, seluruh metode retrieval berada pada 0,904 sampai 0,988 akurasi gaya,
jauh di atas aras acak 0,50. Pada target **formal**, seluruh metode retrieval berada pada
0,048 sampai 0,252, yaitu **di bawah aras acak**, dan 82,8% keluaran bertarget formal diprediksi
informal oleh classifier.

Uji berpasangan menegaskan arah yang berbalik: `zero_shot` berbeda bermakna dari seluruh metode
retrieval pada 36 dari 36 pasangan, dengan `d` = −0,732 sampai −0,528 pada target formal dan
`d` = +0,768 sampai +0,852 pada target informal.

Kalimat naskah yang menyiratkan retrieval memperbaiki gaya secara umum tidak dapat dipertahankan.
Yang berdiri adalah dua klaim yang lebih sempit: retrieval memperbaiki gaya pada arah informal, dan
retrieval memperbaiki pemertahanan isi pada kedua arah (`d` = +0,210 sampai +0,311 pada formal dan
+0,165 sampai +0,233 pada informal).

Temuan pendukung dari label korpus: 328 dari 2.499 entri berlabel formal (13,13%) memuat penanda
register informal seperti "kamu", "aku", atau "cuma". Sebagian kesulitan target formal berasal dari
ketidakhomogenan acuan itu sendiri.

### 3.2 Kurva alpha adalah kurva tukar-menukar

Pada korpus brand personality, target competence memperlihatkan pertukaran yang tajam antara gaya dan
isi. Alpha kecil menaikkan gaya dan menjatuhkan isi, dan sebaliknya:

| alpha | akurasi gaya (competence) | isi LaBSE (competence) |
|---|---|---|
| 0,1 | 0,864 | 0,421 |
| 0,3 | 0,842 | 0,497 |
| 0,5 | 0,514 | 0,666 |
| 0,7 | 0,244 | 0,714 |
| 0,9 | 0,200 | 0,719 |

Tiga konfigurasi teratas tidak dapat dibedakan: hybrid alpha 0,1 lawan alpha 0,3 memberi
`d` = +0,022 dengan selang [−0,004; +0,050]. Karena itu naskah tidak boleh menyebut satu metode
terbaik pada target ini.

### 3.3 Alpha yang dipilih adalah keputusan kriteria, bukan alpha optimal

| Korpus | Target | Alpha | Jarak kriteria ke peringkat kedua | Cara menyebut |
|---|---|---|---|---|
| STIF | informal | 0,7 | 0,00093 | dipilih, tidak disebut optimal |
| STIF | formal | tidak ditetapkan | akurasi 0,108–0,136 = aras derau | hasil nol |
| Aaker | competence | 0,3 | 0,06551 | dapat disebut terbedakan |
| Aaker | excitement | 0,5 | 0,01290 | dipilih, tidak disebut optimal |

Pada test set, alpha 0,3 dan 0,7 untuk target informal STIF memang tidak terbedakan pada kolom
kriteria (`d` = −0,008, selang [−0,023; +0,007]), sedangkan pada akurasi gaya alpha 0,7 justru lebih
rendah (`d` = +0,048). Jadi keduanya tidak boleh diklaim lebih baik satu sama lain.

### 3.4 Fluency: satu model untuk kedua korpus, dan rerata tidak terpakai

Versi pertama menghitung fluency korpus STIF dengan `llama3-8b-cpt-sahabatai-v1-instruct` sedangkan
korpus Aaker dengan `gemma2-9b-cpt-sahabatai-v1-instruct`, sehingga kedua kolom tidak sebanding.
Revisi memakai `gemma2-9b` untuk keduanya. Akibatnya seluruh nilai fluency STIF berubah, dan
proporsi keluaran degenerate korpus STIF tidak dapat dibandingkan dengan angka 0,61% pada versi lama.

| Besaran | STIF formal | STIF informal |
|---|---|---|
| Median PPL | 191,45 | 226,18 |
| Trimmed 10% PPL | 287,38 | 342,27 |
| Rerata PPL | 1.436,45 | 1.081,08 |
| Rasio rerata terhadap median | 7,5 | 4,8 |
| Proporsi degenerate (PPL > 1000) | 12,80% | 14,74% |

Sebaran degenerasi tidak merata antar metode pada target formal: bm25 17,00%, dense 16,40%, hybrid
13,28%, random 12,80%, centroid 7,60%, `zero_shot` 2,80%. Pada korpus Aaker proporsinya 5,86%
(5,10% competence, 6,62% excitement), dekat dengan angka lama 5,51% karena model fluency-nya memang
tidak berubah.

Justru inilah dasar empiris untuk mengganti kolom rerata pada Tabel 7 dengan median dan trimmed mean:
lewat pemeriksaan langsung, kolom rerata ditarik oleh ekor sampai 7,5 kali median.

### 3.5 `zero_shot` menyimpang, dan tidak boleh dipakai menyimpulkan keunggulan

`zero_shot` menghasilkan akurasi gaya tertinggi pada target formal, 0,780, dan median PPL terendah,
39,82, tetapi pemertahanan isinya paling buruk (0,517 pada encoder lama dan 0,559 pada LaBSE) dan
akurasi gayanya terendah pada target informal, 0,136. Polanya konsisten dengan model yang secara
diam-diam menulis dalam register formal apa pun arah yang diminta. Karena itu `zero_shot` dilaporkan
sebagai baseline kendali yang berguna untuk menafsirkan target formal, bukan sebagai metode unggulan.

---

## 4. Batasan yang wajib dinyatakan pada naskah

1. **Satu seed.** Ulangan generasi tidak dijalankan, sehingga varians antar-jalan tidak diukur.
   Ketidakpastian dilaporkan sebagai selang bootstrap berpasangan atas butir uji (10.000 resample),
   dan hal ini dinyatakan sebagai limitasi, bukan disamarkan.
2. **Penilaian manusia tidak dijalankan.** Hanya sampelnya yang diekspor, yaitu 400 baris STIF dan
   200 baris Aaker dari 25 indeks sampel yang sama lintas empat metode. Rubrik penilaiannya
   disertakan. Tidak ada angka kesepakatan antar penilai, dan itu dinyatakan.
3. **VRAM 12 GB di bawah anjuran 16 GB.** Tidak pernah terjadi kehabisan memori, tetapi
   penyimpangan ini dilaporkan.
4. **Bobot kelas classifier Aaker dihitung dari frekuensi korpus penuh, bukan dari train split v2.**
   Dibiarkan agar satu-satunya yang berubah dibanding run lama adalah splitnya.
5. **Definisi `eos_reached` berbeda antar berkas.** Pada berkas generasi kolom itu selalu `False`
   untuk Gemma 3, sedangkan pada berkas evaluasi diisi heuristik tanda baca. Interpretasi pemotongan
   harus memakai `output_tokens` terhadap `max_new_tokens`, bukan kolom itu.
6. **Konvensi metrik replikasi.** Nilai pada tabel merata-ratakan tanpa keluaran yang lebih pendek
   dari 8 kata. Jumlah baris yang dikeluarkan harus dicantumkan pada keterangan tabel.

---

## 5. Status 38 butir reviewer

Rincian per butir, termasuk kutipan verbatim komentar reviewer dan jawabannya, ada di
`SURAT_BALASAN_REVIEWER.md`. Rekapitulasi pekerjaan ada di `TABEL_STATUS_BUTIR.md`.

| Status | Jumlah | Arti |
|---|---|---|
| Selesai, bukti ada | 17 | rerun, kalibrasi, split, uji signifikansi, artefak, dan angka baru sudah tersedia |
| Menunggu penyuntingan naskah | 17 | bukti dan keputusan sudah ada, kalimat pada naskah belum diubah |
| Tanpa tindakan | 4 | pujian Reviewer 3, dicatat dan dipertahankan |

Butir yang menunggu penyuntingan naskah adalah pekerjaan yang tinggal di sisi berkas naskah:
R2-01 (related work query-centroid), R2-02 (pelunakan klaim), R2-04 (judul), R2-05 (kualifikasi
abstract), R2-13 (notasi split), R2-14 (terminologi BM25+), R2-15 (bagian setup), R2-16 (atribusi
dataset), R2-19 (sumber model Sahabat-AI), R2-20 (keterangan Tabel 1), R2-23 (kalimat kesimpulan),
R2-24, R2-25, R2-26, R2-27, R2-28, dan R3-W1 (penomoran serta penyuntingan bahasa).

---

## 6. Artefak

Seluruh angka pada laporan ini dan pada surat balasan dapat dilacak ke berkas berikut.

| Berkas | Isi |
|---|---|
| `TABEL_ringkasan_formality.csv`, `TABEL_ringkasan_aaker.csv` | 66 kolom statistik per konfigurasi, termasuk proporsi degenerate |
| `TABEL_uji_<korpus>_<metrik>.csv` | 12 berkas, 342 pasangan sebanding untuk STIF dan 90 untuk Aaker |
| `TABEL_kepekaan_k_formality.csv` | 108 baris, k = 10 lawan k = 5 |
| `TABEL_ppl_formality_per_target.csv` | median, trimmed, rerata, dan simpangan baku per target |
| `TABEL_replikasi_formality.csv`, `TABEL_replikasi_aaker.csv` | laju replikasi templat per konfigurasi |
| `HASIL/evaluated_v2_*_seed42_results.csv` | 58 berkas, 19.500 baris, satu baris per sampel |
| `HASIL/keluaran_generasi/` | 116 berkas generasi berpenanda seed 42 saja |
| `fewshot_*/data/*_splits_v2/split_manifest.json` | ukuran split dan hasil gerbang kebocoran |

Skrip bantu yang ditambahkan pada revisi, dengan hash yang dicatat pada `LAPORAN_AKHIR.md` bagian
12.4: `k_sensitivity.py`, `ppl_per_target.py`, `export_human_eval.py`.

---

## 7. Sisa pekerjaan

1. **Menyunting naskah** untuk 17 butir pada bagian 5, termasuk penomoran gambar dan tabel yang harus
   dikerjakan dalam satu pass bersama pergeseran nomor rujukan akibat R2-16 dan R2-19.
2. **Memastikan surat balasan dan naskah saling cocok.** Surat balasan menyatakan perubahan yang
   harus benar-benar ada pada naskah; jangan mengirimkannya sebelum naskah selesai disunting.
3. **Menyiapkan paket reproduksi** untuk repositori ber-DOI: kode, konfigurasi, prompt, manifes split,
   skrip evaluasi, keluaran per sampel, dan 19 tabel.
4. **Memutuskan apakah paket data 294 MB dan 20 MB disertakan** sebagai materi suplemen atau hanya
   lewat repositori.
