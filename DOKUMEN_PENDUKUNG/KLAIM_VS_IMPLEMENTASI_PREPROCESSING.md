# Klaim Sub-bab Data Preprocessing vs Implementasi

Perbandingan antara apa yang naskah *JCCE-10619-Revision.docx* nyatakan tentang cara data dibagi,
dan apa yang benar-benar dilakukan kode serta berkas split yang dipakai eksperimen.

Letak di naskah: sub-bab **Data Preprocessing**, tepat setelah keterangan Tabel 1, paragraf 95
sampai 103.

---

## 1. Kalimat naskah yang diperiksa

> To preserve the stylistic integrity of the original corpora, data preprocessing was kept minimal,
> strictly limited to lowercasing terms, stripping URLs/mentions, and removing extraneous
> whitespaces. However, the data partitioning strategy was heavily redesigned to enforce a
> zero-leakage evaluation protocol.
>
> A common pitfall in evaluating generative style transfer via a trained classifier is data leakage,
> where the LLM utilizes few-shot examples from the same pool of data used to train the evaluator
> classifier. This often inflates style strength evaluation. To prevent this, we discarded standard
> two-way splits often used in natural language processing tasks and implemented a three-way data
> partitioning across all datasets:
>
> Classifier Train Set (60%): This set is utilized for fine-tuning the style evaluation classifier
> (with an internal 50:10 train-validation split).
>
> Retrieval Index Pool (30%): Served as the isolated knowledge base for retrieval methods. All the
> retrieval methods source their few-shot reference examples exclusively from this subset.
>
> Test Set (10%): The untouched texts that the LLM is tasked with modifying. This test set is not
> leaked to retrieval or classifier train set. This ensures that our classifier evaluator is not
> biased.
>
> For the formality dataset (STIF), which natively consists of parallel pairs (formal-informal), we
> flattened the structure into a single corpus for unsupervised generation. However, to maintain
> integrity, parallel sentences were locked via a pair_id before splitting. If a formal sentence was
> assigned to the Test Set, its informal counterpart was explicitly restricted from entering the
> Retrieval Pool or Classifier Train Set. Hence, the data is structured as non-parallel.
>
> For the brand personality dataset, the splitting was executed via a stratified approach ensuring
> balanced representation across all five stylistic personas (Competence, Excitement, Ruggedness,
> Sincerity, Sophistication) within the 60-30-10 distribution. Because the classifier never
> encountered the retrieved few-shot examples nor the test sentences during its training phase, any
> evaluated style strength accurately reflects the LLM's true generalization capabilities.

---

## 2. Hasil pemeriksaan per klaim

### Klaim A. Preprocessing "strictly limited to lowercasing terms, stripping URLs/mentions, and removing extraneous whitespaces"

`clean_text()` pada `fewshot_formality.py` dan `main.py` hanya melakukan empat hal: menghapus URL,
menghapus sebutan akun, menghapus tagar, dan merapikan spasi. Tidak ada operasi lowercasing.
Penghapusan tagar juga tidak disebut naskah.

Pemeriksaan pada teks contoh yang benar-benar masuk ke dalam prompt: seluruh 750 teks contoh pool
STIF sudah huruf kecil, sedangkan pada korpus Aaker **5.937 dari 5.965 teks (99,5%) masih memuat
huruf kapital**. Jadi klaim lowercasing benar untuk STIF karena korpus sumbernya memang sudah huruf
kecil, dan tidak benar untuk korpus Aaker.

Penilaian: **sebagian tidak akurat**, dan perlu dinyatakan terpisah per korpus.

### Klaim B. "Retrieval Index Pool (30%) ... all the retrieval methods source their few-shot reference examples exclusively from this subset"

Benar bahwa semua metode retrieval hanya mengambil dari berkas pool. Yang tidak dinyatakan adalah
bahwa indeks difilter per kelas target. Kode menjalankan
`filtered_df = df_pool[df_pool[rag_personality_col] == personality]`, sehingga indeks untuk sebuah
target hanya memuat kalimat bergaya target itu.

| Korpus | Ukuran pool | Ukuran indeks efektif per target |
|---|---|---|
| STIF | 1.500 | 750 (formal), 750 (informal) |
| Aaker | 22.727 | competence 5.965, sophistication 5.242, excitement 4.581, sincerity 3.573, ruggedness 3.366 |

Penilaian: **tidak lengkap**. Satu kalimat tambahan diperlukan, dan ini sekaligus menjelaskan
mengapa eksemplar yang diambil selalu bergaya target.

### Klaim C. "Test Set (10%): The untouched texts that the LLM is tasked with modifying"

Untuk STIF, seluruh kandidat dipakai, yaitu 250 kalimat per target dari test set berisi 500. Klaim
ini akurat.

Untuk korpus Aaker, test set berisi 7.576 teks, tetapi eksperimen hanya memakai **500 kalimat per
target**, diambil dengan `random.sample` dan seed 42 dari kandidat sebanyak:

| Target | Kandidat (test dengan gaya berbeda) | Benar-benar dipakai |
|---|---|---|
| competence | 5.587 | 500 |
| excitement | 6.049 | 500 |
| ruggedness | 6.454 | 500 |
| sincerity | 6.385 | 500 |
| sophistication | 5.829 | 500 |

Penilaian: **tidak akurat untuk korpus Aaker**. N yang dilaporkan harus 500 per target, bukan
7.576, dan ini langsung menyangkut butir R2-06 dari Reviewer 2.

### Klaim D. "This test set is not leaked to retrieval or classifier train set"

| Pemeriksaan | STIF | Aaker |
|---|---|---|
| Teks identik test vs retrieval pool | 4 | **629** |
| Teks identik test vs classifier train | 3 | **777** |
| Teks identik classifier train vs retrieval pool | 9 | **1.715** |
| Akun yang muncul di train dan di test | tidak berlaku | **24 dari 24** |
| Baris test dari percakapan yang juga ada di train | tidak berlaku | **33,5%** |
| Duplikat teks di dalam test set | 0 | **703** |

Penilaian: **akurat pada tingkat teks untuk STIF** (praktis nol), tetapi **tidak akurat untuk korpus
Aaker**. Perlu dicatat bahwa klaim ini juga belum menangkap kebocoran pasangan paralel pada STIF
yang dijelaskan pada klaim F.

### Klaim E. "the classifier never encountered the retrieved few-shot examples nor the test sentences during its training phase"

Diuji pada eksemplar yang benar-benar diambil, bukan pada potensi: untuk metode centroid, lima
eksemplar teratas kelas competence berisi **4 teks yang juga ada di classifier train set**, dan
kelas excitement **2 dari 5**. Ditambah 1.715 teks identik antara train dan pool secara keseluruhan.

Penilaian: **tidak akurat**, dan ini penting karena kalimat tersebut merupakan dasar argumen bahwa
skor gaya mencerminkan kemampuan generalisasi. Argumennya perlu ditulis ulang.

### Klaim F. "parallel sentences were locked via a pair_id before splitting"

Berkas `stif_formal.txt` dan `stif_informal.txt` sejajar baris demi baris, jadi penguncian dapat
diperiksa langsung. Hasilnya: hanya **893 dari 2.499 pasangan (35,7%)** berada di split yang sama,
sedangkan ekspektasi bila tidak ada penguncian sama sekali adalah **36,0%**. Angka yang berhimpit ini
menunjukkan tidak ada korelasi antar pasangan.

Pemeriksaan berikutnya menunjukkan penguncian itu tidak pernah ditulis di kode:

| Pemeriksaan | Hasil |
|---|---|
| String `pair_id` di seluruh kode | tidak ada kemunculan di seluruh `*.py` pada `C:\Devs\Code\Python` |
| Langkah di `formality_cls - Copy/main.py` | hanya A (test 10%), B (retrieval pool), C (train/val) |
| Kesesuaian split tersimpan dengan tiga langkah `train_test_split` | cocok persis, jadi tidak ada koreksi pasca-proses |

Dampaknya per arah transfer: untuk target formal, 77 dari 246 kalimat uji (31,3%) memiliki pasangan
targetnya di dalam retrieval pool. Untuk target informal, 66 dari 244 (27,0%).

Penilaian: **tidak diimplementasikan di kode**. Kalimat pada naskah menggambarkan protokol yang
direncanakan, bukan yang dijalankan.

### Klaim G. "an internal 50:10 train-validation split" di dalam set classifier 60%

Rasio train terhadap validation adalah 5,00:1 pada kedua korpus, yaitu **50% dan 10% terhadap total
korpus**, bukan terhadap subset 60%. Kata "internal" menyesatkan, dan inilah yang ditanyakan
Reviewer 2 pada butir 13.

Penilaian: **notasi menyesatkan**, perlu dinyatakan sebagai persentase total.

### Klaim H. (Aaker) "splitting was executed via a stratified approach ... within the 60-30-10 distribution"

Stratifikasi memang diterapkan pada ketiga tahap `train_test_split`.

Penilaian: **akurat**. Yang perlu ditambahkan adalah detail seed, urutan tahap, serta pengakuan
bahwa deduplikasi dan pengelompokan percakapan tidak dilakukan.

---

## 3. Ringkasan

| Klaim | STIF | Aaker |
|---|---|---|
| A. Preprocessing lowercasing | akurat (korpus sudah huruf kecil) | tidak akurat (99,5% masih berkapital) |
| B. Pool 30% sebagai satu-satunya sumber | tidak lengkap (indeks difilter per target) | tidak lengkap (indeks difilter per target) |
| C. Test set 10% sebagai yang dimodifikasi | akurat | tidak akurat (500 per target, bukan 7.576) |
| D. Test set tidak bocor | akurat pada tingkat teks | tidak akurat |
| E. Classifier tidak pernah menemui eksemplar | tidak diuji | tidak akurat |
| F. Penguncian pasangan paralel | tidak akurat | tidak berlaku |
| G. Internal 50:10 | notasi menyesatkan | notasi menyesatkan |
| H. Stratifikasi lima persona | tidak berlaku | akurat |

Tiga klaim yang perlu diperbaiki segera karena menjadi dasar argumen utama naskah: D dan E untuk
korpus Aaker, serta F untuk korpus STIF. Ketiganya bersinggungan langsung dengan butir Reviewer 1
tentang grouped data splits, serta butir R2-06 dan R2-13 dari Reviewer 2.

---

## 4. Draf pengganti untuk sub-bab Data Preprocessing

Draf berikut memakai bahasa Inggris agar dapat langsung ditempel, dan memuat penanda angka yang
harus diisi setelah eksperimen ulang selesai. Jangan pakai angka lama, karena split akan berubah.

> To preserve the stylistic integrity of the original corpora, preprocessing was kept minimal and is
> reported separately for the two corpora. The formality corpus (STIF) is distributed in lowercased
> form, so processing was limited to whitespace normalization. For the brand personality corpus,
> URLs, user mentions, and hashtags were removed and whitespace was normalized, while capitalization
> was retained.
>
> The data partitioning strategy was designed to enforce a zero-leakage evaluation protocol. A
> common pitfall in evaluating generative style transfer with a trained classifier is data leakage,
> where the LLM uses few-shot examples drawn from the same data that trained the evaluator
> classifier, which inflates style strength estimates. To prevent this, we discarded the usual
> two-way split and adopted a three-way partition, applied identically to both corpora using
> stratified sampling with a fixed random state:
>
> Classifier Train Set (60%): used to fine-tune the style evaluation classifier. Training and
> validation comprise 50% and 10% of the full corpus respectively.
>
> Retrieval Index Pool (30%): the isolated knowledge base for all retrieval methods. Because each
> configuration targets one style, the index used for a given target contains only pool sentences
> carrying that target style. Index sizes per target are reported in Table {X}.
>
> Test Set (10%): texts the LLM is asked to rewrite. For the formality corpus, all test sentences
> whose style differs from the target were used, giving {N} sentences per target. For the brand
> personality corpus, per-target evaluation used a fixed random subsample of {N} sentences drawn
> with a fixed seed from {M} candidate sentences, and the same sample indices were reused across all
> retrieval methods to keep comparisons paired.
>
> For the formality corpus, which natively consists of parallel pairs, we flattened the structure
> into a single corpus and locked each pair with a `pair_id` before splitting. The counterpart of a
> sentence assigned to the test set was excluded from both the retrieval pool and the classifier
> training set.
>
> For the brand personality corpus, the split was stratified over all five personas at every stage.
> Because the corpus is drawn from repetitive customer-service communication, duplicate texts were
> removed before splitting, and multi-post threads were kept intact by grouping on conversation
> identifier. Grouping by account was not feasible: all posts originate from {number} brand
> accounts, so holding out accounts would remove entire brand styles from the retrieval index. As a
> result of deduplication and thread-level grouping, the residual textual overlap between the test
> set and the retrieval index is {number} sentences, and between the retrieval index and the
> classifier training set it is {number} sentences.
>
> The style evaluation classifier was trained exclusively on the Classifier Train Set. Overlap
> between that set and the retrieval index, and the proportion of retrieved exemplars that also
> occur in the classifier training data, are reported in Table {X} so that the independence of the
> evaluation metric can be assessed directly.

---

## 5. Berkas terkait

- `verify_split_protocol.py`: mereproduksi kedua split dan menguji klaim penguncian pasangan.
- `PROTOKOL_SPLIT_JCCE-10619.md`: protokol split lengkap beserta hasil verifikasi.
- Sheet `Klaim vs Implementasi` pada `JCCE-10619_Alur_Perbaikan_v1.xlsx`: versi tabel dari dokumen ini.
