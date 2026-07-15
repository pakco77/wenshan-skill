# Wenshan.skill English workflow

![Wenshan Chinese and English output comparison](../assets/demo-bilingual.png)

**Map your writing as mountains.**

## Inputs

- An author nickname for attribution.
- A selected Obsidian folder, Markdown folder, or explicit article list.
- Interface language: `en`.

Analyze only the selected collection. Never scan an entire vault by default.

## Three-stage pipeline

### 1. Semantic judgment

Use the local Agent to create auditable cards. Keep the user's durable judgments and exclude prompts, operating instructions, templates, third-party examples, empty files, and invalid data. Preserve original titles and source paths.

### 2. Version consolidation and rule extraction

Group drafts, finals, and rewrites into version families and select one canonical representative per family.

Compare canonical judgments and cluster articles that repeatedly express the same causal relationship, selection principle, or decision rule. A mountain name must be an Agent-extracted rule from the current corpus, not a user-entered topic such as “AI Tools” or “Product Management.”

A good rule:

- remains meaningful outside the source article;
- expresses a relationship rather than an object;
- can be supported or contradicted by evidence;
- transfers to another user or knowledge base;
- usually fits in two to six English words.

Examples:

| Evidence domain | Invalid mountain name | Valid rule mountain |
|---|---|---|
| AI Tools | AI Tools | Friction Determines Adoption |
| AI Cognition | AI Cognition | Capability Spreads, Judgment Compounds |
| Product Management | Product Management | Direction Before Execution |

Require at least three independent canonical articles. No evidence means no mountain and no placeholder.

### 3. Map generation

Use the extracted rule as the main title, an optional evidence domain as subordinate context, and a concise evidence explanation as the subtitle. Article count determines altitude and mass.

Store bilingual copy in `rule`, `rule_en`, `explanation`, and `explanation_en`. Keep evidence article titles in their source language.

```bash
python3 scripts/render_territory_demo.py \
  --scope "/absolute/path/article-collection" \
  --nickname "Author" \
  --language en \
  --output-name "Wenshan"
```

## Reading the map

- Main title: a transferable rule extracted from the selected corpus.
- Evidence domain: optional context for where the rule appears.
- Subtitle: why the included evidence supports the rule.
- `13 pieces`: altitude supported by 13 independent canonical articles.
- Dots: evidence articles that open the original note.
- Contours: the internal concentration of evidence.
- Cross-links: visible bridges that never add duplicate altitude.

## Pre-release checks

- Mountain names are not topics, tools, vendors, or folder names.
- Every mountain has at least three unique canonical source paths.
- The sum of mountain counts equals the unique rendered article count.
- No local absolute path, debug label, or invented candidate mountain is visible.
- The full frame fits on a 13-inch display, and the 1080×1440 export contains no controls or cropped terrain.
