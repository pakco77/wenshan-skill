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

Store the reviewed rule clusters at `wenshan-terrain.json`:

```json
{
  "version": 2,
  "semantic_contract": "mountain_title_is_agent_extracted_transferable_rule",
  "territories": [
    {
      "id": "friction-determines-adoption",
      "domain": "AI工具",
      "domain_en": "AI Tools",
      "rule": "摩擦决定采用",
      "rule_en": "Friction Determines Adoption",
      "explanation": "能嵌入工作流，比功能最强更重要。",
      "explanation_en": "Workflow fit beats feature strength.",
      "status": "evidenced",
      "cards": [
        {
          "id": "card-id",
          "title": "Original article title",
          "judgment": "Why this article supports the rule.",
          "crosses": []
        }
      ]
    }
  ]
}
```

`id` is internal and stable. It must not be treated as user-facing copy. `domain` is optional subordinate context. `rule` is the mountain's main title.

## Invariants

- A visible mountain has `status: evidenced` and at least three eligible unique card paths.
- A canonical article belongs to one primary mountain.
- `crosses` may reference up to two other mountain IDs but never add altitude there.
- Article titles remain in the source language.
- Bilingual UI copy may be reviewed or omitted; missing English falls back to the source-language field.
- The renderer rechecks card decisions and paths. A stale terrain file cannot force an excluded or non-canonical card onto the map.
- Legacy `title`, `title_en`, `llm_answer`, and `llm_answer_en` fields are accepted for one compatibility release, but new outputs must use `domain`, `rule`, and `explanation`.
