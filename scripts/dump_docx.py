#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dump_docx.py
============
Membuang seluruh isi .docx (paragraf dan tabel) menjadi teks datar dengan penomoran baris,
supaya isinya bisa dicari dengan grep. Read-only terhadap .docx; hanya menulis satu berkas teks.

Pemakaian:
    python dump_docx.py <berkas.docx> [keluaran.txt]
"""
import sys
import zipfile

from docx import Document


def dump(path_docx, path_txt):
    doc = Document(path_docx)
    lines = []

    def walk(body, depth=0):
        for child in body.iterchildren():
            tag = child.tag.split("}")[-1]
            if tag == "p":
                t = "".join(n.text or "" for n in child.iter() if n.tag.endswith("}t"))
                if t.strip():
                    lines.append(t.strip())
            elif tag == "tbl":
                lines.append("<TABEL>")
                for row in child.findall(".//{*}tr"):
                    cells = []
                    for tc in row.findall("{*}tc"):
                        cells.append(" ".join(
                            "".join(n.text or "" for n in p.iter() if n.tag.endswith("}t")).strip()
                            for p in tc.findall("{*}p")).strip())
                    lines.append(" | ".join(cells))
                lines.append("</TABEL>")
            elif tag == "sdt":
                walk(child, depth + 1)
            elif tag in ("sdtContent",):
                walk(child, depth + 1)

    walk(doc.element.body)
    for t in doc.tables:
        pass

    with open(path_txt, "w", encoding="utf-8") as f:
        for i, ln in enumerate(lines, 1):
            f.write(f"{i:5d}| {ln}\n")
    print(f"{len(lines)} baris ditulis ke {path_txt}")
    return lines


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.rsplit(".", 1)[0] + "_dump.txt"
    dump(src, dst)
