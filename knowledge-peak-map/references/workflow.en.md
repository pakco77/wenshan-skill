# Wenshan.skill English workflow

![Wenshan monochrome mountain-range output with a Chinese and English language switch](../assets/demo-bilingual.png)

**Map your writing as mountains.**

## Inputs

- An author nickname for attribution.
- A selected Obsidian folder, Markdown folder, or explicit article list.
- Interface language: `en`.

Analyze only the selected collection. The user chooses the corpus but does not predefine mountain names.

## EGLFA eight-step pipeline

Read the complete [EGLFA method specification](methodology.en.md).

1. Bound author, files, time range, document kinds, and authorship.
2. Resolve versions and use one canonical article as one analysis unit.
3. Extract scene, industry, role, practice, knowledge domain, claim, premises, evidence, date, and confidence.
4. Declare one classification axis, form MECE candidate main mountains, demote contained media, formats, methods, or perspectives to subpeaks, and review mountain-to-mountain relation strength.
5. Require three independent canonical articles to pass the evidence gate.
6. Audit mountain boundaries and containment with six fixed questions and require human review when triggered.
7. Synthesize early, revised, and stable claims in time order into the current answer.
8. Analyze the same corpus independently three times and publish only after stability thresholds pass.

A valid label:

- has a strong scene or industry anchor;
- is primarily a noun or noun phrase;
- usually fits in one to four English words;
- is specific enough to show what the writing concerns;
- is broad enough to be supported by at least three independent articles.

Examples:

| Article evidence | Valid main title | Abstract answer that belongs in the subtitle |
|---|---|---|
| Models, tool choice, workflow adoption | AI Tools | Friction Determines Adoption |
| Model industry, access, and human responsibility boundaries | AI Industry | Capability Spreads, Judgment Compounds |
| Validation, user needs, release decisions | Product Management | Direction Before Execution |
| Machines, tooling, and manufacturing process | CNC | Precision Emerges from Constraints |
| Devices, sensors, and hardware experience | Smart Hardware | Experience Requires System Integration |
| Parenting, family, and growth records | Parenting Life | Presence Cannot Be Accelerated |

The right-hand phrases may become subtitles or detail judgments, but never replace the mountain name.

Require at least three independent canonical articles. No evidence means no mountain and no placeholder.

## Map generation

Use the Agent-identified scene or industry keyword as the main title. Use the Agent's evidence-backed answer about that keyword as the subtitle. Article count determines altitude and mass.

The public map has no hard mountain limit. Every evidence-gated, MECE main mountain belongs to one range. Parent-child containment is represented through main mountains and subpeaks; peer mountains differ through reviewed proximity, connection, and local density. Large corpora use scale, label collision, and progressive detail rather than deleting valid themes.

Article count represents accumulated writing volume, not knowledge level or correctness. Show the generation time at the bottom right of the map.

Store bilingual copy in `label`, `label_en`, `answer`, and `answer_en`. Keep evidence article titles in their source language.

```bash
python3 scripts/render_territory_demo.py \
  --scope "/absolute/path/article-collection" \
  --nickname "Author" \
  --language en \
  --output-name "Wenshan"
```

## Reading the map

- Main title: a concrete scene or industry keyword identified from the selected corpus.
- Subtitle: the Agent's answer about what the included writing says in that area.
- `13 pieces`: altitude supported by 13 independent canonical articles.
- Dots: evidence articles that open the original note.
- Contours: the internal concentration of evidence.
- Cross-links: visible bridges that never add duplicate altitude.
- Mountain distance: stronger shared scenes, practices, arguments, or longitudinal transitions place peaks closer together.
- Ridges and saddles: nearby altitude fields connect without duplicating article membership.

## Pre-release checks

- Mountain names are not abstract rules, slogans, quotes, sentences, or aspirations.
- Each name has a strong relationship to a real scene, industry, role, or practice.
- Names are Agent-identified from the corpus, not unreviewed copies of folder names.
- Main mountains share one classification axis and pass a MECE review; contained media, formats, methods, or perspectives remain subpeaks.
- Every mountain has at least three unique canonical source paths.
- The sum of mountain counts equals the unique rendered article count.
- Important spatial relations have reviewed rationales; unrelated mountains are never pulled together merely for visual convenience.
- No local absolute path, debug label, or invented candidate mountain is visible.
- The full frame fits on a 13-inch display, and the 1080×1440 export contains no controls or cropped terrain.
