# Status 38 butir reviewer

Status dan jawaban lengkap per butir ada di `SURAT_BALASAN_REVIEWER.md`. Tabel ini untuk
memantau pekerjaan yang tinggal di sisi naskah.

| ID | Reviewer | Bagian | Status | Yang diminta |
|---|---|---|---|---|
| R1-01 | Reviewer 1 | Seluruh naskah | Selesai, bukti ada | Menuntut eksperimen ulang dengan evaluasi tervalidasi, pemilihan alpha berbasis development set, baseline yang lebih kuat, split data berbasis kelompo |
| R2-01 | Reviewer 2 | Significance & Novelty / Sec. 2 & 3.3.2 | Menunggu penyuntingan naskah | Hybrid early fusion secara struktural menyerupai Rocchio-style query modification dan centroid-based pseudo-relevance feedback; novelty harus diposisi |
| R2-02 | Reviewer 2 | Significance & Novelty / klaim kontribusi 2 | Menunggu penyuntingan naskah | Klaim “a first style-aware hybrid retrieval approach” sulit diverifikasi; harus dilunakkan. |
| R2-03 | Reviewer 2 | Significance & Novelty / Sec. 3.3.2 & 4.3 | Selesai, bukti ada | Metode centroid bersifat query-independent (satu centang c per korpus target), sehingga set eksemplar yang diambil identik untuk semua kalimat sumber; |
| R2-04 | Reviewer 2 | Judul | Menunggu penyuntingan naskah | Dua kesalahan gramatikal pada judul: “on” seharusnya “for”; “Large Language Model” seharusnya “a Large Language Model”. |
| R2-05 | Reviewer 2 | Abstract | Menunggu penyuntingan naskah | Klaim abstract “relative style strength < 0.001” hanya berlaku untuk brand personality (Tabel 8), tidak untuk task formality (median dense = 0.014 unt |
| R2-06 | Reviewer 2 | Design & Methods / Sec. 3.1-3.2 | Selesai, bukti ada | Tidak ada statistik dataset: ukuran kedua korpus, jumlah kalimat pada train classifier, retrieval pool, test set, dan distribusi kelas lima brand pers |
| R2-07 | Reviewer 2 | Design & Methods / Sec. 3.4 & seluruh hasil | Selesai, bukti ada | Tidak ada uji signifikansi dan pelaporan varians: semua hasil adalah point estimate dari satu kali generasi (temperature 0.7); perbedaan beberapa pers |
| R2-08 | Reviewer 2 | Design & Methods / Sec. 3.3.3 & 3.5 | Selesai, bukti ada | Encoder retrieval hanya disebut “SentenceBERT” tanpa checkpoint, sedangkan content preservation dievaluasi dengan SentenceBERT (LazarusNLP/simcse-indo |
| R2-09 | Reviewer 2 | Design & Methods / Sec. 3.3.1 vs Sec. 4.3 | Selesai, bukti ada | Premis teoretis metode centroid dibantah oleh analisis error naskah sendiri: tidak ada justifikasi mengapa rata-rata menghapus konten alih-alih gaya,  |
| R2-10 | Reviewer 2 | Design & Methods / Sec. 3.4 & Tabel 8 | Selesai, bukti ada | Output classifier style strength saturasi dan kemungkinan tidak terkalibrasi (median 0.99997-0.99999 vs 0.00002-0.00008); memperlakukan softmax mentah |
| R2-11 | Reviewer 2 | Design & Methods / Sec. 3.5 & limitasi | Selesai, bukti ada | Tidak ada human evaluation, padahal temuan utama bertumpu pada ketegangan tiga metrik otomatis. Evaluasi manusia kecil (50-100 sampel dinilai penutur  |
| R2-12 | Reviewer 2 | Design & Methods / Sec. 3.3 (k=5) | Selesai, bukti ada | Justifikasi k=5 hanya bersandar pada klaim “most few-shot prompt TST research” tanpa sitasi. Minta sitasi atau sensitivity analysis kecil terhadap k. |
| R2-13 | Reviewer 2 | Design & Methods / Sec. 3.2 | Menunggu penyuntingan naskah | “an internal 50:10 train-validation split” di dalam set classifier 60% adalah notasi yang tidak jelas. |
| R2-14 | Reviewer 2 | Design & Methods / Sec. 3.3.3 (Persamaan 6) | Menunggu penyuntingan naskah | BM25+ disebut menghasilkan “sparse embedding”, padahal BM25+ adalah fungsi skor atas statistik term, bukan metode embedding. |
| R2-15 | Reviewer 2 | Design & Methods / Sec. 3.4 | Menunggu penyuntingan naskah | Tidak ada detail hardware dan komputasi (GPU, framework inferensi, kuantisasi) yang memengaruhi reproduksibilitas. |
| R2-16 | Reviewer 2 | Sec. 3.1, Sec. 2.2, keterangan Tabel 1 | Menunggu penyuntingan naskah | Atribusi dataset formality salah: STIF-Indonesia dibuat Wibowo et al. (2020, IALP), bukan [11] (Irnawan & Adi, 2023) yang hanya memakainya. Keterangan |
| R2-17 | Reviewer 2 | Data Availability Statement | Selesai, bukti ada | Data Availability hanya mencakup dataset sumber. Tidak ada kode, prompt di luar Textbox 1, indeks retrieval, checkpoint classifier, maupun output gene |
| R2-18 | Reviewer 2 | Sec. 4.3 / materi suplemen | Selesai, bukti ada | Analisis error memuat klaim per-sampel yang tidak dapat diverifikasi dari naskah (mis. output hybrid “scores 141 in individual perplexity”; lonjakan P |
| R2-19 | Reviewer 2 | Daftar referensi [27], [28] | Menunggu penyuntingan naskah | [27] dan [28] dikutip sebagai sumber model perplexity Sahabat-AI, padahal keduanya paper aplikasi chatbot penyakit ginjal yang memakai model tersebut. |
| R2-20 | Reviewer 2 | Tabel 1 | Menunggu penyuntingan naskah | Dua baris pertama Tabel 1 dilabeli “formal” tetapi memuat penanda register informal (mis. “kan akun kamu private”). Karena STIF-Indonesia adalah korpu |
| R2-21 | Reviewer 2 | Results / Tabel 7 | Selesai, bukti ada | Mean perplexity tidak kredibel: nilai 276.051.597; 277.913.427; 276.066.747; 2.644.748 mengindikasikan generasi degenerate, ketidakcocokan tokenizer,  |
| R2-22 | Reviewer 2 | Sec. 4.3.1 & keterangan Tabel 9 | Selesai, bukti ada | Kriteria pemilihan sampel tidak konsisten: Sec. 4.3.1 menyebut content preservation tinggi (>0.8) dan style strength rendah (<0.1), tetapi analisisnya |
| R2-23 | Reviewer 2 | Kesimpulan | Menunggu penyuntingan naskah | Kalimat kesimpulan “this study doesn’t warrant a single metric that generally choose the best method” tidak jelas. |
| R2-24 | Reviewer 2 | Gambar 1-3 & rujukan dalam teks | Menunggu penyuntingan naskah | Penomoran gambar rusak: dua gambar sama-sama berlabel “Figure 1” (overview metodologi dan ilustrasi centroid retrieval); gambar hybrid berlabel “Figur |
| R2-25 | Reviewer 2 | Penomoran tabel & Sec. 4.1, 4.3.1, 4.3.2 | Menunggu penyuntingan naskah | Penomoran tabel rusak: melompat dari Tabel 2 ke Tabel 5 (tidak ada Tabel 3 dan 4), Sec. 4.3.1 merujuk “the table 4 and 5”, serta merujuk tabel contoh  |
| R2-26 | Reviewer 2 | Seluruh naskah / Sec. 1, 3.1, 3.3.2, 3.4, 4.2.1, 4.3.1 | Menunggu penyuntingan naskah | Kualitas bahasa perlu suntingan menyeluruh: “While it beings underexplored”, “different with several study”, “Content Perservation” (salah eja di dua  |
| R2-27 | Reviewer 2 | Tabel 2, 9, 11 & Sec. 4.3 | Menunggu penyuntingan naskah | Artefak encoding karakter (“â€œ” dan emoji rusak) muncul di Tabel 2, 9, dan 11. Artefak ini juga membuat penilaian apakah artefak tanda kutip pada out |
| R2-28 | Reviewer 2 | Sec. 4.1 & daftar referensi [8] | Menunggu penyuntingan naskah | Sec. 4.1 membuka dengan merujuk “Tables 5 and 6” sebagai berisi hasil, yang harus diperbarui setelah renomori (komentar 25). Entri referensi [8] memua |
| R3-S1 | Reviewer 3 | Sec. 1 (motivasi) | Tanpa tindakan | Kekuatan: fokus masalah terdefinisi baik (bagaimana memilih eksemplar in-context untuk few-shot TST), bukan evaluasi luas kemampuan style transfer LLM |
| R3-S2 | Reviewer 3 | Sec. 3.3 (metode) | Tanpa tindakan | Kekuatan: centroid-based style representation dan Hybrid Early Fusion dirancang jelas dan menjawab langsung trade-off gaya vs konten. Catatan: kekuata |
| R3-S3 | Reviewer 3 | Kontekstualisasi (bahasa Indonesia) | Tanpa tindakan | Kekuatan: studi few-shot TST sebelumnya mayoritas pada bahasa sumber daya tinggi; eksperimen pada Bahasa Indonesia dengan dua korpus (formality dan br |
| R3-S4 | Reviewer 3 | Sec. 4.3 (analisis error) | Tanpa tindakan | Kekuatan: analisis error kualitatif (Semantic Drift, Template Hallucination) memberi insight mengapa strategi retrieval berperilaku berbeda. Catatan:  |
| R3-W1 | Reviewer 3 | Seluruh naskah (gambar/tabel) | Menunggu penyuntingan naskah | Nomor gambar dan cross-reference tidak konsisten sehingga berpotensi membingungkan pembaca; minta seluruh penomoran dan rujukan dicek agar berurutan d |
| R3-W2 | Reviewer 3 | Sec. 3.3 (k=5) | Selesai, bukti ada | Eksperimen konsisten memakai lima eksemplar few-shot, tetapi justifikasinya ringkas; minta referensi pendukung lebih kuat atau pembahasan apakah jumla |
| R3-W3 | Reviewer 3 | Sec. 3.4 (Style Strength) | Selesai, bukti ada | Style Strength diukur dari probabilitas kelas target; meski akurasi dan Macro-F1 classifier dilaporkan kuat, diperlukan klarifikasi kalibrasi karena b |
| R3-W4 | Reviewer 3 | Sec. 4.3 (analisis error) | Selesai, bukti ada | Analisis error kualitatif informatif tetapi berbasis purposive sampling; jumlah sampel dan prosedur pemilihan hanya dijelaskan singkat, sehingga repro |
| R3-W5 | Reviewer 3 | Tabel hasil utama (PPL) | Selesai, bukti ada | Sebagian nilai PPL pada eksperimen brand personality besar dan berbeda beberapa orde magnitudo; penjelasan singkat di dekat tabel hasil utama akan mem |

## Rekapitulasi

- Total butir pada workbook: 38
- Butir yang jawabannya sudah ditulis: 38
- Selesai dengan bukti pada bundel hasil: 17
- Menunggu penyuntingan naskah: 17
- Tanpa tindakan, hanya pujian: 4

Butir berstatus menunggu penyuntingan naskah berarti bukti dan keputusannya sudah ada,
tetapi kalimat pada berkas naskah belum diubah. Daftar itu yang harus ditutup sebelum
naskah dikirim ulang.
