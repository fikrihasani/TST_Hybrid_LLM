# Spesifikasi Rerun JCCE-10619

Dokumen ini adalah spesifikasi kerja untuk dijalankan di remote PC: apa yang harus diubah di kode,
urutan eksekusinya, dan cara memastikan hasilnya sah. Semua angka di sini berasal dari pengukuran
langsung atas data dan artefak eksperimen yang ada, dan sudah diverifikasi ulang.

Pasangan dokumen: `PERUBAHAN_NASKAH.md` untuk apa yang ditulis ke manuskrip setelah rerun selesai.

---

## 0. Keputusan yang harus diambil sebelum menulis kode

Lima hal ini menentukan bentuk kode. Kalau salah pilih, eksperimen harus diulang.

| # | Keputusan | Pilihan | Rekomendasi |
|---|---|---|---|
| K1 | Skema split untuk pemilihan alpha | (a) pakai `val_set` yang ada, atau (b) buat split dev tersendiri dari porsi classifier | (b) 45% train / 10% classifier-val / 5% alpha-dev / 30% pool / 10% test. Opsi (a) memakai himpunan yang sama untuk early stopping classifier dan pemilihan alpha, sehingga perlu diungkapkan dan tetap bisa dipersoalkan |
| K2 | Ukuran sampel uji korpus Aaker | 500 per target (seperti sekarang) atau lebih besar | 500 dipertahankan agar beban komputasi terkendali, tetapi dinyatakan eksplisit. Setiap kelipatan 2 menambah waktu sekitar 4,6 jam per ulangan |
| K3 | Jumlah ulangan generasi | 1, 3, atau 5 | 3 ulangan untuk konfigurasi utama saja, bukan untuk seluruh sapuan alpha. Lihat anggaran di bagian 3 |
| K4 | Sumber label korpus Aaker | `v0` atau `v1 - With Human Validation` | `v0`. Pemeriksaan menunjukkan label pada `v1` identik dengan `v0` untuk seluruh baris yang dapat dicocokkan, jadi tidak ada perubahan hasil. Cukup tambahkan satu kalimat sebagai pemeriksaan kestabilan |
| K5 | Evaluasi manusia pada output generasi | jalankan atau nyatakan sebagai limitasi | jalankan versi kecil (sekitar 100 sampel, 3 penilai). Rubrik sudah tersedia |

Catatan untuk K4 dan untuk butir R2-11: berkas rating studi validitas **n=385** di repo
(`... n385 - MASTER.csv` dan tiga berkas per penilai) seluruhnya **kosong**, kolom penilaiannya
belum terisi. Yang benar-benar terisi hanya pilot **n=100**. Jadi jangan menyatakan adanya validasi
manusia n=385 tanpa data pendukungnya. Pilot n=100 sendiri berisi temuan yang perlu keputusan
terpisah, lihat bagian 5.

---

## 1. Perubahan kode

### 1.1 Script baru: `make_splits_formality.py`

Menggantikan blok split di `formality_cls - Copy/main.py` baris 46 sampai 60. Inti perubahannya:
split dilakukan pada **pasangan**, bukan pada baris, sehingga penguncian berlaku dengan sendirinya.

```python
import pandas as pd
from sklearn.model_selection import train_test_split

FORMAL   = "data/stif_formal.txt"
INFORMAL = "data/stif_informal.txt"
OUT      = "data/formality_splits"
SEED     = 42

fa  = [x.strip() for x in open(FORMAL,   encoding="utf-8") if x.strip()]
inf = [x.strip() for x in open(INFORMAL, encoding="utf-8") if x.strip()]
assert len(fa) == len(inf), "berkas paralel tidak sejajar"

# pair_id = nomor baris pada berkas paralel
rows = []
for pid, (f, i) in enumerate(zip(fa, inf)):
    rows.append({"pair_id": pid, "text": f, "formality": "formal"})
    rows.append({"pair_id": pid, "text": i, "formality": "informal"})
df = pd.DataFrame(rows)

pairs      = df["pair_id"].unique()
rest, test = train_test_split(pairs, test_size=0.10, random_state=SEED)
clf,  pool = train_test_split(rest,  test_size=(1/3), random_state=SEED)
train, val = train_test_split(clf,   test_size=(1/6), random_state=SEED)

for name, ids in {"train_set": train, "val_set": val,
                  "retrieval_pool": pool, "test_set": test}.items():
    sub = df[df.pair_id.isin(ids)].copy()
    sub["label_id"] = sub["formality"].map({"formal": 0, "informal": 1})
    sub.to_csv(f"{OUT}/{name}.csv", index=False)
```

Hasil ukurannya sudah saya uji: train 2.498, val 500, pool 1.500, test 500, total 4.998, yaitu
50/10/30/10 persis sama seperti split lama. Karena kedua anggota pasangan selalu berada di split
yang sama, keseimbangan formal dan informal terjaga dengan sendirinya, sehingga `stratify` tidak
diperlukan. Kolom `pair_id` ikut diekspor agar klaim penguncian dapat diverifikasi pembaca.

Catatan: `fewshot_formality.py` membaca kolom berdasarkan nama, jadi penambahan kolom ini tidak
merusak pipeline.

### 1.2 Script baru: `make_splits_brand.py`

Menggantikan blok split di `brand_personality_classification - Copy/main.py` baris 49 sampai 57.
Inti perubahannya: deduplikasi teks sebelum split, lalu pengelompokan per percakapan.

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

SRC   = "data/Combined Aaker Brand Personality - Cleaned v0.csv"
OUT   = "data/brand_splits"
SEED  = 42
TEXT, STYLE, GROUP = "cleaned_text", "personality", "conversation_id_str"

df = pd.read_csv(SRC).dropna(subset=[TEXT, STYLE]).copy()
df[TEXT] = df[TEXT].astype(str)

# 1. deduplikasi teks ternormalisasi
df["_norm"] = (df[TEXT].str.lower().str.replace(r"\s+", " ", regex=True).str.strip())
before = len(df)
df = df.drop_duplicates(subset="_norm").reset_index(drop=True)
print(f"dedup: {before} -> {len(df)} (dibuang {before - len(df)})")

# 2. split berstrata sekaligus bergrup: seluruh percakapan masuk ke satu split
y, g = df[STYLE].values, df[GROUP].values
sgkf = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=SEED)
fold = np.empty(len(df), dtype=int)
for k, (_, vidx) in enumerate(sgkf.split(df, y, groups=g)):
    fold[vidx] = k
df["_fold"] = fold

# 3. pemetaan fold -> split (test 10%, pool 30%, val 10% classifier, train 50%)
for name, folds in {"test_set": [0], "retrieval_pool": [1, 2, 3],
                    "val_set": [4], "train_set": [5, 6, 7, 8, 9]}.items():
    df[df._fold.isin(folds)].drop(columns=["_norm", "_fold"]) \
      .to_csv(f"{OUT}/{name}.csv", index=False)
```

Hasil yang sudah saya uji pada data sebenarnya:

| Split | n | Persentase |
|---|---|---|
| train | 31.025 | 50,0% |
| val classifier | 6.205 | 10,0% |
| retrieval pool | 18.617 | 30,0% |
| test | 6.205 | 10,0% |
| total setelah dedup | 62.052 | dari 75.756 baris awal |

Deduplikasi membuang 13.704 baris (18,1%). Setelah split baru: **nol teks identik dan nol percakapan
bersama** antar split, dibandingkan keadaan sebelumnya yang memiliki 629 teks test identik dengan
pool, 1.715 teks train identik dengan pool, dan 33,5% baris test berasal dari percakapan yang juga
ada di train. Ukuran fold berimbang (6.205 sampai 6.206 baris).

Kalau memilih K1 opsi (b), tambahkan satu fold lagi sebagai alpha-dev: test `[0]`, pool `[1,2,3]`,
classifier-val `[4]`, alpha-dev `[5]`, train `[6,7,8,9]`.

Verifikasi wajib setelah script ini dijalankan:

```python
# tumpang tindih harus nol
assert len(set(train.cleaned_text.map(n)) & set(test.cleaned_text.map(n))) == 0
assert len(set(pool.conversation_id_str) & set(test.conversation_id_str)) == 0
```

### 1.3 `formality_cls - Copy/main.py` dan `brand_personality_classification - Copy/main.py`

Setelah split dipindahkan ke script tersendiri, kedua script ini hanya melatih classifier. Yang perlu
diubah:

1. Hapus blok split, ganti dengan pembacaan berkas split.
2. Samakan seed. `brand_personality_classification` sudah memakai `set_seed(42)`;
   `formality_cls` tidak menetapkan seed sama sekali. Tambahkan `set_seed(42)` di keduanya.
3. Simpan `temperature` hasil kalibrasi (lihat 1.5) ke dalam folder `style_classifier/` supaya
   pipeline evaluasi dapat memakainya.
4. Tambahkan penyimpanan probabilitas kelas penuh pada `val_set`, bukan hanya prediksi, karena
   dipakai untuk temperature scaling.

Classifier **harus dilatih ulang** karena train, val, dan test berubah, dan untuk korpus Aaker
jumlah barisnya turun dari 37.877 menjadi 31.025.

### 1.4 `fewshot_formality.py` dan `TST_fewshot_aaker - Copy/main.py`

Ini perubahan terpenting pada sisi generasi. Ada lima hal.

**(a) Catat eksemplar dan prompt per sampel.** Sekarang `style_examples` dibangun lalu dibuang,
sehingga metrik replikasi tidak dapat dihitung dan klaim analisis error tidak dapat diperiksa
reviewer. Ubah `generate_paraphrases_sequential` agar mengembalikan tiga hal, bukan satu:

```python
def generate_paraphrases_sequential(...):
    paraphrased, exemplars, fallbacks = [], [], []
    for i, msg_idx in enumerate(sample_indices):
        style_examples = get_style_examples(...)   # kembalikan (examples, used_fallback)
        ...
        paraphrased.append(paraphrased_text)
        exemplars.append(style_examples)
        fallbacks.append(used_fallback)
    return paraphrased, exemplars, fallbacks
```

lalu simpan ke hasil:

```python
results_df["retrieved_exemplars"] = [json.dumps(e, ensure_ascii=False) for e in exemplars]
results_df["retrieval_fallback"]  = fallbacks
results_df["prompt_chars"]        = [len(p) for p in prompts]
results_df["output_chars"]        = [len(t) for t in paraphrased]
results_df["eos_reached"]         = eos_flags
results_df["run_seed"]            = run_seed
results_df["sample_seed"]         = sample_seeds
```

`retrieval_fallback` perlu ada karena `get_style_examples` sekarang menelan exception dan diam-diam
jatuh ke `retrieve_random`. Kalau itu terjadi pada sebagian sampel, hasilnya tercampur dan sekarang
tidak dapat dideteksi. Setelah rerun, jumlah fallback harus dilaporkan, dan idealnya nol.

**(b) Kunci seed generasi.** Sekarang seed 42 hanya dipakai untuk sampling partisi, sedangkan
`generate` berjalan tanpa seed. Tambahkan seed per sampel yang deterministik:

```python
sample_seed = run_seed * 100000 + i
generator = torch.Generator(device=hf_model.device).manual_seed(sample_seed)
outputs = hf_model.generate(**inputs, ..., do_sample=True, generator=generator)
```

dan tambahkan `"run_seeds": [42, 43, 44]` pada config. Cara ini membuat ulangan dapat direproduksi
dan menjadikan varians antar ulangan dapat dilaporkan, yang langsung menutup butir R2-07.

**(c) Tambahkan baseline.** `retrieve_random` sudah ada di `retrieval_utils.py` tetapi tidak pernah
dijalankan. Dua baseline yang diminta Reviewer 1:

```python
"retrieval_methods": ["dense", "centroid", "bm25", "hybrid_early", "random", "zero_shot"],
```

`zero_shot` berarti tanpa eksemplar sama sekali. Perlu dua penyesuaian kecil: `get_style_examples`
mengembalikan daftar kosong untuk `zero_shot`, dan template prompt perlu cabang yang menghilangkan
blok `### CONTOH REFERENSI` bila daftar eksemplar kosong.

Catatan: `retrieve_random` memakai `random.sample` tanpa seed. Tambahkan seed eksplisit agar
baseline ini pun dapat direproduksi.

**(d) Script baru: `select_alpha_dev.py`.** Menjalankan sapuan alpha pada himpunan alpha-dev, bukan
pada test set. Kriteria pemilihan harus ditetapkan lebih dulu dan ditulis di naskah. Rekomendasi:
alpha* = argmax dari rata-rata harmonik antara akurasi gaya biner dan content preservation pada
alpha-dev, lalu laporkan kurva lengkapnya sebagai bahan pembaca. Simpan hasil sapuan sebagai tabel.

**(e) Catat informasi komputasi.** Tipe GPU, VRAM, versi `transformers` dan `torch`, jenis
kuantisasi, waktu per konfigurasi. Ini untuk butir R2-15 dan diperlukan agar hasil dapat
direproduksi.

### 1.5 `eval.py`

**(a) Encoder content preservation yang independen.** Sekarang memakai
`LazarusNLP/simcse-indobert-base`, yaitu model yang sama dengan encoder retrieval, sehingga
sirkularitasnya nyata. Hitung content preservation dengan dua encoder independen, misalnya
`sentence-transformers/LaBSE` dan `intfloat/multilingual-e5-base`, lalu simpan sebagai kolom
terpisah. Kolom lama tetap dihitung dan diberi nama yang jelas bahwa encoder-nya sama dengan
encoder retrieval, supaya pembaca dapat membandingkan dan melihat besarnya perbedaan.

**(b) Tambahkan kalibrasi.** Script baru `calibrate_classifier.py`: jalankan classifier pada
`val_set`, cari suhu `T` yang meminimalkan NLL, lalu simpan `T` ke folder `style_classifier/`.
`eval.py` memakai `T` untuk menghasilkan kolom probabilitas terkalibrasi di samping kolom
probabilitas mentah. Ini yang diminta butir R2-10 dan R3-W3.

**(c) Statistik yang benar untuk fluency.** Ganti pelaporan mean menjadi median dan trimmed mean,
laporkan proporsi output dengan PPL di atas ambang, dan simpan penanda degenerate per sampel.
Pelaporan mean saja yang membuat kolom fluency tidak terbaca.

**(d) Script baru: `bootstrap_significance.py`.** Untuk setiap pasangan metode pada target yang
sama, hitung selisih berpasangan pada sampel uji yang identik, lalu laporkan interval keyakinan
bootstrap dan uji Wilcoxon signed-rank. Semua metode memang dijalankan pada indeks uji yang sama,
jadi pengujian berpasangan sah dan lebih peka.

**(e) Metrik replikasi template.** Hitung proporsi n-gram (n=8) output yang muncul pada eksemplar
yang benar-benar diambil untuk sampel itu, memakai kolom `retrieved_exemplars` dari 1.4(a). Kolom
ini yang mengubah klaim inti paper menjadi temuan yang dapat dipertanggungjawabkan. Angka dasarnya
sudah saya ukur dari output lama: pada korpus Aaker, 76,6% output metode centroid memuat 8-gram
eksemplar dibandingkan 0,4% pada dense; pada STIF hanya 1,2% dibandingkan 0,0%.

**(f) G-score.** `eval.py` menghitung `g_score` dari median PPL, tetapi angka itu tidak pernah
dilaporkan di naskah. Karena kode akan dirilis, putuskan: laporkan sebagai metrik sekunder dengan
justifikasi, atau hapus dari kode.

---

## 2. Urutan eksekusi

Urutan ini bukan pilihan gaya, melainkan syarat agar tidak mengerjakan dua kali.

| Langkah | Isi | Keluaran | Prasyarat |
|---|---|---|---|
| 1 | Jalankan `make_splits_formality.py` dan `make_splits_brand.py`, lalu verifikasi tumpang tindih nol | 8 berkas split baru + manifest | K1 |
| 2 | Latih ulang kedua classifier, simpan probabilitas val, latih kalibrasi, simpan suhu | `style_classifier/` baru + `T` | 1 |
| 3 | Patch pipeline generasi: pencatatan eksemplar, seed, baseline, zero-shot | pipeline siap | 2 |
| 4 | Jalankan `select_alpha_dev.py` pada alpha-dev | alpha* + kurva sapuan dev | K1, 3 |
| 5 | Jalankan seluruh konfigurasi pada test set, ulangan tunggal | hasil lengkap 1 ulangan | 3, 4 |
| 6 | Jalankan ulangan kedua dan ketiga untuk konfigurasi utama saja | 3 ulangan | 5 |
| 7 | Jalankan `eval.py` versi baru, `bootstrap_significance.py`, hitung metrik replikasi | tabel hasil final | 5, 6 |
| 8 | Evaluasi manusia sekitar 100 sampel, 3 penilai | hasil penilaian | 5 |
| 9 | Susun materi suplemen: output per sampel + seluruh skor per sampel | berkas suplemen | 7 |

Langkah 8 dapat berjalan paralel dengan langkah 6 dan 7.

---

## 3. Anggaran waktu komputasi

Dasar perhitungan dari timestamp run asli: 8,5 menit per konfigurasi untuk STIF (250 sampel) dan
27,7 menit untuk korpus Aaker (500 sampel).

| Bagian | STIF | Aaker | Catatan |
|---|---|---|---|
| Sapuan alpha pada alpha-dev | 0,7 jam | 1,4 jam | 10 konfigurasi hybrid, N lebih kecil |
| Seluruh konfigurasi pada test set, 1 ulangan | 5,4 jam | 9,2 jam | 19 konfigurasi STIF, 20 konfigurasi Aaker |
| Ulangan ke-2 dan ke-3 untuk konfigurasi utama | 3,4 jam | 11,1 jam | 8 konfigurasi per korpus |
| Latih ulang classifier | 0,5 jam | 1,5 jam | estimasi, belum diukur |
| Evaluasi lengkap termasuk bootstrap | 2 jam | 3 jam | dapat dijalankan di CPU |
| **Total GPU** | **kira-kira 12 jam** | **kira-kira 26 jam** | sekitar 1,5 sampai 2 hari |

Kalau anggaran lebih ketat, yang dapat dipotong lebih dulu: ulangan ketiga (hemat 7 jam), lalu
metode random pada k=10 (STIF), lalu sensitivity k (butir R2-12 opsional, sekitar 6 jam).
Yang tidak dapat dipotong: sapuan alpha pada alpha-dev dan ulangan kedua, karena keduanya menutup
butir reviewer yang eksplisit.

---

## 4. Kriteria lulus sebelum hasil dipakai

Jangan menulis apa pun ke naskah sebelum seluruh pemeriksaan ini lolos.

**Split**

- [ ] Ukuran split persis 50/10/30/10 pada kedua korpus
- [ ] STIF: setiap split berisi jumlah formal dan informal yang sama, dan setiap pasangan utuh dalam satu split
- [ ] Aaker: nol teks identik antar split, nol percakapan bersama antar split
- [ ] Tidak ada baris hilang: STIF tetap 4.998, Aaker turun tepat 13.704 dari 75.756
- [ ] Manifest split tersimpan, memuat seed, versi pustaka, dan hash berkas sumber

**Generasi**

- [ ] Setiap berkas hasil memuat kolom `retrieved_exemplars` yang terisi seluruhnya
- [ ] Jumlah fallback ke `retrieve_random` dilaporkan, idealnya nol
- [ ] Untuk konfigurasi yang sama, himpunan eksemplar identik antar ulangan (retrieval bersifat deterministik, yang berbeda hanya generasi)
- [ ] Distribusi panjang output dan proporsi `eos_reached` wajar
- [ ] Generasi dengan seed sama menghasilkan berkas identik (uji reproduksibilitas)

**Evaluasi**

- [ ] Encoder content preservation tercatat dan berbeda dari encoder retrieval
- [ ] Suhu kalibrasi tercatat dan probabilitas terkalibrasi tersedia
- [ ] Proporsi output degenerate per metode dilaporkan
- [ ] Uji signifikansi dijalankan pada indeks sampel yang identik
- [ ] Himpunan sampel uji per target sama di seluruh metode dan seluruh ulangan

---

## 5. Temuan pilot validitas yang perlu keputusan terpisah

Ini bukan bagian dari rerun, tetapi menyentuh butir R2-10 dan menanggung risiko kalau diabaikan.

Berkas pilot n=100 (60 penilaian dari 3 penilai atas 100 teks, seimbang 20 per persona) berisi:

| Ukuran | Nilai |
|---|---|
| Kesesuaian antar penilai | 0,810 |
| Ketiga penilai sepakat | 72% |
| Kesesuaian label dataset dengan penilai 1, 2, 3 | 0,360 / 0,400 / 0,360 |
| Rata-rata kesesuaian label dataset dengan manusia | 0,373 |

Antar manusia sepakat pada 81% kasus, tetapi label dataset yang dipakai untuk melatih classifier
gaya hanya selaras dengan penilaian manusia pada sekitar 37% kasus. Peluang acak untuk lima kelas
adalah 20%, jadi posisi 37% berada di atas acak tetapi jauh dari kesepakatan antar manusia.
Perlu dicatat bahwa sampel pilot diseimbangkan 20 per kelas, sehingga angka ini bukan estimasi
tingkat kesalahan pada distribusi korpus yang sebenarnya.

Dua pilihan:

1. **Ungkapkan sebagai limitasi.** Ini menjelaskan mengapa akurasi gaya biner pada korpus Aaker
   menengah, dan memperkuat posisi paper terhadap kritik bahwa metrik gaya tidak tervalidasi.
2. **Jalankan validasi label pada skala penuh** sebelum revisi, memakai protokol pilot yang sama.
   Lebih kuat, tetapi menambah beban di luar rerun.

Yang harus dihindari: menyatakan adanya studi validitas n=385. Berkasnya ada, tetapi kolom
penilaiannya kosong, dan hanya pilot n=100 yang benar-benar terisi.

---

## 6. Hal yang tidak perlu diubah

- Fungsi retrieval di `retrieval_utils.py`. Formulasinya benar dan pembagian cosine similarity tepat. Kritik reviewer menyangkut interpretasi, bukan bug. Satu-satunya perubahan adalah seed pada `retrieve_random`.
- Isi template prompt generasi. Pertahankan agar perbandingan dengan hasil sebelumnya tetap mungkin, tambahkan hanya cabang zero-shot.
- Model (`google/gemma-3-4b-it`), kuantisasi 4-bit nf4, `temperature=0.7`, `top_p=0.9`, `max_new_tokens=1500`. Mengubahnya akan membatalkan seluruh perbandingan.
- Model fluency (`Sahabat-AI/llama3-8b-cpt-sahabatai-v1-instruct`). Yang salah adalah cara pelaporannya, bukan modelnya.
