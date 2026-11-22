#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cek_paritas_prompt.py
=====================
Memeriksa bahwa templat prompt v2 memenuhi aturan simetri pada
PROTOKOL_PERBAIKAN_R2.md bagian 3.5 dan menghasilkan perbedaan antar kondisi hanya pada
blok "CONTOH REFERENSI".

Empat pemeriksaan:
  1. {target_label} dan {target_definition} muncul pada setiap render.
  2. Tidak ada placeholder yang tersisa setelah penggantian.
  3. Render dengan isi contoh dan render tanpa isi contoh identik setelah isi contoh dihapus.
  4. Bagian templat di luar blok target dan blok contoh identik pada keempat target.

Pemakaian:
    python cek_paritas_prompt.py --template ../04_Rerun_v2/prompts/generation_prompt_v2_id.txt \
        --targets ../04_Rerun_v2/prompts/targets.json

Keluaran yang diharapkan pada templat yang benar:
    OK 4 target, 8 render, 0 temuan

Kode keluar 0 bila nol temuan, 1 bila ada temuan.
"""
import argparse
import json
import os
import re
import sys

SENTINEL = "<<<ISI_EKSEMPLAR>>>"
SOURCE = "Kalimat sumber untuk pemeriksaan."
LABEL_TOKEN = "<TARGET>"


def render(template, label, definition, isi_contoh):
    out = template.replace("{target_label}", label)
    out = out.replace("{target_definition}", definition)
    out = out.replace("{original_message}", SOURCE)
    out = out.replace("{style_examples_str}", isi_contoh)
    return out


def tanpa_isi(teks):
    return teks.replace(SENTINEL, "")


def normal_target(teks, label, definition):
    return teks.replace(label, LABEL_TOKEN).replace(definition, LABEL_TOKEN)


def blok_target(template):
    """Mengembalikan teks blok target, yaitu isi setelah header sampai header berikutnya."""
    header = None
    for kandidat in ("### GAYA TARGET", "### TARGET STYLE"):
        if kandidat in template:
            header = kandidat
            break
    if header is None:
        return None
    lines = template.splitlines()
    mulai = next(i for i, ln in enumerate(lines) if ln.strip() == header)
    isi = []
    for ln in lines[mulai + 1:]:
        if ln.strip().startswith("###"):
            break
        isi.append(ln)
    return header, "\n".join(isi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True, nargs="+", help="satu atau beberapa berkas templat")
    ap.add_argument("--targets", required=True, help="berkas JSON berisi peta target")
    ap.add_argument("--keluaran", default=None)
    args = ap.parse_args()

    data = json.load(open(args.targets, encoding="utf-8"))
    targets = data["targets"] if "targets" in data else data
    temuan = []
    laporan = []
    w = laporan.append

    for path in args.template:
        nama = os.path.basename(path)
        template = open(path, encoding="utf-8").read()
        w(f"\n## Templat `{nama}`\n")
        w(f"- sha256: `{__import__('hashlib').sha256(template.encode('utf-8')).hexdigest()}`")
        w(f"- panjang: {len(template)} karakter")

        blok = blok_target(template)
        if blok is None:
            temuan.append(f"{nama}: header blok target tidak ditemukan (harus '### GAYA TARGET' atau '### TARGET STYLE')")
            w("- header blok target: TIDAK DITEMUKAN")
        else:
            header, isi_blok = blok
            w(f"- header blok target: `{header}`")
            w(f"- isi blok target: {isi_blok.strip()!r}")

        dasar = None
        for nama_target, isi in targets.items():
            label, definisi = isi["label"], isi["definition"]
            r_contoh = render(template, label, definisi, SENTINEL)
            r_kosong = render(template, label, definisi, "")

            # 1. label dan definisi hadir di dalam blok target pada teks yang sudah dirender
            if blok is not None:
                blok_r = blok_target(r_contoh)
                isi_r = blok_r[1] if blok_r else ""
                if label not in isi_r:
                    temuan.append(f"{nama}/{nama_target}: label tidak berada di dalam blok target")
                if definisi not in isi_r:
                    temuan.append(f"{nama}/{nama_target}: definisi tidak berada di dalam blok target")
                if r_contoh.count(definisi) != 1:
                    temuan.append(f"{nama}/{nama_target}: definisi muncul {r_contoh.count(definisi)} kali, seharusnya 1")

            # 2. tidak ada placeholder tersisa
            sisa = re.findall(r"\{[a-z_]+\}", r_contoh)
            if sisa:
                temuan.append(f"{nama}/{nama_target}: placeholder tersisa {sorted(set(sisa))}")

            # 3. paritas kondisi
            if tanpa_isi(r_contoh) != r_kosong:
                temuan.append(f"{nama}/{nama_target}: render dengan dan tanpa contoh berbeda di luar blok contoh")

            # 4. bagian di luar blok target dan contoh sama antar target
            norm = normal_target(tanpa_isi(r_contoh), label, definisi)
            if dasar is None:
                dasar = norm
            elif norm != dasar:
                temuan.append(f"{nama}/{nama_target}: templat berbeda dari target pertama di luar blok target")

            w(f"- {nama_target:11s} label={label!r} panjang_render={len(r_contoh)}")

        # ringkasan per templat
        n_render = 2 * len(targets)
        w(f"- render diperiksa: {n_render}")

    header = [
        "# Hasil pemeriksaan paritas prompt v2",
        "",
        f"Berkas target: `{os.path.basename(args.targets)}`",
        f"Jumlah templat: {len(args.template)}",
    ]
    ekor = [
        "",
        "## Temuan",
        "",
    ]
    if temuan:
        ekor += [f"{i}. {t}" for i, t in enumerate(temuan, 1)]
        ekor += ["", f"GAGAL: {len(temuan)} temuan"]
    else:
        ekor += [f"OK {len(targets)} target, {2 * len(targets) * len(args.template)} render, 0 temuan"]

    teks = "\n".join(header + laporan + ekor) + "\n"
    if args.keluaran:
        with open(args.keluaran, "w", encoding="utf-8") as f:
            f.write(teks)
    print(teks)
    sys.exit(1 if temuan else 0)


if __name__ == "__main__":
    main()
