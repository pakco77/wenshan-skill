# MECE case: 0_文池

This compact case shows how Wenshan separates main mountains from contained subpeaks. It is an example, not a fixed taxonomy.

## Corpus

- 102 source Markdown files
- 87 independent canonical articles
- 80 articles assigned to main mountains
- 7 valid outliers below the three-article evidence gate
- Classification axis: `primary_problem_space`

## Final main mountains

| Main mountain | Articles |
|---|---:|
| 产品经理 | 18 |
| AI工具 | 16 |
| AI行业 | 15 |
| Vibe Coding | 14 |
| SaaS产品 | 6 |
| 学习方法 | 6 |
| 内容传播 | 5 |

The result has seven mountains because seven problem spaces passed the reviews. Seven is not a target or limit.

## Containment corrections

| Rejected peer mountain | Final location | Reason |
|---|---|---|
| HTML表达 · 5 articles | `AI工具 / HTML表达` subpeak | HTML is the production medium through which AI tools enter layout, presentation, and visual-expression workflows. It is contained by the broader AI-tool problem space. |
| AI认知 · 9 articles | `AI行业 / 人机边界` subpeak | These articles explain how industry change alters human judgment, work boundaries, and responsibility. The stable problem space is the AI industry; “AI cognition” is an analytical perspective inside it. |

## Reusable decision test

1. Declare one main-mountain classification axis.
2. Give every canonical article one primary assignment.
3. Ask whether a candidate is a medium, format, technique, tool, or perspective fully contained by another candidate.
4. If yes, retain its evidence as a `subpeak`; do not render it as a peer mountain.
5. Keep distinct sibling problem spaces even when they are strongly related.
6. Use reviewed relations to determine proximity and connecting ridges; never use duplicate assignment to connect mountains.

Minimal reviewed structure:

```json
{
  "range_review": {
    "classification_axis": "primary_problem_space",
    "main_mountains_mece": true,
    "contained_practices_as_subpeaks": true,
    "primary_assignment_exclusive": true
  },
  "territories": [
    {
      "label": "AI工具",
      "cards": 16,
      "subpeaks": [
        {"label": "模型与Agent评测", "count": 11},
        {"label": "HTML表达", "count": 5}
      ]
    },
    {
      "label": "AI行业",
      "cards": 15,
      "subpeaks": [
        {"label": "产业格局", "count": 6},
        {"label": "人机边界", "count": 9}
      ]
    }
  ]
}
```

