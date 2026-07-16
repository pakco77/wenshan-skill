# Data contract

The renderer consumes two auditable layers under `Cognitive Map/Agent Atlas/`.

## Card

Store one JSON file per reviewed document at `cards/<stable-id>.json`:

```json
{
  "version": 2,
  "source": {
    "path": "relative/path/article.md",
    "hash": "sha256",
    "title": "Original source title",
    "date": "2026-07-01",
    "authorship": "self"
  },
  "decision": {
    "include": true,
    "document_kind": "published_article",
    "version_family": "optional-family-slug",
    "canonical": true
  },
  "interpretation": {
    "scene": [],
    "industry": [],
    "role": [],
    "practice": [],
    "knowledge_domain": [],
    "claim": "The article's central claim.",
    "premises": ["A premise supporting the claim."],
    "evidence": ["A short source-grounded excerpt or paraphrase."],
    "confidence": 0.84
  }
}
```

Only `decision.include: true` and `decision.canonical: true` cards can add altitude. `source.path` must be unique inside a mountain.

## Terrain

Store the reviewed scene or industry clusters at `wenshan-terrain.json`:

```json
{
  "version": 6,
  "analysis_method": "EGLFA",
  "generated_at": "2026-07-16T10:30:00+08:00",
  "semantic_contract": "mountain_title_is_agent_identified_scene_or_industry_keyword",
  "corpus": {
    "author": "Author nickname",
    "time_range": ["2025-01-01", "2026-07-01"],
    "document_kinds": ["draft_article", "published_article"],
    "authorship": "self",
    "canonical_units": 54
  },
  "stability_review": {
    "runs": 3,
    "peak_count_delta": 0,
    "label_semantic_agreement": 0.86,
    "primary_assignment_jaccard": 0.79,
    "altitude_exact": true,
    "all_sources_traceable": true,
    "status": "passed"
  },
  "range_review": {
    "layout_method": "reviewed_relation_graph",
    "classification_axis": "primary_problem_space",
    "primary_assignment_exclusive": true,
    "displayed_units_covered": true,
    "relations_auditable": true,
    "main_mountains_mece": true,
    "contained_practices_as_subpeaks": true,
    "embedding_distance_used": false,
    "status": "passed"
  },
  "relations": [
    {
      "source": "ai-tools",
      "target": "vibe-coding",
      "strength": 0.82,
      "reason": "Both repeatedly discuss using AI tools to complete real creation workflows."
    }
  ],
  "territories": [
    {
      "id": "ai-tools",
      "label": "AI工具",
      "label_en": "AI Tools",
      "label_kind": "knowledge_domain",
      "label_rationale": "多篇文章反复讨论AI工具选择、评测与工作流接入。",
      "answer": "工具要真正进入工作流，低摩擦比功能最强更重要。",
      "answer_en": "For tools to enter real workflows, low friction matters more than maximum features.",
      "subpeaks": [
        {"label": "HTML表达", "label_en": "HTML Expression", "count": 5}
      ],
      "status": "evidenced",
      "boundary_review": {
        "absorbs_over_half": false,
        "stable_subthemes": 2,
        "five_article_sample_explainable": true,
        "answer_coverage": 0.82,
        "split_yields_valid_subpeaks": false,
        "status": "passed",
        "note": ""
      },
      "claim_history": {
        "early": ["An early recurring claim."],
        "revised": ["A later correction or conflict."],
        "stable": "The current stable answer."
      },
      "cards": [
        {
          "id": "card-id",
          "title": "Original article title",
          "judgment": "Why this article belongs to the peak and supports its answer.",
          "crosses": []
        }
      ]
    }
  ]
}
```

`id` is internal and stable. It must not be treated as user-facing copy. `label` is the mountain's main title and must be a concrete scene or industry keyword identified by the Agent. `answer` is the Agent's evidence-backed subtitle judgment.

`label_kind` must be one of `scene`, `industry`, `role`, `practice`, or `knowledge_domain`. `label_rationale` records why the source articles justify that concrete label. These audit fields are required in schema version 3 but are not rendered on the public map.

Schema version 4 applies the Wenshan-defined **Evidence-Gated Longitudinal Framework Analysis (EGLFA)** contract. It adds a bounded corpus record, open-coding fields, mountain-boundary review, longitudinal claim synthesis, stability results, and an auditable generation timestamp. Older versions remain readable for compatibility; new semantic outputs should use version 6.

Schema version 6 replaces the fixed main-mountain count with a MECE mountain-range contract. Every evidence-gated main mountain may remain visible, but all main mountains must share one declared `classification_axis`. A contained medium, tool, format, or method is recorded in `subpeaks` instead of appearing beside its parent as a peer mountain. `relations` stores reviewed mountain pairs with a strength from `0` to `1` and a plain-language rationale. The deterministic renderer uses this graph for proximity and connecting ridges; it must never substitute embedding distance or arbitrary visual placement. Article membership remains exclusive.

`boundary_review.status` must be `passed`, `human_approved`, or `review_required`. A version 4 terrain file cannot be treated as final while any visible mountain remains `review_required`.

`stability_review.status` must be `passed` only after three independent analyses meet the declared thresholds. Until then, use `pending` and describe the map as an analysis draft rather than a stable knowledge map.

## Invariants

- A visible mountain has `status: evidenced` and at least three eligible unique card paths.
- Schema version 3 fails rendering when a visible mountain lacks a reviewed `label_kind` or `label_rationale`.
- Schema version 4 records `analysis_method: EGLFA`, `generated_at`, corpus boundaries, boundary review, claim history, and stability review.
- Schema version 6 additionally requires a passed `range_review`, one declared classification axis, MECE main mountains, contained practices represented as subpeaks, auditable relation rationales, no embedding-derived distance, exclusive primary assignment, and coverage of all displayed units. It imposes no fixed visible mountain limit.
- A canonical article belongs to one primary mountain.
- `crosses` may reference up to two other mountain IDs but never add altitude there.
- Article count represents accumulated writing volume, not knowledge level, authority, or correctness.
- Article titles remain in the source language.
- Bilingual UI copy may be reviewed or omitted; missing English falls back to the source-language field.
- The renderer rechecks card decisions and paths. A stale terrain file cannot force an excluded or non-canonical card onto the map.
- Legacy `title`, `title_en`, `llm_answer`, `llm_answer_en`, `domain`, `rule`, and `explanation` fields are accepted for one compatibility release, but new outputs must use `label` and `answer`.
