"""Menyusun surat balasan reviewer dan tabel status butir dari workbook pemetaan.

Komentar reviewer, nomor butir, dan lokasinya TIDAK ditulis ulang di sini: semuanya dibaca dari
workbook `JCCE-10619_Mapping_Reviewer_Comments_v1.xlsx`, sehingga kutipan pada surat balasan selalu
identik dengan sumber aslinya. Yang ditulis tangan hanya jawabannya, ada di `jawaban_en.py`.

Keluaran:
  SURAT_BALASAN_REVIEWER.md   surat balasan berbahasa Inggris, siap ditempel ke sistem jurnal
  TABEL_STATUS_BUTIR.md       tabel status 38 butir berbahasa Indonesia, untuk laporan internal

Contoh:
    python build_dokumen.py
    python build_dokumen.py --workbook sumber/JCCE-10619_Mapping_Reviewer_Comments_v1.xlsx
"""
import argparse
import os
import sys

import pandas as pd

from jawaban_en import JAWABAN

HERE = os.path.dirname(os.path.abspath(__file__))
JUDUL_BARU = ("Retrieval Strategies for Indonesian Text Style Transfer "
              "using a Large Language Model")

URUTAN_REVIEWER = ["Reviewer 1", "Reviewer 2", "Reviewer 3"]

# Rujukan baru yang ditambahkan pada revisi ini, dipakai menjawab R2-12 dan R3-W2.
# Seluruh entri sudah diperiksa langsung dari PDF-nya; rincian dan kutipannya ada di
# C:\Obsidian\Notes\S3\references\markdown\Few-shot exemplar count\CATATAN_SITASI.md
RUJUKAN_BARU = [
    "Chen, J., Chen, L., Zhu, C., and Zhou, T. (2023). How Many Demonstrations Do You Need for "
    "In-context Learning? In Findings of the Association for Computational Linguistics: EMNLP 2023. "
    "Association for Computational Linguistics.",
    "Liu, J., Shen, D., Zhang, Y., Dolan, B., Carin, L., and Chen, W. (2022). What Makes Good "
    "In-Context Examples for GPT-3? In Proceedings of Deep Learning Inside Out (DeeLIO 2022): The 3rd "
    "Workshop on Knowledge Extraction and Integration for Deep Learning Architectures, pages 100-114. "
    "Association for Computational Linguistics.",
    "Liu, S., Agarwal, S., and May, J. (2024). Authorship Style Transfer with Policy Optimization. "
    "arXiv preprint arXiv:2403.08043.",
    "Lu, Y., Bartolo, M., Moore, A., Riedel, S., and Stenetorp, P. (2022). Fantastically Ordered "
    "Prompts and Where to Find Them: Overcoming Few-Shot Prompt Order Sensitivity. In Proceedings of "
    "the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), "
    "pages 8086-8098. Association for Computational Linguistics.",
    "Min, S., Lyu, X., Holtzman, A., Artetxe, M., Lewis, M., Hajishirzi, H., and Zettlemoyer, L. "
    "(2022). Rethinking the Role of Demonstrations: What Makes In-Context Learning Work? In "
    "Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing. "
    "Association for Computational Linguistics.",
]

LABEL_STATUS = {
    "selesai": "Selesai, bukti ada",
    "menunggu_naskah": "Menunggu penyuntingan naskah",
    "tanpa_tindakan": "Tanpa tindakan",
}


def baca_workbook(path):
    d = pd.read_excel(path, sheet_name="Mapping")
    perlu = ["ID", "Reviewer", "Bagian / Lokasi", "Inti permintaan reviewer",
             "Teks komentar asli (EN)"]
    hilang = [c for c in perlu if c not in d.columns]
    if hilang:
        sys.exit(f"kolom tidak ditemukan pada workbook: {hilang}")
    if len(d) != 38:
        print(f"catatan: workbook memuat {len(d)} baris, bukan 38")
    return d


def surat_balasan(d):
    b = []
    b += ["# Response to Reviewers", "",
          f"**Manuscript:** JCCE-10619", "",
          f"**Revised title:** {JUDUL_BARU}", "",
          "**Revision round:** first", "",
          "---", "",
          "## Summary of the revision", "",
          "We thank the reviewers for comments that changed the paper substantially. In response we "
          "rebuilt both corpora with leakage-free grouped splits, reran the full grid of retrieval "
          "configurations, selected alpha on development data under a criterion fixed in advance, "
          "added two control baselines, calibrated both style classifiers, measured content "
          "preservation with two encoders independent of the retrieval pipeline, and ran pairwise "
          "significance tests with bootstrap confidence intervals on every reported comparison.", "",
          "The rerun also led us to withdraw or narrow three claims from the first version: that the "
          "centroid encodes style, that retrieval improves style transfer in general, and that the "
          "mean perplexity column is interpretable. Style gains now hold for the informal direction "
          "of STIF only, content preservation improves in both directions for every retrieval method, "
          "and fluency is reported with median and trimmed statistics beside the proportion of "
          "degenerate outputs. We also corrected an inconsistency in the fluency computation itself, "
          "where the two corpora had been scored with different language models.", "",
          "The supplementary package contains the split manifests, the leakage gate results, the "
          "per-sample evaluation outputs (58 files, 19,500 items), the twelve significance tables, "
          "the k-sensitivity table, the calibration parameters, and the exported human-evaluation "
          "sample. Numbers quoted below are traceable to those files.", "",
          "---", ""]
    for rev in URUTAN_REVIEWER:
        sub = d[d.Reviewer == rev]
        if not len(sub):
            continue
        b += [f"## {rev}", ""]
        for _, r in sub.iterrows():
            isi = JAWABAN.get(r.ID)
            b += [f"### {r.ID} — {r['Bagian / Lokasi']}", ""]
            kutipan = "\n".join(f"> {t}" if t.strip() else ">"
                                for t in str(r["Teks komentar asli (EN)"]).strip().splitlines())
            b += ["**Comment.**", "", kutipan, ""]
            if isi is None:
                b += ["**Response.** _Belum ditulis._", ""]
            else:
                jawab = " ".join(str(isi["jawab"]).split())
                b += ["**Response.**", "", jawab, ""]
        b += ["---", ""]
    b += ["## Closing", "",
          "We are grateful for the detailed reading both reviewers gave the manuscript, and for the "
          "specific pointers that let us find a genuine inconsistency in our own fluency pipeline. "
          "All changes are marked in the revised manuscript, and every number in this letter is "
          "traceable to a file in the supplementary package.", "",
          "## References added in this revision", "",
          "The following entries respond to the request for supporting citations on the number of "
          "in-context exemplars (R2-12 and R3-W2). Each was verified against the published record; "
          "the preprint is cited as such.", ""]
    for r in RUJUKAN_BARU:
        b += [f"- {r}"]
    b += [""]
    return "\n".join(b)


def tabel_status(d):
    b = ["# Status 38 butir reviewer", "",
         "Status dan jawaban lengkap per butir ada di `SURAT_BALASAN_REVIEWER.md`. Tabel ini untuk",
         "memantau pekerjaan yang tinggal di sisi naskah.", "",
         "| ID | Reviewer | Bagian | Status | Yang diminta |", "|---|---|---|---|---|"]
    kurang = []
    for _, r in d.iterrows():
        isi = JAWABAN.get(r.ID)
        if isi is None:
            kurang.append(r.ID)
            st = "BELUM DITULIS"
        else:
            st = LABEL_STATUS.get(isi["status"], isi["status"])
        b.append(f"| {r.ID} | {r.Reviewer} | {r['Bagian / Lokasi']} | {st} | "
                 f"{str(r['Inti permintaan reviewer'])[:150]} |")
    b += [""]
    jml = {k: sum(1 for v in JAWABAN.values() if v["status"] == k) for k in LABEL_STATUS}
    b += ["## Rekapitulasi", "",
          f"- Total butir pada workbook: {len(d)}",
          f"- Butir yang jawabannya sudah ditulis: {len(JAWABAN)}",
          f"- Selesai dengan bukti pada bundel hasil: {jml.get('selesai', 0)}",
          f"- Menunggu penyuntingan naskah: {jml.get('menunggu_naskah', 0)}",
          f"- Tanpa tindakan, hanya pujian: {jml.get('tanpa_tindakan', 0)}"]
    if kurang:
        b.append(f"- Butir yang belum ditulis jawabannya: {', '.join(kurang)}")
    b += ["", "Butir berstatus menunggu penyuntingan naskah berarti bukti dan keputusannya sudah ada,",
          "tetapi kalimat pada berkas naskah belum diubah. Daftar itu yang harus ditutup sebelum",
          "naskah dikirim ulang.", ""]
    return "\n".join(b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook", default=os.path.join(
        HERE, "sumber", "JCCE-10619_Mapping_Reviewer_Comments_v1.xlsx"))
    args = ap.parse_args()
    if not os.path.exists(args.workbook):
        sys.exit(f"workbook tidak ditemukan: {args.workbook}")
    d = baca_workbook(args.workbook)

    surat = surat_balasan(d)
    with open(os.path.join(HERE, "SURAT_BALASAN_REVIEWER.md"), "w", encoding="utf-8") as f:
        f.write(surat)
    tabel = tabel_status(d)
    with open(os.path.join(HERE, "TABEL_STATUS_BUTIR.md"), "w", encoding="utf-8") as f:
        f.write(tabel)

    kurang = [r.ID for _, r in d.iterrows() if r.ID not in JAWABAN]
    print(f"butir pada workbook      : {len(d)}")
    print(f"jawaban ditulis          : {len(JAWABAN)}")
    print(f"belum ditulis            : {len(kurang)} {kurang if kurang else ''}")
    print(f"SURAT_BALASAN_REVIEWER.md: {len(surat.splitlines())} baris")
    print(f"TABEL_STATUS_BUTIR.md    : {len(tabel.splitlines())} baris")


if __name__ == "__main__":
    main()
