# EGLFA: Evidence-Gated Longitudinal Framework Analysis

## Positioning

**Evidence-Gated Longitudinal Framework Analysis (EGLFA)** is a Wenshan-defined composite specification for personal writing corpora. It is **not the established name of a published research method**.

Its intended use is:

> Evidence-gated longitudinal thematic analysis and knowledge-map visualization of a person's writing corpus.

It combines:

- the [Framework Method](https://doi.org/10.1186/1471-2288-13-117) for auditable case-by-code matrices;
- [qualitative content analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC7932246/) for systematic coding and category development;
- [grounded-theory open and axial coding](https://link.springer.com/chapter/10.1007/978-3-030-15636-7_4);
- [longitudinal qualitative analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC8459825/) for change over time;
- [argument mining](https://aclanthology.org/J19-4006/) for claims, premises, evidence, and support relations;
- human interpretability validation motivated by [Reading Tea Leaves](https://papers.nips.cc/paper_files/paper/2009/hash/f92586a25bb3145facd64ab20fd554ff-Abstract.html).

Wenshan is neither topic modeling nor embedding clustering. It treats canonical articles as analysis units, uses a framework matrix as the audit structure, applies an evidence gate to visible peaks, and synthesizes the author's current answer from longitudinal claims.

## Fixed eight-step method

### 1. Bound the corpus

Record the author, selected files, time range, document types, and authorship. Exclude third-party references, prompts, manuals, templates, empty files, unfinished fragments, and non-author work.

Do not claim longitudinal analysis when reliable document dates or a meaningful time range are unavailable. Repair the dates first, or downgrade the output to an evidence-gated framework map without early, revised, or stable temporal claims.

### 2. Fix the analysis unit

One version-resolved canonical article is one independent analysis unit. Drafts, finals, and rewrites never add duplicate altitude.

### 3. Open-code every article

Extract at least:

```json
{
  "scene": [],
  "industry": [],
  "role": [],
  "practice": [],
  "knowledge_domain": [],
  "claim": "",
  "premises": [],
  "evidence": [],
  "date": "",
  "confidence": 0.0
}
```

### 4. Axially code candidate peaks

First form any number of evidence-backed candidate subpeaks. A candidate label must be a noun or noun phrase anchored to a scene, industry, role, practice, or knowledge domain. Reject full conclusions, quotes, slogans, unreviewed folder names, and incidental vendor repetition.

Then audit the **mountain-range relations**:

1. Declare one main-mountain classification axis, such as `primary_problem_space`.
2. Require MECE main mountains on that axis. Merge true synonyms and duplicate labels, but keep distinct related domains as separate mountains.
3. If a candidate is a medium, format, tool, method, or analytical perspective contained by another candidate, retain it as an auditable subpeak rather than a peer mountain.
4. Keep one altitude-bearing primary mountain per article; cross-mountain relations never duplicate counts.
5. Record strength and rationale for important mountain pairs, such as shared scene, practice, causal connection, or longitudinal transition.
6. Relation strength controls proximity and ridge connection, not article membership.
7. Do not impose a fixed visible mountain limit. Every interpretable, evidence-gated, MECE main mountain may enter the same range.
8. Handle large ranges through scale, label collision, and progressive detail rather than deleting themes.

### 5. Apply the evidence gate

A visible peak requires at least three independent canonical articles, an explainable assignment for every article, subtitle coverage of most included articles, and one altitude-bearing primary peak per article. No evidence means no peak.

### 6. Audit mountain boundaries

Answer six fixed questions:

1. Does the peak absorb more than half of all eligible articles?
2. Does it contain at least three stable subthemes?
3. Can any sample of five articles be explained as belonging to it?
4. Does the subtitle cover at least 70% of its articles?
5. Would a split produce subpeaks with at least three articles each?
6. Is the candidate only a medium, format, method, tool, or analytical perspective contained by another mountain?

If the first two answers are yes and any of questions three through five is no, or question six is yes, require human review. Persist the review in terrain data rather than leaving it only in the Agent conversation.

Also audit the complete range: every important spatial relation needs an evidence-backed rationale, and unrelated mountains must not be pulled together merely for layout convenience.

### 7. Synthesize the current answer

Do not freely generate the subtitle. Extract each claim, merge synonymous claims, find counterexamples and conflicts, order claims by time, separate early, revised, and stable claims, then write the current answer.

Preferred full form:

> In **[domain]**, the author's recurring answer is: **[stable judgment]**.

The map may display only the stable judgment.

### 8. Test stability

Analyze the same corpus independently three times. Require:

- peak-count delta ≤ 1;
- core-label semantic agreement ≥ 80%;
- primary-assignment Jaccard ≥ 0.75;
- 100% identical altitude counts;
- every evidence item traceable to source.

If the thresholds fail, label the result as pending review rather than a stable knowledge map.

## Map semantics

- Article count represents accumulated writing volume, not knowledge level or correctness.
- The peak label represents a recurring concrete domain.
- The public map is one range containing every evidence-gated mountain.
- Mountain distance represents reviewed relation strength, never embedding distance.
- Local density represents the concentration of related mountains and evidence.
- The subtitle represents the author's current stable answer in that domain.
- Time strata represent early, revised, and stable claims.
- Evidence points are independent canonical articles with source traceability.
- Contours are generated from the combined altitude fields of all mountains. Related nearby peaks share ridges and saddles while distant peaks remain sparse. High-resolution smoothing keeps the global linework fluid. Evidence-point jitter never represents embedding distance.
