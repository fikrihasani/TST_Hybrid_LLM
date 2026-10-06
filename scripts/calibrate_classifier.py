#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
import torch

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
except ImportError:
    sys.exit("transformers belum terpasang: pip install transformers")

def expected_calibration_error(probs, correct, n_bins=15):
    conf = probs.max(axis=1) if probs.ndim > 1 else probs
    pred_correct = correct.astype(float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (conf > lo) & (conf <= hi)
        if not m.any():
            continue
        ece += (m.sum() / len(conf)) * abs(pred_correct[m].mean() - conf[m].mean())
    return float(ece)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classifier", required=True)
    ap.add_argument("--val", required=True)
    ap.add_argument("--text-col", required=True)
    ap.add_argument("--style-col", required=True)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--max-length", type=int, default=128)
    ap.add_argument("--out", default=None, help="default: <classifier>/calibration.json")
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(args.classifier)
    model = AutoModelForSequenceClassification.from_pretrained(args.classifier).to(device)
    model.eval()
    id2label = {int(k): v for k, v in model.config.id2label.items()}
    label2id = {v: int(k) for k, v in id2label.items()}
    print(f"classifier: {args.classifier}")
    print(f"label: {label2id}")

    df = pd.read_csv(args.val).dropna(subset=[args.text_col, args.style_col])
    texts = df[args.text_col].astype(str).tolist()
    labels = np.array([label2id[str(s).lower().strip()] for s in df[args.style_col]])

    logits_all = []
    for i in range(0, len(texts), args.batch_size):
        batch = texts[i:i + args.batch_size]
        enc = tok(batch, return_tensors="pt", padding=True, truncation=True,
                  max_length=args.max_length).to(device)
        with torch.no_grad():
            logits_all.append(model(**enc).logits.cpu())
    logits = torch.cat(logits_all, dim=0)
    y = torch.tensor(labels, dtype=torch.long)
    print(f"validation set: {len(texts)} baris")

    with torch.no_grad():
        raw_probs = torch.nn.functional.softmax(logits, dim=-1).numpy()
    raw_pred = raw_probs.argmax(axis=1)
    acc_before = float((raw_pred == labels).mean())
    nll_before = float(torch.nn.functional.cross_entropy(logits, y).item())
    ece_before = expected_calibration_error(raw_probs, raw_pred == labels)

    logT = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([logT], lr=0.1, max_iter=200)

    def closure():
        opt.zero_grad()
        loss = torch.nn.functional.cross_entropy(logits / torch.exp(logT), y)
        loss.backward()
        return loss

    try:
        opt.step(closure)
        T = float(torch.exp(logT).item())
    except Exception as e:
        print(f"optimasi gagal ({e}), memakai grid search")
        grid = np.exp(np.linspace(np.log(0.05), np.log(50.0), 400))
        nlls = [float(torch.nn.functional.cross_entropy(logits / t, y).item()) for t in grid]
        T = float(grid[int(np.argmin(nlls))])
    T = min(max(T, 0.05), 100.0)

    with torch.no_grad():
        cal_probs = torch.nn.functional.softmax(logits / T, dim=-1).numpy()
    nll_after = float(torch.nn.functional.cross_entropy(logits / T, y).item())
    ece_after = expected_calibration_error(cal_probs, cal_probs.argmax(axis=1) == labels)

    print(f"\n  T hasil kalibrasi        : {T:.4f}")
    print(f"  akurasi (tidak berubah)  : {acc_before:.4f}")
    print(f"  NLL  sebelum -> sesudah  : {nll_before:.4f} -> {nll_after:.4f}")
    print(f"  ECE  sebelum -> sesudah  : {ece_before:.4f} -> {ece_after:.4f}")
    print(f"  keyakinan rata-rata sebelum: {raw_probs.max(axis=1).mean():.4f}")
    print(f"  keyakinan rata-rata sesudah: {cal_probs.max(axis=1).mean():.4f}")

    tgt_idx = labels
    tgt_before = raw_probs[np.arange(len(labels)), tgt_idx]
    tgt_after = cal_probs[np.arange(len(labels)), tgt_idx]
    print(f"  probabilitas kelas target sebelum: median {np.median(tgt_before):.5f}, "
          f"persentil 5-95 [{np.percentile(tgt_before, 5):.5f}, {np.percentile(tgt_before, 95):.5f}]")
    print(f"  probabilitas kelas target sesudah: median {np.median(tgt_after):.5f}, "
          f"persentil 5-95 [{np.percentile(tgt_after, 5):.5f}, {np.percentile(tgt_after, 95):.5f}]")

    out = args.out or os.path.join(args.classifier, "calibration.json")
    payload = {
        "temperature": T,
        "val_file": os.path.abspath(args.val),
        "n_val": int(len(texts)),
        "accuracy": acc_before,
        "nll_before": nll_before,
        "nll_after": nll_after,
        "ece_before": ece_before,
        "ece_after": ece_after,
        "mean_confidence_before": float(raw_probs.max(axis=1).mean()),
        "mean_confidence_after": float(cal_probs.max(axis=1).mean()),
        "label2id": label2id,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nDisimpan: {out}")
    print("Laporkan akurasi, NLL, ECE, dan sebaran probabilitas kelas target sebelum dan "
          "sesudah kalibrasi di naskah.")

if __name__ == "__main__":
    main()
