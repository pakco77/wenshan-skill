---
name: knowledge-peak-map
description: Create bilingual evidence-gated Wenshan contour maps that identify concrete scene or industry peaks from reviewed Obsidian or Markdown article collections. Use when the user asks for 文山.skill, Wenshan.skill, knowledge mountains, knowledge peaks, article terrain, contour visualization, or a personal knowledge map built from canonical evidence without embedding-based similarity.
---

# 文山.skill / Wenshan.skill

![文山.skill / Wenshan.skill 双语效果 Demo](assets/demo-bilingual.png)

**中文：用山脉展示你的篇章。** Read [中文工作流](references/workflow.zh.md).
**English: Map your writing as mountains.** Read the [English workflow](references/workflow.en.md).

For source ingestion, read [文章与文档进入 Markdown/Obsidian 的前置链路](references/article-ingestion.md).
For exact card and terrain fields, read the [data contract](references/data-contract.md).
For host installation, read [Agent compatibility](references/agent-compatibility.md).
For the Obsidian shell, read [中文方案](references/obsidian-plugin.zh.md) or [English architecture](references/obsidian-plugin.en.md).

## Product contract

Render reviewed judgments; never infer document proximity with embeddings.

- Make the mountain's main title a concrete scene, practice, or industry keyword identified by the local Agent from the current corpus.
- Never ask the user to predefine mountain names or long-term directions; the user selects the corpus and reviews the result.
- Make the subtitle the Agent's concise evidence-backed answer or judgment about that keyword.
- Require `label_kind` and `label_rationale` so every title is explicitly reviewed as a scene, industry, role, practice, or knowledge domain.
- Count only cards with `decision.include: true` and `decision.canonical: true`.
- Require at least three independent source paths before rendering a keyword as a mountain.
- Render no label, contour, placeholder, or “to be explored” state below the evidence gate.
- Use the number of independent canonical articles as altitude.
- Keep original evidence article titles in their source language.

Prefer recognizable noun phrases with a strong scene or industry anchor, such as `AI工具`, `产品经理`, `CNC`, `智能硬件`, `AI认知`, or `育儿生活`. Reject slogans, full-sentence conclusions, abstract laws, user-entered aspirations, folder names copied without semantic review, and vendor names unless the corpus genuinely centers on that vendor.

## Inputs

Accept:

1. `nickname`: attribution in the map and share export.
2. `scope`: an absolute path to a selected Obsidian or Markdown collection.
3. `language`: `zh` or `en`.

Do not scan an entire vault by default. Analyze only the collection the user selected.

The reviewed scope contains:

```text
Cognitive Map/Agent Atlas/
├── cards/*.json
└── wenshan-terrain.json
```

Write `wenshan-terrain.json` as the auditable semantic source. Each retained mountain stores a stable `id`, Agent-identified `label`, evidence-backed `answer`, bilingual reviewed variants, and card IDs. Use the exact schema in [data-contract.md](references/data-contract.md).

If English copy is absent, preserve the source language. Never silently machine-translate evidence article titles.

## Semantic workflow

Use the user's local Agent to:

1. Collect only the selected article set.
2. Exclude prompts, templates, operating manuals, third-party examples, empty files, and invalid JSON.
3. Resolve drafts, finals, and rewrites into version families with one canonical representative.
4. Compare canonical judgments and cluster articles that repeatedly concern the same real-world scene, practice, role, or industry.
5. Name each cluster with a compact, concrete keyword that a reader can immediately recognize.
6. Retain only labels supported by at least three independent canonical source paths.
7. Assign every article to one primary mountain; allow up to two non-altitude cross-links.
8. Write one evidence-backed answer that expresses what the corpus says about that keyword.
9. Reject over-abstract titles even when the underlying answer contains a transferable rule.
10. Validate IDs, counts, paths, inclusion decisions, and bilingual fields.

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

## Geometry and interaction

- Generate contours from deterministic evidence points, a Gaussian density field, and marching squares.
- Let article count determine relative altitude and mass.
- Preserve contour lines as the core visual asset; use shading only to improve depth perception.
- Fit mountains into the framed viewport on desktop and portrait exports.
- Open a detail panel with the extracted keyword, Agent answer, count, and original article titles.
- Export a 1080×1440 share image without controls or local source paths.

## Validation

Run:

```bash
python3 scripts/self_check.py
```

Then verify that every visible mountain has at least three unique canonical paths, the summed mountain count equals the unique rendered article count, Chinese and English outputs share identical terrain data, generated JavaScript parses, and both pages render without clipping.

## Reuse boundary

Apply the same contract to essays, research notes, project retrospectives, decision records, reading notes, portfolios, or any Markdown collection that has passed semantic review and canonical version resolution. Do not tie labels or geometry to public-account articles, a single user's taxonomy, or fixed topic IDs.
