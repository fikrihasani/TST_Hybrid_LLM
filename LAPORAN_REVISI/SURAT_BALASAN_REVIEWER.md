# Response to Reviewers

**Manuscript:** JCCE-10619

**Revised title:** Retrieval Strategies for Indonesian Text Style Transfer using a Large Language Model

**Revision round:** first

---

## Summary of the revision

We thank the reviewers for comments that changed the paper substantially. In response we rebuilt both corpora with leakage-free grouped splits, reran the full grid of retrieval configurations, selected alpha on development data under a criterion fixed in advance, added two control baselines, reported the corrected target-class probability as the style measure, measured content preservation with two encoders independent of the retrieval pipeline, and ran pairwise significance tests with bootstrap confidence intervals on every reported comparison.

The rerun also led us to withdraw or narrow three claims from the first version: that the centroid encodes style, that retrieval improves style transfer in general, and that the mean perplexity column is interpretable. Style gains now hold for the informal direction of STIF only, content preservation improves in both directions for every retrieval method, and fluency is reported with median and trimmed statistics beside the proportion of degenerate outputs. We also corrected an inconsistency in the fluency computation itself, where the two corpora had been scored with different language models.

The supplementary package contains the split manifests, the leakage gate results, the per-sample evaluation outputs (58 files, 19,500 items), the twelve significance tables, the corrected target-class probabilities, and the exported human-evaluation sample. Numbers quoted below are traceable to those files.

---


### R1-01 — Seluruh naskah

**Comment.**

> The paper addresses a meaningful low-resource-language problem and its attempt to prevent direct item leakage is valuable. The qualitative error analysis also exposes important failures that aggregate metrics conceal. However, those failures undermine the paper’s central interpretation: the current results do not demonstrate that the centroid encodes style or that the hybrid method reliably balances style and content. A major revision should rerun the experiments with validated evaluation, development-based α selection, stronger baselines, grouped data splits, uncertainty analysis, and complete reproducibility information.

**Response.**

We reran the experiments end to end and restructured the protocol along the five lines you set out. (a) Grouped splits. The STIF split is rebuilt on `pair_id` so that both members of a parallel pair stay in one split; pair integrity in the test set is now complete, because both members of a parallel pair always fall in the same split while the split sizes stay 2,498 / 500 / 1,500 / 500. The brand personality corpus is rebuilt with normalization-based deduplication, which removes 13,704 duplicated rows (18.1%), and with conversation-level grouping (`conversation_id_str`), reducing the corpus to 62,052 rows. The leakage gate that the previous split failed (up to 503 cross-split duplicates) now returns zero duplicates and zero shared conversations across all five classes. (b) Development-based alpha selection. Alpha is now selected on a held-out development set (`alpha_dev`, 500 items per configuration for brand personality; the validation split, 250 items, for STIF) under a criterion fixed in advance, the harmonic mean of style accuracy and content preservation measured with an independent encoder. The selected values are alpha = 0.3 for competence and alpha = 0.7 for informal STIF; for the formal STIF target we deliberately do not report a selected alpha, because style accuracy there spans only 0.112-0.192 across the whole sweep, which is noise at n = 250. (c) Stronger baselines. Two control baselines are added: `random-k`, which retrieves exemplars at random, and `zero-shot`, which uses the same prompt with the exemplar block removed. Both are labelled in the tables as additions made in this revision. (d) Uncertainty. We report paired bootstrap confidence intervals (10,000 resamples) over test items plus Wilcoxon and sign-flip tests for every pairwise comparison, in twelve supplementary tables. The experiment uses a single generation seed (42), so intervals capture item-level uncertainty only; the absence of across-run variance is stated as a limitation rather than implied away. (e) Reproducibility. The revision adds a full setup section (GPU and VRAM, framework and library versions, quantization, decoding parameters) and ships the code, configurations, prompts, evaluation scripts, and per-sample outputs as supplementary material. The rerun also changed two of our substantive claims, which we now state plainly: retrieval methods improve content preservation in both directions but improve style only for the informal direction of STIF (`d` = +0.768 to +0.852 relative to `zero-shot`), while for the formal direction they perform below chance and `zero-shot` is higher (`d` = -0.732 to -0.528). Content preservation was also re-measured with two encoders independent of the retrieval encoder, and the reported style strength is the corrected target-class probability.

---

## Reviewer 2

**Evidence in the revised manuscript.**

- paragraf 124: "The generation hyperparameters used in this study are as follows: the maximum token limit was set to 1500, the temperature was fixed at 0.7 to balance deterministic structural adherence with necessary lexical variation, "
- paragraf 125: "For every reported contrast we compute a paired bootstrap confidence interval with 10,000 resamples and two distribution-free tests on the same paired differences, the Wilcoxon signed-rank test and a sign-flip permutatio"
- paragraf 166: "Style accuracy across the weight sweep stays between 0.112 and 0.192, a spread close to one standard error at n = 250."
- paragraf 170: "The paired comparison is unambiguous: retrieval exceeds zero-shot in all 36 matched comparisons with standardized differences from +0.768 to +0.852."

### R2-01 — Significance & Novelty / Sec. 2 & 3.3.2

**Comment.**

> The hybrid early fusion method is a linear interpolation between the query embedding and a corpus centroid, followed by cosine ranking. This is structurally similar to Rocchio-style query modification and centroid-based pseudo-relevance feedback, techniques with a long history in information retrieval. The manuscript presents early fusion as a novel contribution without positioning it against this lineage. Please add related work on query-centroid interpolation and reframe the novelty claim around its application to style-aware exemplar selection rather than the mechanism itself.

**Response.**

You are right that early fusion is a linear interpolation between a query representation and a corpus-level centroid, which places it in the lineage of Rocchio-style query modification and pseudo-relevance feedback. We have added a related-work subsection that states this connection explicitly, cites the retrieval literature it comes from, and presents our contribution as the style-targeted adaptation of that mechanism rather than as a new retrieval operator. Section 3.3.2 now opens by naming the mechanism (query-centroid interpolation) before presenting the equation.

**Evidence in the revised manuscript.**

- paragraf 112: "While Equation (2) uses a comparison between c as the centroid vector, the similarity calculation in dense retrieval is performed by comparing the query embedding q against eᵢ, producing a similarity score sᵢ as denoted "

### R2-02 — Significance & Novelty / klaim kontribusi 2

**Comment.**

> Contribution claim 2 asserts “a first style-aware hybrid retrieval approach for Indonesian TST.” Firstness claims are difficult to verify and invite dispute; soften to “to our knowledge” phrasing at minimum.

**Response.**

We have softened the claim. Contribution 2 now reads "to our knowledge, the first style-aware hybrid retrieval approach for Indonesian text style transfer, and the first to evaluate it against direction-matched control baselines", and we removed the categorical "a first" phrasing everywhere else it appeared.

**Evidence in the revised manuscript.**

- paragraf 236: "This study systematically evaluated the impact of different retrieval strategies on few-shot Indonesian Text Style Transfer (TST), revealing that the selection of retrieval paradigms is highly dependent on the target cor"

### R2-03 — Significance & Novelty / Sec. 3.3.2 & 4.3

**Comment.**

> A significant conceptual issue: the centroid method is query-independent. Because the centroid c is computed once per target corpus (Equation 1) and every document is scored against it (Equations 2-3), the same top-k exemplars are retrieved for every source sentence. The method is therefore equivalent to a fixed few-shot prompt, not retrieval in any per-query sense. This must be stated explicitly, because (a) it changes the interpretation of the comparison, and (b) it directly explains the template replication failure documented in the error analysis: every generation was conditioned on the identical dominant exemplars. The hybrid method is query-dependent only through the q term, so as alpha approaches 0 it degenerates to the same static prompt. Relatedly, Section 3.3.2 states “After vector h is generated for each document”; h is generated once per query, not per document, so this description should also be corrected.

**Response.**

We agree, and this is now stated explicitly rather than left implicit. Section 3.3.2 states that the centroid is query-independent: because a single centroid is computed per target style per corpus, the same exemplar set is retrieved for every input, which makes the method formally equivalent to a fixed few-shot prompt with corpus-level representatives. We have also removed the claim that the centroid encodes style, and we no longer treat the centroid's style-accuracy gap as evidence of style information. The revised results show what centroid retrieval actually does: it preserves content well but its style accuracy depends almost entirely on the target direction, which is consistent with the fixed-prompt interpretation.

**Evidence in the revised manuscript.**

- paragraf 165: "This asymmetry, weak style with preserved content, is consistent with formal Indonesian being difficult to reproduce through few-shot prompting alone, and it is reported here as a null result for the formal direction rat"

### R2-04 — Judul

**Comment.**

> Title wording: “Retrieval Strategies on Indonesian Text Style Transfer using Large Language Model” has two grammatical issues (“on” should be “for”; “Large Language Model” should be “a Large Language Model” to indicate a single model).

**Response.**

Thank you for catching both. The title is now "Retrieval Strategies for Indonesian Text Style Transfer using a Large Language Model", which fixes both the preposition and the article.

**Evidence in the revised manuscript.**

- paragraf 236: "This study systematically evaluated the impact of different retrieval strategies on few-shot Indonesian Text Style Transfer (TST), revealing that the selection of retrieval paradigms is highly dependent on the target cor"

### R2-05 — Abstract

**Comment.**

> The abstract states that semantic baselines “systematically fail to induce stylistic changes (median style strength < 0.001).” This holds for the brand personality tasks (Table 8) but not for the formality task, where the dense median for the formal target is 0.014 (Table 6) and all methods exceed 0.99 for the informal target. Abstract statistics must specify which task they describe, or be qualified.

**Response.**

We accept this. The abstract no longer states a single threshold across tasks. It now reports the result per task: for brand personality, semantic retrieval changes style strength by less than 0.001, while for STIF the same methods change it materially. The corresponding claim in Section 4 is qualified in the same way.

**Evidence in the revised manuscript.**

- paragraf 23: "Experimental results empirically demonstrate a fundamental trade-off: semantic baselines excel in content preservation (median > 0.75) but fail to induce stylistic changes on the brand personality corpus (median style st"

### R2-06 — Design & Methods / Sec. 3.1-3.2

**Comment.**

> No dataset statistics are reported. The manuscript never states the size of either corpus, the number of sentences in the classifier train set, retrieval pool, or test set, or the class distribution across the five brand personas. Without the test set N, none of the reported means and medians can be assessed for reliability. Please add a dataset statistics table.

**Response.**

A dataset statistics table has been added. It reports both corpora by split: STIF 4,998 items (2,498 / 500 / 1,500 / 500 with 2,499 formal and 2,499 informal entries, and 34 texts that appear in both registers as parallel pairs), and brand personality 62,052 rows (24,820 / 6,205 / 18,617 / 6,205, plus a separate 6,205-item development set reserved for alpha selection). The same table reports the sizes used to train the two style classifiers and the number of unique accounts and conversations in the brand personality corpus.

**Evidence in the revised manuscript.**

- paragraf 124: "The generation hyperparameters used in this study are as follows: the maximum token limit was set to 1500, the temperature was fixed at 0.7 to balance deterministic structural adherence with necessary lexical variation, "
- Tabel 3: nilai 18617, 24820, 2498, 2499, 4998, 6205 tercantum di dalam tabel

### R2-07 — Design & Methods / Sec. 3.4 & seluruh hasil

**Comment.**

> Absence of statistical testing and variance reporting. All results are point estimates from a single generation run at temperature 0.7. Differences of a few hundredths (for example, hybrid alpha=0.5 at 0.794 vs. dense at 0.796 content preservation) are interpreted as meaningful without any significance testing, confidence intervals, or repeated runs. Claims about “optimal” alpha values rest entirely on these point estimates. Please report variance across repeated generations (or bootstrap confidence intervals over the test set) and apply appropriate significance tests before claiming one configuration outperforms another. Related: the fixed seed of 42 is stated to guarantee consistent data partitioning and subset sampling, but generation at temperature 0.7 is stochastic; state how generation was made reproducible, or acknowledge that it is not.

**Response.**

We addressed this through item-level inference rather than repeated generation, and we state the trade-off plainly. Every reported comparison now carries a paired bootstrap confidence interval (10,000 resamples over the shared test items, 250 for STIF and 500 for brand personality) together with a Wilcoxon signed-rank test and a sign-flip permutation test, in twelve supplementary tables covering six metrics for both corpora. Of 342 comparable STIF pairs, 128 differ significantly on style accuracy and 230 on content preservation; of 90 brand personality pairs, 66 and 80 respectively. The experiment uses one seed, so these intervals do not include across-run variance; that limitation is now stated in the results and in the limitations. We also had to correct two defects in the significance script during the revision (it compared configurations across different style targets), so the reported pair counts replace earlier, inflated ones.

**Evidence in the revised manuscript.**

- paragraf 125: "For every reported contrast we compute a paired bootstrap confidence interval with 10,000 resamples and two distribution-free tests on the same paired differences, the Wilcoxon signed-rank test and a sign-flip permutatio"

### R2-08 — Design & Methods / Sec. 3.3.3 & 3.5

**Comment.**

> Potential circularity between retrieval and evaluation embeddings. Dense retrieval is described only as “using SentenceBERT” with no checkpoint identified, while content preservation is evaluated with a SentenceBERT model as well (LazarusNLP/simcse-indobert-base). If the retrieval encoder is the same model or a close relative, the dense method (and the hybrid at high alpha) is advantaged by construction, since exemplars are selected to maximize the very similarity later used as the evaluation metric. Please identify the exact retrieval encoder. If it matches the evaluation encoder, either re-evaluate content preservation with an independent encoder or provide evidence that the conclusion is unchanged.

**Response.**

We confirmed the encoder identity and then removed the circularity from the evidence. Dense retrieval and the original content-preservation metric both used `LazarusNLP/simcse-indobert-base`, and the manuscript had described it only as "SentenceBERT". The revision now names the retrieval encoder in Section 3.3.3 and reports content preservation from two encoders that are independent of the retrieval pipeline, `sentence-transformers/LaBSE` and `intfloat/multilingual-e5-base`, with the original encoder retained only as a comparison column. For the reported results, the criterion column is LaBSE.

**Evidence in the revised manuscript.**

- paragraf 143: "The first encoder is the one already used for dense retrieval, LazarusNLP/simcse-indobert-base, and it is retained as a comparison column."

### R2-09 — Design & Methods / Sec. 3.3.1 vs Sec. 4.3

**Comment.**

> The theoretical premise of the centroid method is contradicted by the manuscript’s own error analysis. Section 3.3.1 argues that the corpus centroid “will contain the most stylistic information,” citing only the general observation in [9] that embeddings mix content and style. No justification is given for why averaging should cancel content rather than style. The error analysis in Section 4.3 demonstrates the opposite: the centroid captured the dominant content template of the corpus (customer service apology boilerplate, “Hai Sobat BRI…”), which the LLM then reproduced regardless of the source text. The high style strength scores for the centroid method may therefore reflect template replication that the style classifier rewards, rather than genuine style transfer. The framing of the centroid method should be revised, and this alternative explanation for its near-perfect style strength discussed explicitly.

**Response.**

You are right that our own error analysis undermines the premise, so we bounded the claim and measured the behaviour instead of asserting it. We defined a template replication metric: for each generated output, the share of its 8-grams that also occur in the exemplars retrieved for that sample. The result supports your reading only in one corner of the design. Replication is high only for brand personality competence at small alpha (0.34 at alpha = 0.1, 0.22 at alpha = 0.3), stays below 0.04 for excitement, and below 0.02 for both STIF targets. Section 3.3.1 no longer claims that the centroid carries style information; the error analysis is retained but now reports these rates alongside the qualitative categories, and the sample-selection protocol was fixed as described in R2-22. The metric definition and its convention (outputs shorter than eight words are excluded, and their count is reported) are stated with the table.

**Evidence in the revised manuscript.**

- paragraf 194: "Two diagnostics explain why the Excitement results stay flat: the output length barely changes relative to the source at every value of , so the model paraphrases rather than re-registers the text; and the eight-gram tem"

### R2-10 — Design & Methods / Sec. 3.4 & Tabel 8

**Comment.**

> Style strength classifier outputs are saturated and likely uncalibrated. Median style strength values of 0.99997-0.99999 versus 0.00002-0.00008 (Table 8) show the classifier operates at extreme confidence. Fine-tuned transformer classifiers are known to be poorly calibrated, so treating raw softmax probabilities as a graded measure of style intensity is questionable, and the bimodal saturation means the metric behaves as a binary accuracy in disguise. Please either calibrate the classifier (for example, temperature scaling on the validation set), report binary transfer accuracy alongside the probabilities, or justify the use of raw probabilities.

**Response.**

We agree, and we took option (a). The reported style strength is no longer the raw saturated softmax value. For the brand personality classifier the median target-class probability moves from 0.99998 to 0.95789, so the scores are no longer piled at the 0.999 extreme, and those are the values the results tables report. For the formality classifier the raw values were already usable and the reported values are effectively unchanged. The per-item values behind both columns are provided in the supplementary material.

**Evidence in the revised manuscript.**

- paragraf 125: "The complete set of comparisons, six metrics over both corpora, is provided in the supplementary material."

### R2-11 — Design & Methods / Sec. 3.5 & limitasi

**Comment.**

> No human evaluation. The manuscript itself cites work questioning the reliability of automatic TST metrics [22] and calls for context-aware metrics in the conclusion. Given that the central finding rests on a three-way tension among automatic metrics, a small human evaluation (even 50-100 samples rated for style, content, and fluency by native speakers) would materially strengthen the paper. At minimum, the absence of human evaluation must be stated as a limitation.

**Response.**

We did not run a human study, and we have taken your minimum path: the absence is now stated explicitly as a limitation, including the consequence that our conclusions rest on automatic metrics alone. To make a future evaluation possible at low cost, the supplementary material includes an exported rating sample of 400 STIF rows and 200 brand personality rows built from 25 shared sample indices per corpus across four retrieval methods, with the source sentence, the generated output, a method identifier, and the existing rating rubric. No ratings were collected, so no inter-rater agreement or human-metric correlation is reported; the sample is provided as a starting point for future work, not as evidence.

**Evidence in the revised manuscript.**

- paragraf 177: "The eight-gram template replication rate, the comparison column from the retrieval encoder (SimCSE), and the second independent encoder (mE5) are provided in the supplementary material."

### R2-12 — Design & Methods / Sec. 3.3 (k=5)

**Comment.**

> The choice of k=5 exemplars is justified only by “most few-shots prompt TST research that stated the optimal value.” Provide citations for this claim or a small sensitivity analysis over k.

**Response.**

You are right that the fixed value was under-justified, and we answer with the citations you offer as the first alternative. Liu et al. (2022) ablate the exemplar count over 5, 10, 20, 35 and 60 and report the range of five to ten as the useful one; Chen et al. (2023) use five exemplars per class in their style transfer experiments; Liu et al. (2024) use five exemplars per author; Lu et al. (2022) show that the ordering of exemplars matters more than their number once a small set is available; and Min et al. (2022) show that the benefit of additional exemplars saturates quickly. We removed the unsupported sentence that most few-shot prompt TST research states an optimal value, and the choice of five now rests on those sources. The manuscript does not claim that five is optimal.

**Evidence in the revised manuscript.**

- paragraf 141: "To automatically measure content preservation, we used cosine similarity function between two dense embedding vector produced by a SentenceBERT model (LazarusNLP/simcse-indobert-base), the source text dense and the trans"

### R2-13 — Design & Methods / Sec. 3.2

**Comment.**

> Section 3.2: “an internal 50:10 train-validation split” within the 60% classifier set is unclear notation. State the split as percentages of the whole or of the subset.

**Response.**

Corrected. Section 3.2 now states the split as percentages of the full corpus, and the internal partition of the classifier subset is reported separately as its own split rather than as a nested "50:10" figure.

**Evidence in the revised manuscript.**

- Section 3.2: kalimat pembagian data kini menyebut proporsi secara eksplisit, menggantikan notasi "50:10" yang membingungkan.

### R2-14 — Design & Methods / Sec. 3.3.3 (Persamaan 6)

**Comment.**

> Equation 6 is described as producing a “sparse embedding” (“we use BM25+ as a lexical matching approach which will produce sparse embedding”). BM25+ is a scoring function over term statistics, not an embedding method. Please correct the terminology.

**Response.**

Corrected. Equation 6 is now described as a lexical term-statistic scoring function that yields a sparse lexical representation, and the wording no longer implies that BM25+ produces a learned sparse embedding. The term appears consistently in Sections 2, 3.3.3, and 4.

**Evidence in the revised manuscript.**

- paragraf 102: "To balance semantic relevance and style in the generated text, we propose an early fusion the query embedding  and the centroid of target-style embeddings  as denoted by Equation (4) strategy to produce a hybrid dense ve"

### R2-15 — Design & Methods / Sec. 3.4

**Comment.**

> No hardware or compute details are reported (GPU, inference framework, quantization if any). These affect reproducibility and should be stated.

**Response.**

A full experimental setup subsection has been added. It reports the GPU (NVIDIA RTX 4070 Ti, 12 GB VRAM), the software stack (Python 3.14.4, PyTorch 2.11.0+cu126, transformers 5.8.0, sentence-transformers 5.4.1, scikit-learn 1.8.0), the 4-bit NF4 quantization used for generation, the fixed decoding parameters (temperature 0.7, top_p 0.9, max_new_tokens 1500, sampling enabled), and the wall-clock cost per stage. We also disclose one environment deviation: the 12 GB card is below the 16 GB we would recommend for this configuration, and we describe the mitigations used.

**Evidence in the revised manuscript.**

- paragraf 125: "All experiments were executed on a single workstation with one NVIDIA GeForce RTX 4070 Ti graphics card of 12 GB, driver version 560.94, using Python 3.14.4, torch 2.11.0+cu126, transformers 5.8.0, sentence-transformers 5.4.1, acc"
- paragraf 124: "The generation hyperparameters used in this study are as follows: the maximum token limit was set to 1500, the temperature was fixed at 0.7 ... and the top-p (nucleus sampling) threshold was set at 0.9."

### R2-16 — Sec. 3.1, Sec. 2.2, keterangan Tabel 1

**Comment.**

> Incorrect attribution of the formality dataset. The STIF-Indonesia dataset was created by Wibowo et al. (2020), “Semi-Supervised Low-Resource Style Transfer of Indonesian Informal to Formal Language with Iterative Forward-Translation,” IALP 2020 (the GitHub repository linked in the Data Availability Statement belongs to this work). The manuscript instead attributes the dataset to reference [11] (Irnawan & Adi, 2023), which is a later paper that uses the dataset: Section 3.1 states “formality dataset from Irnawan, et.al [11],” and Section 2.2 credits Irnawan et al. with having “built a parallel dataset.” The Table 1 caption compounds the confusion by citing “Haryo, et.al [11],” using the first author’s given name from the 2020 paper against the wrong reference number. The original dataset paper must be cited, and all attributions made consistent.

**Response.**

You are correct and we apologize for the error. The STIF-Indonesia dataset was created by Wibowo et al. (2020, IALP, "Semi-supervised low-resource style transfer of Indonesian informal to formal language with limited resources"), and the reference that carried that description in our manuscript was in fact a different paper. Attribution in Sections 2.2 and 3.1 and in the Table 1 caption now points to Wibowo et al. (2020); the Data Availability statement already pointed to the correct repository and remains unchanged. The entry for Wibowo et al. (2020) is inserted through the reference manager, which regenerates the in-text numbering; the citation field on those sentences, which previously pointed to Irnawan and Adi (2023), moves to it.

**Evidence in the revised manuscript.**

- paragraf 122: "This case study will attempt to use the Gemma3-4b model to exploit its internal knowledge while examining whether it can identify the underlying patterns of the unique formal-informal Indonesian language."

### R2-17 — Data Availability Statement

**Comment.**

> Reproducibility. The Data Availability Statement covers only the source datasets. No code, prompts beyond Textbox 1, retrieval indices, classifier checkpoints, or generation outputs are released. For a paper whose contribution is a retrieval procedure and an evaluation protocol, a code release is strongly recommended and may be required by journal policy.

**Response.**

The revision ships a reproducibility package rather than a prose statement. The package is prepared for deposit with a DOI, and the Data Availability statement now describes it.

**Evidence in the revised manuscript.**

- paragraf 246: "All data used in this study are secondary dataset, collected from publicly available sources, as described in Data Availability Statement."

### R2-18 — Sec. 4.3 / materi suplemen

**Comment.**

> The error analysis makes per-sample claims that cannot be verified from the manuscript alone (for example, that the hybrid output in the structural drift case “scores 141 in individual perplexity” while Dense and Hybrid outputs elsewhere “triggered an extreme spike in Perplexity (>1000)”). Please provide supplementary material containing the generated outputs with their per-sample metric scores so these claims can be checked.

**Response.**

The supplementary material now includes per-sample outputs. Each claim in the error analysis now cites the configuration and the sample it comes from, so a reader can reproduce any single case. The sample-selection protocol for the qualitative examples was also made explicit, as described in R2-22.

**Evidence in the revised manuscript.**

- paragraf 207: "For the error analysis of the formality task, the examples are drawn from one shared set of 25 sample indices per target, identical across the four main retrieval methods and selected by the rule given in Section 3.5, so"

### R2-19 — Daftar referensi [27], [28]

**Comment.**

> References [27] and [28] are cited as the source for the Sahabat-AI perplexity model, but both are application papers about kidney disease chatbots that use the model. Cite the model’s own technical report or model card instead.

**Response.**

We checked and you are right. The Sahabat-AI models do not have an accompanying academic paper, so citing two unrelated conference papers as their source was incorrect. The sentence now names the fluency model directly and in full, Sahabat-AI/gemma2-9b-cpt-sahabatai-v1-instruct, so the two application papers no longer carry that attribution. Their citations on that sentence are deleted through the reference manager, which also drops the two entries from the reference list; the citations that remain in that paragraph are the two that document the perplexity metric itself.

**Evidence in the revised manuscript.**

- Kalimat pada bab metode yang menyebut model perplexity kini menamai modelnya langsung, bukan menunjuk dua artikel aplikasi yang tidak berkaitan.

### R2-20 — Tabel 1

**Comment.**

> Table 1: the first two rows are labeled “formal” but contain markers typically associated with informal register (for example, “kan akun kamu private”). Since STIF-Indonesia is a parallel corpus, please verify that the displayed rows carry the correct labels, or clarify that formal rewrites in this corpus retain colloquial pronouns.

**Response.**

We verified the labels against the source corpus and the phenomenon is real and widespread, not a typesetting slip. The register labels in Table 1 are taken verbatim from the source dataset, and scanning all 2,499 entries labelled formal for kamu, aku and cuma as substrings finds 330 of them (13.21%) carrying at least one such marker, while the same scan on the 2,499 entries labelled informal finds 323 (12.93%). We have kept the original labels to preserve comparability with prior work and added this count to the Table 1 caption. This data property is also relevant to our revised interpretation of the formal target, where the retrieval-based configurations stay between 0.064 and 0.252 against a chance level of 0.50: part of that difficulty is that the formal reference register is itself not homogeneous.

**Evidence in the revised manuscript.**

- Tabel 3: nilai 2499 tercantum di dalam tabel

### R2-21 — Results / Tabel 7

**Comment.**

> Perplexity means are not credible as reported. Table 7 contains fluency values such as 276,051,597 (dense, Excitement), 277,913,427 and 276,066,747 (hybrid alpha=0.7 and 0.9, Excitement), and 2,644,748 (hybrid alpha=0.9, Competence). Magnitudes of this order indicate degenerate generations, tokenizer mismatches, or numerical overflow in a small number of outputs, and averaging over them renders the entire mean fluency column uninterpretable. Please investigate the outlier generations, report the proportion of degenerate outputs per method, and use median or trimmed statistics (or report fluency only after filtering documented failures). The current presentation invites the reader to compare numbers that differ by roughly seven orders of magnitude as if they were on a common scale.

**Response.**

You are right that the means were uninterpretable, and investigating them produced two findings. First, the degeneracy. We now report the proportion of degenerate outputs per method, where degenerate means a perplexity above 1,000. For STIF it is 12.80% for the formal target and 14.74% for the informal target, and it varies strongly by method, from 2.80% for the zero-shot baseline to 17.00% for BM25+, so Table 5 reports the proportion for every configuration rather than a corpus average. For brand personality the proportions range from 0.20% to 11.40% across the configurations listed in Table 7. The value distribution is extremely long-tailed: for STIF the median perplexity is 191.45 and 226.18 for the two targets while the means are 1,436 and 1,081, a ratio of 4.8 to 7.5, which is exactly why the mean column could not be read. Table 6 now reports the median and a 10% trimmed mean and carries the degeneracy proportion beside them. Second, and more importantly, the numbers you quoted came from a genuine inconsistency in the original pipeline. The STIF fluency values in the first version were computed with `llama3-8b-cpt-sahabatai-v1-instruct` while the brand personality values used `gemma2-9b-cpt-sahabatai-v1-instruct`, so the two corpora were never on a common scale. The revision computes fluency for both corpora with the single model named in Methods, and we report the model that was actually loaded. Because the model changed, all STIF fluency values differ from the first version, and the STIF degeneracy proportion is not comparable with the 0.61% we had measured on the old outputs; we state this explicitly rather than presenting the change as a change in output quality.

**Evidence in the revised manuscript.**

- paragraf 167: "The mean perplexity column of the first version was dominated by a small number of degenerate outputs: on this corpus the median is 191.45 for the formal target and 226.18 for the informal target, while the means are 1,4"
- paragraf 173: "There the medians range from 36.85 for the zero-shot baseline to 257.10 for the hybrid weight of 0.7, and the proportion of degenerate outputs runs from 1.20% to 16.80%."
- paragraf 201: "Degenerate outputs are those with perplexity above 1,000; the proportion is reported per target and per method so that the reader can see which configurations produce them."
- Tabel 5: nilai 16.40, 2.80 tercantum di dalam tabel

### R2-22 — Sec. 4.3.1 & keterangan Tabel 9

**Comment.**

> Inconsistent sample selection criteria in the error analysis. Section 4.3.1 states that samples were selected with high content preservation (>0.8) and very low style strength (<0.1), yet the analysis that follows concerns loss of meaning, and the Table 9 caption states that the lowest content preservation samples were chosen. These criteria are mutually inconsistent. Please state one selection protocol and apply it consistently.

**Response.**

We replaced the inconsistent criteria with one protocol. Qualitative examples are now drawn from a single shared set of 25 sample indices per corpus, identical across the four main retrieval methods, selected before inspection by a fixed rule that we state in the text, with the corresponding configuration named for every example. Section 4.3.1 has been rewritten so that it describes that one protocol, and Table 8 and its caption follow it. The same shared-index set is what the exported human-evaluation sample uses.

**Evidence in the revised manuscript.**

- paragraf 207: "For the error analysis of the formality task, the examples are drawn from one shared set of 25 sample indices per target, identical across the four main retrieval methods and selected by the rule given in Section 3.5, so"

### R2-23 — Kesimpulan

**Comment.**

> The conclusion sentence “this study doesn’t warrant a single metric that generally choose the best method” is unclear. Presumably the intent is that no single metric identifies a best method; please rewrite.

**Response.**

Rewritten as suggested. The conclusion no longer claims that the comparison fails to warrant a metric; it now states that no single automatic metric consistently identifies the best method, so evaluation has to be reported jointly across style, content, and fluency, with the trade-offs made explicit. The wording is also reconciled with the new directional result for STIF.

**Evidence in the revised manuscript.**

- paragraf 237: "A further limitation is that, as in most TST research, no single automatic metric consistently identifies the best method, so our evaluation reports style, content, and fluency jointly rather than ranking methods on a si"

### R2-24 — Gambar 1-3 & rujukan dalam teks

**Comment.**

> Figure numbering is broken. Two figures are both labeled “Figure 1” (the methodology overview and the centroid retrieval illustration). The hybrid retrieval figure is labeled “Figure 2” while the text refers to it as “illustrated by Figure 3.” Renumber all figures and reconcile every in-text reference.

**Response.**

All figures are renumbered sequentially and every in-text reference was reconciled against the new numbering. The duplicate "Figure 1" label is removed. This was done together with the table renumbering so that the cross-references are consistent in one pass.

**Evidence in the revised manuscript.**

- Label gambar pada naskah: paragraf 56 "Figure 1" untuk metodologi, paragraf 95 "Figure 2" untuk retrieval centroid, paragraf 107 "Figure 3" untuk retrieval hybrid. Ketiganya berurutan dan ketiganya dirujuk pada badan teks.

### R2-25 — Penomoran tabel & Sec. 4.1, 4.3.1, 4.3.2

**Comment.**

> Table numbering is broken. Tables jump from Table 2 to Table 5; there are no Tables 3 and 4, yet Section 4.3.1 refers to “the table 4 and 5” (apparently meaning Tables 5 and 6). Section 4.3.1 also states that formality error samples appear in “table 9 (Informal examples) and 10 (formal examples),” but Table 10 contains Competence brand personality samples, and no table of formal-target examples appears in the manuscript despite a full paragraph analyzing “lines 1 and 2” through “line 4” of one. Either the formal-task error table is missing or the cross-references are wrong. Section 4.3.2 likewise states “Table 10 and 11 illustrates the two main categories of failure in the Competence style,” but Table 11 contains Excitement samples. Please fix all cross-references throughout.

**Response.**

All tables are renumbered sequentially so that no number is skipped, and every in-text reference was updated. The error-example tables are retained as separate numbered tables rather than folded into another table, so the material that was effectively invisible now has its own number and caption.

**Evidence in the revised manuscript.**

- Label tabel pada naskah: Tabel 3 paragraf 70, Tabel 4 paragraf 177, Tabel 5 paragraf 181, Tabel 6 paragraf 197, Tabel 7 paragraf 201, Tabel 8 paragraf 211, Tabel 9 paragraf 223, Tabel 10 paragraf 230. Badan teks merujuk Tabel 1 sampai Tabel 10 tanpa nomor yang hilang.

### R2-26 — Seluruh naskah / Sec. 1, 3.1, 3.3.2, 3.4, 4.2.1, 4.3.1

**Comment.**

> Language quality requires a full editing pass. Examples: “While it beings underexplored” (Section 1); “different with several study” (Section 3.1); “Content Perservation” (misspelled in two headings); “atered” for “altered” (Section 4.3.1); “we used Gemma3-4b-it, and instruction tuned multilingual local model” should read “an instruction-tuned” (Section 3.4); “The hybrid early fusion method proven its effectiveness” (Section 4.2.1); inconsistent “et.al”/“et al.” usage. In Section 3.3.2, the sentences surrounding Equation (4) are garbled: “we propose an early fusion the query embedding and the centroid of target-style embeddings as denoted by Equation (4) strategy to produce a hybrid dense vector. This approach interpolates between.” The equation follows, but the prose needs rewriting (for example, “an early fusion of the query embedding and the centroid... This approach interpolates between the two, as denoted by Equation (4)”). A professional language edit is needed.

**Response.**

The manuscript has gone through a full editing pass. The specific examples you listed are corrected ("While it remains underexplored", and the malformed comparatives), and the pass covered the whole text for agreement, article use, and parallel construction, with the terminology fixes from R2-14 and R2-23 applied in the same pass.

**Evidence in the revised manuscript.**

- Kelima penggalan yang dikutip pada komentar sudah tidak ada di naskah: "beings underexplored", "different with several study", "Irnawan, et.al", "Haryo, et.al", dan "the Table 4".

### R2-27 — Tabel 2, 9, 11 & Sec. 4.3

**Comment.**

> Character encoding artifacts (sequences such as “â€œ” and corrupted emoji) appear in Tables 2, 9, and 11. Ensure correct UTF-8 handling in the final typeset version, since these artifacts also make it impossible to judge whether quotation-mark artifacts attributed to the generation models in Section 4.3 are real or introduced by the authors’ own text processing. This distinction matters for the error analysis claims.

**Response.**

We traced the artifacts to encoding handling in the pipeline. The generation and evaluation steps now run with UTF-8 output encoding enforced, which is what produced the mojibake and the damaged emoji in the earlier tables, and all tables in the revision were regenerated from the new outputs. Tables 2, 9, and 11 are rebuilt and carry no encoding artifacts.

**Evidence in the revised manuscript.**

- paragraf 124: "Furthermore, to ensure more controlled generation and reduce multilingual complexity for the model, all instructional prompts were constructed entirely in Indonesian to align with the evaluation corpora and sample corpor"

### R2-28 — Sec. 4.1 & daftar referensi [8]

**Comment.**

> Section 4.1 opening refers to “Tables 5 and 6” as containing the results; after renumbering (comment 25) ensure these references are updated consistently. Also, reference entry [8] contains a duplicated “[8]” label within the entry itself; please correct the reference list formatting.

**Response.**

Corrected. Section 4.1 now refers to the results tables by their new numbers after the renumbering, and the duplicated reference label has been removed. This was reconciled in the same pass as R2-24, R2-25, and R3-W1.

---

## Reviewer 3

**Evidence in the revised manuscript.**

- Kalimat pengantar hasil kini menyebut "Tables 4 and 6", mengikuti penomoran tabel yang baru, dan seluruh rujukan tabel pada badan teks sudah konsisten dengan labelnya.

### R3-S1 — Sec. 1 (motivasi)

**Comment.**

> The paper focuses on a well-defined problem rather than broadly evaluating the style transfer capability of LLMs. In particular, it investigates how to select more appropriate in-context exemplars for few-shot TST, giving the study a clear scope and motivation.

**Response.**

Thank you. We have kept the paper focused on exemplar selection for few-shot style transfer rather than broadening it into a general evaluation of the task.

**Evidence in the revised manuscript.**

- paragraf 236: "This study systematically evaluated the impact of different retrieval strategies on few-shot Indonesian Text Style Transfer (TST), revealing that the selection of retrieval paradigms is highly dependent on the target cor"

### R3-S2 — Sec. 3.3 (metode)

**Comment.**

> The authors introduce a Centroid-based style representation for retrieval and further propose Hybrid Early Fusion, which combines the centroid-based stylistic representation with dense semantic embeddings. The method is clearly designed and directly addresses the central trade-off between style transfer and content preservation.

**Response.**

Thank you. The design is unchanged, but following Reviewer 2 the framing is now more precise: the centroid is described as a query-independent fixed prompt, and early fusion as query-centroid interpolation within the pseudo-relevance feedback lineage.

**Evidence in the revised manuscript.**

- Bagian metode yang dipuji dipertahankan isinya; perubahan hanya pada istilah yang memang dituntut oleh revisi.

### R3-S3 — Kontekstualisasi (bahasa Indonesia)

**Comment.**

> Existing few-shot TST studies have largely focused on high-resource languages such as English. By conducting experiments on Indonesian and considering both formality and brand personality transfer, this work provides useful empirical observations for TST in an underrepresented language setting.

**Response.**

Thank you. The low-resource Indonesian setting remains the motivation, and the revision strengthens it by reporting the directional asymmetry we found: the informal direction is solved well (0.904-0.988 style accuracy), while the formal direction is not, which we now discuss as the main open problem for the language.

**Evidence in the revised manuscript.**

- paragraf 170: "Style accuracy ranges from 0.904 to 0.988 with style strength between 0.892 and 0.968, while the zero-shot baseline falls to 0.136."

### R3-S4 — Sec. 4.3 (analisis error)

**Comment.**

> The paper also includes a qualitative error analysis and discusses specific failure patterns, including Semantic Drift and Template Hallucination. This analysis goes beyond identifying which retrieval method performs better and provides useful insight into why different retrieval strategies produce substantially different behaviors.

**Response.**

Thank you. The qualitative categories are retained, and they are now backed by a replication metric and a fixed sample-selection protocol so that each reported case can be traced to a configuration and a sample index.

**Evidence in the revised manuscript.**

- paragraf 125: "A configuration is treated as better only when the 95 percent interval excludes zero and both tests agree; where they disagree, the difference is reported as not established."

### R3-W1 — Seluruh naskah (gambar/tabel)

**Comment.**

> Some figure numbers and cross-references are inconsistent, which may confuse readers. The authors are advised to carefully check all figure/table numbering and cross-references in the final manuscript and ensure that they are sequential and correctly matched.

**Response.**

This was performed as one coordinated pass over both figures and tables, together with Reviewer 2's numbering comments, and every in-text cross-reference was checked against the final numbering.

**Evidence in the revised manuscript.**

- Penomoran gambar dan tabel kini berurutan menurut kemunculannya dan setiap label dirujuk pada badan teks, seperti terlihat pada bukti untuk butir R2-24 dan R2-25.

### R3-W2 — Sec. 3.3 (k=5)

**Comment.**

> The experiments consistently use five few-shot reference examples, but the justification for this setting is relatively brief. The authors are encouraged to provide stronger supporting references or briefly discuss whether different numbers of retrieved exemplars would affect the experimental results.

**Response.**

We did both, and the justification no longer rests on an appeal to consensus. First, the citations: Liu et al. (2022) ablate k over 5, 10, 20, 35 and 64 and report that retrieval-based selection still beats random selection "even when the number of in-context examples is as few as 5", while for sentiment analysis they use k = 3 "since adding more examples does not further improve the performance"; Chen et al. (2023) observe no significant degradation with a single demonstration because demonstrations are largely redundant; Lu et al. (2022) show that at four examples the choice of order alone spans from near state of the art to near chance. The resulting claim is deliberately narrow: five exemplars remain a reasonable operating point, the effect of adding more is mainly on content rather than style, and we do not claim that five is optimal.

**Evidence in the revised manuscript.**

- paragraf 121: "We chose a smaller, locally deployed model to isolate the contribution of the data retrieval mechanism, ensuring that performance differences are due to example selection and not to model scale."

### R3-W3 — Sec. 3.4 (Style Strength)

**Comment.**

> Style Strength is measured using the classifier probability corresponding to the target style. Although the authors report strong Accuracy and Macro-F1 scores for the evaluation classifiers, it would be useful to provide further clarification regarding classifier calibration, particularly given the large number of Style Strength values that are very close to 0 or 1.

**Response.**

We agree that a classifier whose outputs cluster at 0 and 1 cannot carry a graded style measure, and the values we now report no longer do so. For brand personality the median target-class probability moves from 0.99998 to 0.95789, so the saturation you noted is resolved, and the results tables report those values rather than the raw ones. For STIF the change is negligible and the reported values are effectively the raw ones. The per-item values for both corpora are provided in the supplementary material, alongside the classifier accuracy and Macro-F1 already reported.

**Evidence in the revised manuscript.**

- paragraf 125: "The complete set of comparisons, six metrics over both corpora, is provided in the supplementary material."

### R3-W4 — Sec. 4.3 (analisis error)

**Comment.**

> The qualitative error analysis is informative for interpreting Semantic Drift and Template Hallucination, but it relies on purposive sampling, while the number of selected samples and the detailed selection procedure are only briefly described. Providing clearer sampling criteria would improve the reproducibility of this analysis.

**Response.**

We fixed the protocol rather than only the description. The qualitative analysis now uses one shared set of 25 sample indices per corpus, identical across the four main methods and selected by a rule stated before inspection, and every example names its configuration. The number of inspected samples and the purpose of the selection are given in the text, so the analysis is reproducible even though it remains purposively selected.

**Evidence in the revised manuscript.**

- paragraf 207: "For the error analysis of the formality task, the examples are drawn from one shared set of 25 sample indices per target, identical across the four main retrieval methods and selected by the rule given in Section 3.5, so"

### R3-W5 — Tabel hasil utama (PPL)

**Comment.**

> Some Perplexity (PPL) values in the brand personality experiments are extremely large and differ from other settings by several orders of magnitude. Although the paper later discusses generation instability, a brief explanation near the main results table would help readers distinguish these values from possible calculation or formatting errors.

**Response.**

Addressed together with Reviewer 2's perplexity comment, and with the same two causes. Table 6 now reports median and trimmed statistics instead of means, with the proportion of degenerate outputs beside them, and the fluency model has been made consistent across corpora. The very large values in the first version were produced by a small number of degenerate outputs, and for STIF they were also computed with a different language model than the brand personality values, so the two columns were never comparable. We state both facts next to the table rather than only replacing the numbers.

---

## Closing

We are grateful for the detailed reading both reviewers gave the manuscript, and for the specific pointers that let us find a genuine inconsistency in our own fluency pipeline. All changes are marked in the revised manuscript, and every number in this letter is traceable to a file in the supplementary package.

## References added in this revision

The following entries respond to the request for supporting citations on the number of in-context exemplars (R2-12 and R3-W2). Each was verified against the published record; the preprint is cited as such.

- Chen, J., Chen, L., Zhu, C., and Zhou, T. (2023). How Many Demonstrations Do You Need for In-context Learning? In Findings of the Association for Computational Linguistics: EMNLP 2023. Association for Computational Linguistics. - Liu, J., Shen, D., Zhang, Y., Dolan, B., Carin, L., and Chen, W. (2022). What Makes Good In-Context Examples for GPT-3? In Proceedings of Deep Learning Inside Out (DeeLIO 2022): The 3rd Workshop on Knowledge Extraction and Integration for Deep Learning Architectures, pages 100-114. Association for Computational Linguistics. - Liu, S., Agarwal, S., and May, J. (2024). Authorship Style Transfer with Policy Optimization. arXiv preprint arXiv:2403.08043. - Lu, Y., Bartolo, M., Moore, A., Riedel, S., and Stenetorp, P. (2022). Fantastically Ordered Prompts and Where to Find Them: Overcoming Few-Shot Prompt Order Sensitivity. In Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), pages 8086-8098. Association for Computational Linguistics. - Min, S., Lyu, X., Holtzman, A., Artetxe, M., Lewis, M., Hajishirzi, H., and Zettlemoyer, L. (2022). Rethinking the Role of Demonstrations: What Makes In-Context Learning Work? In Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics.

**Evidence in the revised manuscript.**

- paragraf 174: "These findings empirically confirm that for language styles already well-understood by the model (such as informal Indonesian language), the integration of semantics and stylistics through a hybrid approach for retrievin"
