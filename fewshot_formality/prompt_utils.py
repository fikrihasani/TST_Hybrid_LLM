#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Target-aware prompt rendering utilities for Indonesian text style transfer.
Uses standard library modules only so template parity can be verified without GPU dependencies.

Canonical templates contain four placeholders:
    {target_label}, {target_definition}, {style_examples_str}, {original_message}

Design invariants:
1. The TARGET STYLE (GAYA TARGET) block is included in every condition, including zero-shot.
2. Zero-shot differs from retrieval solely by leaving the REFERENCE EXAMPLES body empty.
3. Target definitions use a uniform one-clause format with three descriptors.
"""
from __future__ import annotations

import hashlib
import os

DEFAULT_PROMPT_FILE = "generation_prompt_v2_id.txt"
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

REQUIRED_PLACEHOLDERS = (
    "{target_label}",
    "{target_definition}",
    "{style_examples_str}",
    "{original_message}",
)


def prompt_file_path(root=".", filename=None):
    """Return path to a prompt template file inside the corpus directory."""
    return os.path.join(root, "prompts", filename or DEFAULT_PROMPT_FILE)


def load_template(root=".", filename=None):
    with open(prompt_file_path(root, filename), encoding="utf-8") as f:
        return f.read()


def sha256_template(template):
    return hashlib.sha256(template.encode("utf-8")).hexdigest()


def check_template(template):
    """Validate template placeholders and required target block header."""
    issues = []
    for ph in REQUIRED_PLACEHOLDERS:
        n = template.count(ph)
        if n != 1:
            issues.append(f"placeholder {ph} appears {n} times (expected 1)")
    if "### GAYA TARGET" not in template and "### TARGET STYLE" not in template:
        issues.append("missing target style header ('### GAYA TARGET' or '### TARGET STYLE')")
    if "{target_label}" not in template:
        issues.append("template missing {target_label}")
    return issues


def render_prompt(template, examples_str, original_message, target):
    """Render a prompt for one source item using a target entry from TARGETS."""
    if "label" not in target or "definition" not in target:
        raise ValueError("target dict must include 'label' and 'definition'")
    if examples_str is None:
        examples_str = ""
    return template.format(
        target_label=target["label"],
        target_definition=target["definition"],
        style_examples_str=examples_str,
        original_message=original_message,
    )


def slice_example_block(rendered):
    """Split a rendered prompt into (before, example_body, after) around the reference block."""
    markers = ("### CONTOH REFERENSI", "### REFERENCE EXAMPLES")
    header = next((p for p in markers if p in rendered), None)
    if header is None:
        return rendered, "", ""
    start = rendered.index(header) + len(header)
    rest = rendered[start:]
    end_rel = rest.find("\n### ")
    if end_rel == -1:
        return rendered[:start], rendered[start:], ""
    end = start + end_rel
    return rendered[:start], rendered[start:end], rendered[end:]
