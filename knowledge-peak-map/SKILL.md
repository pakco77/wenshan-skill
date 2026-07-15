---
name: knowledge-peak-map
description: Create bilingual evidence-gated Wenshan contour maps that identify concrete scene or industry peaks from reviewed Obsidian or Markdown article collections. Use when the user asks for 文山.skill, Wenshan.skill, knowledge mountains, knowledge peaks, article terrain, contour visualization, or a personal knowledge map built from canonical evidence without embedding-based similarity.
---

# 文山.skill / Wenshan.skill

![文山.skill / Wenshan.skill 双语效果 Demo](assets/demo-bilingual.png)

**中文：用山脉展示你的篇章。** Read [中文工作流](references/workflow.zh.md).
**English: Map your writing as mountains.** Read the [English workflow](references/workflow.en.md).

Read only what the task needs: [source ingestion](references/article-ingestion.md), [data contract](references/data-contract.md), [host installation](references/agent-compatibility.md), or the [Obsidian shell](references/obsidian-plugin.zh.md).

## Contract

Render reviewed judgments; never infer document proximity with embeddings.

- Let the local Agent identify a concrete scene, practice, role, industry, or knowledge-domain keyword from the selected corpus. Never ask the user to predefine mountains.
- Use the Agent's evidence-backed answer as the subtitle.
- Count only unique source paths whose cards are both `include: true` and `canonical: true`; three paths make one mountain. Below that: render nothing.
- Use article count as altitude. Keep evidence titles in their source language.
- Require reviewed `label_kind` and `label_rationale` fields before rendering.

Prefer recognizable noun phrases with a strong scene or industry anchor, such as `AI工具`, `产品经理`, `CNC`, `智能硬件`, `AI认知`, or `育儿生活`. Reject slogans, full-sentence conclusions, abstract laws, user-entered aspirations, folder names copied without semantic review, and vendor names unless the corpus genuinely centers on that vendor.

## Input

Accept `nickname`, an absolute `scope` to a selected Markdown/Obsidian collection, and `language` (`zh` or `en`). Never scan the whole vault by default.

The reviewed scope contains:

```text
Cognitive Map/Agent Atlas/
├── cards/*.json
└── wenshan-terrain.json
```

Write `wenshan-terrain.json` as the auditable semantic source. Follow [data-contract.md](references/data-contract.md). If English copy is absent, preserve the source language; never silently translate evidence titles.

## Workflow

Use the user's local Agent to:

1. Exclude prompts, templates, manuals, third-party examples, empty files, and invalid JSON from the selected set.
2. Resolve drafts and rewrites into version families with one canonical article.
3. Cluster canonical judgments around repeated real-world scenes, practices, roles, industries, or knowledge domains.
4. Name each cluster with a compact keyword; reject slogans, conclusions, abstract laws, aspirations, and unreviewed folder names.
5. Keep clusters with three unique canonical paths. Assign each article to one primary mountain and at most two non-altitude cross-links.
6. Write one evidence-backed answer per mountain, then validate the schema and render.

The renderer is deterministic after semantic preparation. Fix a wrong mountain by revising the evidence or label extraction, never by tuning coordinates.

## Render

Chinese:

```bash
python3 scripts/render_territory_demo.py \
  --scope "/absolute/content-scope" \
  --nickname "作者昵称" \
  --language zh \
  --output-name "文山"
```

English:

```bash
python3 scripts/render_territory_demo.py \
  --scope "/absolute/content-scope" \
  --nickname "Author" \
  --language en \
  --output-name "Wenshan"
```

Write derived HTML and Markdown only inside `Cognitive Map/Agent Atlas/`. Never edit source notes or semantic cards during rendering.

## Validation

Run:

```bash
python3 scripts/self_check.py
```

Then verify counts, Chinese/English data parity, generated JavaScript, desktop fit, and the 1080×1440 export.

## Reuse boundary

Apply the same contract to essays, research notes, project retrospectives, decision records, reading notes, portfolios, or any Markdown collection that has passed semantic review and canonical version resolution. Do not tie labels or geometry to public-account articles, a single user's taxonomy, or fixed topic IDs.
