#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
prompt_utils.py
===============
Perender prompt v2 untuk JCCE-10619 putaran 2. Pustaka standar saja, tanpa torch atau transformers,
sehingga dapat diuji tanpa GPU.

Peran
-----
Templat kanonis memuat empat placeholder: {target_label}, {target_definition},
{style_examples_str}, dan {original_message}. Fungsi render_prompt mengganti keempatnya.

Aturan yang dijaga
------------------
1. Blok GAYA TARGET selalu ada, pada semua kondisi, termasuk zero-shot.
2. Kondisi zero-shot hanya mengosongkan isi blok CONTOH REFERENSI. Header blok tetap ada,
   sehingga satu-satunya perbedaan antar kondisi terletak pada isi blok itu.
3. Definisi target simetris: satu klausa, tiga sifat, tanpa petunjuk leksikal.

Pemakaian di kode generasi
--------------------------
    from prompt_utils import TARGETS, render_prompt
    user_prompt = render_prompt(gen_template, examples_str, orig_msg, TARGETS[personality.lower()])
"""
from __future__ import annotations

import hashlib
import os

DEFAULT_PROMPT_FILE = "generation_prompt_v2_id.txt"
# Varian prompt dibaca dari lingkungan, karena harness memilih L1 atau L2 dan menyetel variabel ini
# saat menjalankan generasi. Nilai bawaan L1 hanya untuk pemakaian di luar harness.
PROMPT_VERSION = os.environ.get("JCCE_PROMPT_VERSION", "v2-L1")

TARGETS = {
    "formal": {
        "label": "Formal",
        "definition": "ragam bahasa Indonesia resmi dan baku",
    },
    "informal": {
        "label": "Informal",
        "definition": "ragam bahasa Indonesia percakapan sehari-hari yang santai",
    },
    "competence": {
        "label": "Competence",
        "definition": "persona merek yang kompeten, kredibel, dan meyakinkan",
    },
    "excitement": {
        "label": "Excitement",
        "definition": "persona merek yang bersemangat, ceria, dan menggugah",
    },
}

REQUIRED_PLACEHOLDERS = ("{target_label}", "{target_definition}",
                         "{style_examples_str}", "{original_message}")


def prompt_file_path(root=".", filename=None):
    """Jalur berkas templat di dalam folder kerja korpus."""
    return os.path.join(root, "prompts", filename or DEFAULT_PROMPT_FILE)


def load_template(root=".", filename=None):
    with open(prompt_file_path(root, filename), encoding="utf-8") as f:
        return f.read()


def sha256_template(template):
    return hashlib.sha256(template.encode("utf-8")).hexdigest()


def check_template(template):
    """Memeriksa kelengkapan templat. Mengembalikan daftar masalah; kosong berarti lolos."""
    masalah = []
    for ph in REQUIRED_PLACEHOLDERS:
        n = template.count(ph)
        if n != 1:
            masalah.append(f"placeholder {ph} muncul {n} kali, seharusnya 1")
    if "### GAYA TARGET" not in template and "### TARGET STYLE" not in template:
        masalah.append("header blok target tidak ditemukan")
    if "{target_label}" not in template:
        masalah.append("templat tidak memuat {target_label}")
    return masalah


def render_prompt(template, examples_str, original_message, target):
    """Merender prompt untuk satu contoh. `target` adalah salah satu isi TARGETS."""
    if "label" not in target or "definition" not in target:
        raise ValueError("target harus memuat label dan definition")
    if examples_str is None:
        examples_str = ""
    return template.format(
        target_label=target["label"],
        target_definition=target["definition"],
        style_examples_str=examples_str,
        original_message=original_message,
    )


def slice_example_block(rendered):
    """Mengembalikan (sebelum, isi, sesudah) untuk blok CONTOH REFERENSI pada prompt terender.

    Dipakai oleh pemeriksa paritas untuk membuktikan bahwa perbedaan antar kondisi hanya
    berada di dalam isi blok ini.
    """
    penanda = ("### CONTOH REFERENSI", "### REFERENCE EXAMPLES")
    header = next((p for p in penanda if p in rendered), None)
    if header is None:
        return rendered, "", ""
    awal = rendered.index(header) + len(header)
    sisa = rendered[awal:]
    akhir_rel = sisa.find("\n### ")
    if akhir_rel == -1:
        return rendered[:awal], rendered[awal:], ""
    akhir = awal + akhir_rel
    return rendered[:awal], rendered[awal:akhir], rendered[akhir:]
