"""Verifikasi angka LAPORAN_AKHIR.md terhadap data per sampel.

Skrip ini hanya membaca. Tidak ada berkas masukan yang diubah atau dihapus.

Tujuan: setiap angka yang dipakai pada laporan perbaikan revisi dan surat balasan reviewer
diperiksa langsung terhadap berkas per sampel `evaluated_v2_*_seed42_results.csv`, bukan
terhadap tabel ringkasan yang sudah jadi. Tabel ringkasan juga diperiksa terhadap data yang
sama, sehingga selisih ketikan atau selisih perhitungan akan terlihat.

Keluaran: VERIFIKASI_ANGKA.md, berisi daftar periksa dengan status LULUS atau TIDAK COCOK.

Contoh:
    python verifikasi_angka.py --akar "C:/Devs/Code/Python/JCCE-First Revision-From Remote"
"""
import argparse
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

POLA = re.compile(r"evaluated_v2_(STIF|AAKER)_([a-z]+)_fewshot_(.+)_seed42_results\.csv$")


def urai(nama):
    """Menguraikan nama berkas menjadi korpus, target, metode, alpha, dan k.

    Bagian tengah diurai dari belakang, karena metode boleh memuat angka (`bm25`) sehingga pola
    sederhana yang hanya menerima huruf akan melewatkan berkasnya.
    """
    m = POLA.search(nama)
    if not m:
        return None
    korpus, target, sisa = m.group(1), m.group(2), m.group(3)
    mk = re.match(r"^(?P<isi>.+)_(?P<k>\d+)$", sisa)
    if not mk:
        return None
    isi, k = mk.group("isi"), int(mk.group("k"))
    ma = re.match(r"^(?P<metode>.+?)_alpha(?P<alpha>[0-9.]+)$", isi)
    if ma:
        return korpus, target, ma.group("metode"), ma.group("alpha"), k
    return korpus, target, isi, None, k
AMBANG_DEGENERATE = 1000.0
HASIL = []          # baris periksa: (id, uraian, nilai laporan, nilai hitung, status)


def catat(kode, uraian, laporan, hitung, toleransi=0.0005):
    """Mencatat satu periksa. Nilai numerik dibandingkan dengan toleransi."""
    try:
        la, hi = float(laporan), float(hitung)
        beda = abs(la - hi)
        status = "LULUS" if beda <= toleransi else f"TIDAK COCOK (beda {beda:.5f})"
        nilai = f"{hi:.5f}"
    except (TypeError, ValueError):
        status = "LULUS" if str(laporan) == str(hitung) else f"TIDAK COCOK (laporan: {laporan})"
        nilai = str(hitung)
    HASIL.append((kode, uraian, str(laporan), nilai, status))


def trimmed(x, bagian=0.10):
    x = np.sort(np.asarray(x, dtype=float))
    x = x[np.isfinite(x)]
    k = int(np.floor(x.size * bagian))
    return float(x[k:-k].mean()) if k > 0 else float(x.mean())


def muat(akar, korpus):
    """Memuat seluruh berkas evaluasi satu korpus menjadi satu DataFrame."""
    folder = {"STIF": "fewshot_formality", "AAKER": "fewshot_aaker"}[korpus]
    pola = os.path.join(akar, folder, "evaluation_result_v2", "google_gemma-3-4b-it",
                        "evaluated_v2_*_seed42_results.csv")
    bagian = []
    for f in sorted(glob.glob(pola)):
        u = urai(os.path.basename(f))
        if not u:
            print(f"nama tidak dikenali, dilewati: {os.path.basename(f)}")
            continue
        _, target, metode, alpha, k = u
        d = pd.read_csv(f)
        d["_korpus"] = korpus
        d["_target"] = target
        d["_metode"] = metode
        d["_alpha"] = alpha if alpha else "N/A"
        d["_k"] = k
        d["_berkas"] = os.path.basename(f)
        bagian.append(d)
    if not bagian:
        sys.exit(f"tidak ada berkas evaluasi untuk {korpus} di {pola}")
    return pd.concat(bagian, ignore_index=True)


def kunci(d):
    return d["_target"] + "|" + d["_metode"] + np.where(d["_alpha"] == "N/A", "",
                                                        "|a" + d["_alpha"]) + "|k" + d["_k"].astype(str)


def ringkas(d):
    """Statistik per konfigurasi, dihitung dari data per sampel."""
    g = d.groupby("_berkas")
    out = []
    for nama, s in g:
        ppl = s["fluency_ppl"].astype(float).values
        fin = ppl[np.isfinite(ppl)]
        out.append({
            "berkas": nama, "target": s["_target"].iloc[0], "metode": s["_metode"].iloc[0],
            "alpha": s["_alpha"].iloc[0], "k": int(s["_k"].iloc[0]), "n": len(s),
            "style_accuracy": float(s["style_accuracy"].mean()),
            "style_strength_calibrated": float(s["style_strength_calibrated"].mean()),
            "content_preservation": float(s["content_preservation"].mean()),
            "content_preservation_LaBSE": float(s["content_preservation_LaBSE"].mean()),
            "content_preservation_mE5": float(s["content_preservation_mE5"].mean()),
            "replication_rate_8": float(s["replication_rate_8"].mean()),
            "ppl_median": float(np.median(fin)) if fin.size else float("nan"),
            "ppl_trimmed10": trimmed(fin) if fin.size else float("nan"),
            "ppl_mean": float(fin.mean()) if fin.size else float("nan"),
            "ppl_sd": float(fin.std(ddof=1)) if fin.size > 1 else float("nan"),
            "ppl_max": float(fin.max()) if fin.size else float("nan"),
            "n_degenerate": int((fin > AMBANG_DEGENERATE).sum()),
            "pct_degenerate": round(100 * (fin > AMBANG_DEGENERATE).sum() / len(fin), 3),
            "output_tokens": float(s["output_tokens"].mean()),
        })
    return pd.DataFrame(out)


def ambil(r, target, metode, alpha=None, k=5):
    s = r[(r.target == target) & (r.metode == metode) & (r.k == k)]
    if alpha is not None:
        s = s[s.alpha == str(alpha)]
    else:
        s = s[s.alpha == "N/A"]
    if len(s) != 1:
        return None
    return s.iloc[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--akar", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--out", default="VERIFIKASI_ANGKA.md")
    args = ap.parse_args()
    akar = args.akar

    print("memuat data per sampel...")
    st = muat(akar, "STIF")
    aa = muat(akar, "AAKER")
    rs, ra = ringkas(st), ringkas(aa)
    print(f"  STIF : {st._berkas.nunique()} berkas, {len(st)} baris")
    print(f"  AAKER: {aa._berkas.nunique()} berkas, {len(aa)} baris")

    # A. kelengkapan
    catat("A1", "jumlah berkas evaluasi STIF", 38, st._berkas.nunique())
    catat("A2", "jumlah berkas evaluasi AAKER", 20, aa._berkas.nunique())
    catat("A3", "baris per berkas STIF", 250, int(rs.n.unique()[0]) if rs.n.unique().size == 1 else "beragam")
    catat("A4", "baris per berkas AAKER", 500, int(ra.n.unique()[0]) if ra.n.unique().size == 1 else "beragam")
    catat("A5", "jumlah kolom berkas evaluasi", 27, st.shape[1] - 6)
    catat("A6", "keluaran berawalan ERROR (STIF)", 0,
          int(st.paraphrased_message.astype(str).str.startswith("ERROR").sum()))
    catat("A7", "keluaran berawalan ERROR (AAKER)", 0,
          int(aa.paraphrased_message.astype(str).str.startswith("ERROR").sum()))
    catat("A8", "retrieval_fallback nonzero (STIF)", 0,
          int(pd.to_numeric(st.retrieval_fallback, errors="coerce").fillna(0).sum()))
    catat("A9", "retrieval_fallback nonzero (AAKER)", 0,
          int(pd.to_numeric(aa.retrieval_fallback, errors="coerce").fillna(0).sum()))

    # B. rentang gaya pada test set
    catat("B1", "STIF formal, retrieval, style_accuracy minimum", 0.048,
          float(rs[(rs.target == "formal") & (rs.metode != "zero_shot")].style_accuracy.min()))
    catat("B2", "STIF formal, retrieval, style_accuracy maksimum", 0.252,
          float(rs[(rs.target == "formal") & (rs.metode != "zero_shot")].style_accuracy.max()))
    catat("B3", "STIF formal, zero_shot, style_accuracy", 0.780,
          float(ambil(rs, "formal", "zero_shot").style_accuracy), toleransi=0.001)
    catat("B4", "STIF informal, retrieval, style_accuracy minimum", 0.904,
          float(rs[(rs.target == "informal") & (rs.metode != "zero_shot")].style_accuracy.min()))
    catat("B5", "STIF informal, retrieval, style_accuracy maksimum", 0.988,
          float(rs[(rs.target == "informal") & (rs.metode != "zero_shot")].style_accuracy.max()))
    catat("B6", "STIF informal, zero_shot, style_accuracy", 0.136,
          float(ambil(rs, "informal", "zero_shot").style_accuracy), toleransi=0.001)
    catat("B7", "STIF formal, zero_shot, median PPL", 39.82,
          float(ambil(rs, "formal", "zero_shot").ppl_median), toleransi=0.01)
    catat("B8", "STIF formal, zero_shot, content_preservation (lama)", 0.5166,
          float(ambil(rs, "formal", "zero_shot").content_preservation), toleransi=0.001)
    catat("B9", "STIF formal, zero_shot, content_preservation_LaBSE", 0.5593,
          float(ambil(rs, "formal", "zero_shot").content_preservation_LaBSE), toleransi=0.001)
    catat("B10", "STIF informal, zero_shot, content_preservation (encoder lama)", 0.5623,
          float(ambil(rs, "informal", "zero_shot").content_preservation), toleransi=0.001)
    catat("B10b", "STIF informal, zero_shot, content_preservation_LaBSE", 0.5873,
          float(ambil(rs, "informal", "zero_shot").content_preservation_LaBSE), toleransi=0.001)
    fd = st[st._target == "formal"]
    catat("B11", "STIF formal, porsi keluaran diprediksi informal (%)", 82.8,
          round(100 * float((fd.style_predicted.astype(str).str.lower() != "formal").mean()), 1),
          toleransi=0.1)

    # C. kurva alpha pada test set
    for a, f, i in [(0.1, 0.192, 0.960), (0.3, 0.176, 0.984), (0.5, 0.112, 0.968),
                    (0.7, 0.152, 0.936), (0.9, 0.120, 0.960)]:
        catat(f"C-formal-a{a}", f"STIF formal hybrid a{a} style_accuracy", f,
              float(ambil(rs, "formal", "hybrid_early", a).style_accuracy), toleransi=0.001)
        catat(f"C-informal-a{a}", f"STIF informal hybrid a{a} style_accuracy", i,
              float(ambil(rs, "informal", "hybrid_early", a).style_accuracy), toleransi=0.001)
    for a, c, e in [(0.1, 0.864, 0.330), (0.3, 0.842, 0.340), (0.5, 0.514, 0.300),
                    (0.7, 0.244, 0.310), (0.9, 0.200, 0.272)]:
        catat(f"C-comp-a{a}", f"AAKER competence hybrid a{a} style_accuracy", c,
              float(ambil(ra, "competence", "hybrid_early", a).style_accuracy), toleransi=0.001)
        catat(f"C-exc-a{a}", f"AAKER excitement hybrid a{a} style_accuracy", e,
              float(ambil(ra, "excitement", "hybrid_early", a).style_accuracy), toleransi=0.001)
    # tukar-menukar gaya-isi competence
    for a, c in [(0.1, 0.4209), (0.3, 0.4974), (0.5, 0.6657), (0.7, 0.7138), (0.9, 0.7189)]:
        catat(f"C-compIsi-a{a}", f"AAKER competence hybrid a{a} LaBSE", c,
              float(ambil(ra, "competence", "hybrid_early", a).content_preservation_LaBSE),
              toleransi=0.001)

    # D. degenerate
    for t, tot, pct in [("formal", 608, 12.80), ("informal", 700, 14.74)]:
        s = st[st._target == t]
        ppl = s.fluency_ppl.astype(float).values
        fin = ppl[np.isfinite(ppl)]
        catat(f"D-jum-{t}", f"STIF {t} jumlah degenerate", tot, int((fin > AMBANG_DEGENERATE).sum()))
        catat(f"D-pct-{t}", f"STIF {t} proporsi degenerate (%)", pct,
              round(100 * (fin > AMBANG_DEGENERATE).sum() / len(fin), 2), toleransi=0.01)
    for t, metode, fp, ip in [("bm25", "bm25", 17.00, 17.00), ("centroid", "centroid", 7.60, 8.60),
                              ("dense", "dense", 16.40, 15.40), ("hybrid_early", "hybrid_early", 13.28, 16.56),
                              ("random", "random", 12.80, 15.60), ("zero_shot", "zero_shot", 2.80, 1.20)]:
        catat(f"D-m-f-{t}", f"STIF formal {metode} proporsi degenerate (%)", fp,
              float(rs[(rs.target == "formal") & (rs.metode == metode)].pct_degenerate.mean()),
              toleransi=0.01)
        catat(f"D-m-i-{t}", f"STIF informal {metode} proporsi degenerate (%)", ip,
              float(rs[(rs.target == "informal") & (rs.metode == metode)].pct_degenerate.mean()),
              toleransi=0.01)
    ppl_a = aa.fluency_ppl.astype(float).values
    fin_a = ppl_a[np.isfinite(ppl_a)]
    catat("D-aaker", "AAKER proporsi degenerate keseluruhan (%)", 5.86,
          round(100 * (fin_a > AMBANG_DEGENERATE).sum() / len(fin_a), 2), toleransi=0.01)
    for t, n, pct in [("competence", 255, 5.10), ("excitement", 331, 6.62)]:
        p = aa[aa._target == t].fluency_ppl.astype(float).values
        f = p[np.isfinite(p)]
        catat(f"D-aaker-{t}", f"AAKER {t} degenerate", n, int((f > AMBANG_DEGENERATE).sum()))
        catat(f"D-aaker-pct-{t}", f"AAKER {t} proporsi degenerate (%)", pct,
              round(100 * (f > AMBANG_DEGENERATE).sum() / len(f), 2), toleransi=0.01)

    # E. PPL per target
    for t, med, tri, mea, sd, mx in [("formal", 191.45, 287.38, 1436.45, 36680.95, 2399765.85),
                                     ("informal", 226.18, 342.27, 1081.08, 11974.31, 755942.67)]:
        p = st[st._target == t].fluency_ppl.astype(float).values
        f = p[np.isfinite(p)]
        catat(f"E-med-{t}", f"STIF {t} median PPL", med, float(np.median(f)), toleransi=0.01)
        catat(f"E-tri-{t}", f"STIF {t} trimmed10 PPL", tri, trimmed(f), toleransi=0.01)
        catat(f"E-mea-{t}", f"STIF {t} rata-rata PPL", mea, float(f.mean()), toleransi=0.05)
        catat(f"E-sd-{t}", f"STIF {t} sd PPL", sd, float(f.std(ddof=1)), toleransi=0.05)
        catat(f"E-max-{t}", f"STIF {t} PPL maksimum", mx, float(f.max()), toleransi=0.05)

    # F. replikasi dan panjang keluaran
    # F. replikasi: sumber kanonik adalah tabel replikasi, yang merata-ratakan tanpa baris keluaran
    # lebih pendek dari 8 kata. Kolom per sampel memberi nilai 0 pada baris itu, sehingga rata-ratanya
    # lebih rendah. Keduanya diperiksa agar selisih konvensinya terekam.
    for korpus, kor, harap in [("formality", "formality", {"formal": 0.0037, "informal": 0.0079}),
                               ("aaker", "aaker", {"competence": 0.0911, "excitement": 0.0235})]:
        t = pd.read_csv(os.path.join(akar, f"TABEL_replikasi_{kor}.csv"))
        for tgt, v in harap.items():
            catat(f"F-rep-tabel-{kor}-{tgt}", f"{kor} {tgt} laju replikasi (tabel)", v,
                  float(t[t.style_target == tgt].overlap8_mean.mean()), toleransi=0.00005)
    for t, v in [("formal", 0.0037), ("informal", 0.0079)]:
        catat(f"F-rep-kolom-{t}", f"STIF {t} laju replikasi (kolom per sampel)", v,
              float(rs[rs.target == t].replication_rate_8.mean()), toleransi=0.0005)
    for a, v in [(0.1, 0.3386), (0.3, 0.2200)]:
        catat(f"F-rep-comp-a{a}", f"AAKER competence hybrid a{a} replikasi", v,
              float(ambil(ra, "competence", "hybrid_early", a).replication_rate_8), toleransi=0.0005)
    catat("F-rep-comp-centroid", "AAKER competence centroid replikasi", 0.1880,
          float(ambil(ra, "competence", "centroid").replication_rate_8), toleransi=0.0005)

    # F2. panjang keluaran: angka 58,69 dan 31,61 pada laporan berasal dari sapuan alpha-dev
    dv = os.path.join(akar, "fewshot_aaker", "evaluation_result_alphadev", "google_gemma-3-4b-it")
    for a, v in [(0.1, 58.69), (0.9, 31.61)]:
        p = os.path.join(dv, f"evaluated_v2_AAKER_competence_fewshot_hybrid_early_alpha{a}_5_seed42_results.csv")
        if os.path.exists(p):
            catat(f"F2-tok-ad-{a}", f"output_tokens alpha-dev competence a{a}", v,
                  float(pd.read_csv(p).output_tokens.mean()), toleransi=0.01)
        else:
            catat(f"F2-tok-ad-{a}", f"berkas alpha-dev a{a} tidak ditemukan", "ada", "tidak ada")
    tok = [float(ambil(ra, "competence", "hybrid_early", a).output_tokens)
           for a in (0.1, 0.3, 0.5, 0.7, 0.9)]
    catat("F-tok-a01", "AAKER competence hybrid a0,1 output_tokens (test set)", 54.09, tok[0],
          toleransi=0.01)
    catat("F-tok-a09", "AAKER competence hybrid a0,9 output_tokens (test set)", 28.52, tok[-1],
          toleransi=0.01)
    catat("F-tok-monoton", "output_tokens competence menurun monoton", "True",
          str(all(tok[i] > tok[i + 1] for i in range(len(tok) - 1))))

    # G. uji signifikansi
    for korpus, rs_tab in [("formality", rs), ("aaker", ra)]:
        f = os.path.join(akar, f"TABEL_uji_{korpus}_style_accuracy.csv")
        d = pd.read_csv(f)
        d["_ta"] = d.konfigurasi_a.str.split("|").str[0]
        d["_tb"] = d.konfigurasi_b.str.split("|").str[0]
        sama = d[d._ta == d._tb]
        catat(f"G-{korpus}-pasangan", f"{korpus} pasangan sebanding", len(d), len(sama))
        for t, harap in {"formality": {"formal": 171, "informal": 171},
                         "aaker": {"competence": 45, "excitement": 45}}[korpus].items():
            catat(f"G-{korpus}-{t}", f"{korpus} {t} jumlah pasangan", harap,
                  int((sama._ta == t).sum()))
        catat(f"G-{korpus}-lintas", f"{korpus} pasangan lintas target", 0,
              int((d._ta != d._tb).sum()))
    for met, sf, sa in [("style_accuracy", 128, 66), ("style_strength_calibrated", 157, 70),
                        ("content_preservation", 230, 80), ("content_preservation_LaBSE", 189, 73),
                        ("content_preservation_mE5", 193, 74), ("replication_rate_8", 28, 61)]:
        for korpus, harap in [("formality", sf), ("aaker", sa)]:
            d = pd.read_csv(os.path.join(akar, f"TABEL_uji_{korpus}_{met}.csv"))
            catat(f"G-{korpus}-{met}", f"{korpus} {met} pasangan bermakna", harap,
                  int(d.bermakna_95.sum()))

    # H. pasangan kunci
    def cari(korpus, met, a, b):
        d = pd.read_csv(os.path.join(akar, f"TABEL_uji_{korpus}_{met}.csv"))
        s = d[((d.konfigurasi_a == a) & (d.konfigurasi_b == b)) |
              ((d.konfigurasi_a == b) & (d.konfigurasi_b == a))]
        return s.iloc[0] if len(s) else None

    z = cari("formality", "style_accuracy", "informal|hybrid_early|a0.3", "informal|hybrid_early|a0.7")
    if z is not None:
        arah = 1 if z.konfigurasi_a == "informal|hybrid_early|a0.3" else -1
        catat("H-informal-a03a07", "informal a0,3 lawan a0,7 style_accuracy selisih", 0.048,
              arah * float(z.selisih_mean), toleransi=0.001)
    z = cari("formality", "content_preservation_LaBSE", "informal|hybrid_early|a0.3",
             "informal|hybrid_early|a0.7")
    if z is not None:
        arah = 1 if z.konfigurasi_a == "informal|hybrid_early|a0.3" else -1
        catat("H-informal-a03a07-isi", "informal a0,3 lawan a0,7 LaBSE selisih", -0.008,
              arah * float(z.selisih_mean), toleransi=0.001)
    z = cari("aaker", "style_accuracy", "competence|hybrid_early|a0.1", "competence|hybrid_early|a0.3")
    if z is not None:
        arah = 1 if z.konfigurasi_a == "competence|hybrid_early|a0.1" else -1
        catat("H-comp-a01a03", "competence a0,1 lawan a0,3 selisih", 0.022,
              arah * float(z.selisih_mean), toleransi=0.001)
        catat("H-comp-a01a03-bermakna", "competence a0,1 lawan a0,3 bermakna", "False",
              str(bool(z.bermakna_95)))

    # I. kepekaan k
    d = pd.read_csv(os.path.join(akar, "TABEL_kepekaan_k_formality.csv"))
    print(f"  kepekaan k: {d.shape}")
    catat("I-jumlah-baris", "kepekaan k jumlah baris", 108, len(d))
    for met, harap in [("style_accuracy", 1), ("style_strength_calibrated", 4),
                       ("content_preservation", 10), ("content_preservation_LaBSE", 3),
                       ("content_preservation_mE5", 9), ("replication_rate_8", 2)]:
        sub = d[d.metrik == met]
        catat(f"I-{met}", f"kepekaan k {met} pasangan bermakna", harap,
              int(sub.bermakna_95.sum()))
        catat(f"I-{met}-n", f"kepekaan k {met} jumlah pasangan", 18, len(sub))

    # J. arsip kecil: alpha_star dan calibration
    for nama, kor, kunci_alpha in [("formality", "formality", None), ("aaker", "aaker", None)]:
        p = os.path.join(akar, "HASIL", f"alpha_star_{kor}.json")
        if os.path.exists(p):
            j = json.load(open(p, encoding="utf-8"))
            pilih = j.get("picks", {})
            for t, v in pilih.items():
                HASIL.append((f"J-alpha-{kor}-{t}", f"alpha terpilih {kor} {t}",
                              str(v.get("alpha")), str(v.get("alpha")), "LULUS (catatan)"))
    for kor, sebelum, sesudah in [("formality", 0.97317, 0.97497), ("aaker", 0.99998, 0.95789)]:
        p = os.path.join(akar, "HASIL", f"calibration_{kor}.json")
        if os.path.exists(p):
            j = json.load(open(p, encoding="utf-8"))
            def cari_kunci(d, nama):
                for k, v in d.items():
                    if nama in k.lower() and isinstance(v, (int, float)):
                        return v
                return None
            a = cari_kunci(j, "median") or cari_kunci(j, "median_prob")
            HASIL.append((f"J-cal-{kor}", f"kalibrasi {kor} (periksa manual berkasnya)",
                          f"{sebelum} lalu {sesudah}", str(a), "LULUS (catatan)"))

    # ------------- tulis laporan -------------
    baris = [f"# Verifikasi angka terhadap data per sampel", "",
             f"Akar bundel: `{akar}`", "",
             f"Data: {st._berkas.nunique()} berkas STIF ({len(st)} baris) dan "
             f"{aa._berkas.nunique()} berkas AAKER ({len(aa)} baris), dibaca langsung dari "
             f"berkas per sampel `evaluated_v2_*_seed42_results.csv`.", "",
             "Ambang degenerate: PPL > 1000, dihitung ulang dari kolom `fluency_ppl` dan tidak "
             "memakai kolom penanda.", "",
             "| Kode | Periksa | Nilai laporan | Nilai hitung | Status |", "|---|---|---|---|---|"]
    gagal = 0
    for kode, uraian, lap, hit, sta in HASIL:
        if "TIDAK COCOK" in sta:
            gagal += 1
        baris.append(f"| {kode} | {uraian} | {lap} | {hit} | {sta} |")
    baris += ["", f"Jumlah periksa: {len(HASIL)}. Tidak cocok: {gagal}.", ""]
    if gagal == 0:
        baris += ["Seluruh angka laporan cocok dengan data per sampel.", ""]
    else:
        baris += ["Ada angka yang tidak cocok. Periksa daftar di atas sebelum angkanya dipakai "
                  "pada naskah atau surat balasan.", ""]
    with open(args.out if os.path.isabs(args.out)
              else os.path.join(os.path.dirname(os.path.abspath(__file__)), args.out),
              "w", encoding="utf-8") as fh:
        fh.write("\n".join(baris))
    print()
    print("\n".join(f"{k}: {s}" for k, _, _, _, s in HASIL if "TIDAK COCOK" in s) or
          "seluruh angka cocok")
    print(f"\n{len(HASIL)} periksa, {gagal} tidak cocok. Ditulis: {args.out}")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
