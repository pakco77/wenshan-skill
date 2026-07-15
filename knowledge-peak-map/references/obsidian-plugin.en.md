# Obsidian plugin architecture

## Recommendation

Build an Obsidian plugin as a **desktop launcher and viewer for Wenshan.skill**, not as a second semantic engine.

## MVP responsibilities

The plugin should only:

1. Select a vault folder or explicit article collection.
2. Collect the author nickname and `zh` or `en` language.
3. Invoke the local Skill/Agent to generate or refresh the map.
4. Open the generated HTML in an Obsidian view.
5. Open evidence articles through Obsidian URIs.

## Keep outside the plugin

- LLM-provider adapters.
- API keys in generated HTML.
- Duplicate implementations of version consolidation, evidence gates, semantic assignment, or contour generation.
- Automatic full-vault scanning.
- Local Agent or Python execution on mobile.

Keep these in the Skill/CLI so CodeWhale, Codex, and Obsidian share one semantic source of truth.

## Suggested commands and settings

Commands:

- `Wenshan: Configure article collection`
- `Wenshan: Generate or refresh map`
- `Wenshan: Open map`
- `Wenshan: Export share image`

Settings:

- `collectionPath`
- `nickname`
- `language: zh | en`
- `skillCommand`
- `outputPath`

## Initial data contract

Reuse the existing folder to avoid premature migration:

```text
Cognitive Map/Agent Atlas/
├── cards/*.json
├── wenshan-terrain.json
├── 文山.html
└── Wenshan.html
```

Keep `knowledge-peaks-demo-data.json` only as a one-release legacy input fallback.

The plugin reads outputs and invokes commands. It never edits `cards/*.json` directly.

## Delivery sequence

1. Desktop MVP: settings, three commands, a map view, and Obsidian URI backlinks.
2. Real task status for collection, judgment, consolidation, rendering, and errors.
3. Read-only mobile viewing of pre-generated maps.
4. Consider a TypeScript renderer only after the data contract is stable.

Stabilize the Skill's inputs, outputs, and failure states before building the plugin. This keeps the plugin small while the semantic engine can evolve independently.
