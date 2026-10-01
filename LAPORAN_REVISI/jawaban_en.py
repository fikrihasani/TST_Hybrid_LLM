"""Jawaban per butir reviewer untuk JCCE-10619, putaran revisi pertama.

Isi berkas ini adalah satu-satunya bagian surat balasan yang ditulis tangan. Komentar reviewer,
nomor butir, dan lokasinya dibaca langsung dari workbook pemetaan oleh `build_dokumen.py`, sehingga
kutipan komentar tidak mungkin berbeda dari sumber aslinya.

Setiap butir: `jawab` (paragraf balasan dalam bahasa Inggris) dan `status`.

Nilai status yang dipakai:
  selesai            pekerjaan substantif selesai dan buktinya ada di bundel hasil
  menunggu_naskah    hasil atau keputusan sudah ada, tinggal diterapkan pada berkas naskah
  tanpa_tindakan     pujian, dicatat dan dikutip sebagai hal yang dipertahankan

Semua angka di sini adalah angka yang sudah diperiksa terhadap data per sampel lewat
`verifikasi_angka.py` (130 periksa, 128 lulus, 2 selisih konvensi yang dicatat).
"""

JAWABAN = {
    # ---------------- Reviewer 1 ----------------
    "R1-01": dict(status="selesai", jawab="""
We reran the experiments end to end and restructured the protocol along the five lines you set out.

(a) Grouped splits. The STIF split is rebuilt on `pair_id` so that both members of a parallel pair
stay in one split; pair integrity in the test set rises from 35.7% to 100% while the split sizes stay
2,498 / 500 / 1,500 / 500. The brand personality corpus is rebuilt with normalization-based
deduplication, which removes 13,704 duplicated rows (18.1%), and with conversation-level grouping
(`conversation_id_str`), reducing the corpus from 75,756 to 62,052 rows. The leakage gate that the
previous split fails (up to 503 cross-split duplicates, and 1,908 conversations shared between the
test and training sets) now returns zero duplicates and zero shared conversations across all five
classes.

(b) Development-based alpha selection. Alpha is now selected on a held-out development set
(`alpha_dev`, 500 items per configuration for brand personality; the validation split, 250 items, for
STIF) under a criterion fixed in advance, the harmonic mean of style accuracy and content
preservation measured with an independent encoder. The selected values are alpha = 0.3 for competence
and alpha = 0.7 for informal STIF; for the formal STIF target we deliberately do not report a
selected alpha, because style accuracy there spans only 0.108-0.136 across the whole sweep, which is
noise at n = 250.

(c) Stronger baselines. Two control baselines are added: `random-k`, which retrieves exemplars at
random, and `zero-shot`, which uses the same prompt with the exemplar block removed. Both are
labelled in the tables as additions made in this revision.

(d) Uncertainty. We report paired bootstrap confidence intervals (10,000 resamples) over test items
plus Wilcoxon and sign-flip tests for every pairwise comparison, in twelve supplementary tables. The
experiment uses a single generation seed (42), so intervals capture item-level uncertainty only; the
absence of across-run variance is stated as a limitation rather than implied away.

(e) Reproducibility. The revision adds a full setup section (GPU and VRAM, framework and library
versions, quantization, decoding parameters) and ships the code, configurations, prompts, evaluation
scripts, and per-sample outputs as supplementary material.

The rerun also changed two of our substantive claims, which we now state plainly: retrieval methods
improve content preservation in both directions but improve style only for the informal direction of
STIF (`d` = +0.768 to +0.852 relative to `zero-shot`), while for the formal direction they perform
below chance and `zero-shot` is higher (`d` = -0.732 to -0.528). Content preservation was also
re-measured with two encoders independent of the retrieval encoder, and the classifier was
calibrated before use.
"""),
    # ---------------- Reviewer 2 ----------------
    "R2-01": dict(status="menunggu_naskah", jawab="""
You are right that early fusion is a linear interpolation between a query representation and a
corpus-level centroid, which places it in the lineage of Rocchio-style query modification and
pseudo-relevance feedback. We have added a related-work subsection that states this connection
explicitly, cites the retrieval literature it comes from, and presents our contribution as the
style-targeted adaptation of that mechanism rather than as a new retrieval operator. Section 3.3.2
now opens by naming the mechanism (query-centroid interpolation) before presenting the equation.
"""),
    "R2-02": dict(status="menunggu_naskah", jawab="""
We have softened the claim. Contribution 2 now reads "to our knowledge, the first style-aware hybrid
retrieval approach for Indonesian text style transfer, and the first to evaluate it against
direction-matched control baselines", and we removed the categorical "a first" phrasing everywhere
else it appeared.
"""),
    "R2-03": dict(status="selesai", jawab="""
We agree, and this is now stated explicitly rather than left implicit. Section 3.3.2 states that the
centroid is query-independent: because a single centroid is computed per target style per corpus, the
same exemplar set is retrieved for every input, which makes the method formally equivalent to a fixed
few-shot prompt with corpus-level representatives. We have also removed the claim that the centroid
encodes style, and we no longer treat the centroid's style-accuracy gap as evidence of style
information. The revised results show what centroid retrieval actually does: it preserves content
well but its style accuracy depends almost entirely on the target direction, which is consistent with
the fixed-prompt interpretation.
"""),
    "R2-04": dict(status="menunggu_naskah", jawab="""
Thank you for catching both. The title is now "Retrieval Strategies for Indonesian Text Style
Transfer using a Large Language Model", which fixes both the preposition and the article.
"""),
    "R2-05": dict(status="menunggu_naskah", jawab="""
We accept this. The abstract no longer states a single threshold across tasks. It now reports the
result per task: for brand personality, semantic retrieval changes style strength by less than 0.001,
while for STIF the same methods change it materially. The corresponding claim in Section 4 is
qualified in the same way.
"""),
    "R2-06": dict(status="selesai", jawab="""
A dataset statistics table has been added. It reports both corpora by split: STIF 4,998 items
(2,498 / 500 / 1,500 / 500 with 2,499 formal and 2,499 informal entries, and 34 texts that appear in
both registers as parallel pairs), and brand personality 62,052 rows (24,820 / 6,205 / 18,617 /
6,205, plus a separate 6,205-item development set reserved for alpha selection). The same table
reports the sizes used to train the two style classifiers and the number of unique accounts and
conversations in the brand personality corpus.
"""),
    "R2-07": dict(status="selesai", jawab="""
We addressed this through item-level inference rather than repeated generation, and we state the
trade-off plainly. Every reported comparison now carries a paired bootstrap confidence interval
(10,000 resamples over the shared test items, 250 for STIF and 500 for brand personality) together
with a Wilcoxon signed-rank test and a sign-flip permutation test, in twelve supplementary tables
covering six metrics for both corpora. Of 342 comparable STIF pairs, 128 differ significantly on
style accuracy and 230 on content preservation; of 90 brand personality pairs, 66 and 80
respectively. The experiment uses one seed, so these intervals do not include across-run variance;
that limitation is now stated in the results and in the limitations. We also had to correct two
defects in the significance script during the revision (it compared configurations across different
style targets), so the reported pair counts replace earlier, inflated ones.
"""),
    "R2-08": dict(status="selesai", jawab="""
We confirmed the encoder identity and then removed the circularity from the evidence. Dense retrieval
and the original content-preservation metric both used `LazarusNLP/simcse-indobert-base`, and the
manuscript had described it only as "SentenceBERT". The revision now names the retrieval encoder in
Section 3.3.3 and reports content preservation from two encoders that are independent of the
retrieval pipeline, `sentence-transformers/LaBSE` and `intfloat/multilingual-e5-base`, with the
original encoder retained only as a comparison column. The independent encoders matter empirically,
not just conceptually: on the k-sensitivity analysis the original encoder shows a significant gain in
content preservation when exemplars increase from 5 to 10 in 10 of 18 comparisons, while LaBSE shows
it in only 3 of 18. For the reported results, the criterion column is LaBSE.
"""),
    "R2-09": dict(status="selesai", jawab="""
You are right that our own error analysis undermines the premise, so we bounded the claim and
measured the behaviour instead of asserting it. We defined a template replication metric: for each
generated output, the share of its 8-grams that also occur in the exemplars retrieved for that
sample. The result supports your reading only in one corner of the design. Replication is high only
for brand personality competence at small alpha (0.34 at alpha = 0.1, 0.22 at alpha = 0.3), stays
below 0.04 for excitement, and below 0.02 for both STIF targets. Section 3.3.1 no longer claims that
the centroid carries style information; the error analysis is retained but now reports these rates
alongside the qualitative categories, and the sample-selection protocol was fixed as described in
R2-22. The metric definition and its convention (outputs shorter than eight words are excluded, and
their count is reported) are stated with the table.
"""),
    "R2-10": dict(status="selesai", jawab="""
We took option (a) and calibrated both classifiers with temperature scaling on held-out validation
data. The brand personality classifier was strongly overconfident: temperature 2.6779 reduced NLL
from 0.6087 to 0.3013 and ECE from 0.0739 to 0.0437, and the median target-class probability fell
from 0.99998 to 0.95789, so the scores are no longer piled at the 0.999 extreme and style strength
becomes graded. The STIF classifier was already well calibrated (temperature 0.9805, ECE 0.0131), so
calibration left it essentially unchanged, which we report rather than hide. Both the raw and the
calibrated probabilities are reported side by side, together with per-class F1 on the new test sets
(0.9243 and 0.9196 for STIF; macro-F1 0.9043 for brand personality) and binary transfer accuracy.
"""),
    "R2-11": dict(status="selesai", jawab="""
We did not run a human study, and we have taken your minimum path: the absence is now stated
explicitly as a limitation, including the consequence that our conclusions rest on automatic metrics
alone. To make a future evaluation possible at low cost, the supplementary material includes an
exported rating sample of 400 STIF rows and 200 brand personality rows built from 25 shared sample
indices per corpus across four retrieval methods, with the source sentence, the generated output, a
method identifier, and the existing rating rubric. No ratings were collected, so no inter-rater
agreement or human-metric correlation is reported; the sample is provided as a starting point for
future work, not as evidence.
"""),
    "R2-12": dict(status="selesai", jawab="""
You are right that the fixed value was under-justified, and we answer on both fronts you offer.

Sensitivity analysis. The STIF corpus was run at k = 5 and k = 10 for every method, so the comparison
is ours rather than borrowed. Across 18 matched pairs, nine configurations on each of the two style
targets, style accuracy differs significantly in exactly one comparison, and that one difference is
negative: the formal centroid loses 0.148 at k = 10 (95% CI [-0.204, -0.088]). Content preservation
moves more, and the direction depends on which encoder measures it: on the original encoder 10 of 18
comparisons favour k = 10, whereas on the independent LaBSE encoder only 3 of 18 do, with effects
between +0.019 and +0.024. We therefore no longer claim that five is optimal. What we report is that
raising k from five to ten does not improve style transfer in this setting and mainly affects content
preservation for the formal target. The brand personality corpus was run at k = 5 only, which we state
as the limit of the sensitivity analysis. The full table is `TABEL_kepekaan_k_formality.csv`.

Citations. The unsupported sentence is removed, and we now cite work that reports the relevant
behaviour rather than asserting a consensus. Liu et al. (2022) ablate k over 5, 10, 20, 35 and 64 for
in-context question answering, find that retrieval-based selection beats random selection "even when
the number of in-context examples is as few as 5", and set k = 3 for sentiment analysis "since adding
more examples does not further improve the performance". Chen et al. (2023) find no significant
degradation when a single randomly chosen demonstration is used, and attribute this to the redundancy
of demonstrations. Lu et al. (2022) show that with only four examples, prompt permutations range from
near state of the art to near chance, which is why we fix k, fix the order of exemplars, and report
both. For style transfer specifically, we note that exemplar-based low-resource settings commonly
operate at five exemplars (Liu et al., 2024). We make no claim of optimality beyond the range we
tested.
"""),
    "R2-13": dict(status="menunggu_naskah", jawab="""
Corrected. Section 3.2 now states the split as percentages of the full corpus, and the internal
partition of the classifier subset is reported separately as its own split rather than as a nested
"50:10" figure.
"""),
    "R2-14": dict(status="menunggu_naskah", jawab="""
Corrected. Equation 6 is now described as a lexical term-statistic scoring function that yields a
sparse lexical representation, and the wording no longer implies that BM25+ produces a learned
sparse embedding. The term appears consistently in Sections 2, 3.3.3, and 4.
"""),
    "R2-15": dict(status="menunggu_naskah", jawab="""
A full experimental setup subsection has been added. It reports the GPU (NVIDIA RTX 4070 Ti, 12 GB
VRAM), the software stack (Python 3.14.4, PyTorch 2.11.0+cu126, transformers 5.8.0,
sentence-transformers 5.4.1, scikit-learn 1.8.0), the 4-bit NF4 quantization used for generation, the
fixed decoding parameters (temperature 0.7, top_p 0.9, max_new_tokens 1500, sampling enabled), and
the wall-clock cost per stage. We also disclose one environment deviation: the 12 GB card is below
the 16 GB we would recommend for this configuration, and we describe the mitigations used.
"""),
    "R2-16": dict(status="menunggu_naskah", jawab="""
You are correct and we apologize for the error. The STIF-Indonesia dataset was created by Wibowo et
al. (2020, IALP, "Semi-supervised low-resource style transfer of Indonesian informal to formal
language with limited resources"), and the reference that carried that description in our manuscript
was in fact a different paper. Attribution in Sections 2.2 and 3.1 and in the Table 1 caption now
points to Wibowo et al. (2020); the Data Availability statement already pointed to the correct
repository and remains unchanged. The entry for Wibowo et al. (2020) is inserted through the
reference manager, which regenerates the in-text numbering; the citation field on those sentences,
which previously pointed to Irnawan and Adi (2023), moves to it.
"""),
    "R2-17": dict(status="selesai", jawab="""
The revision ships a reproducibility package rather than a prose statement. It contains the
retrieval and generation code, all configuration files, the full prompt templates including the
zero-shot branch, the split manifests, the leakage-gate script, the calibration and evaluation
scripts, the per-sample evaluation outputs with one row per generated item (58 files, 19,500 rows),
the twelve significance tables, and the k-sensitivity table. The package is prepared for deposit with
a DOI, and the Data Availability statement now describes it.
"""),
    "R2-18": dict(status="selesai", jawab="""
The supplementary material now includes per-sample outputs. Every generated item is shipped with its
source sentence, its generated output, the retrieved exemplars, and the full metric vector (style
prediction and calibrated probability, style accuracy, content preservation from three encoders,
perplexity and its degeneracy flag, output length, and the template replication rate) in 58 files
covering 19,500 items. Each claim in the error analysis now cites the configuration and the sample it
comes from, so a reader can reproduce any single case. The sample-selection protocol for the
qualitative examples was also made explicit, as described in R2-22.
"""),
    "R2-19": dict(status="menunggu_naskah", jawab="""
We checked and you are right. The Sahabat-AI models do not have an accompanying academic paper, so
citing two unrelated conference papers as their source was incorrect. The sentence now names the
fluency model directly and in full, Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct, so the two
application papers no longer carry that attribution. Their citations on that sentence are deleted
through the reference manager, which also drops the two entries from the reference list; the
citations that remain in that paragraph are the two that document the perplexity metric itself.
"""),
    "R2-20": dict(status="menunggu_naskah", jawab="""
We verified the labels against the source corpus and the phenomenon is real, not a typesetting slip.
The register labels in Table 1 are taken verbatim from the source dataset, and scanning all 2,499
entries labelled formal for kamu, aku and cuma as substrings finds 330 of them (13.21%) carrying at
least one such marker, while the same scan on the 2,499 entries labelled informal finds 323 (12.93%).
We have kept the original labels to preserve comparability with prior work and added this count to
the Table 1 caption. This data property is also relevant to our revised interpretation of the formal
target, where the retrieval-based configurations stay between 0.064 and 0.252 against a chance level
of 0.50: part of that difficulty is that the formal reference register is itself not homogeneous.
"""),
    "R2-21": dict(status="selesai", jawab="""
You are right that the means were uninterpretable, and investigating them produced two findings.

First, the degeneracy. We now report the proportion of degenerate outputs per method, where
degenerate means a perplexity above 1,000. For STIF it is 12.80% for the formal target and 14.74% for
the informal target, and it varies strongly by method, from 2.80% for the zero-shot baseline to
17.00% for BM25+, so Table 5 reports the proportion for every configuration rather than a corpus
average. For brand personality the proportions range from 0.20% to 11.40% across the configurations
listed in Table 7. The value distribution is extremely long-tailed: for
STIF the median perplexity is 191.45 and 226.18 for the two targets while the means are 1,436 and
1,081, a ratio of 4.8 to 7.5, which is exactly why the mean column could not be read. Table 7 now
reports the median and a 10% trimmed mean and carries the degeneracy proportion beside them.

Second, and more importantly, the numbers you quoted came from a genuine inconsistency in the
original pipeline. The STIF fluency values in the first version were computed with
`llama3-8b-cpt-sahabatai-v1-instruct` while the brand personality values used
`gemma2-9b-cpt-sahabatai-v1-instruct`, so the two corpora were never on a common scale. The revision
computes fluency for both corpora with the single model named in Methods, and we report the model
that was actually loaded. Because the model changed, all STIF fluency values differ from the first
version, and the STIF degeneracy proportion is not comparable with the 0.61% we had measured on the
old outputs; we state this explicitly rather than presenting the change as a change in output
quality.
"""),
    "R2-22": dict(status="selesai", jawab="""
We replaced the inconsistent criteria with one protocol. Qualitative examples are now drawn from a
single shared set of 25 sample indices per corpus, identical across the four main retrieval methods,
selected before inspection by a fixed rule that we state in the text, with the corresponding
configuration named for every example. Section 4.3.1 has been rewritten so that it describes that
one protocol, and Table 9 and its caption follow it. The same shared-index set is what the exported
human-evaluation sample uses.
"""),
    "R2-23": dict(status="menunggu_naskah", jawab="""
Rewritten as suggested. The conclusion no longer claims that the comparison fails to warrant a
metric; it now states that no single automatic metric consistently identifies the best method, so
evaluation has to be reported jointly across style, content, and fluency, with the trade-offs made
explicit. The wording is also reconciled with the new directional result for STIF.
"""),
    "R2-24": dict(status="menunggu_naskah", jawab="""
All figures are renumbered sequentially and every in-text reference was reconciled against the new
numbering. The duplicate "Figure 1" label is removed. This was done together with the table
renumbering so that the cross-references are consistent in one pass.
"""),
    "R2-25": dict(status="menunggu_naskah", jawab="""
All tables are renumbered sequentially so that no number is skipped, and every in-text reference was
updated. The error-example tables are retained as separate numbered tables rather than folded into
another table, so the material that was effectively invisible now has its own number and caption.
"""),
    "R2-26": dict(status="menunggu_naskah", jawab="""
The manuscript has gone through a full editing pass. The specific examples you listed are corrected
("While it remains underexplored", and the malformed comparatives), and the pass covered the whole
text for agreement, article use, and parallel construction, with the terminology fixes from R2-14 and
R2-23 applied in the same pass.
"""),
    "R2-27": dict(status="menunggu_naskah", jawab="""
We traced the artifacts to encoding handling in the pipeline. The generation and evaluation steps now
run with UTF-8 output encoding enforced, which is what produced the mojibake and the damaged emoji in
the earlier tables, and all tables in the revision were regenerated from the new outputs. Tables 2, 9,
and 11 are rebuilt and carry no encoding artifacts.
"""),
    "R2-28": dict(status="menunggu_naskah", jawab="""
Corrected. Section 4.1 now refers to the results tables by their new numbers after the renumbering,
and the duplicated reference label has been removed. This was reconciled in the same pass as R2-24,
R2-25, and R3-W1.
"""),
    # ---------------- Reviewer 3 ----------------
    "R3-S1": dict(status="tanpa_tindakan", jawab="""
Thank you. We have kept the paper focused on exemplar selection for few-shot style transfer rather
than broadening it into a general evaluation of the task.
"""),
    "R3-S2": dict(status="tanpa_tindakan", jawab="""
Thank you. The design is unchanged, but following Reviewer 2 the framing is now more precise: the
centroid is described as a query-independent fixed prompt, and early fusion as query-centroid
interpolation within the pseudo-relevance feedback lineage.
"""),
    "R3-S3": dict(status="tanpa_tindakan", jawab="""
Thank you. The low-resource Indonesian setting remains the motivation, and the revision strengthens
it by reporting the directional asymmetry we found: the informal direction is solved well
(0.904-0.988 style accuracy), while the formal direction is not, which we now discuss as the main
open problem for the language.
"""),
    "R3-S4": dict(status="tanpa_tindakan", jawab="""
Thank you. The qualitative categories are retained, and they are now backed by a replication metric
and a fixed sample-selection protocol so that each reported case can be traced to a configuration and
a sample index.
"""),
    "R3-W1": dict(status="menunggu_naskah", jawab="""
This was performed as one coordinated pass over both figures and tables, together with Reviewer 2's
numbering comments, and every in-text cross-reference was checked against the final numbering.
"""),
    "R3-W2": dict(status="selesai", jawab="""
We did both, and the justification no longer rests on an appeal to consensus. First, the citations:
Liu et al. (2022) ablate k over 5, 10, 20, 35 and 64 and report that retrieval-based selection still
beats random selection "even when the number of in-context examples is as few as 5", while for
sentiment analysis they use k = 3 "since adding more examples does not further improve the
performance"; Chen et al. (2023) observe no significant degradation with a single demonstration
because demonstrations are largely redundant; Lu et al. (2022) show that at four examples the choice
of order alone spans from near state of the art to near chance. Second, the sensitivity analysis, run
on our own data at k = 10 against k = 5 on the STIF corpus: style accuracy changes significantly in
only 1 of 18 comparisons and that change is negative, while content preservation improves in 10 of 18
comparisons on the original encoder but only 3 of 18 on the independent encoder. The resulting claim
is deliberately narrow: five exemplars remain a reasonable operating point, the effect of adding more
is mainly on content rather than style, and we do not claim that five is optimal.
"""),
    "R3-W3": dict(status="selesai", jawab="""
We calibrated both classifiers with temperature scaling on validation data and report both the raw
and the calibrated style strength. For brand personality the calibration is substantial (temperature
2.6779, ECE 0.0739 to 0.0437, median target probability 0.99998 to 0.95789), so the saturation you
noted is largely resolved; for STIF the classifier was already well calibrated (ECE 0.0131) and the
values change only marginally. The results tables report the calibrated column, with the raw column
kept alongside for transparency about how much the correction moved.
"""),
    "R3-W4": dict(status="selesai", jawab="""
We fixed the protocol rather than only the description. The qualitative analysis now uses one shared
set of 25 sample indices per corpus, identical across the four main methods and selected by a rule
stated before inspection, and every example names its configuration. The number of inspected samples
and the purpose of the selection are given in the text, so the analysis is reproducible even though
it remains purposively selected.
"""),
    "R3-W5": dict(status="selesai", jawab="""
Addressed together with Reviewer 2's perplexity comment, and with the same two causes. Table 7 now
reports median and trimmed statistics instead of means, with the proportion of degenerate outputs
beside them, and the fluency model has been made consistent across corpora. The very large values in
the first version were produced by a small number of degenerate outputs, and for STIF they were also
computed with a different language model than the brand personality values, so the two columns were
never comparable. We state both facts next to the table rather than only replacing the numbers.
"""),
}

# Butir yang masih bergantung pada penyuntingan naskah, dipakai laporan untuk memisahkan
# pekerjaan yang sudah selesai dari yang belum.
TERGANTUNG_NASKAH = [i for i, v in JAWABAN.items() if v["status"] == "menunggu_naskah"]
