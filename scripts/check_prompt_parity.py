#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_prompt_parity.py
======================
Verifies that target-aware prompt templates maintain strict symmetry across retrieval
and zero-shot conditions, differing only inside the reference-examples block.

Checks performed:
  1. Both {target_label} and {target_definition} appear inside the target-style block.
  2. No unexpanded placeholders remain after rendering.
  3. Retrieval and zero-shot renders are byte-identical once the exemplar body is stripped.
  4. Template framing outside the target and example blocks is identical across all targets.

Usage:
    python scripts/check_prompt_parity.py \
        --template fewshot_formality/prompts/generation_prompt_v2_id.txt \
                   fewshot_formality/prompts/generation_prompt_v2_en.txt \
        --targets  fewshot_formality/prompts/targets.json

Exit code 0 when no issues are found; 1 otherwise.
"""
import argparse
import hashlib
import json
import os
import re
import sys

SENTINEL = "<<<EXEMPLAR_BODY>>>"
SOURCE = "Sample source sentence for parity verification."
LABEL_TOKEN = "<TARGET>"


def render(template, label, definition, examples_body):
    out = template.replace("{target_label}", label)
    out = out.replace("{target_definition}", definition)
    out = out.replace("{original_message}", SOURCE)
    out = out.replace("{style_examples_str}", examples_body)
    return out


def strip_examples(text):
    return text.replace(SENTINEL, "")


def normalize_target(text, label, definition):
    return text.replace(label, LABEL_TOKEN).replace(definition, LABEL_TOKEN)


def extract_target_block(template):
    """Return (header, body) for the target-style section."""
    header = None
    for candidate in ("### GAYA TARGET", "### TARGET STYLE"):
        if candidate in template:
            header = candidate
            break
    if header is None:
        return None
    lines = template.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == header)
    body = []
    for ln in lines[start + 1:]:
        if ln.strip().startswith("###"):
            break
        body.append(ln)
    return header, "\n".join(body)


def main():
    ap = argparse.ArgumentParser(description="Verify symmetry of target-aware prompt templates.")
    ap.add_argument("--template", required=True, nargs="+", help="One or more prompt template files")
    ap.add_argument("--targets", required=True, help="JSON file containing target labels and definitions")
    ap.add_argument("--out", "--keluaran", dest="out", default=None, help="Optional Markdown report path")
    args = ap.parse_args()

    with open(args.targets, encoding="utf-8") as f:
        data = json.load(f)
    targets = data["targets"] if "targets" in data else data
    issues = []
    report = []
    w = report.append

    for path in args.template:
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            template = f.read()
        sha = hashlib.sha256(template.encode("utf-8")).hexdigest()
        w(f"\n## Template `{name}`\n")
        w(f"- sha256: `{sha}`")
        w(f"- length: {len(template)} chars")

        block = extract_target_block(template)
        if block is None:
            issues.append(f"{name}: missing target block header ('### GAYA TARGET' or '### TARGET STYLE')")
            w("- target block header: NOT FOUND")
        else:
            header, block_body = block
            w(f"- target block header: `{header}`")
            w(f"- target block body: {block_body.strip()!r}")

        baseline = None
        for target_name, entry in targets.items():
            label, definition = entry["label"], entry["definition"]
            r_fewshot = render(template, label, definition, SENTINEL)
            r_zeroshot = render(template, label, definition, "")

            if block is not None:
                block_r = extract_target_block(r_fewshot)
                body_r = block_r[1] if block_r else ""
                if label not in body_r:
                    issues.append(f"{name}/{target_name}: target label missing from target block")
                if definition not in body_r:
                    issues.append(f"{name}/{target_name}: target definition missing from target block")
                if r_fewshot.count(definition) != 1:
                    issues.append(f"{name}/{target_name}: target definition appears {r_fewshot.count(definition)} times (expected 1)")

            leftover = re.findall(r"\{[a-z_]+\}", r_fewshot)
            if leftover:
                issues.append(f"{name}/{target_name}: unexpanded placeholders {sorted(set(leftover))}")

            if strip_examples(r_fewshot) != r_zeroshot:
                issues.append(f"{name}/{target_name}: few-shot and zero-shot renders differ outside reference block")

            norm = normalize_target(strip_examples(r_fewshot), label, definition)
            if baseline is None:
                baseline = norm
            elif norm != baseline:
                issues.append(f"{name}/{target_name}: template framing differs across targets")

            w(f"- {target_name:11s} label={label!r} rendered_chars={len(r_fewshot)}")

        w(f"- renders checked: {2 * len(targets)}")

    header_lines = [
        "# Prompt Parity Verification Report",
        "",
        f"Targets file: `{os.path.basename(args.targets)}`",
        f"Templates checked: {len(args.template)}",
    ]
    footer_lines = ["", "## Findings", ""]
    if issues:
        footer_lines += [f"{i}. {t}" for i, t in enumerate(issues, 1)]
        footer_lines += ["", f"FAILED: {len(issues)} issues"]
    else:
        footer_lines += [f"OK: {len(targets)} targets, {2 * len(targets) * len(args.template)} renders, 0 issues"]

    output = "\n".join(header_lines + report + footer_lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
    print(output)
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
