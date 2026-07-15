# Data contract

The renderer consumes two auditable layers under `Cognitive Map/Agent Atlas/`.

## Card

Store one JSON file per reviewed document at `cards/<stable-id>.json`:

```json
{
  "version": 1,
  "source": {
    "path": "relative/path/article.md",
    "hash": "sha256",
    "title": "Original source title"
  },
  "decision": {
    "include": true,
    "document_kind": "published_article",
    "version_family": "optional-family-slug",
    "canonical": true
  },
  "interpretation": {
    "core_judgment": "The durable judgment in this article.",
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
  "version": 3,
  "semantic_contract": "mountain_title_is_agent_identified_scene_or_industry_keyword",
  "territories": [
    {
      "id": "ai-tools",
      "label": "AI工具",
      "label_en": "AI Tools",
      "label_kind": "knowledge_domain",
      "label_rationale": "多篇文章反复讨论AI工具选择、评测与工作流接入。",
      "answer": "工具要真正进入工作流，低摩擦比功能最强更重要。",
      "answer_en": "For tools to enter real workflows, low friction matters more than maximum features.",
      "status": "evidenced",
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

## Invariants

- A visible mountain has `status: evidenced` and at least three eligible unique card paths.
- Schema version 3 fails rendering when a visible mountain lacks a reviewed `label_kind` or `label_rationale`.
- A canonical article belongs to one primary mountain.
- `crosses` may reference up to two other mountain IDs but never add altitude there.
- Article titles remain in the source language.
- Bilingual UI copy may be reviewed or omitted; missing English falls back to the source-language field.
- The renderer rechecks card decisions and paths. A stale terrain file cannot force an excluded or non-canonical card onto the map.
- Legacy `title`, `title_en`, `llm_answer`, `llm_answer_en`, `domain`, `rule`, and `explanation` fields are accepted for one compatibility release, but new outputs must use `label` and `answer`.
