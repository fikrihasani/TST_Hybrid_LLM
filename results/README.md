# Results

Hasil yang dipakai naskah, dikelompokkan supaya mudah diperiksa. Semua berkas di sini dihasilkan oleh
pipeline di folder induk; perintah untuk menghasilkannya ada pada `README.md` repositori.

| Folder | Isi |
|---|---|
| `tables/formality/` | tabel ringkasan, uji signifikansi pasangan, laju replikasi, dan perplexity per target untuk korpus formality |
| `tables/brand_personality/` | tabel setara untuk korpus brand personality |
| `per_sample/formality/` | keluaran per sampel untuk 19 konfigurasi korpus formality (38 berkas hasil + berkas evaluasi manusia) |
| `per_sample/brand_personality/` | keluaran per sampel untuk 10 konfigurasi korpus brand personality |
| `raw_generations/formality/` | keluaran generasi mentah dan berkas penilaian manusia per konfigurasi, korpus formality |
| `raw_generations/brand_personality/` | keluaran generasi mentah per konfigurasi, korpus brand personality |
| `human_evaluation/` | sampel penilaian manusia siap dibagikan ke penilai (400 baris formality, 200 baris brand personality) |
| `error_analysis/` | sampel yang dipakai pada analisis galat |
| `calibration/` | hasil kalibrasi classifier, bobot alpha terpilih, dan konfigurasi pemilihannya |

Catatan kolom pada `per_sample/`: `content_preservation_LaBSE` adalah ukuran yang dilaporkan naskah,
`content_preservation` adalah encoder lama yang disimpan sebagai pembanding, `style_strength_calibrated`
adalah probabilitas kelas target setelah temperature scaling, dan `ppl_degenerate` menandai keluaran dengan
perplexity di atas 1.000.
