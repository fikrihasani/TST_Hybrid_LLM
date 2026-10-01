# RUN_LOG

Catatan kerja saat menjalankan `PROTOKOL_RERUN.md`. Salin berkas ini menjadi `RUN_LOG.md` lalu
perbarui setiap kali satu langkah selesai.

---

## Lingkungan

| Item | Nilai |
|---|---|
| Tanggal mulai | |
| Tanggal selesai | |
| GPU dan VRAM | |
| Python | |
| torch / transformers / sentence-transformers | |
| scikit-learn / pandas / numpy | |
| `HF_TOKEN` terpasang | ya / tidak |

---

## Catatan per langkah

Format untuk setiap langkah: perintah yang dijalankan, waktu mulai dan selesai, keluaran penting,
status.

### Langkah 1. Verifikasi split baru

```
perintah:
mulai:
selesai:
hasil:
status: lulus / gagal
```

### Langkah 2. Patch konfigurasi dan pipeline

```
perintah:
mulai:
selesai:
berkas yang diubah:
hasil py_compile:
status:
```

### Langkah 3. Uji jalur dengan sampel kecil

```
perintah:
mulai:
selesai:
jumlah fallback:
kolom baru terisi:
status:
```

### Langkah 4. Latih ulang classifier dan kalibrasi

```
perintah:
mulai:
selesai:
macro-F1 formality:
accuracy Aaker:
suhu formality:
suhu Aaker:
NLL dan ECE sebelum -> sesudah:
status:
```

### Langkah 5. Sapuan alpha pada development set

```
perintah:
mulai:
selesai:
alpha terpilih per target:
nilai kriteria pada titik terpilih:
status:
```

### Langkah 6. Seluruh konfigurasi, ulangan pertama

```
perintah:
mulai:
selesai:
jumlah konfigurasi formality:
jumlah konfigurasi Aaker:
jumlah fallback:
jumlah keluaran ERROR:
status:
```

### Langkah 7. Ulangan kedua dan ketiga

```
seed yang dijalankan:
mulai:
selesai:
konfigurasi yang diulang:
bagian yang dipotong (bila ada) dan alasannya:
status:
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
perintah:
mulai:
selesai:
berkas tabel yang dihasilkan:
status:
```

### Langkah 10. Sampel evaluasi manusia

```
perintah:
mulai:
selesai:
jumlah sampel:
jumlah penilai:
status:
```

### Langkah 11. Pengepakan keluaran

```
berkas di HASIL/:
status:
```

---

## Kendala dan keputusan

Catat setiap kegagalan, peringatan, dan keputusan yang diambil di luar protokol. Sertakan pesan
galat apa adanya.

| Waktu | Langkah | Gejala | Tindakan | Alasan |
|---|---|---|---|---|
| | | | | |

---

## Ringkasan waktu

| Langkah | Estimasi protokol | Waktu nyata |
|---|---|---|
| 1 | 5 menit | |
| 2 | 1 jam | |
| 3 | 30 menit | |
| 4 | 2 jam | |
| 5 | 2 jam | |
| 6 | 15 jam | |
| 7 | 15 jam | |
| 8 | 5 jam | |
| 9 | 1 jam | |
| 10 | 1 jam | |
| 11 | 1 jam | |
