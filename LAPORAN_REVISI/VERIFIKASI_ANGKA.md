# Verifikasi angka terhadap data per sampel

Akar bundel: `C:/Devs/Code/Python/JCCE-First Revision-From Remote`

Data: 38 berkas STIF (9500 baris) dan 20 berkas AAKER (10000 baris), dibaca langsung dari berkas per sampel `evaluated_v2_*_seed42_results.csv`.

Ambang degenerate: PPL > 1000, dihitung ulang dari kolom `fluency_ppl` dan tidak memakai kolom penanda.

| Kode | Periksa | Nilai laporan | Nilai hitung | Status |
|---|---|---|---|---|
| A1 | jumlah berkas evaluasi STIF | 38 | 38.00000 | LULUS |
| A2 | jumlah berkas evaluasi AAKER | 20 | 20.00000 | LULUS |
| A3 | baris per berkas STIF | 250 | 250.00000 | LULUS |
| A4 | baris per berkas AAKER | 500 | 500.00000 | LULUS |
| A5 | jumlah kolom berkas evaluasi | 27 | 27.00000 | LULUS |
| A6 | keluaran berawalan ERROR (STIF) | 0 | 0.00000 | LULUS |
| A7 | keluaran berawalan ERROR (AAKER) | 0 | 0.00000 | LULUS |
| A8 | retrieval_fallback nonzero (STIF) | 0 | 0.00000 | LULUS |
| A9 | retrieval_fallback nonzero (AAKER) | 0 | 0.00000 | LULUS |
| B1 | STIF formal, retrieval, style_accuracy minimum | 0.048 | 0.04800 | LULUS |
| B2 | STIF formal, retrieval, style_accuracy maksimum | 0.252 | 0.25200 | LULUS |
| B3 | STIF formal, zero_shot, style_accuracy | 0.78 | 0.78000 | LULUS |
| B4 | STIF informal, retrieval, style_accuracy minimum | 0.904 | 0.90400 | LULUS |
| B5 | STIF informal, retrieval, style_accuracy maksimum | 0.988 | 0.98800 | LULUS |
| B6 | STIF informal, zero_shot, style_accuracy | 0.136 | 0.13600 | LULUS |
| B7 | STIF formal, zero_shot, median PPL | 39.82 | 39.81710 | LULUS |
| B8 | STIF formal, zero_shot, content_preservation (lama) | 0.5166 | 0.51656 | LULUS |
| B9 | STIF formal, zero_shot, content_preservation_LaBSE | 0.5593 | 0.55928 | LULUS |
| B10 | STIF informal, zero_shot, content_preservation (encoder lama) | 0.5623 | 0.56229 | LULUS |
| B10b | STIF informal, zero_shot, content_preservation_LaBSE | 0.5873 | 0.58732 | LULUS |
| B11 | STIF formal, porsi keluaran diprediksi informal (%) | 82.8 | 82.80000 | LULUS |
| C-formal-a0.1 | STIF formal hybrid a0.1 style_accuracy | 0.192 | 0.19200 | LULUS |
| C-informal-a0.1 | STIF informal hybrid a0.1 style_accuracy | 0.96 | 0.96000 | LULUS |
| C-formal-a0.3 | STIF formal hybrid a0.3 style_accuracy | 0.176 | 0.17600 | LULUS |
| C-informal-a0.3 | STIF informal hybrid a0.3 style_accuracy | 0.984 | 0.98400 | LULUS |
| C-formal-a0.5 | STIF formal hybrid a0.5 style_accuracy | 0.112 | 0.11200 | LULUS |
| C-informal-a0.5 | STIF informal hybrid a0.5 style_accuracy | 0.968 | 0.96800 | LULUS |
| C-formal-a0.7 | STIF formal hybrid a0.7 style_accuracy | 0.152 | 0.15200 | LULUS |
| C-informal-a0.7 | STIF informal hybrid a0.7 style_accuracy | 0.936 | 0.93600 | LULUS |
| C-formal-a0.9 | STIF formal hybrid a0.9 style_accuracy | 0.12 | 0.12000 | LULUS |
| C-informal-a0.9 | STIF informal hybrid a0.9 style_accuracy | 0.96 | 0.96000 | LULUS |
| C-comp-a0.1 | AAKER competence hybrid a0.1 style_accuracy | 0.864 | 0.86400 | LULUS |
| C-exc-a0.1 | AAKER excitement hybrid a0.1 style_accuracy | 0.33 | 0.33000 | LULUS |
| C-comp-a0.3 | AAKER competence hybrid a0.3 style_accuracy | 0.842 | 0.84200 | LULUS |
| C-exc-a0.3 | AAKER excitement hybrid a0.3 style_accuracy | 0.34 | 0.34000 | LULUS |
| C-comp-a0.5 | AAKER competence hybrid a0.5 style_accuracy | 0.514 | 0.51400 | LULUS |
| C-exc-a0.5 | AAKER excitement hybrid a0.5 style_accuracy | 0.3 | 0.30000 | LULUS |
| C-comp-a0.7 | AAKER competence hybrid a0.7 style_accuracy | 0.244 | 0.24400 | LULUS |
| C-exc-a0.7 | AAKER excitement hybrid a0.7 style_accuracy | 0.31 | 0.31000 | LULUS |
| C-comp-a0.9 | AAKER competence hybrid a0.9 style_accuracy | 0.2 | 0.20000 | LULUS |
| C-exc-a0.9 | AAKER excitement hybrid a0.9 style_accuracy | 0.272 | 0.27200 | LULUS |
| C-compIsi-a0.1 | AAKER competence hybrid a0.1 LaBSE | 0.4209 | 0.42089 | LULUS |
| C-compIsi-a0.3 | AAKER competence hybrid a0.3 LaBSE | 0.4974 | 0.49742 | LULUS |
| C-compIsi-a0.5 | AAKER competence hybrid a0.5 LaBSE | 0.6657 | 0.66570 | LULUS |
| C-compIsi-a0.7 | AAKER competence hybrid a0.7 LaBSE | 0.7138 | 0.71375 | LULUS |
| C-compIsi-a0.9 | AAKER competence hybrid a0.9 LaBSE | 0.7189 | 0.71891 | LULUS |
| D-jum-formal | STIF formal jumlah degenerate | 608 | 608.00000 | LULUS |
| D-pct-formal | STIF formal proporsi degenerate (%) | 12.8 | 12.80000 | LULUS |
| D-jum-informal | STIF informal jumlah degenerate | 700 | 700.00000 | LULUS |
| D-pct-informal | STIF informal proporsi degenerate (%) | 14.74 | 14.74000 | LULUS |
| D-m-f-bm25 | STIF formal bm25 proporsi degenerate (%) | 17.0 | 17.00000 | LULUS |
| D-m-i-bm25 | STIF informal bm25 proporsi degenerate (%) | 17.0 | 17.00000 | LULUS |
| D-m-f-centroid | STIF formal centroid proporsi degenerate (%) | 7.6 | 7.60000 | LULUS |
| D-m-i-centroid | STIF informal centroid proporsi degenerate (%) | 8.6 | 8.60000 | LULUS |
| D-m-f-dense | STIF formal dense proporsi degenerate (%) | 16.4 | 16.40000 | LULUS |
| D-m-i-dense | STIF informal dense proporsi degenerate (%) | 15.4 | 15.40000 | LULUS |
| D-m-f-hybrid_early | STIF formal hybrid_early proporsi degenerate (%) | 13.28 | 13.28000 | LULUS |
| D-m-i-hybrid_early | STIF informal hybrid_early proporsi degenerate (%) | 16.56 | 16.56000 | LULUS |
| D-m-f-random | STIF formal random proporsi degenerate (%) | 12.8 | 12.80000 | LULUS |
| D-m-i-random | STIF informal random proporsi degenerate (%) | 15.6 | 15.60000 | LULUS |
| D-m-f-zero_shot | STIF formal zero_shot proporsi degenerate (%) | 2.8 | 2.80000 | LULUS |
| D-m-i-zero_shot | STIF informal zero_shot proporsi degenerate (%) | 1.2 | 1.20000 | LULUS |
| D-aaker | AAKER proporsi degenerate keseluruhan (%) | 5.86 | 5.86000 | LULUS |
| D-aaker-competence | AAKER competence degenerate | 255 | 255.00000 | LULUS |
| D-aaker-pct-competence | AAKER competence proporsi degenerate (%) | 5.1 | 5.10000 | LULUS |
| D-aaker-excitement | AAKER excitement degenerate | 331 | 331.00000 | LULUS |
| D-aaker-pct-excitement | AAKER excitement proporsi degenerate (%) | 6.62 | 6.62000 | LULUS |
| E-med-formal | STIF formal median PPL | 191.45 | 191.45198 | LULUS |
| E-tri-formal | STIF formal trimmed10 PPL | 287.38 | 287.37609 | LULUS |
| E-mea-formal | STIF formal rata-rata PPL | 1436.45 | 1436.44768 | LULUS |
| E-sd-formal | STIF formal sd PPL | 36680.95 | 36680.95151 | LULUS |
| E-max-formal | STIF formal PPL maksimum | 2399765.85 | 2399765.85256 | LULUS |
| E-med-informal | STIF informal median PPL | 226.18 | 226.17715 | LULUS |
| E-tri-informal | STIF informal trimmed10 PPL | 342.27 | 342.26940 | LULUS |
| E-mea-informal | STIF informal rata-rata PPL | 1081.08 | 1081.07709 | LULUS |
| E-sd-informal | STIF informal sd PPL | 11974.31 | 11974.30710 | LULUS |
| E-max-informal | STIF informal PPL maksimum | 755942.67 | 755942.67472 | LULUS |
| F-rep-tabel-formality-formal | formality formal laju replikasi (tabel) | 0.0037 | 0.00375 | LULUS |
| F-rep-tabel-formality-informal | formality informal laju replikasi (tabel) | 0.0079 | 0.00786 | LULUS |
| F-rep-tabel-aaker-competence | aaker competence laju replikasi (tabel) | 0.0911 | 0.09107 | LULUS |
| F-rep-tabel-aaker-excitement | aaker excitement laju replikasi (tabel) | 0.0235 | 0.02346 | LULUS |
| F-rep-kolom-formal | STIF formal laju replikasi (kolom per sampel) | 0.0037 | 0.00318 | TIDAK COCOK (beda 0.00052) |
| F-rep-kolom-informal | STIF informal laju replikasi (kolom per sampel) | 0.0079 | 0.00664 | TIDAK COCOK (beda 0.00126) |
| F-rep-comp-a0.1 | AAKER competence hybrid a0.1 replikasi | 0.3386 | 0.33861 | LULUS |
| F-rep-comp-a0.3 | AAKER competence hybrid a0.3 replikasi | 0.22 | 0.22005 | LULUS |
| F-rep-comp-centroid | AAKER competence centroid replikasi | 0.188 | 0.18799 | LULUS |
| F2-tok-ad-0.1 | output_tokens alpha-dev competence a0.1 | 58.69 | 58.69000 | LULUS |
| F2-tok-ad-0.9 | output_tokens alpha-dev competence a0.9 | 31.61 | 31.61200 | LULUS |
| F-tok-a01 | AAKER competence hybrid a0,1 output_tokens (test set) | 54.09 | 54.08600 | LULUS |
| F-tok-a09 | AAKER competence hybrid a0,9 output_tokens (test set) | 28.52 | 28.51800 | LULUS |
| F-tok-monoton | output_tokens competence menurun monoton | True | True | LULUS |
| G-formality-pasangan | formality pasangan sebanding | 342 | 342.00000 | LULUS |
| G-formality-formal | formality formal jumlah pasangan | 171 | 171.00000 | LULUS |
| G-formality-informal | formality informal jumlah pasangan | 171 | 171.00000 | LULUS |
| G-formality-lintas | formality pasangan lintas target | 0 | 0.00000 | LULUS |
| G-aaker-pasangan | aaker pasangan sebanding | 90 | 90.00000 | LULUS |
| G-aaker-competence | aaker competence jumlah pasangan | 45 | 45.00000 | LULUS |
| G-aaker-excitement | aaker excitement jumlah pasangan | 45 | 45.00000 | LULUS |
| G-aaker-lintas | aaker pasangan lintas target | 0 | 0.00000 | LULUS |
| G-formality-style_accuracy | formality style_accuracy pasangan bermakna | 128 | 128.00000 | LULUS |
| G-aaker-style_accuracy | aaker style_accuracy pasangan bermakna | 66 | 66.00000 | LULUS |
| G-formality-style_strength_calibrated | formality style_strength_calibrated pasangan bermakna | 157 | 157.00000 | LULUS |
| G-aaker-style_strength_calibrated | aaker style_strength_calibrated pasangan bermakna | 70 | 70.00000 | LULUS |
| G-formality-content_preservation | formality content_preservation pasangan bermakna | 230 | 230.00000 | LULUS |
| G-aaker-content_preservation | aaker content_preservation pasangan bermakna | 80 | 80.00000 | LULUS |
| G-formality-content_preservation_LaBSE | formality content_preservation_LaBSE pasangan bermakna | 189 | 189.00000 | LULUS |
| G-aaker-content_preservation_LaBSE | aaker content_preservation_LaBSE pasangan bermakna | 73 | 73.00000 | LULUS |
| G-formality-content_preservation_mE5 | formality content_preservation_mE5 pasangan bermakna | 193 | 193.00000 | LULUS |
| G-aaker-content_preservation_mE5 | aaker content_preservation_mE5 pasangan bermakna | 74 | 74.00000 | LULUS |
| G-formality-replication_rate_8 | formality replication_rate_8 pasangan bermakna | 28 | 28.00000 | LULUS |
| G-aaker-replication_rate_8 | aaker replication_rate_8 pasangan bermakna | 61 | 61.00000 | LULUS |
| I-jumlah-baris | kepekaan k jumlah baris | 108 | 108.00000 | LULUS |
| I-style_accuracy | kepekaan k style_accuracy pasangan bermakna | 1 | 1.00000 | LULUS |
| I-style_accuracy-n | kepekaan k style_accuracy jumlah pasangan | 18 | 18.00000 | LULUS |
| I-style_strength_calibrated | kepekaan k style_strength_calibrated pasangan bermakna | 4 | 4.00000 | LULUS |
| I-style_strength_calibrated-n | kepekaan k style_strength_calibrated jumlah pasangan | 18 | 18.00000 | LULUS |
| I-content_preservation | kepekaan k content_preservation pasangan bermakna | 10 | 10.00000 | LULUS |
| I-content_preservation-n | kepekaan k content_preservation jumlah pasangan | 18 | 18.00000 | LULUS |
| I-content_preservation_LaBSE | kepekaan k content_preservation_LaBSE pasangan bermakna | 3 | 3.00000 | LULUS |
| I-content_preservation_LaBSE-n | kepekaan k content_preservation_LaBSE jumlah pasangan | 18 | 18.00000 | LULUS |
| I-content_preservation_mE5 | kepekaan k content_preservation_mE5 pasangan bermakna | 9 | 9.00000 | LULUS |
| I-content_preservation_mE5-n | kepekaan k content_preservation_mE5 jumlah pasangan | 18 | 18.00000 | LULUS |
| I-replication_rate_8 | kepekaan k replication_rate_8 pasangan bermakna | 2 | 2.00000 | LULUS |
| I-replication_rate_8-n | kepekaan k replication_rate_8 jumlah pasangan | 18 | 18.00000 | LULUS |
| J-alpha-formality-formal | alpha terpilih formality formal | 0.1 | 0.1 | LULUS (catatan) |
| J-alpha-formality-informal | alpha terpilih formality informal | 0.7 | 0.7 | LULUS (catatan) |
| J-alpha-aaker-competence | alpha terpilih aaker competence | 0.3 | 0.3 | LULUS (catatan) |
| J-alpha-aaker-excitement | alpha terpilih aaker excitement | 0.5 | 0.5 | LULUS (catatan) |
| J-cal-formality | kalibrasi formality (periksa manual berkasnya) | 0.97317 lalu 0.97497 | None | LULUS (catatan) |
| J-cal-aaker | kalibrasi aaker (periksa manual berkasnya) | 0.99998 lalu 0.95789 | None | LULUS (catatan) |

Jumlah periksa: 130. Tidak cocok: 2.

Ada angka yang tidak cocok. Periksa daftar di atas sebelum angkanya dipakai pada naskah atau surat balasan.
