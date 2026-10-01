# LAPORAN_REVISI

Folder ini memuat dua dokumen hasil putaran revisi pertama JCCE-10619 beserta skrip yang
menghasilkannya. Skrip disertakan supaya angkanya dapat diperiksa dan diperbarui, dan supaya model
lain dapat menilai kodenya sebelum dipakai.

## Dokumen

| Berkas | Untuk siapa | Isi |
|---|---|---|
| `SURAT_BALASAN_REVIEWER.md` | editor dan reviewer jurnal | Surat balasan bahasa Inggris, 38 butir, komentar reviewer dikutip verbatim |
| `LAPORAN_PERBAIKAN_REVISI.md` | pemilik naskah | Laporan bahasa Indonesia: apa yang dikerjakan, temuan yang mengubah klaim, batasan, sisa pekerjaan |
| `TABEL_STATUS_BUTIR.md` | pemantauan | Tabel status 38 butir, memisahkan yang selesai dari yang menunggu penyuntingan naskah |
| `VERIFIKASI_ANGKA.md` | pemeriksa | 130 angka laporan hasil rerun diperiksa terhadap data per sampel |

## Skrip

| Berkas | Peran |
|---|---|
| `verifikasi_angka.py` | Membaca 58 berkas `evaluated_v2_*_seed42_results.csv` dan memeriksa setiap angka laporan terhadapnya. Hanya membaca. |
| `jawaban_en.py` | Satu-satunya berkas yang ditulis tangan: jawaban per butir reviewer dan statusnya. |
| `build_dokumen.py` | Membaca workbook pemetaan dan `jawaban_en.py`, lalu menulis surat balasan dan tabel status. |

## Cara menjalankan ulang

```
cd LAPORAN_REVISI
python verifikasi_angka.py --akar "C:/Devs/Code/Python/JCCE-First Revision-From Remote"
python build_dokumen.py
```

`verifikasi_angka.py` menulis `VERIFIKASI_ANGKA.md` di folder ini. `build_dokumen.py` menulis ulang
`SURAT_BALASAN_REVIEWER.md` dan `TABEL_STATUS_BUTIR.md`.

Bila teks jawaban diubah, yang perlu disunting hanya `jawaban_en.py`. Komentar reviewer tidak pernah
disalin ke dalam kode, melainkan dibaca dari `sumber/JCCE-10619_Mapping_Reviewer_Comments_v1.xlsx`,
sehingga kutipan pada surat balasan selalu identik dengan sumbernya.

## Dua hal yang perlu dijaga

1. **Surat balasan harus cocok dengan naskah.** Surat ini menyatakan perubahan yang harus benar-benar
   ada pada berkas naskah. Jangan mengirimkannya sebelum penyuntingan naskah selesai.
2. **Tiga angka pada laporan agen sudah dikoreksi** dan koreksinya ada di bagian 2
   `LAPORAN_PERBAIKAN_REVISI.md`: porsi keluaran formal yang diprediksi informal adalah 82,8% bukan
   88%, nilai tingkat target pada metrik replikasi harus diambil dari tabel replikasi, dan panjang
   keluaran yang dipakai di naskah harus dari test set, yaitu 54,09 dan 28,52, bukan angka sapuan
   alpha-dev 58,69 dan 31,61.
