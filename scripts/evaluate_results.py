#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluate_results.py
===================
Pipeline evaluasi versi baru untuk hasil generasi few-shot.

Menggantikan eval.py lama dengan empat perbaikan yang diminta reviewer:

1. Content preservation dihitung dengan encoder yang BERBEDA dari encoder
   retrieval (R2-08). Encoder lama memakai LazarusNLP/simcse-indobert-base,
   yaitu model yang sama dengan encoder retrieval, sehingga metode dense
   diuntungkan secara konstruksi. Kolom lama tetap dihitung agar besarnya
   perbedaan dapat dilihat pembaca.
2. Style strength dilaporkan bersama probabilitas terkalibrasi dan akurasi
   biner (R2-10, R3-W3).
3. Fluency dilaporkan sebagai PPL per sampel; median, trimmed mean, dan
   proporsi degenerate dihitung oleh report_metrics.py (R2-21, R3-W5).
4. Laju replikasi templat dihitung dari kolom retrieved_exemplars (R2-03, R2-09).

Keluaran
--------
Untuk setiap berkas `<nama>_results.csv` di folder hasil, ditulis
`evaluated_v2_<nama>_results.csv` ke folder keluaran, dengan kolom:
    content_preservation            encoder lama (pembanding)
    content_preservation_<tag>      satu kolom per encoder independen
    style_strength                  probabilitas mentah kelas target
    style_strength_calibrated       probabilitas setelah temperature scaling
    style_accuracy                  benar atau tidaknya kelas target diprediksi
    fluency_ppl                     perplexity per sampel
    replication_rate_8              overlap n-gram dengan eksemplar terambil
    output_tokens, eos_reached      diagnostik degenerasi

Pemakaian
---------
    python evaluate_results.py \
        --results ../fewshot_aaker/model_results_dir/google_gemma-3-4b-it \
        --classifier ../fewshot_aaker/style_classifier \
        --out ../fewshot_aaker/evaluation_result_v2/google_gemma-3-4b-it \
        --encoder LaBSE=sentence-transformers/LaBSE \
        --encoder mE5=intfloat/multilingual-e5-base \
        --legacy-encoder LazarusNLP/simcse-indobert-base \
        --calibration ../fewshot_aaker/style_classifier/calibration.json

Catatan: script ini memerlukan GPU atau CPU dengan RAM memadai. Model dimuat
satu per satu lalu dilepas untuk menghemat memori.
"""
import argparse
import gc
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import torch

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    TRANSFORMERS_TERSEDIA = True
except ImportError:
    AutoModelForSequenceClassification = AutoTokenizer = None
    TRANSFORMERS_TERSEDIA = False


def butuh_transformers():
    """Dipanggil di tempat yang benar-benar memerlukan transformers.

    Pemeriksaan dijadikan malas, bukan saat impor modul, supaya jalur yang tidak memerlukan model
    tetap dapat dijalankan dan diuji, misalnya pemeriksaan argumen dan mode --only-fluency pada
    mesin tanpa transformers.
    """
    if not TRANSFORMERS_TERSEDIA:
        sys.exit("transformers belum terpasang: pip install transformers")


try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

NGRAM = 8


def clean_tag(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


def ngrams(text, n=NGRAM):
    w = re.findall(r"\w+", str(text).lower())
    return set(tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1)))


class StyleClassifier:
    def __init__(self, model_dir, temperature=None):
        butuh_transformers()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(self.device)
        self.model.eval()
        self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}
        self.label2id = {v: int(k) for k, v in self.id2label.items()}
        self.T = float(temperature) if temperature else 1.0

    def predict(self, texts, batch_size=32, max_length=128):
        probs_target, preds, correct = [], [], []
        for i in range(0, len(texts), batch_size):
            batch = [str(t) for t in texts[i:i + batch_size]]
            enc = self.tok(batch, return_tensors="pt", padding=True, truncation=True,
                           max_length=max_length).to(self.device)
            with torch.no_grad():
                logits = self.model(**enc).logits
            raw = torch.nn.functional.softmax(logits, dim=-1)
            cal = torch.nn.functional.softmax(logits / self.T, dim=-1)
            probs_target.append(cal.cpu().numpy())
            preds.append(torch.argmax(raw, dim=-1).cpu().numpy())
        return np.vstack(probs_target), np.concatenate(preds)

    def release(self):
        del self.model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class Fluency:
    """Perplexity dari model bahasa kausal, sama seperti eval.py lama."""

    def __init__(self, model_id="Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct"):
        from transformers import AutoModelForCausalLM, BitsAndBytesConfig
        bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_use_double_quant=True,
                                 bnb_4bit_quant_type="nf4",
                                 bnb_4bit_compute_dtype=torch.float16)
        self.tok = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, quantization_config=bnb, device_map="auto", low_cpu_mem_usage=True)
        self.model.eval()
        self.limit = getattr(self.model.config, "max_position_embeddings", 8192)

    def ppl(self, text):
        if not isinstance(text, str) or not text.strip():
            return float("nan"), 0
        enc = self.tok(text, return_tensors="pt", truncation=True,
                       max_length=self.limit).to(self.model.device)
        ids = enc["input_ids"]
        with torch.no_grad():
            out = self.model(ids, labels=ids)
        return float(np.exp(out.loss.item())), int(ids.shape[1])

    def release(self):
        del self.model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def content_similarity(model, a, b):
    ea = model.encode(a, convert_to_tensor=True, show_progress_bar=False,
                      batch_size=64, normalize_embeddings=True)
    eb = model.encode(b, convert_to_tensor=True, show_progress_bar=False,
                      batch_size=64, normalize_embeddings=True)
    return (ea * eb).sum(dim=1).cpu().numpy().tolist()


def sudah_ada_fluency(path):
    """Benar bila berkas evaluasi sudah memuat kolom fluency_ppl yang terisi seluruhnya."""
    try:
        kolom = pd.read_csv(path, usecols=["fluency_ppl"])
    except Exception:
        return False
    return bool(len(kolom)) and bool(kolom["fluency_ppl"].notna().all())


def hanya_fluency(args):
    """Menambahkan kolom fluency pada berkas evaluasi yang sudah ada.

    Dipisahkan dari alur utama supaya puncak pemakaian memori hanya berasal dari model fluency,
    bukan model fluency bersama classifier dan encoder sekaligus. Dipakai bila evaluasi penuh
    kehabisan memori pada kartu grafis kecil.
    """
    import glob

    files = sorted(glob.glob(os.path.join(args.out, "evaluated_*.csv")))
    files = [f for f in files if not os.path.basename(f).endswith("_HUMAN_EVAL.csv")]
    if not files:
        sys.exit(f"tidak ada berkas evaluated_*.csv di {args.out}. Jalankan evaluasi penuh dengan "
                 f"--skip-fluency lebih dulu, lalu ulangi dengan --only-fluency")
    belum = [f for f in files if not sudah_ada_fluency(f)]
    print(f"{len(belum)} dari {len(files)} berkas perlu dihitung fluency-nya")
    if not belum:
        print("seluruh berkas sudah memuat fluency_ppl, tidak ada yang dikerjakan")
        return 0

    print(f"model fluency: {args.fluency_model}")
    try:
        flu = Fluency(args.fluency_model)
    except Exception as e:
        sys.exit(f"gagal memuat model fluency {args.fluency_model}: {e}")

    for f in belum:
        df = pd.read_csv(f)
        if args.limit:
            df = df.head(args.limit).copy()
        outputs = df["paraphrased_message"].astype(str).tolist()
        ppl, ntokens = [], []
        for t in outputs:
            p, n = flu.ppl(t)
            ppl.append(p)
            ntokens.append(n)
        df["fluency_ppl"] = ppl
        df["output_tokens"] = ntokens
        df["eos_reached"] = [bool(re.search(r'[.!?"\u201d]\s*$', t.strip())) for t in outputs]
        df["ppl_degenerate"] = [bool(np.isfinite(p) and p > 1000) for p in ppl]
        df.to_csv(f, index=False)
        med = float(np.nanmedian(ppl)) if ppl else float("nan")
        degen = int(np.nansum([p > 1000 for p in ppl if np.isfinite(p)]))
        print(f"  {os.path.basename(f)}: median PPL {med:.2f}, degenerate {degen}/{len(ppl)}")

    print(f"selesai: kolom fluency_ppl, output_tokens, eos_reached, dan ppl_degenerate ditulis ke "
          f"{len(belum)} berkas di {args.out}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=None, help="folder berisi *_results.csv")
    ap.add_argument("--classifier", default=None, help="folder style_classifier")
    ap.add_argument("--out", required=True)
    ap.add_argument("--encoder", action="append", default=[],
                    help="TAG=model_id untuk encoder independen, boleh diulang")
    ap.add_argument("--legacy-encoder", default="LazarusNLP/simcse-indobert-base",
                    help="encoder lama, dihitung sebagai pembanding")
    ap.add_argument("--calibration", default=None, help="berkas calibration.json")
    ap.add_argument("--fluency-model", default="Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct",
                    help="model untuk perplexity. Wajib sama dengan yang dipakai naskah dan "
                         "fewshot_aaker/eval.py, yaitu gemma2-9b-cpt-sahabatai-v1-instruct. Nilai "
                         "PPL bergantung pada model dan tokenizernya, sehingga model yang berbeda "
                         "membuat kolom fluency tidak dapat dibandingkan")
    ap.add_argument("--skip-fluency", action="store_true")
    ap.add_argument("--only-fluency", action="store_true",
                    help="hitung fluency saja, pada berkas evaluasi yang sudah ada di --out. Tidak "
                         "memuat classifier maupun encoder, sehingga puncak pemakaian memori hanya "
                         "berasal dari model fluency. Dipakai bila evaluasi penuh kehabisan memori "
                         "pada kartu grafis kecil: jalankan evaluasi penuh dengan --skip-fluency "
                         "lebih dulu, lalu jalankan tahap ini. Berkas yang sudah memuat fluency_ppl "
                         "dilewati, sehingga aman diulang")
    ap.add_argument("--legacy-eval-dir", default=None,
                    help="folder evaluation_result lama, dipakai menyalin fluency_ppl bila "
                         "--skip-fluency aktif")
    ap.add_argument("--patterns", default="*_results.csv")
    ap.add_argument("--limit", type=int, default=None, help="batasi jumlah baris per berkas (uji cepat)")
    args = ap.parse_args()

    if args.only_fluency:
        return hanya_fluency(args)

    if not args.results or not args.classifier:
        sys.exit("--results dan --classifier wajib diisi untuk evaluasi penuh. Keduanya hanya boleh "
                 "dikosongkan bila memakai --only-fluency")

    butuh_transformers()
    os.makedirs(args.out, exist_ok=True)
    temperature = None
    if args.calibration and os.path.exists(args.calibration):
        temperature = json.load(open(args.calibration, encoding="utf-8")).get("temperature")
        print(f"temperature scaling: T = {temperature}")

    import glob
    files = sorted(glob.glob(os.path.join(args.results, args.patterns)))
    files = [f for f in files if not os.path.basename(f).endswith("_HUMAN_EVAL.csv")]
    if not files:
        sys.exit(f"tidak ada berkas cocok '{args.patterns}' di {args.results}")
    print(f"{len(files)} berkas akan dievaluasi")

    clf = StyleClassifier(args.classifier, temperature)
    encoders = {}
    if SentenceTransformer is not None:
        if args.legacy_encoder:
            encoders["legacy"] = (clean_tag("simcse_indobert_base"),
                                  SentenceTransformer(args.legacy_encoder))
        for spec in args.encoder:
            if "=" not in spec:
                sys.exit(f"format --encoder salah: {spec} (harus TAG=model_id)")
            tag, mid = spec.split("=", 1)
            encoders[tag] = (clean_tag(tag), SentenceTransformer(mid))
    else:
        print("PERINGATAN: sentence-transformers tidak terpasang, kolom content preservation dilewati")

    flu = None if args.skip_fluency else Fluency(args.fluency_model)

    for f in files:
        df = pd.read_csv(f)
        if args.limit:
            df = df.head(args.limit).copy()
        out_name = "evaluated_v2_" + os.path.basename(f)
        originals = df["original_message"].astype(str).tolist()
        outputs = df["paraphrased_message"].astype(str).tolist()
        targets = [str(t).lower().strip() for t in df["style_target"]]

        probs, preds = clf.predict(outputs)
        df["style_strength_calibrated"] = [probs[i][clf.label2id.get(targets[i], 0)]
                                           for i in range(len(outputs))]
        df["style_predicted"] = [clf.id2label[int(p)] for p in preds]
        df["style_accuracy"] = [1 if clf.id2label[int(p)].lower() == targets[i] else 0
                                for i, p in enumerate(preds)]

        for tag, (cleaned, model) in encoders.items():
            col = "content_preservation" if tag == "legacy" else f"content_preservation_{cleaned}"
            df[col] = content_similarity(model, originals, outputs)

        if flu is not None:
            ppl, ntokens = [], []
            for t in outputs:
                p, n = flu.ppl(t)
                ppl.append(p)
                ntokens.append(n)
            df["fluency_ppl"] = ppl
            df["output_tokens"] = ntokens
            df["eos_reached"] = [bool(re.search(r'[.!?"\u201d]\s*$', t.strip()))
                                 for t in outputs]
            if len(ppl):
                med = float(np.nanmedian(ppl))
                df["ppl_degenerate"] = [bool(np.isfinite(p) and p > 1000) for p in ppl]
                print(f"  {out_name}: median PPL {med:.2f}, degenerate "
                      f"{int(np.nansum([p > 1000 for p in ppl if np.isfinite(p)]))}/{len(ppl)}")
        else:
            # Fluency dilewati: salin PPL dari hasil evaluasi lama bila tersedia dan panjangnya sama.
            # Gunakan --legacy-eval-dir agar jalurnya eksplisit, bukan ditebak.
            if args.legacy_eval_dir:
                src = os.path.join(args.legacy_eval_dir, "evaluated_" + os.path.basename(f))
                if os.path.exists(src):
                    old = pd.read_csv(src)
                    if "fluency_ppl" in old.columns and len(old) == len(df):
                        df["fluency_ppl"] = old["fluency_ppl"].values
                        print(f"  {out_name}: fluency disalin dari {src}")
                    else:
                        print(f"  {out_name}: fluency lama tidak dipakai "
                              f"(panjang {len(old)} vs {len(df)})")
                else:
                    print(f"  {out_name}: berkas lama tidak ditemukan di {args.legacy_eval_dir}")

        if "retrieved_exemplars" in df.columns:
            rates = []
            for txt, ex in zip(outputs, df["retrieved_exemplars"]):
                try:
                    exs = json.loads(ex) if isinstance(ex, str) else ex
                    if isinstance(exs, dict):
                        exs = exs.get("examples", [])
                except Exception:
                    exs = []
                og = ngrams(txt)
                eg = set()
                for e in (exs or []):
                    eg |= ngrams(e)
                rates.append(len(og & eg) / len(og) if og and eg else 0.0)
            df["replication_rate_8"] = rates
        else:
            print(f"  {out_name}: tanpa kolom retrieved_exemplars, laju replikasi tidak dihitung")

        df.to_csv(os.path.join(args.out, out_name), index=False)
        print(f"  ditulis {os.path.join(args.out, out_name)}")

    clf.release()
    if flu is not None:
        flu.release()
    print("\nSelesai. Lanjutkan dengan report_metrics.py pada folder keluaran ini.")


if __name__ == "__main__":
    main()
