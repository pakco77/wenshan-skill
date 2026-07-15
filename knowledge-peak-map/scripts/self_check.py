#!/usr/bin/env python3
"""Small standard-library check for reusable evidence gating and layout."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from render_territory_demo import build_payload


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        vault = Path(temporary) / "Vault"
        scope = vault / "Collection"
        (vault / ".obsidian").mkdir(parents=True)
        cards_dir = scope / "Cognitive Map" / "Agent Atlas" / "cards"
        territories = []
        for territory_index in range(4):
            cards = []
            for card_index in range(3):
                card_id = f"topic-{territory_index}-card-{card_index}"
                source_index = 0 if territory_index == 3 and card_index == 1 else card_index
                source = f"notes/topic-{territory_index}-{source_index}.md"
                write_json(cards_dir / f"{card_id}.json", {
                    "source": {"path": source},
                    "decision": {"include": True, "canonical": True},
                })
                cards.append({"id": card_id, "title": f"Original {card_id}", "judgment": "Evidence", "crosses": []})
            territories.append({
                "id": f"custom-topic-{territory_index}",
                "label": f"行业 {territory_index}",
                "label_en": f"Industry {territory_index}",
                "label_kind": "industry",
                "label_rationale": "三篇独立文章都在讨论同一行业场景",
                "status": "evidenced",
                "answer": "Agent 对该行业文章的回答",
                "answer_en": "The Agent's answer about this industry",
                "cards": cards,
            })

        payload = build_payload(scope, {"version": 3, "territories": territories}, "", str(scope), "en")
        assert payload["profile"]["nickname"] == "Anonymous"
        assert [item["id"] for item in payload["territories"]] == [
            "custom-topic-0", "custom-topic-1", "custom-topic-2"
        ]
        assert all(item["count"] == 3 for item in payload["territories"])
        assert payload["territories"][0]["label_en"] == "Industry 0"
        assert payload["territories"][0]["answer"] == "Agent 对该行业文章的回答"
        assert len({(item["x"], item["y"]) for item in payload["territories"]}) == 3
        (vault / ".obsidian").rmdir()
        markdown_payload = build_payload(scope, {"version": 3, "territories": territories}, "", str(scope), "en")
        assert markdown_payload["territories"][0]["points"][0]["url"].startswith("file://")
        print("PASS scene-and-industry label schema, evidence gate, canonical filter, layout, and Markdown fallback")


if __name__ == "__main__":
    main()
