# PROTOKOL RERUN EKSPERIMEN, JCCE-10619 First Revision

Dokumen ini adalah instruksi kerja untuk agen LLM yang menjalankan ulang seluruh eksperimen
few-shot text style transfer untuk manuscript JCCE-10619. Bacalah seluruh dokumen sebelum
menjalankan perintah pertama.

**Konteks singkat.** Manuscript ini menerima major revision. Alasannya bukan bug pada kode,
melainkan protokol data dan evaluasi yang tidak sesuai dengan apa yang ditulis di manuscript:
penguncian pasangan paralel tidak pernah diterapkan, korpus brand personality memuat duplikat
teks yang menumpuk di retrieval index, encoder content preservation sama dengan encoder
retrieval, dan pelaporan fluency memakai mean sehingga angka tidak terbaca. Tugas Anda adalah
menjalankan protokol yang sudah diperbaiki dan menghasilkan angka baru untuk revisi.

**Berkas pendamping di folder ini.**

| Berkas | Isi |
|---|---|
| `README.md` | peta folder dan berkas penting |
| `requirements.txt` | dependensi dengan batas versi minimum |
| `RUN_LOG.md` | catatan kerja, sudah siap diisi |
| `scripts/` | Dua belas script yang dijalankan, semuanya dapat dipanggil dari baris perintah |
| `DOKUMEN_PENDUKUNG/` | protokol split, hasil audit klaim, spesifikasi lengkap, dan pemetaan butir reviewer |

---

## 0. Aturan kerja

Ikuti aturan ini tanpa pengecualian.

1. **Jangan mengubah manuscript.** Tugas Anda menghasilkan artefak eksperimen dan tabel angka.
   Penulisan naskah dilakukan manusia.
2. **Jangan mengarang angka.** Setiap angka yang Anda laporkan harus berasal dari berkas yang
   benar-benar dihasilkan oleh perintah yang Anda jalankan. Sebutkan jalur berkasnya.
3. **Jangan melewati gerbang pemeriksaan.** Setiap langkah punya pemeriksaan. Bila pemeriksaan
   gagal, hentikan langkah itu, laporkan, dan jangan lanjutkan ke langkah berikutnya.
4. **Jangan menghapus split lama.** Folder `*_splits` (tanpa `_v2`) adalah referensi pembanding.
   Split baru ditulis ke `*_splits_v2`.
5. **Catat setiap keputusan.** Bila Anda harus memilih (misalnya memotong ulangan karena waktu),
   tulis di laporan akhir apa yang dipotong dan alasannya.
6. **Bila gagal, jangan diam.** Laporkan perintah, pesan galat, dan berkas yang terlibat.
   Jangan menambal dengan nilai perkiraan.
7. **Perbarui `RUN_LOG.md`** di akar folder ini setiap kali menyelesaikan satu langkah: perintah,
   waktu mulai dan selesai, keluaran penting, dan status lulus atau gagal.
8. **Jalankan tugas panjang lewat `scripts/launch_detached.py`, bukan lewat perintah shell.**
   Generasi per korpus memerlukan 4 sampai 15 jam. Proses harus hidup terlepas dari giliran agen,
   supaya tetap berjalan meskipun percakapan di panel agen dihentikan atau ada pesan baru masuk.

   ```bash
   cd ..
   python scripts/launch_detached.py --nama formality_step6 --cwd fewshot_formality -- python fewshot_formality.py
   python scripts/launch_detached.py --status --nama formality_step6
   ```

   Peluncur itu memisahkan stdout dan stderr ke dua berkas, melepaskan proses dari sesi pemanggil,
   mencatat PID serta SHA-256 berkas config ke `LOGS/detached_<nama>.json`, lalu menunggu beberapa
   detik dan memeriksa bahwa prosesnya hidup dan lognya bertambah. Bila pemeriksaan itu gagal, ia
   mencetak isi stderr dan keluar dengan kode bukan nol, sehingga kegagalan tidak pernah lewat tanpa
   jejak.

   Pola `Start-Process -RedirectStandardOutput/-RedirectStandardError` pada PowerShell sudah
   terbukti gagal pada mesin ini: proses mati seketika, kedua berkas log tetap 0 byte, dan tidak ada
   pesan galat. Jangan memakai pola itu.

   Catat PID ke `RUN_LOG.md`. Jangan pernah menjalankan dua proses generasi sekaligus pada satu GPU,
   karena keduanya akan kehabisan memori dan keduanya batal.
9. **Jangan membaca seluruh folder hasil ke dalam konteks.** Folder `evaluation_result` dan
   `model_results_dir` memuat ratusan berkas CSV. Pakai script di `scripts/` yang sudah
   meringkasnya.
10. **Saat proses panjang berjalan, jawab pertanyaan agen dengan instruksi ringan saja.** Proses
   generasi berjalan di luar giliran agen, sehingga pesan baru tidak mematikannya. Tetapi pesan
   baru memang menghentikan giliran agen yang sedang berjalan, jadi:
   - Jangan meminta agen melakukan pekerjaan berat, mengubah konfigurasi, atau meluncurkan proses
     lain selama generasi berjalan.
   - Mintalah agen mencatat keputusan ke `RUN_LOG.md`, karena itu pekerjaan tanpa GPU.
   - Setelah keputusan dicatat, minta agen kembali memantau log, bukan memulai langkah berikutnya
     yang menuntut GPU.
   - Verifikasi bahwa prosesnya masih hidup dengan memeriksa PID dan melihat apakah log masih
     bertambah panjang. Bila log berhenti tumbuh padahal prosesnya hilang, proses itu dahulu
     terikat pada terminal agen dan harus diluncurkan ulang dengan cara pada butir 8.

---

## 1. Prasyarat lingkungan

| Komponen | Syarat |
|---|---|
| GPU | minimal 16 GB VRAM. Model utama 4-bit, model fluency 8B 4-bit |
| Python | 3.10 atau lebih baru |
| Paket wajib | `torch`, `transformers`, `sentence-transformers`, `scikit-learn >= 0.24` (butuh `StratifiedGroupKFold`), `pandas`, `numpy`, `rank-bm25`, `tqdm`, `scipy` (opsional, untuk uji Wilcoxon) |
| Token | variabel lingkungan `HF_TOKEN` yang sah untuk mengunduh model di Hugging Face |
| Disk | minimal 20 GB bebas untuk hasil generasi |

Pemeriksaan awal, jalankan dan pastikan semuanya lolos sebelum lanjut:

```bash
# 1. pasang dependensi
pip install -r requirements.txt

# 2. pemeriksaan kesiapan menyeluruh: versi pustaka, GPU, token, kelengkapan berkas, dan
#    kebocoran split. Perintah ini keluar dengan kode 1 bila ada kegagalan.
python scripts/preflight.py

# 3. bila perlu lebih rinci, pemeriksaan manual berikut dapat dijalankan terpisah
python -c "
import sys, torch, sklearn, pandas, numpy, transformers, sentence_transformers
print('python      ', sys.version.split()[0])
print('torch       ', torch.__version__, 'cuda', torch.cuda.is_available())
print('sklearn     ', sklearn.__version__)
print('pandas      ', pandas.__version__)
print('transformers', transformers.__version__)
print('cuda device ', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU saja')
from sklearn.model_selection import StratifiedGroupKFold
print('StratifiedGroupKFold tersedia')
"
test -n "$HF_TOKEN" && echo "HF_TOKEN terpasang" || echo "HF_TOKEN BELUM terpasang, unduhan model akan gagal"
```

`scripts/preflight.py` memeriksa sekaligus: versi Python, seluruh paket beserta batas minimum,
ketersediaan GPU beserta kapasitas memori, variabel `HF_TOKEN`, kelengkapan dua puluh enam berkas
penting, dan kebocoran keempat folder split. Gunakan `--json <berkas>` bila hasilnya perlu
dilampirkan pada laporan.

Catat versi pustaka dan tipe GPU di `RUN_LOG.md`. Informasi ini dipakai di manuscript bagian
setup komputasi (butir R2-15).

---

## 2. Peta folder

```
JCCE-First Revision/
├── PROTOKOL_RERUN.md            dokumen ini
├── RUN_LOG.md                   dibuat dan diperbarui oleh Anda
├── README.md
├── scripts/                     sembilan script yang dijalankan
├── DOKUMEN_PENDUKUNG/           protokol split, audit klaim, spesifikasi, pemetaan butir
├── classifier_formality/        scripts pelatihan classifier korpus STIF
│   ├── main.py                  SCRIPT LAMA, jangan dijalankan sebelum dipatch
│   └── data/
│       ├── combined_stif.csv    korpus rata, 4.998 baris
│       ├── stif_formal.txt      2.499 baris, sejajar baris demi baris dengan berkas berikut
│       ├── stif_informal.txt    2.499 baris
│       ├── formality_splits/    SPLIT LAMA, jangan diubah. Referensi pembanding
│       └── formality_splits_v2/ split baru, sudah dibuat dan terverifikasi
├── classifier_brand/            scripts pelatihan classifier korpus Aaker
│   ├── main.py
│   └── data/
│       ├── Combined Aaker Brand Personality - Cleaned v0.csv   75.756 baris
│       ├── brand_splits/        SPLIT LAMA, jangan diubah
│       └── brand_splits_v2/     split baru, sudah dibuat dan terverifikasi
├── fewshot_formality/           pipeline generasi korpus STIF
│   ├── fewshot_formality.py     SCRIPT GENERASI, perlu patch (bagian 5)
│   ├── eval.py                  evaluator lama, tetap ada sebagai referensi
│   ├── retrieval_utils.py       perlu patch kecil pada retrieve_random
│   ├── fewshot_config.json      perlu patch (bagian 5)
│   ├── prompts/                 template prompt
│   ├── style_classifier/        classifier lama, hanya konfigurasi dan tokenizer
│   ├── data/formality_splits_v2/  split baru, dibaca pipeline
│   └── evaluation_result/       hasil lama, referensi pembanding
└── fewshot_aaker/               pipeline generasi korpus Aaker, struktur sama
```

Catatan penting: berkas bobot classifier (`model.safetensors`) **tidak disertakan** karena
ukurannya besar. Classifier akan dilatih ulang pada langkah 4. Yang disertakan hanya
`config.json`, tokenizer, dan laporan klasifikasi lama sebagai pembanding.

---

## 3. Ringkasan urutan kerja

| Langkah | Isi | Butuh GPU | Estimasi |
|---|---|---|---|
| 1 | Verifikasi split baru (sudah dibuat, tinggal diverifikasi) | tidak | 5 menit |
| 2 | Patch konfigurasi dan pipeline | tidak | 1 jam |
| 3 | Uji jalur pipeline dengan 5 sampel | ya | 30 menit |
| 4 | Latih ulang dua classifier dan jalankan kalibrasi | ya | 2 jam |
| 5 | Sapuan alpha pada alpha_dev | ya | 2 jam |
| 6 | Jalankan seluruh konfigurasi pada test set, ulangan pertama | ya | 15 jam |
| 7 | Ulangan kedua dan ketiga untuk konfigurasi utama | ya | 15 jam |
| 8 | Evaluasi lengkap seluruh hasil | ya | 5 jam |
| 9 | Statistik, uji signifikansi, metrik replikasi | tidak | 1 jam |
| 10 | Sampel evaluasi manusia | tidak | 1 jam |
| 11 | Pengepakan keluaran untuk manuscript | tidak | 1 jam |

Langkah 10 dapat berjalan paralel dengan langkah 7 dan 8.

---

## 4. Langkah 1: verifikasi split baru

Split baru sudah dibuat dan sudah lulus pemeriksaan saat folder ini disusun. Verifikasi ulang
sebelum dipakai.

```bash
cd scripts

# korpus brand personality: split lama harus GAGAL, split baru harus LOLOS
python verify_splits.py --dir ../fewshot_aaker/data/brand_splits    --gate ; echo "lama exit=$?"
python verify_splits.py --dir ../fewshot_aaker/data/brand_splits_v2 --gate ; echo "baru exit=$?"

# korpus formality
python verify_splits.py --dir ../fewshot_formality/data/formality_splits    --gate ; echo "lama exit=$?"
python verify_splits.py --dir ../fewshot_formality/data/formality_splits_v2 --gate --tolerance 5 ; echo "baru exit=$?"
```

Untuk korpus formality, gerbang dijalankan dengan `--tolerance 5`. Alasannya: berkas sumber
`stif_informal.txt` sendiri memuat dua baris ganda, sehingga satu teks informal pasti muncul di
dua split berbeda. Tidak ada algoritma split yang dapat menghilangkannya tanpa membuang pasangan
yang sah. Angka sebenarnya adalah satu teks, dan itu harus dilaporkan apa adanya di `RUN_LOG.md`
serta di laporan akhir. Untuk korpus brand personality, gerbangnya harus lolos tanpa toleransi.

Yang harus terlihat:

- Split lama korpus Aaker **gagal** dengan ratusan teks identik antar split dan ribuan
  percakapan bersama. Ini memang keadaan sebelumnya, bukan kesalahan Anda.
- Split baru kedua korpus **lolos** dengan nol teks identik dan nol percakapan bersama, kecuali
  satu teks informal pada korpus formality yang berasal dari baris ganda di berkas sumber. Angka
  itu dilaporkan, bukan diabaikan.
- Ukuran split baru tidak berubah dari split lama pada korpus formality
  (2.498 / 500 / 1.500 / 500 kalimat). Pada korpus Aaker ukurannya turun karena deduplikasi,
  dari 75.756 menjadi 62.052 baris.

Bila split baru gagal, jangan lanjutkan. Buat ulang dengan `python make_splits_formality.py`
dan `python make_splits_brand.py --alpha-dev`, lalu laporkan.

Gerbang lanjut: kedua split baru lolos.

---

## 5. Langkah 2: patch konfigurasi dan pipeline

Terapkan lima perubahan berikut. Sesudah setiap perubahan, jalankan pemeriksaan sintaks
`python -m py_compile <berkas>`.

### 5.1 `fewshot_config.json` pada kedua repo

Ganti nilai berikut. Sisanya jangan diubah.

```json
{
    "split_dir": "data/formality_splits_v2",
    "retrieval_methods": ["dense", "centroid", "bm25", "hybrid_early", "random", "zero_shot"],
    "num_examples_range": [5, 10],
    "hybrid_alphas": [0.1, 0.3, 0.5, 0.7, 0.9],
    "run_seeds": [42],
    "human_eval_samples": 25,
    "sampling_seed": 42
}
```

Untuk `fewshot_aaker/fewshot_config.json` nilai yang berbeda hanya `split_dir` menjadi
`data/brand_splits_v2` dan `num_examples_range` tetap `[5]`.

Catatan: `run_seeds` akan dipakai pada langkah 7. Pada langkah 6 jalankan hanya seed pertama.

### 5.2 `retrieval_utils.py` pada kedua repo

Baseline `random` harus dapat direproduksi. Ganti fungsi `retrieve_random` menjadi:

```python
def retrieve_random(texts, k=5, seed=None):
    """Random-k baseline. Bila seed diberikan, hasilnya dapat direproduksi."""
    rng = random.Random(seed) if seed is not None else random
    return rng.sample(texts, min(k, len(texts)))
```

### 5.3 `get_style_examples` pada `fewshot_formality.py` dan `fewshot_aaker/main.py`

Ganti seluruh fungsi dengan versi ini. Tujuannya: menambah mode `zero_shot`, memberi seed pada
baseline random, dan melaporkan apakah terjadi fallback diam-diam.

```python
def get_style_examples(rag_data, sentence_model, num_examples, anchor_message,
                       method="dense", alpha=0.5, seed=None):
    """Mengembalikan (examples, used_fallback). Kosong berarti zero-shot."""
    if method == "zero_shot":
        return [], False
    if not rag_data:
        return [], True
    texts = rag_data["texts"]
    embeddings = rag_data["embeddings"]
    centroid = rag_data["centroid"]

    query_emb = sentence_model.encode([clean_text(anchor_message)])

    try:
        if method == "dense":
            return retrieve_dense(query_emb, embeddings, texts, num_examples), False
        elif method == "centroid":
            return retrieve_centroid(centroid, embeddings, texts, num_examples), False
        elif method == "bm25":
            return retrieve_bm25(clean_text(anchor_message), rag_data.get("bm25_model"),
                                 texts, num_examples), False
        elif method == "hybrid_early":
            return retrieve_hybrid_early_fusion(query_emb, centroid, embeddings, texts,
                                                num_examples, alpha), False
        elif method == "random":
            return retrieve_random(texts, num_examples, seed=seed), False
        else:
            return retrieve_random(texts, num_examples, seed=seed), True
    except Exception as e:
        logging.warning(f"Retrieval {method} gagal, fallback random: {e}")
        return retrieve_random(texts, num_examples, seed=seed), True
```

### 5.4 `robust_chat_completion` pada kedua pipeline

Ganti seluruh fungsi. Tujuannya: mengunci seed per sampel dan mencatat diagnostik degenerasi.

```python
def robust_chat_completion(hf_model, tokenizer, messages, options, seed=None):
    """Mengembalikan (teks, n_token_baru, eos_tercapai)."""
    try:
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(hf_model.device)

        gen_kwargs = dict(
            max_new_tokens=options.get("max_new_tokens", 1500),
            temperature=options.get("temperature", 0.7),
            top_p=options.get("top_p", 0.9),
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
        if seed is not None:
            gen_kwargs["generator"] = torch.Generator(device=hf_model.device).manual_seed(int(seed))

        outputs = hf_model.generate(**inputs, **gen_kwargs)

        input_length = inputs.input_ids.shape[1]
        new_ids = outputs[0][input_length:]
        response = tokenizer.decode(new_ids, skip_special_tokens=True)
        n_new = int(new_ids.shape[0])
        eos = bool(n_new > 0 and int(new_ids[-1]) == tokenizer.eos_token_id)
        return response.strip(), n_new, eos
    except Exception as e:
        logging.error(f"Hugging Face generation failed: {e}")
        return "ERROR: Gagal memproses hasil.", 0, False
```

### 5.5 `generate_paraphrases_sequential` pada kedua pipeline

Ganti seluruh fungsi. Tujuannya: mengembalikan eksemplar yang diambil, penanda fallback, prompt
lengkap, dan diagnostik per sampel. **Ini perubahan paling penting dalam protokol ini**: tanpa
kolom eksemplar, metrik replikasi templat dan materi suplemen tidak dapat dihasilkan.

```python
def generate_paraphrases_sequential(config, hf_model, tokenizer, sample_indices, df_test,
                                    rag_data, sentence_model, personality, method,
                                    num_examples, alpha=None, run_seed=None):
    gen_template = load_prompt_template("fewshot_generation_prompt.txt")
    rec = {"paraphrased": [], "exemplars": [], "fallback": [], "prompt_len": [],
           "n_new_tokens": [], "eos": [], "sample_index": [], "sample_seed": []}

    desc_str = f"Target: {personality} | {method}"
    if alpha is not None:
        desc_str += f" (alpha={alpha})"
    if run_seed is not None:
        desc_str += f" | seed={run_seed}"

    with tqdm(total=len(sample_indices), desc=desc_str, leave=True, ncols=100) as pbar:
        for i, msg_idx in enumerate(sample_indices):
            orig_msg = df_test.loc[msg_idx, config["message_col"]]
            sample_seed = None if run_seed is None else int(run_seed) * 100000 + i

            examples, used_fallback = get_style_examples(
                rag_data, sentence_model, num_examples, orig_msg, method,
                alpha if alpha is not None else 0.5, seed=sample_seed)

            if examples:
                user_prompt = gen_template.format(
                    style_examples_str=format_few_shot_examples(examples),
                    original_message=orig_msg)
            else:
                # cabang zero-shot: hilangkan blok contoh referensi
                user_prompt = gen_template.replace(
                    "### CONTOH REFERENSI\n{style_examples_str}\n\n", "").format(
                    style_examples_str="", original_message=orig_msg)

            messages = [
                {"role": "system", "content": "Anda adalah asisten linguistik ahli yang "
                                              "memodifikasi gaya bahasa teks."},
                {"role": "user", "content": user_prompt},
            ]
            options = {"max_new_tokens": config.get("max_new_tokens", 1500),
                       "temperature": config.get("temperature", 0.7),
                       "top_p": config.get("top_p", 0.9)}

            text, n_new, eos = robust_chat_completion(hf_model, tokenizer, messages, options,
                                                      seed=sample_seed)
            rec["paraphrased"].append(text)
            rec["exemplars"].append(examples)
            rec["fallback"].append(used_fallback)
            rec["prompt_len"].append(len(user_prompt))
            rec["n_new_tokens"].append(n_new)
            rec["eos"].append(eos)
            rec["sample_index"].append(int(msg_idx))
            rec["sample_seed"].append(sample_seed)
            pbar.update(1)
    return rec
```

Perhatikan: sistem prompt pada `fewshot_aaker/main.py` berbunyi
`"Anda adalah asisten linguistik ahli yang memodifikasi gaya bahasa teks."` tanpa keterangan
formality. Jangan menyamakan keduanya, biarkan seperti aslinya.

### 5.6 Blok penyusunan hasil pada `main()` kedua pipeline

Ini bagian yang menyusun `results_df`. Ganti menjadi:

```python
                    run_rec = generate_paraphrases_sequential(
                        config, hf_model, tokenizer, test_indices, df_test, rag_data,
                        sentence_model, personality, method, num_examples, alpha,
                        run_seed=run_seed
                    )

                    results_df = pd.DataFrame({
                        "model_id": [config["model_id"]] * len(test_indices),
                        "original_style": [df_test.loc[idx, config["style_col"]] for idx in test_indices],
                        "style_target": [personality] * len(test_indices),
                        "retrieval_method": [method] * len(test_indices),
                        "alpha": [alpha if alpha is not None else "N/A"] * len(test_indices),
                        "original_message": [df_test.loc[idx, config["message_col"]] for idx in test_indices],
                        "paraphrased_message": run_rec["paraphrased"],
                        "is_human_eval": [True if idx in human_eval_indices else False for idx in test_indices],
                        "sample_index": run_rec["sample_index"],
                        "sample_seed": run_rec["sample_seed"],
                        "run_seed": [run_seed] * len(test_indices),
                        "retrieved_exemplars": [json.dumps(e, ensure_ascii=False) for e in run_rec["exemplars"]],
                        "retrieval_fallback": run_rec["fallback"],
                        "n_exemplars": [len(e) for e in run_rec["exemplars"]],
                        "prompt_chars": run_rec["prompt_len"],
                        "output_tokens": run_rec["n_new_tokens"],
                        "eos_reached": run_rec["eos"],
                        "output_chars": [len(t) for t in run_rec["paraphrased"]],
                    })
```

### 5.7 Penyesuaian loop konfigurasi pada `main()`

Tiga hal yang perlu diubah pada loop yang mengiterasi `num_examples`, `method`, dan `alpha`:

1. **Lewati `zero_shot` untuk k lebih dari satu.** Mode ini tidak memakai eksemplar, jadi cukup
   dijalankan sekali. Tambahkan di awal iterasi `num_examples`:

   ```python
                    if method == "zero_shot" and num_examples != min(config.get("num_examples_range", [5])):
                        continue
   ```

2. **Tambahkan seed ulangan pada nama berkas.** Setelah baris `filename_suffix`, sisipkan
   `run_seed` agar hasil tiap ulangan tidak saling menimpa:

   ```python
                    filename_suffix = f"{filename_suffix}_seed{run_seed}"
   ```

3. **Iterasi `run_seeds`.** Bungkus loop `num_examples` dengan loop baru, atau jalankan pipeline
   terpisah per seed dengan mengubah `run_seeds` pada config menjadi satu nilai. Cara kedua lebih
   aman untuk pemantauan. Gunakan `--only-seed` yang Anda tambahkan sendiri:

   ```python
   # pada load_config() atau setelah config dibaca di main():
   if len(sys.argv) > 2 and sys.argv[1] == "--only-seed":
       config["run_seeds"] = [int(sys.argv[2])]
   ```

   lalu di dalam loop: `for run_seed in config.get("run_seeds", [42]):`

### 5.8 Pemeriksaan sesudah patch

```bash
cd fewshot_formality && python -m py_compile fewshot_formality.py retrieval_utils.py
cd ../fewshot_aaker  && python -m py_compile main.py retrieval_utils.py
python -c "import json;print(json.load(open('fewshot_config.json'))['split_dir'])"
```

---

## 6. Langkah 3: uji jalur dengan sampel kecil

Sebelum menjalankan apa pun yang panjang, uji saluran pipa dengan lima sampel.

```bash
cd fewshot_formality
python -c "
import json
cfg = json.load(open('fewshot_config.json'))
cfg['num_samples'] = 5
cfg['num_examples_range'] = [5]
cfg['retrieval_methods'] = ['dense', 'centroid', 'zero_shot']
cfg['run_seeds'] = [42]
cfg['hybrid_alphas'] = []
json.dump(cfg, open('fewshot_config.json', 'w'), indent=4)
"
python fewshot_formality.py
```

Yang harus diperiksa pada berkas hasil:

- Kolom `retrieved_exemplars` ada dan **terisi** untuk metode dense dan centroid.
- Kolom `retrieved_exemplars` berisi daftar kosong `[]` untuk `zero_shot`.
- Kolom `retrieval_fallback` seluruhnya bernilai `False`. Bila ada yang `True`, laporkan jumlahnya.
- Kolom `sample_index`, `sample_seed`, `output_tokens`, `eos_reached` ada dan terisi.
- Untuk metode centroid, eksemplar pada baris pertama dan baris kedua **identik**. Ini sifat
  yang memang diharapkan dan akan dibahas di manuscript.

Kelima butir di atas diperiksa otomatis oleh script berikut. Jalankan dan pastikan keluar dengan
kode 0. Script ini menangkap kesalahan patch yang lolos sintaks tetapi tidak mencatat eksemplar
atau seed, yaitu kesalahan yang akibatnya baru terlihat setelah belasan jam generasi.

```bash
cd ../scripts
python check_smoke_output.py --dir ../fewshot_formality/model_results_dir/google_gemma-3-4b-it \
    --num-examples 5 --json ../smoke_formality.json
```

Script yang sama memeriksa bahwa himpunan `sample_index` identik di seluruh metode, karena tanpa
itu perbandingan berpasangan pada langkah 9 menjadi tidak sah.

Setelahnya, kembalikan `fewshot_config.json` ke nilai penuh.

Gerbang lanjut: `check_smoke_output.py` keluar dengan kode 0.

---

## 7. Langkah 4: latih ulang classifier dan kalibrasi

Split berubah, sehingga classifier gaya harus dilatih ulang pada kedua korpus. Ini juga
menghasilkan metrik gaya yang akan dipakai seluruh evaluasi.

```bash
cd classifier_formality
# patch main.py: hapus blok split (baris 46 sampai 60), ganti dengan pembacaan berkas split
#   train = pd.read_csv("data/formality_splits_v2/train_set.csv")
#   val   = pd.read_csv("data/formality_splits_v2/val_set.csv")
#   test  = pd.read_csv("data/formality_splits_v2/test_set.csv")
# dan tambahkan set_seed(42) setelah blok import
python main.py
cp -r model_results_dir/formality_model_roberta ../fewshot_formality/style_classifier

cd ../classifier_brand
# patch main.py sama: arahkan ke data/brand_splits_v2, hapus blok split, simpan split tidak lagi
python main.py
cp -r model_results_dir/brand_model_roberta ../fewshot_aaker/style_classifier

cd ../scripts
python calibrate_classifier.py --classifier ../fewshot_formality/style_classifier \
    --val ../fewshot_formality/data/formality_splits_v2/val_set.csv \
    --text-col text --style-col formality

python calibrate_classifier.py --classifier ../fewshot_aaker/style_classifier \
    --val ../fewshot_aaker/data/brand_splits_v2/val_set.csv \
    --text-col cleaned_text --style-col personality
```

Yang harus dilaporkan dari langkah ini:

- Akurasi macro-F1 dan laporan klasifikasi per kelas pada test set baru, untuk kedua korpus.
- Suhu `T` hasil kalibrasi, NLL dan ECE sebelum dan sesudah kalibrasi, serta sebaran
  probabilitas kelas target sebelum dan sesudah.
- Perbandingan dengan angka lama: korpus formality akurasi 0,9220 dengan support 500, korpus
  Aaker accuracy 0,93 dengan support 7.576. Angka baru akan berbeda karena split berubah.

Gerbang lanjut: `calibration.json` terbentuk di kedua folder `style_classifier`.

---

## 8. Langkah 5: sapuan alpha pada development set

```bash
cd fewshot_formality
python -c "
import json
cfg = json.load(open('fewshot_config.json'))
cfg['split_dir'] = 'data/formality_splits_v2'
cfg['num_samples'] = 'all'
cfg['num_examples_range'] = [5]
cfg['retrieval_methods'] = ['hybrid_early']
cfg['run_seeds'] = [42]
json.dump(cfg, open('fewshot_config_alphadev.json', 'w'), indent=4)
"
# jalankan dengan split_dir diarahkan ke alpha_dev untuk korpus Aaker, dan
# untuk korpus formality gunakan val_set_v2 sebagai development set karena
# korpus STIF tidak menyediakan alpha_dev terpisah
python fewshot_formality.py
```

Untuk korpus formality, development set untuk pemilihan alpha adalah `val_set_v2`. Untuk korpus
Aaker tersedia `alpha_dev` yang terpisah. Ini perbedaan yang perlu dinyatakan di manuscript.

Evaluasi lalu pilih alpha:

```bash
cd ../scripts
python evaluate_results.py \
    --results ../fewshot_formality/model_results_dir/google_gemma-3-4b-it \
    --classifier ../fewshot_formality/style_classifier \
    --out ../fewshot_formality/evaluation_result_alphadev/google_gemma-3-4b-it \
    --calibration ../fewshot_formality/style_classifier/calibration.json \
    --encoder LaBSE=sentence-transformers/LaBSE

python select_alpha_dev.py --dir ../fewshot_formality/evaluation_result_alphadev/google_gemma-3-4b-it \
    --out ../fewshot_formality/alpha_star.json
```

Ulangi untuk korpus Aaker dengan `--dir` menunjuk ke folder alpha_dev-nya.

Kriteria bawaan adalah rata-rata harmonik antara akurasi gaya dan content preservation. Bila
manusia memutuskan kriteria lain, jalankan `select_alpha_dev.py` dengan `--criterion` yang sesuai.

Yang harus dilaporkan: kurva sapuan lengkap kelima alpha per target, alpha terpilih, dan nilai
kriteria pada titik terpilih.

---

## 9. Langkah 6: jalankan seluruh konfigurasi pada test set

Inilah langkah terpanjang. Sekitar 5 jam untuk korpus formality dan 9 jam untuk korpus Aaker.

```bash
# korpus formality
cd fewshot_formality
python -c "
import json
cfg = json.load(open('fewshot_config.json'))
cfg['split_dir'] = 'data/formality_splits_v2'
cfg['num_samples'] = 'all'
cfg['num_examples_range'] = [5, 10]
cfg['retrieval_methods'] = ['dense', 'centroid', 'bm25', 'hybrid_early', 'random', 'zero_shot']
cfg['hybrid_alphas'] = [0.1, 0.3, 0.5, 0.7, 0.9]
cfg['run_seeds'] = [42]
json.dump(cfg, open('fewshot_config.json', 'w'), indent=4)
"
python fewshot_formality.py 2>&1 | tee ../run_formality_seed42.log

# korpus Aaker
cd ../fewshot_aaker
# lakukan hal yang sama, num_samples tetap 500, num_examples_range tetap [5]
python main.py 2>&1 | tee ../run_aaker_seed42.log
```

Pantau pada log:

- Jumlah sampel per konfigurasi harus tetap: 250 per target untuk formality, 500 untuk Aaker.
- Jumlah `retrieval_fallback` harus nol. Bila tidak, laporkan berapa dan pada konfigurasi mana.
- Tidak ada teks hasil yang diawali `ERROR:`.

---

## 10. Langkah 7: ulangan generasi untuk varians

**Tidak dijalankan pada revisi ini.** Struktur yang dipakai adalah satu seed (42) untuk seluruh
konfigurasi, sehingga tidak ada ulangan generasi. Konsekuensinya varians antar-jalan tidak diukur,
dan ukuran ketidakpastian yang dilaporkan adalah bootstrap berpasangan atas butir uji. Konsekuensi
itu wajib diungkapkan di naskah dan di surat balasan.

Hanya untuk konfigurasi utama, bukan seluruh sapuan. Konfigurasi utama adalah `dense`,
`centroid`, `bm25`, dan `hybrid_early` pada alpha terpilih, untuk setiap target.

```bash
cd fewshot_formality
python fewshot_formality.py --only-seed 43
python fewshot_formality.py --only-seed 44
```

Ulangi untuk korpus Aaker. Perkirakan 4 jam per ulangan untuk formality dan 11 jam untuk Aaker,
sehingga langkah ini sekitar 15 jam total.

Bila waktu tersedia terbatas, potong urutan ini: ulangan ketiga lebih dulu, lalu metode `random`
pada k lebih dari satu. **Jangan memotong ulangan kedua**, karena reviewer meminta pelaporan
varians.

Seluruh isi bagian di atas hanya berlaku bila struktur berulang seed dipakai. Pada revisi ini
langkah ini tidak dijalankan, sehingga perintah dan urutan pemotongannya disimpan sebagai catatan
untuk keperluan mendatang, bukan sebagai rencana kerja.

---

## 11. Langkah 8: evaluasi lengkap

```bash
cd scripts

# korpus formality. --patterns wajib: model_results_dir juga memuat berkas lama tanpa penanda seed
python evaluate_results.py \
    --results ../fewshot_formality/model_results_dir/google_gemma-3-4b-it \
    --patterns "*_seed42*_results.csv" \
    --classifier ../fewshot_formality/style_classifier \
    --out ../fewshot_formality/evaluation_result_v2/google_gemma-3-4b-it \
    --calibration ../fewshot_formality/style_classifier/calibration.json \
    --encoder LaBSE=sentence-transformers/LaBSE \
    --encoder mE5=intfloat/multilingual-e5-base \
    --legacy-encoder LazarusNLP/simcse-indobert-base \
    --fluency-model Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct

# korpus Aaker
python evaluate_results.py \
    --results ../fewshot_aaker/model_results_dir/google_gemma-3-4b-it \
    --patterns "*_seed42*_results.csv" \
    --classifier ../fewshot_aaker/style_classifier \
    --out ../fewshot_aaker/evaluation_result_v2/google_gemma-3-4b-it \
    --calibration ../fewshot_aaker/style_classifier/calibration.json \
    --encoder LaBSE=sentence-transformers/LaBSE \
    --encoder mE5=intfloat/multilingual-e5-base \
    --legacy-encoder LazarusNLP/simcse-indobert-base \
    --fluency-model Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct
```

Tiga encoder sengaja dihitung: `LazarusNLP/simcse-indobert-base` adalah encoder lama yang sama
dengan encoder retrieval, sehingga kolomnya dipakai untuk memperlihatkan besarnya perbedaan.
LaBSE dan mE5 adalah encoder independen yang menjadi acuan baru untuk content preservation.

Fluency memakai `Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct` pada KEDUA korpus. Model itulah yang
dinyatakan naskah, dan model itu pula yang dipakai `fewshot_aaker/eval.py`. Perlu diketahui bahwa
`fewshot_formality/eval.py` aslinya memakai `Sahabat-AI/llama3-8b-cpt-sahabatai-v1-instruct`, sehingga
kedua pipeline asli tidak seragam. Rerun ini menyeragamkannya pada gemma2-9b, supaya naskah hanya
perlu menyebut satu model dan kedua korpus dapat dibandingkan. Nilai PPL bergantung pada model dan
tokenizernya, jadi jangan mencampur keduanya dalam satu kolom. Laporkan nama model yang benar-benar
dimuat dari log, bukan hanya nilai bawaan opsinya.

Bila memori tidak cukup pada GPU 12 GB, pakai jalur dua tahap berikut. Puncak pemakaian memori tahap
kedua hanya berasal dari model fluency, bukan dari model fluency bersama classifier dan dua encoder
sekaligus.

```bash
# tahap 1: tanpa fluency, memuat classifier dan encoder saja
python evaluate_results.py \
    --results ../fewshot_aaker/model_results_dir/google_gemma-3-4b-it \
    --patterns "*_seed42*_results.csv" \
    --classifier ../fewshot_aaker/style_classifier \
    --out ../fewshot_aaker/evaluation_result_v2/google_gemma-3-4b-it \
    --calibration ../fewshot_aaker/style_classifier/calibration.json \
    --encoder LaBSE=sentence-transformers/LaBSE \
    --encoder mE5=intfloat/multilingual-e5-base \
    --skip-fluency

# tahap 2: hanya fluency, membaca berkas hasil tahap 1 lalu menambahkan kolomnya
python evaluate_results.py \
    --out ../fewshot_aaker/evaluation_result_v2/google_gemma-3-4b-it \
    --only-fluency \
    --fluency-model Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct
```

Tahap kedua aman diulang, karena berkas yang sudah memuat kolom `fluency_ppl` dilewati. Kolom yang
ditulis tahap kedua adalah `fluency_ppl`, `output_tokens`, `eos_reached`, dan `ppl_degenerate`.
Catat di `RUN_LOG.md` bahwa fluency dihitung pada tahap terpisah.

Jangan memakai `--legacy-eval-dir` untuk menyalin PPL lama pada revisi ini, karena berkas lama tidak
memuat penanda seed sehingga jumlah barisnya berbeda dan penyalinan itu tidak sah.

---

## 12. Langkah 9: statistik dan metrik baru

```bash
cd scripts

# ringkasan statistik, termasuk median dan proporsi degenerate
python report_metrics.py --dir ../fewshot_formality/evaluation_result_v2/google_gemma-3-4b-it \
    --only-seed 42 --out ../TABEL_ringkasan_formality.csv
python report_metrics.py --dir ../fewshot_aaker/evaluation_result_v2/google_gemma-3-4b-it \
    --only-seed 42 --out ../TABEL_ringkasan_aaker.csv

# uji signifikansi berpasangan, untuk setiap metrik yang dilaporkan
for M in style_accuracy style_strength_calibrated content_preservation_LaBSE replication_rate_8; do
  python bootstrap_significance.py --dir ../fewshot_formality/evaluation_result_v2/google_gemma-3-4b-it \
      --only-seed 42 --metric $M --out ../TABEL_uji_formality_$M.csv
  python bootstrap_significance.py --dir ../fewshot_aaker/evaluation_result_v2/google_gemma-3-4b-it \
      --only-seed 42 --metric $M --out ../TABEL_uji_aaker_$M.csv
done

# laju replikasi templat dari kolom retrieved_exemplars
python replication_metric.py --dir ../fewshot_aaker/evaluation_result_v2/google_gemma-3-4b-it \
    --only-seed 42 --from-column --out ../TABEL_replikasi_aaker.csv
python replication_metric.py --dir ../fewshot_formality/evaluation_result_v2/google_gemma-3-4b-it \
    --only-seed 42 --from-column --out ../TABEL_replikasi_formality.csv
```

Angka pembanding dari eksperimen lama yang perlu dicek ulang: pada korpus Aaker laju replikasi
metode centroid adalah 76,6% dan dense 0,4%; pada korpus formality 1,2% dan 0,0%. Setelah
deduplikasi pool, angka replikasi korpus Aaker diharapkan turun. Bila tidak turun, laporkan apa
adanya.

---

## 13. Langkah 10: sampel untuk evaluasi manusia

Sampel harus tetap dan sama lintas metode agar penilaian dapat dibandingkan.

```bash
python - <<'PY'
import glob, json, os
import pandas as pd

# ambil 25 sampel dengan sample_index terkecil dari empat metode utama,
# untuk satu target per korpus
for repo, tag, target in [
    ("../fewshot_formality", "formality", "informal"),
    ("../fewshot_aaker", "aaker", "competence"),
]:
    src = glob.glob(os.path.join(repo, "model_results_dir", "google_gemma-3-4b-it",
                                 f"*{target}*_seed42*_results.csv"))
    picks, keys = {}, None
    for f in sorted(src):
        name = os.path.basename(f)
        if not any(m in name for m in ("dense", "centroid", "bm25", "hybrid_early")):
            continue
        d = pd.read_csv(f)
        if "sample_index" not in d.columns:
            continue
        idx = sorted(d["sample_index"].unique())[:25]
        if keys is None:
            keys = set(idx)
        idx = sorted(keys)
        picks[name] = d[d["sample_index"].isin(idx)][
            ["sample_index", "original_message", "paraphrased_message"]]
    out = []
    for name, d in picks.items():
        d = d.assign(method_file=name)
        out.append(d)
    if out:
        df = pd.concat(out, ignore_index=True)
        p = f"../EVAL_MANUSIA_{tag}.csv"
        df.to_csv(p, index=False)
        print(f"ditulis {p}: {len(df)} baris, {df['sample_index'].nunique()} kalimat sumber")
PY
```

Rubrik penilaian sudah tersedia di
`fewshot_aaker/data/Aaker Brand Personality - Human Validity Rubric.md`. Susun lembar penilaian
dengan tiga kolom per penilai: kekuatan gaya, pemeliharaan konten, dan kelancaran, masing-masing
skala 1 sampai 5. Tiga penilai mengisi secara terpisah. Hitung kesepakatan antar penilai dan
korelasinya dengan metrik otomatis.

Catatan penting yang harus dilaporkan apa adanya: studi validitas label n=385 pada repo ini
**belum terisi** kolom penilaiannya, dan hanya pilot n=100 yang terisi. Jangan menyatakan adanya
studi n=385 dalam laporan mana pun.

---

## 14. Langkah 11: pengepakan keluaran

Susun folder `HASIL/` di akar dengan isi berikut.

| Berkas | Isi |
|---|---|
| `TABEL_ringkasan_*.csv` | statistik per konfigurasi, termasuk median, trimmed mean, proporsi degenerate |
| `TABEL_uji_*.csv` | interval keyakinan bootstrap dan nilai p berpasangan |
| `TABEL_replikasi_*.csv` | laju replikasi templat per metode per korpus |
| `alpha_star.json` | alpha terpilih dan kurva sapuan lengkap |
| `calibration.json` | suhu kalibrasi dan metrik kalibrasi kedua korpus |
| `split_manifest.json` | manifes kedua split baru |
| `EVAL_MANUSIA_*.csv` | sampel untuk penilaian manusia |
| `RUN_LOG.md` | catatan seluruh langkah |
| `LAPORAN_AKHIR.md` | laporan Anda, lihat bagian 16 |
| `evaluated_v2_*.csv` | hasil evaluasi per sampel, untuk materi suplemen |

Salin juga seluruh berkas hasil generasi dari `model_results_dir` ke `HASIL/keluaran_generasi/`
sebagai materi suplemen per sampel.

---

## 15. Daftar periksa penerimaan

Jangan menyatakan pekerjaan selesai sebelum seluruh butir ini terpenuhi.

**Split**

- [ ] Split baru kedua korpus lolos `verify_splits.py --gate`
- [ ] Ukuran split formality tetap 2.498 / 500 / 1.500 / 500
- [ ] Korpus Aaker turun dari 75.756 menjadi 62.052 baris


**Generasi**

- [ ] Kolom `retrieved_exemplars` terisi pada seluruh berkas hasil
- [ ] Jumlah `retrieval_fallback` nol, atau dilaporkan bila tidak nol
- [ ] Tidak ada keluaran yang diawali `ERROR:`
- [ ] Jumlah sampel per konfigurasi sesuai: 250 per target formality, 500 per target Aaker
- [ ] Untuk setiap konfigurasi, himpunan `sample_index` sama di seluruh metode
- [ ] Himpunan eksemplar identik antar ulangan untuk konfigurasi yang sama

**Evaluasi**

- [ ] `calibration.json` ada untuk kedua korpus, dengan suhu dan metrik kalibrasi
- [ ] Kolom content preservation dari ketiga encoder ada
- [ ] Laju replikasi templat terhitung untuk seluruh berkas
- [ ] Uji signifikansi dijalankan pada seluruh metrik yang dilaporkan
- [ ] Proporsi output degenerate dilaporkan per metode

**Pelaporan**

- [ ] `LAPORAN_AKHIR.md` memuat seluruh angka dengan jalur berkas sumbernya
- [ ] Setiap kegagalan atau bagian yang dipotong tercatat, tanpa angka perkiraan

---

## 16. Format laporan akhir

Tulis `LAPORAN_AKHIR.md` dengan struktur berikut. Sertakan jalur berkas untuk setiap angka.

1. **Ringkasan eksekusi.** Langkah mana yang dijalankan, mana yang tidak, total waktu.
2. **Lingkungan.** GPU, VRAM, versi pustaka, dan setelan kuantisasi.
3. **Split baru.** Ukuran per split, hasil gerbang kebocoran, perbandingan dengan split lama,
   dan jumlah duplikat yang dibuang pada korpus Aaker.
4. **Classifier dan kalibrasi.** F1 per kelas pada test set baru, suhu, NLL dan ECE sebelum serta
   sesudah, sebaran probabilitas kelas target sebelum dan sesudah.
5. **Pemilihan alpha.** Kurva sapuan, kriteria, alpha terpilih per target.
6. **Hasil utama.** Untuk setiap korpus dan target: akurasi gaya biner, probabilitas terkalibrasi,
   content preservation dari tiga encoder, median dan trimmed PPL, proporsi degenerate.
7. **Varians.** Sebaran hasil antar tiga ulangan untuk konfigurasi utama.
8. **Uji signifikansi.** Tabel pasangan yang berbeda secara bermakna, dan yang tidak.
9. **Replikasi templat.** Laju per metode per korpus, dan perbandingannya dengan angka lama.
10. **Evaluasi manusia.** Bila dijalankan, hasilnya. Bila tidak, nyatakan tidak dijalankan.
11. **Kendala.** Setiap kegagalan, peringatan, dan keputusan pemotongan.
12. **Berkas keluaran.** Daftar lengkap berkas di `HASIL/`.

---

## 17. Kendala umum dan penanganannya

| Gejala | Penanganan |
|---|---|
| `OSError: CUDA out of memory` | Turunkan `per_device_eval_batch_size` pada `evaluate_results.py` lewat `--limit` untuk uji, atau jalankan fluency terpisah dengan `--skip-fluency` lalu PPL dihitung pada proses terpisah |
| Unduhan model gagal, 401 | `HF_TOKEN` tidak sah atau belum di-export. Periksa dengan `test -n "$HF_TOKEN"` |
| `retrieval_fallback` bernilai True pada banyak sampel | Biasanya `rank-bm25` belum terpasang atau kolom teks kosong. Periksa pesan peringatan pada log |
| Keluaran berisi `ERROR:` | Lihat pesan `Hugging Face generation failed` pada log. Umumnya tokenizer atau panjang prompt melampaui batas. Laporkan konfigurasi dan jumlah kejadiannya |
| Log berhenti bertambah padahal proses seharusnya jalan | Periksa PID lewat `python scripts/launch_detached.py --status --nama <nama>` atau `scripts/status.py`. Bila prosesnya hilang, luncurkan ulang lewat `scripts/launch_detached.py` pada aturan 8, lalu sesuaikan `skip_existing` agar berkas yang sudah selesai tidak diulang |
| Pesan baru di panel agen saat generasi berjalan | Tidak mematikan proses generasi, karena prosesnya terpisah. Yang berhenti adalah giliran agen. Jawab dengan instruksi ringan, minta catat ke `RUN_LOG.md`, lalu minta kembali memantau log |
| GPU kehabisan memori padahal hanya satu proses | Periksa apakah ada proses generasi lama yang belum berhenti. `Get-Process python` pada Windows, `pgrep -af python` pada Linux |
| PPL bernilai besar pada sebagian kecil sampel | Ini keadaan yang sudah diketahui dan akan dilaporkan sebagai proporsi output degenerate. Jangan membuang sampel tanpa mencatat kriteria penyaringan |
| `StratifiedGroupKFold` tidak ditemukan | `scikit-learn` terlalu lama. Naikkan ke versi 0.24 atau lebih baru |
| Uji Wilcoxon tidak muncul di keluaran | `scipy` tidak terpasang. Uji permutasi tanda dipakai otomatis. Pasang `scipy` bila memungkinkan |

---

## 18. Yang tidak boleh diubah

Mengubah hal-hal berikut akan membatalkan seluruh perbandingan dan memaksa pengulangan dari awal.

- Model generasi: tetap `google/gemma-3-4b-it`.
- Kuantisasi: tetap 4-bit nf4 dengan double quantization.
- Parameter dekode: `temperature=0.7`, `top_p=0.9`, `max_new_tokens=1500`, `do_sample=True`.
- Isi template prompt pada `prompts/fewshot_generation_prompt.txt`, kecuali cabang zero-shot yang
  ditambahkan pada bagian 5.5.
- Model fluency: diseragamkan menjadi `Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct` pada kedua
  korpus. Sebelumnya `fewshot_formality/eval.py` memakai
  `Sahabat-AI/llama3-8b-cpt-sahabatai-v1-instruct`, sehingga kedua pipeline asli tidak seragam.
- Formulasi fungsi retrieval di `retrieval_utils.py`, kecuali `retrieve_random` pada bagian 5.2.
- Berkas split lama dan seluruh folder `evaluation_result` serta `model_results_dir` yang lama.
  Keduanya adalah referensi pembanding.
