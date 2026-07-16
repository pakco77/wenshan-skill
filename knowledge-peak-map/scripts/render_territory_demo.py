#!/usr/bin/env python3
"""Render the evidence-gated 文山.skill demo without embeddings.

Terrain position is a stable visual layout. A mountain exists only when an
Agent-identified scene or industry label has three or more independent canonical articles.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode


LABEL_KINDS = {"scene", "industry", "role", "practice", "knowledge_domain"}
BOUNDARY_STATUSES = {"passed", "human_approved"}
CONCLUSION_PATTERNS = (
    r"优先于|先于|取决于|决定了|来自于|无法被|应该|必须|更重要|正在|已经",
    r"\b(should|must|matters? more|depends? on|comes? from|cannot be)\b",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render evidence-gated Knowledge Peaks demo.")
    parser.add_argument("--scope", type=Path, required=True)
    parser.add_argument("--nickname", default="Pakco", help="Name shown in the map header.")
    parser.add_argument("--collection-url", default="", help="Article collection URL or local collection reference.")
    parser.add_argument("--language", choices=("zh", "en"), default="zh", help="Initial interface and export language.")
    parser.add_argument(
        "--theme",
        choices=("survey-parchment", "obsidian-atlas"),
        default="survey-parchment",
        help="Visual skin only. It never changes mountain semantics, counts, evidence, or geometry.",
    )
    parser.add_argument("--output-name", help="Output basename inside Cognitive Map/Agent Atlas.")
    parser.add_argument("--terrain-data", type=Path, help="Optional terrain JSON. Defaults to wenshan-terrain.json.")
    return parser.parse_args()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing evidence file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {path}: {exc}") from exc


def first_text(value: dict, *keys: str) -> str:
    for key in keys:
        item = value.get(key)
        if isinstance(item, str) and item.strip():
            return item
    return ""


def validate_peak_labels(data: dict) -> None:
    if int(data.get("version", 0)) < 3:
        return
    for territory in data.get("territories", []):
        if territory.get("status") != "evidenced":
            continue
        label = first_text(territory, "label")
        kind = territory.get("label_kind")
        rationale = first_text(territory, "label_rationale")
        if kind not in LABEL_KINDS:
            raise SystemExit(f"{territory.get('id', '<unknown>')}: label_kind must be one of {sorted(LABEL_KINDS)}")
        if not label or not rationale:
            raise SystemExit(f"{territory.get('id', '<unknown>')}: label and label_rationale are required")
        if (
            len(label) > 40
            or any(mark in label for mark in "，。！？；：,.!?;:")
            or any(re.search(pattern, label, re.IGNORECASE) for pattern in CONCLUSION_PATTERNS)
        ):
            raise SystemExit(f"{territory.get('id', '<unknown>')}: label must be a compact scene or industry keyword, not a sentence")


def validate_method_contract(data: dict) -> None:
    """Require completed EGLFA reviews for new schema outputs."""
    if int(data.get("version", 0)) < 4:
        return
    if data.get("analysis_method") != "EGLFA" or not first_text(data, "generated_at"):
        raise SystemExit("Schema version 4 requires analysis_method: EGLFA and generated_at.")
    time_range = data.get("corpus", {}).get("time_range", [])
    if not isinstance(time_range, list) or len(time_range) != 2 or not all(time_range):
        raise SystemExit("EGLFA requires a bounded corpus time_range with start and end dates.")
    stability = data.get("stability_review", {})
    if stability.get("status") != "passed":
        raise SystemExit("EGLFA stability_review must pass before final rendering.")
    for territory in data.get("territories", []):
        if territory.get("status") != "evidenced":
            continue
        review = territory.get("boundary_review", {})
        if review.get("status") not in BOUNDARY_STATUSES:
            raise SystemExit(f"{territory.get('id', '<unknown>')}: mountain boundary review is incomplete.")
        if float(review.get("answer_coverage", 0)) < 0.70:
            raise SystemExit(f"{territory.get('id', '<unknown>')}: subtitle coverage must be at least 70%.")
    if int(data.get("version", 0)) == 5:
        taxonomy = data.get("taxonomy_review", {})
        visible = [
            territory for territory in data.get("territories", [])
            if territory.get("status") == "evidenced"
        ]
        if taxonomy.get("status") != "passed":
            raise SystemExit("Schema version 5 requires a passed taxonomy_review.")
        if not first_text(taxonomy, "axis"):
            raise SystemExit("Schema version 5 requires one declared main-mountain classification axis.")
        if not 1 <= len(visible) <= 5:
            raise SystemExit("A final Wenshan map must contain between one and five main mountains.")
        if int(taxonomy.get("main_mountain_count", 0)) != len(visible):
            raise SystemExit("taxonomy_review.main_mountain_count must match visible main mountains.")
        if int(taxonomy.get("count_limit", 0)) != 5:
            raise SystemExit("taxonomy_review.count_limit must be 5.")
        for field in (
            "same_level",
            "no_parent_child_pairs",
            "primary_assignment_exclusive",
            "displayed_units_covered",
        ):
            if taxonomy.get(field) is not True:
                raise SystemExit(f"Schema version 5 taxonomy review failed: {field}.")
    if int(data.get("version", 0)) >= 6:
        range_review = data.get("range_review", {})
        if range_review.get("status") != "passed":
            raise SystemExit("Schema version 6 requires a passed range_review.")
        if range_review.get("layout_method") != "reviewed_relation_graph":
            raise SystemExit("Schema version 6 requires layout_method: reviewed_relation_graph.")
        if not first_text(range_review, "classification_axis"):
            raise SystemExit("Schema version 6 requires one declared MECE main-mountain classification axis.")
        for field in (
            "primary_assignment_exclusive",
            "displayed_units_covered",
            "relations_auditable",
            "main_mountains_mece",
            "contained_practices_as_subpeaks",
        ):
            if range_review.get(field) is not True:
                raise SystemExit(f"Schema version 6 range review failed: {field}.")
        if range_review.get("embedding_distance_used") is not False:
            raise SystemExit("Schema version 6 forbids embedding-derived mountain distance.")
        visible_ids = {
            territory.get("id") for territory in data.get("territories", [])
            if territory.get("status") == "evidenced"
        }
        for relation in data.get("relations", []):
            source, target = relation.get("source"), relation.get("target")
            strength = float(relation.get("strength", -1))
            if source not in visible_ids or target not in visible_ids or source == target:
                raise SystemExit(f"Invalid mountain relation: {source!r} -> {target!r}.")
            if not 0 <= strength <= 1 or not first_text(relation, "reason"):
                raise SystemExit(f"Mountain relation {source!r} -> {target!r} needs strength 0..1 and a reason.")


def validate_evidence_labels(data: dict) -> None:
    """Keep visual evidence labels auditable without promoting them to subpeaks."""
    for territory in data.get("territories", []):
        labels = territory.get("evidence_labels")
        if labels is None:
            continue
        if not isinstance(labels, list) or not 2 <= len(labels) <= 3:
            raise SystemExit(f"{territory.get('id', '<unknown>')}: evidence_labels must contain two or three items.")
        card_ids = {card.get("id") for card in territory.get("cards", [])}
        seen = set()
        for item in labels:
            label = first_text(item, "label")
            article_ids = item.get("article_ids", [])
            if not label or label in seen:
                raise SystemExit(f"{territory.get('id', '<unknown>')}: evidence labels must be unique non-empty noun phrases.")
            if not isinstance(article_ids, list) or len(set(article_ids)) < 2:
                raise SystemExit(f"{territory.get('id', '<unknown>')}: {label} needs at least two supporting articles.")
            if not set(article_ids).issubset(card_ids):
                raise SystemExit(f"{territory.get('id', '<unknown>')}: {label} references a card outside its mountain.")
            if not first_text(item, "rationale"):
                raise SystemExit(f"{territory.get('id', '<unknown>')}: {label} needs an evidence rationale.")
            seen.add(label)


def vault_for(scope: Path) -> Path | None:
    for candidate in (scope, *scope.parents):
        if (candidate / ".obsidian").is_dir():
            return candidate
    return None


def card_record(scope: Path, card_id: str) -> dict:
    return read_json(scope / "Cognitive Map" / "Agent Atlas" / "cards" / f"{card_id}.json")


def source_url(vault: Path | None, scope: Path, card: dict) -> str:
    source = card.get("source", {}).get("path", "")
    if not source:
        return ""
    if vault is None:
        return (scope / source).resolve().as_uri()
    try:
        relative = (scope / source).resolve().relative_to(vault).as_posix().removesuffix(".md")
    except (ValueError, TypeError):
        return ""
    return "obsidian://open?" + urlencode({"vault": vault.name, "file": relative})


def generic_anchors(total: int) -> list[tuple[float, float]]:
    """Lay out arbitrary evidenced territories without topic-specific semantics."""
    if total == 1:
        return [(0.50, 0.48)]
    if total == 2:
        return [(0.34, 0.46), (0.68, 0.54)]
    if total == 3:
        return [(0.34, 0.35), (0.68, 0.34), (0.53, 0.70)]
    if total == 4:
        return [(0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)]
    if total == 5:
        return [(0.50, 0.48), (0.25, 0.22), (0.75, 0.22), (0.25, 0.77), (0.75, 0.77)]
    columns = max(2, math.ceil(math.sqrt(total * 0.76)))
    rows = math.ceil(total / columns)
    result = []
    for index in range(total):
        column, row = index % columns, index // columns
        x = 0.22 + column * (0.56 / max(1, columns - 1))
        y = 0.20 + row * (0.58 / max(1, rows - 1))
        if rows > 1 and row % 2:
            x += 0.025 if column < columns - 1 else -0.025
        result.append((x, y))
    return result


def relation_anchors(candidates: list[dict], relations: list[dict]) -> list[tuple[float, float]]:
    """Deterministic graph-stress layout from reviewed relations; never embeddings."""
    if len(candidates) <= 2 or not relations:
        return generic_anchors(len(candidates))
    identifiers = [str(candidate.get("id", index)) for index, candidate in enumerate(candidates)]
    index_by_id = {identifier: index for index, identifier in enumerate(identifiers)}
    total = len(identifiers)
    infinity = 1_000_000.0
    graph_distance = [
        [0.0 if left == right else infinity for right in range(total)]
        for left in range(total)
    ]
    for relation in relations:
        left, right = index_by_id.get(relation.get("source")), index_by_id.get(relation.get("target"))
        if left is None or right is None or left == right:
            continue
        cost = 0.08 + (1 - float(relation.get("strength", 0))) * 0.72
        graph_distance[left][right] = min(graph_distance[left][right], cost)
        graph_distance[right][left] = min(graph_distance[right][left], cost)
    for middle in range(total):
        for left in range(total):
            for right in range(total):
                graph_distance[left][right] = min(
                    graph_distance[left][right],
                    graph_distance[left][middle] + graph_distance[middle][right],
                )
    finite = [
        graph_distance[left][right]
        for left in range(total)
        for right in range(left + 1, total)
        if graph_distance[left][right] < infinity
    ]
    maximum = max(finite, default=1.0)
    targets = [
        [
            0.0 if left == right else (
                0.11 + 0.62 * graph_distance[left][right] / maximum
                if graph_distance[left][right] < infinity else 0.74
            )
            for right in range(total)
        ]
        for left in range(total)
    ]
    positions = []
    for index, identifier in enumerate(identifiers):
        digest = hashlib.sha256(identifier.encode("utf-8")).digest()
        jitter = (digest[0] / 255 - 0.5) * 0.12
        angle = -math.pi / 2 + math.tau * index / total + jitter
        positions.append([0.5 + math.cos(angle) * 0.33, 0.5 + math.sin(angle) * 0.33])
    for iteration in range(1_200):
        forces = [[0.0, 0.0] for _ in positions]
        for left in range(total):
            for right in range(left + 1, total):
                dx = positions[right][0] - positions[left][0]
                dy = positions[right][1] - positions[left][1]
                distance = max(math.hypot(dx, dy), 0.001)
                error = distance - targets[left][right]
                force = error / (0.12 + targets[left][right]) * 0.055
                fx, fy = dx / distance * force, dy / distance * force
                forces[left][0] += fx
                forces[left][1] += fy
                forces[right][0] -= fx
                forces[right][1] -= fy
        temperature = 0.025 * (1 - iteration / 1_200) + 0.002
        for index, position in enumerate(positions):
            forces[index][0] += (0.5 - position[0]) * 0.01
            forces[index][1] += (0.5 - position[1]) * 0.01
            magnitude = max(math.hypot(*forces[index]), 0.001)
            scale = min(temperature, magnitude) / magnitude
            position[0] += forces[index][0] * scale
            position[1] += forces[index][1] * scale
    min_x, max_x = min(item[0] for item in positions), max(item[0] for item in positions)
    min_y, max_y = min(item[1] for item in positions), max(item[1] for item in positions)
    return [
        (
            0.16 + (x - min_x) / max(max_x - min_x, 0.001) * 0.68,
            0.14 + (y - min_y) / max(max_y - min_y, 0.001) * 0.72,
        )
        for x, y in positions
    ]


def unit_jitter(identifier: str, index: int, total: int) -> tuple[float, float]:
    """Stable sunflower-like spread: visual only, never semantic geometry."""
    digest = hashlib.sha256(identifier.encode("utf-8")).digest()
    angle = (int.from_bytes(digest[:4], "big") / 2**32) * math.tau + index * 2.399963
    radius = (0.018 + 0.078 * math.sqrt((index + 0.45) / max(total, 1))) * (0.82 + digest[4] / 255 * 0.30)
    return radius * math.cos(angle), radius * math.sin(angle)


def build_payload(
    scope: Path,
    data: dict,
    nickname: str,
    collection_url: str,
    language: str,
    theme: str = "survey-parchment",
) -> dict:
    validate_peak_labels(data)
    validate_method_contract(data)
    validate_evidence_labels(data)
    vault = vault_for(scope)
    candidates = [
        territory for territory in data.get("territories", [])
        if territory.get("status") == "evidenced" and len(territory.get("cards", [])) >= 3
    ]
    if not candidates:
        raise SystemExit("No territory has the minimum three independent canonical cards.")
    anchors = relation_anchors(candidates, data.get("relations", []))
    territories = []
    for territory, (ax, ay) in zip(candidates, anchors):
        ident, cards = territory.get("id"), territory.get("cards", [])
        eligible = []
        seen_sources = set()
        for card in cards:
            record = card_record(scope, card["id"])
            decision = record.get("decision", {})
            source = record.get("source", {}).get("path", "")
            if not decision.get("include") or not decision.get("canonical") or not source or source in seen_sources:
                continue
            seen_sources.add(source)
            eligible.append((card, record))
        if len(eligible) < 3:
            continue
        points = []
        for index, (card, record) in enumerate(eligible):
            dx, dy = unit_jitter(card["id"], index, len(eligible))
            points.append({
                **card,
                "x": max(0.05, min(0.95, ax + dx)),
                "y": max(0.08, min(0.93, ay + dy)),
                "date": first_text(record.get("source", {}), "date"),
                "url": source_url(vault, scope, record),
            })
        territories.append({
            "id": ident,
            "label": first_text(territory, "label", "domain", "title", "rule"),
            "label_en": first_text(territory, "label_en", "domain_en", "title_en", "label", "domain", "title", "rule_en", "rule"),
            "answer": first_text(territory, "answer", "explanation", "llm_answer"),
            "answer_en": first_text(territory, "answer_en", "explanation_en", "llm_answer_en", "answer", "explanation", "llm_answer"),
            "count": len(points),
            "subpeaks": territory.get("subpeaks", []),
            "evidence_labels": territory.get("evidence_labels", []),
            "x": ax,
            "y": ay,
            "points": points,
        })
    if not territories:
        raise SystemExit("No territory has the minimum three independent canonical cards.")
    return {
        "territories": territories,
        "generated_at": first_text(data, "generated_at") or datetime.now().astimezone().isoformat(timespec="minutes"),
        "relations": data.get("relations", []),
        "profile": {
            "nickname": nickname.strip() or ("匿名" if language == "zh" else "Anonymous"),
            "collection_url": collection_url.strip(),
            "language": language,
            "theme": theme,
        },
    }


HTML = r'''<!doctype html>
<html lang="__HTML_LANG__"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__PAGE_TITLE__</title>
<style>
:root{--ink:#232721;--muted:#73766d;--paper:#f1efe8;--paper-2:#e9e6dc;--line:#c9c5b9;--night:#26302c}*{box-sizing:border-box}html{background:#dcd9d0}body{min-height:100vh;margin:0;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans CJK SC",sans-serif;background:radial-gradient(ellipse at 50% 10%,#f3f1ea 0,#dfddd5 46%,#d3d0c7 100%)}button,a{font:inherit}.workspace{width:min(1120px,calc(100% - 48px));min-height:100vh;margin:auto;display:grid;grid-template-columns:minmax(156px,1fr) 570px 76px;gap:24px;align-items:center}.context{align-self:center;border-top:1px solid var(--ink);padding-top:13px;color:var(--muted);font-size:11px;letter-spacing:.11em;text-transform:uppercase}.context strong{display:block;color:var(--ink);font-size:13px;font-weight:650;letter-spacing:.16em;margin-bottom:9px}.context p{margin:0;line-height:1.8;letter-spacing:.06em;text-transform:none}.context .rule{width:44px;height:1px;margin:22px 0;background:#98988d}.poster{position:relative;display:grid;grid-template-rows:auto 1fr auto;gap:12px;width:570px;padding:18px;background:var(--paper);border:1px solid #bcb9ad;box-shadow:0 28px 56px #4c4a421f,0 3px 9px #4c4a4218}.poster::after{content:"";position:absolute;inset:7px;pointer-events:none;border:1px solid #d6d2c7}.head,.foot{position:relative;z-index:1;display:flex;justify-content:space-between;align-items:flex-end;gap:14px}.wordmark{font-size:17px;font-weight:680;letter-spacing:.22em;line-height:1}.slogan{margin:6px 0 0;color:#666a61;font-size:11px;letter-spacing:.03em}.index{font-size:10px;color:#6d7169;letter-spacing:.10em;white-space:nowrap}.map-shell{position:relative;isolation:isolate;aspect-ratio:3/4;overflow:hidden;background:#e8e5dc;border:1px solid #cfcbc0}.map-shell::before{content:"";position:absolute;inset:0;z-index:1;pointer-events:none;background-image:linear-gradient(#a8a79e16 1px,transparent 1px),linear-gradient(90deg,#a8a79e16 1px,transparent 1px);background-size:42px 42px}canvas{position:relative;z-index:0;display:block;width:100%;height:100%;cursor:crosshair;touch-action:none}.inspector{position:absolute;z-index:3;left:12px;right:12px;bottom:12px;display:grid;grid-template-columns:1fr auto;gap:10px;padding:13px 14px;background:#f4f2eaeF;border:1px solid #767970;box-shadow:0 12px 24px #292d2820;opacity:0;transform:translateY(14px);pointer-events:none;transition:opacity .18s ease,transform .22s ease}.inspector.show{opacity:1;transform:none;pointer-events:auto}.inspector h2{margin:0 0 5px;font-size:18px;letter-spacing:.08em;font-weight:650}.inspector p{margin:0;color:#4e534b;font-size:12px;line-height:1.6}.inspector .close{border:0;background:none;color:#5e625a;font-size:18px;line-height:1;cursor:pointer}.articles{grid-column:1/-1;display:flex;gap:7px;overflow:auto;padding-top:5px;border-top:1px solid #d0cdc2}.articles a{flex:0 0 auto;max-width:190px;overflow:hidden;color:#363a34;font-size:11px;line-height:1.35;text-decoration:none;white-space:nowrap;text-overflow:ellipsis}.articles a:hover{text-decoration:underline}.foot{font-size:11px;letter-spacing:.08em;color:#60645c}.meta{font-size:15px;font-weight:650;letter-spacing:.05em;color:var(--ink)}.author{font-size:11px;letter-spacing:.14em}.tools{display:flex;flex-direction:column;gap:8px;align-self:center}.tool{width:76px;min-height:60px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px;border:1px solid #a8a69b;background:#eeece4cc;color:#3e433c;text-decoration:none;font-size:10px;letter-spacing:.08em;cursor:pointer;transition:transform .16s ease,background .16s ease,box-shadow .16s ease}.tool:hover{transform:translateX(3px);background:#f8f6ef;box-shadow:5px 6px 0 #96958b33}.tool:focus-visible{outline:2px solid #45534c;outline-offset:3px}.tool .icon{font-size:16px;line-height:1}.desktop-note{display:none}@media(max-width:900px){.workspace{grid-template-columns:570px 76px;width:max-content;max-width:calc(100% - 28px)}.context{display:none}}@media(max-width:680px){body{background:var(--paper)}.workspace{width:100%;max-width:none;display:block;min-height:100vh}.poster{width:100%;min-height:100vh;padding:12px;border:0;box-shadow:none}.tools{display:none}.map-shell{margin-top:auto}.desktop-note{display:block;margin:0 0 8px;font-size:10px;color:var(--muted);letter-spacing:.04em}.inspector{left:9px;right:9px;bottom:9px}.wordmark{font-size:15px}.slogan{font-size:10px}.meta{font-size:13px}}
</style><style>
/* Header identity and the explicit setup step belong to the product shell, not the terrain. */
:root{--poster-w:570px}.poster{width:var(--poster-w)}@media(min-width:681px) and (max-height:860px){:root{--poster-w:min(570px,calc((100dvh - 74px)*.72))}.workspace{gap:clamp(12px,2vw,24px);padding:12px 0}}@media(min-width:681px) and (max-width:900px){.workspace{grid-template-columns:var(--poster-w) 76px;width:max-content;max-width:calc(100% - 28px)}}
.profile{display:grid;justify-items:end;gap:6px;text-align:right}.profile strong{font-size:12px;font-weight:650;letter-spacing:.08em}.profile .meta{font-size:14px}.foot{justify-content:space-between}.foot span:last-child{max-width:46%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right}.setup-sheet{position:fixed;z-index:20;inset:0;display:grid;place-items:center;padding:24px;background:#29312b55;opacity:0;visibility:hidden;transition:opacity .18s ease,visibility .18s}.setup-sheet.show{opacity:1;visibility:visible}.setup-card{position:relative;width:min(450px,100%);padding:27px;background:#f4f1e8;border:1px solid #777b72;box-shadow:0 28px 70px #262b261f}.setup-kicker{margin:0 0 12px;color:#6b6f67;font-size:10px;letter-spacing:.14em}.setup-card h2{margin:0 34px 22px 0;font-size:22px;line-height:1.35;font-weight:650;letter-spacing:.03em}.setup-card label{display:grid;gap:7px;margin:15px 0}.setup-card label span{font-size:11px;color:#4c524a;letter-spacing:.06em}.setup-card input{width:100%;border:0;border-bottom:1px solid #92968d;border-radius:0;padding:9px 0;background:transparent;color:#242a23;font-size:14px;outline:none}.setup-card input:focus{border-bottom:2px solid #46564c}.setup-help{margin:18px 0;color:#6a6e66;font-size:11px;line-height:1.65}.setup-submit{width:100%;padding:12px;border:1px solid #3f4b42;background:#3f4b42;color:#f7f4ec;font-size:12px;letter-spacing:.08em;cursor:pointer}.setup-submit:hover{background:#2d3930}.setup-close{position:absolute;top:14px;right:14px;width:30px;height:30px;border:1px solid #aaa99f;background:transparent;color:#4e534b;font-size:19px;cursor:pointer}
/* Map annotation card: deliberately denser and quieter than a generic modal. */
.inspector{left:14px;right:14px;bottom:14px;max-height:47%;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px 16px;padding:11px 17px 15px;border-color:#4a5048;border-top:2px solid #4a5048;background:#f5f2e9f7;box-shadow:0 -12px 28px #292d2826;overflow:hidden}.inspector::before{content:"";grid-column:1/-1;justify-self:center;width:42px;height:2px;margin-bottom:1px;background:#8a8f87}.inspector h2{margin:4px 0 7px;font-size:21px;letter-spacing:.06em}.inspector .answer{max-width:460px;font-size:12px;line-height:1.65}.inspector .evidence{display:block;color:#6a6e66;font:600 9px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.13em}.inspector .subpeaks{margin-top:5px;color:#646961;font-size:10px}.inspector .close{width:30px;height:30px;border:1px solid #94988f;background:transparent;cursor:pointer}.articles{grid-column:1/-1;display:grid;grid-template-columns:1fr;gap:0;margin-top:2px;padding-top:7px;border-top:1px solid #c6c8c0;overflow:auto}.articles a{display:grid;grid-template-columns:70px minmax(0,1fr);gap:3px 10px;max-width:none;padding:8px 2px;color:#30352f;text-decoration:none;border-bottom:1px solid #d7d5cc}.articles a:last-child{border-bottom:0}.articles time{grid-row:1/3;color:#777c75;font:500 9px ui-monospace,SFMono-Regular,Menlo,monospace}.articles strong{overflow:hidden;font-size:11px;font-weight:650;white-space:nowrap;text-overflow:ellipsis}.articles p{display:-webkit-box;overflow:hidden;color:#666b63;font-size:10px;line-height:1.45;-webkit-line-clamp:2;-webkit-box-orient:vertical}.articles a:hover{background:#e9e7df;text-decoration:none}.articles a::before{content:none}@media(max-width:680px){.inspector{padding:10px 12px 12px;max-height:52%}.inspector h2{font-size:18px}.inspector .answer{font-size:11px}.articles a{grid-template-columns:58px minmax(0,1fr)}}
/* Precision-instrument shell. Terrain stays light; controls carry the machine character. */
html,body{overflow-x:hidden}body{background:radial-gradient(ellipse at 50% 5%,#e8e6de 0,#d6d4cc 48%,#c7c6bf 100%)}.workspace{grid-template-columns:minmax(120px,1fr) var(--poster-w) 80px;gap:16px}.poster{grid-template-rows:auto 1fr;gap:10px;padding:14px;background:#efede6;border-color:#9d9f98;box-shadow:0 26px 62px #30363020,0 1px 0 #fff9}.poster::after{inset:6px;border-color:#cac9c1}.head{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;padding:4px 4px 11px;border-bottom:1px solid #b8bab2}.wordmark{font-size:20px;font-weight:650;letter-spacing:.08em}.slogan{margin-top:7px;font-size:10px;letter-spacing:.04em}.profile{gap:5px;padding-left:18px}.profile strong{font-size:12px}.profile .meta{font-size:13px;font-variant-numeric:tabular-nums}.map-shell{border:1px solid #969b94;box-shadow:inset 0 0 0 5px #e4e2da,inset 0 0 0 6px #c7c8c0;background:#e7e4dc}.timestamp{position:absolute;z-index:2;right:7px;bottom:7px;padding:2px 7px;background:#e8e5dccc;color:#6c716a;font:500 7px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.08em;white-space:nowrap;pointer-events:none}.tools{width:80px;gap:0;padding:6px;background:#202422;border:1px solid #5d625e;box-shadow:0 18px 36px #2a302b30;color:#dbe0dc}.control-head{display:grid;gap:5px;padding:8px 7px 11px;color:#919792;font:600 7px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.12em;border-bottom:1px solid #4a4f4c}.control-head i{color:#a4aaa6;font-style:normal;font-size:7px}.tool{position:relative;width:100%;min-height:64px;display:grid;grid-template-columns:auto 1fr;grid-template-rows:auto auto;align-content:center;justify-items:start;gap:3px 7px;padding:10px 9px;border:0;border-bottom:1px solid #414643;background:transparent;color:#d9dfdb;text-align:left;transition:background .16s ease,color .16s ease;text-decoration:none}.tool b{grid-row:1/3;color:#7f8681;font:500 8px ui-monospace,SFMono-Regular,Menlo,monospace}.tool span{font:600 9px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.08em}.tool small{color:#9da39f;font-size:8px;letter-spacing:.04em}.tool:hover{transform:none;background:#303532;color:#fff;box-shadow:inset 2px 0 #b1b7b3}.tool:disabled{cursor:wait;background:#303532;color:#b1b7b3;box-shadow:inset 2px 0 #b1b7b3}.tool:focus-visible{outline:1px solid #b1b7b3;outline-offset:-3px}.desktop-note{display:none!important}@media(min-width:681px) and (max-width:900px){.workspace{grid-template-columns:var(--poster-w) 80px;gap:12px}}@media(max-width:680px){body{background:#c9c8c1}.workspace{width:100%;max-width:none;min-height:100vh;display:block;padding:7px}.poster{width:100%;min-height:0;padding:9px}.tools{display:none}.head{padding:3px 3px 9px}.wordmark{font-size:16px}.slogan{font-size:9px}.profile{padding-left:8px}.profile strong{font-size:10px}.profile .meta{font-size:11px}.map-shell{margin:0}.inspector{left:8px;right:8px;bottom:8px}.timestamp{right:5px;bottom:5px;font-size:6px}}@media(max-width:410px){.head{grid-template-columns:minmax(0,1fr) auto;gap:6px}.profile{padding-left:4px}.profile strong,.profile .meta{font-size:9px}}
</style><style>
/* Obsidian Atlas is a reading skin. Semantic data and terrain geometry stay untouched. */
body.obsidian-atlas{--ink:#e9dfca;--muted:#a79a85;--paper:#121310;--paper-2:#171814;--line:#8b7b64;--night:#11120f;background:#cbc8bf;color:#292b27}
.obsidian-atlas .poster{background-color:#121310;background-image:url("__PAPER_TEXTURE__");background-size:cover;background-position:center;border-color:#686055;box-shadow:0 30px 74px #23221f40,0 1px 0 #fff2}
.obsidian-atlas .poster::after{border-color:#74695780}.obsidian-atlas .head{border-color:#766b5980}.obsidian-atlas .wordmark,.obsidian-atlas .profile strong,.obsidian-atlas .profile .meta{color:#e9dfca}.obsidian-atlas .slogan{color:#a79a85}
.obsidian-atlas .map-shell{background:#10110f;border-color:#6b6256;box-shadow:inset 0 0 0 5px #151612,inset 0 0 0 6px #514a40}.obsidian-atlas .map-shell::before{background-image:none}
.obsidian-atlas .timestamp{background:#11120fd9;color:#9a8c77}
.obsidian-atlas .inspector{border-color:#8a7b65;border-top-width:1px;background:#171814f5;box-shadow:0 -14px 32px #0008;color:#e9dfca}.obsidian-atlas .inspector::before{height:1px;background:#776b59}.obsidian-atlas .inspector .evidence,.obsidian-atlas .inspector .subpeaks,.obsidian-atlas .inspector .answer{color:#ad9e87}.obsidian-atlas .inspector .close{border-color:#695f50;color:#d8cbb2}.obsidian-atlas .articles{border-color:#514a40}.obsidian-atlas .articles a{color:#ded3bd;border-color:#3e3a33}.obsidian-atlas .articles time,.obsidian-atlas .articles p{color:#8f8371}.obsidian-atlas .articles a:hover{background:#24231e}
.obsidian-atlas .tools{background:#d7d0c1;border-color:#8d826f;color:#292822;box-shadow:0 18px 38px #26231f38}.obsidian-atlas .control-head{color:#726858;border-color:#a69b88}.obsidian-atlas .control-head i{color:#625b4e}.obsidian-atlas .tool{color:#302e28;border-color:#b3a997}.obsidian-atlas .tool b,.obsidian-atlas .tool small{color:#756b5b}.obsidian-atlas .tool:hover{background:#eee7d8;color:#171713;box-shadow:inset 2px 0 #6f6556}.obsidian-atlas .tool:focus-visible{outline-color:#5f574b}.obsidian-atlas .tool:disabled{background:#c5beaf;color:#777065;box-shadow:inset 2px 0 #8f8574}
.obsidian-atlas .setup-sheet{background:#16171399}.obsidian-atlas .setup-card{background:#171814;color:#e8ddc8;border-color:#756a58;box-shadow:0 28px 70px #0008}.obsidian-atlas .setup-kicker,.obsidian-atlas .setup-help,.obsidian-atlas .setup-card label span{color:#a79a85}.obsidian-atlas .setup-card input{color:#eee4d0;border-color:#716754}.obsidian-atlas .setup-submit{background:#ded1b8;border-color:#ded1b8;color:#171814}.obsidian-atlas .setup-submit:hover{background:#f0e5d0}.obsidian-atlas .setup-close{border-color:#5e564a;color:#d9cdb7}
@media(max-width:680px){body.obsidian-atlas{background:#cbc8bf}.obsidian-atlas .poster{background-color:#121310}}
</style></head><body class="__THEME__">
<main class="workspace"><aside class="context" id="context" aria-label="地图索引"><strong id="context-title">文山.skill</strong><p id="context-index"></p><div class="rule"></div><p id="context-guide"></p></aside>
<article class="poster" id="poster"><header class="head"><div><div class="wordmark" id="wordmark">文山.skill</div><p class="slogan" id="slogan"></p></div><div class="profile"><strong id="nickname"></strong><span class="meta" id="meta"></span></div></header><section class="map-shell"><canvas id="map" width="900" height="1200" tabindex="0" aria-label="知识山峰地图"></canvas><aside class="inspector" id="inspector" aria-live="polite"></aside><small class="timestamp" id="timestamp"></small></section></article>
<nav class="tools" id="tools" aria-label="地图控制台"><div class="control-head"><span>CONTROL</span><i>ON</i></div><button class="tool" id="setup" type="button"><b>01</b><span>SET</span><small id="setup-label">设置</small></button><button class="tool" id="language" type="button"><b>02</b><span>LANG</span><small id="language-label">EN</small></button><a class="tool" href="https://github.com/pakco77/wenshan-skill/tree/main/knowledge-peak-map" target="_blank" rel="noopener"><b>03</b><span>SOURCE</span><small>GitHub</small></a><button class="tool" id="theme" type="button"><b>04</b><span>THEME</span><small id="theme-label">夜间</small></button><button class="tool" id="snapshot" type="button"><b>05</b><span>EXPORT</span><small id="snapshot-label">截图</small></button></nav>
<section class="setup-sheet" id="setup-sheet" aria-hidden="true"><form class="setup-card" id="setup-form"><button class="setup-close" id="setup-close" type="button" aria-label="关闭">×</button><p class="setup-kicker" id="setup-kicker">文山.skill / SETUP</p><h2 id="setup-title">先确定这张图属于谁，分析什么。</h2><label><span id="nickname-field-label">01 · 当前用户昵称</span><input id="nickname-input" name="nickname" required maxlength="40" placeholder="例如：Pakco"></label><label><span id="collection-field-label">02 · 文章集合 URL</span><input id="collection-input" name="collection" required maxlength="500" placeholder="粘贴 Obsidian 文件夹、本地集合或文章库 URL"></label><p class="setup-help" id="setup-help">保存后更新地图署名与材料引用。真正的文章读取、证据筛选与重新生成，由本地 Agent 在此集合上执行。</p><button class="setup-submit" id="setup-submit" type="submit">保存此地图设置</button></form></section></main>
<script>
const DATA=__DATA__,canvas=document.querySelector('#map'),ctx=canvas.getContext('2d'),W=canvas.width,H=canvas.height,inspector=document.querySelector('#inspector');
const PALETTES={
  'survey-parchment':{bg:'#e8e5dc',line:'#4c504c',dot:'#30332f',dotStroke:'#e8e5dc',title:'#242722',count:'#4c504c',muted:'#575a53',focus:'#2f3430',grid:'#73776f',dust:'#72766e'},
  'obsidian-atlas':{bg:'#10110f',line:'#8c7a61',dot:'#d9c9a9',dotStroke:'#10110f',title:'#eadfc8',count:'#e0ceb0',muted:'#a49680',focus:'#ded0b5',grid:'#776b59',dust:'#a08d70'}
};
const WORDS={zh:{brand:'文山.skill',slogan:'用山脉展示你的篇章',pageTitle:'文山.skill · 知识山峰',anonymous:'匿名',mapAria:'知识山峰地图',toolsAria:'地图控制台',contextIndex:'KNOWLEDGE PEAKS<br>EVIDENCE-GATED ATLAS<br>LOCAL AGENT',contextGuide:'选择一座山<br>阅读它的回答<br>回到原始文章',setupLabel:'设置',themeDark:'夜间',themeLight:'日间',setupKicker:'文山.skill / 设置',setupTitle:'先确定这张图属于谁，分析什么。',nicknameField:'01 · 当前用户昵称',collectionField:'02 · 文章集合 URL',nicknamePlaceholder:'例如：Pakco',collectionPlaceholder:'粘贴 Obsidian 文件夹、本地集合或文章库 URL',setupHelp:'保存后更新地图署名与材料引用。真正的文章读取、证据筛选与重新生成，由本地 Agent 在此集合上执行。',setupSubmit:'保存此地图设置',stat:(articles,mountains)=>`${articles}文 ≈ ${mountains}山`,pieces:n=>`${n}篇`,articles:n=>`${n} 篇独立文章`,generatedAt:value=>String(value).replace('T',' '),source:'查看文章',close:'关闭',shot:'截图',exporting:'生成中',saved:'已导出'},en:{brand:'Wenshan.skill',slogan:'Map your writing as mountains.',pageTitle:'Wenshan.skill · Knowledge Peaks',anonymous:'Anonymous',mapAria:'Knowledge mountain map',toolsAria:'Map controls',contextIndex:'KNOWLEDGE PEAKS<br>EVIDENCE-GATED ATLAS<br>LOCAL AGENT',contextGuide:'Choose a mountain<br>Read its answer<br>Return to the source',setupLabel:'Setup',themeDark:'Night',themeLight:'Day',setupKicker:'Wenshan.skill / SETUP',setupTitle:'Define whose map this is and which writing to analyze.',nicknameField:'01 · Author nickname',collectionField:'02 · Article collection URL',nicknamePlaceholder:'For example: Pakco',collectionPlaceholder:'Paste an Obsidian folder, local collection, or article-library URL',setupHelp:'Saving updates attribution and the collection reference. Your local Agent performs article reading, evidence review, and regeneration on that collection.',setupSubmit:'Save map settings',stat:(articles,mountains)=>`${articles} pieces ≈ ${mountains} peaks`,pieces:n=>`${n} pieces`,articles:n=>`${n} independent pieces`,generatedAt:value=>String(value).replace('T',' '),source:'Open article',close:'Close',shot:'Capture',exporting:'Rendering',saved:'Exported'}};
let language=DATA.profile?.language==='en'?'en':'zh',theme=DATA.profile?.theme==='obsidian-atlas'?'obsidian-atlas':'survey-parchment',hover=null,active=null;const q=()=>WORDS[language],palette=()=>PALETTES[theme],copy=h=>language==='en'?{label:h.label_en||h.label,answer:h.answer_en||h.answer}:{label:h.label,answer:h.answer},esc=s=>String(s).replace(/[&<>'"]/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[x]));
const settingsKey='wenshan.skill.setup.v1';let settings={...(DATA.profile||{})};try{settings={...settings,...JSON.parse(localStorage.getItem(settingsKey)||'{}')}}catch(_){/* ponytail: file previews may not expose persistent storage. */}
// generic_anchors already reserves safe page margins. Re-normalizing all jittered
// evidence points compressed dense 3x3 maps and made labels collide.
const hills=DATA.territories;
const maxAltitude=Math.max(...hills.map(h=>h.count));
const view={scale:1,x:0,y:0};let drag=null,didDrag=false,animation=0;
function seeded(text,salt){let value=(2166136261^(salt||0))>>>0;for(const ch of text){value^=ch.codePointAt(0);value=Math.imul(value,16777619)}return(value>>>0)/4294967295}
function terrainField(){const nx=240,ny=320,g=new Float32Array(nx*ny),byId=new Map(hills.map(h=>[h.id,h])),profiles=hills.map(h=>{const altitude=.62+.98*Math.sqrt(h.count/maxAltitude),phase2=seeded(h.id,2)*Math.PI*2,phase3=seeded(h.id,3)*Math.PI*2,phase5=seeded(h.id,5)*Math.PI*2,phase7=seeded(h.id,11)*Math.PI*2,tilt=(seeded(h.id,7)-.5)*.55,aspect=.80+seeded(h.id,17)*.40;return{h,altitude,phase2,phase3,phase5,phase7,cosT:Math.cos(tilt),sinT:Math.sin(tilt),rx:(.102+.025*altitude)*aspect,ry:(.086+.023*altitude)*(1.04/aspect)}}),ridges=(DATA.relations||[]).map(relation=>({a:byId.get(relation.source),b:byId.get(relation.target),strength:Number(relation.strength)||0})).filter(r=>r.a&&r.b);let max=0;for(let y=0;y<ny;y++)for(let x=0;x<nx;x++){const px=x/(nx-1),py=y/(ny-1);let value=0;for(const p of profiles){const dx=px-p.h.x,dy=py-p.h.y,localX=dx*p.cosT+dy*p.sinT,localY=-dx*p.sinT+dy*p.cosT,angle=Math.atan2(localY/p.ry,localX/p.rx),rugged=1+.105*Math.sin(angle*2+p.phase2)+.058*Math.sin(angle*3+p.phase3)+.032*Math.sin(angle*5+p.phase5)+.017*Math.sin(angle*7+p.phase7),crossSlope=1+.042*Math.cos(angle*2+p.phase3)+.021*Math.sin(angle*4+p.phase5),distance=(localX/(p.rx*rugged))**2+(localY/(p.ry*crossSlope))**2;value+=p.altitude*Math.exp(-distance*1.58)}for(const ridge of ridges){const vx=ridge.b.x-ridge.a.x,vy=ridge.b.y-ridge.a.y,length2=vx*vx+vy*vy,t=Math.max(0,Math.min(1,((px-ridge.a.x)*vx+(py-ridge.a.y)*vy)/Math.max(length2,.0001))),qx=ridge.a.x+vx*t,qy=ridge.a.y+vy*t,side=Math.hypot(px-qx,py-qy),width=.030+.032*ridge.strength,endTaper=.70+.30*Math.sin(Math.PI*t);value+=(.16+.25*ridge.strength)*endTaper*Math.exp(-Math.pow(side/width,2)*1.35)}g[y*nx+x]=value;if(value>max)max=value}return{g,nx,ny,max}}
const CASES={1:[[3,0]],2:[[0,1]],3:[[3,1]],4:[[1,2]],5:[[0,3],[1,2]],6:[[0,2]],7:[[3,2]],8:[[2,3]],9:[[0,2]],10:[[0,1],[2,3]],11:[[1,2]],12:[[1,3]],13:[[0,1]],14:[[3,0]]};
function edgePoint(edge,x,y,a,b,d,z,level){const between=(u,v)=>u===v?.5:Math.max(0,Math.min(1,(level-u)/(v-u)));if(edge===0)return[x+between(a,b),y];if(edge===1)return[x+1,y+between(b,d)];if(edge===2)return[x+between(z,d),y+1];return[x,y+between(a,z)]}
function levelSegments(field,level){const {g,nx,ny}=field,segments=[];for(let y=0;y<ny-1;y++)for(let x=0;x<nx-1;x++){const a=g[y*nx+x],b=g[y*nx+x+1],d=g[(y+1)*nx+x+1],z=g[(y+1)*nx+x],mask=(a>=level?1:0)|(b>=level?2:0)|(d>=level?4:0)|(z>=level?8:0);for(const pair of CASES[mask]||[])segments.push([edgePoint(pair[0],x,y,a,b,d,z,level),edgePoint(pair[1],x,y,a,b,d,z,level)])}return segments}
function connectSegments(segments){const key=p=>`${p[0].toFixed(4)},${p[1].toFixed(4)}`,lookup=new Map(),used=new Uint8Array(segments.length);segments.forEach((segment,index)=>segment.forEach((point,end)=>{const k=key(point);if(!lookup.has(k))lookup.set(k,[]);lookup.get(k).push([index,end])}));const chains=[];function extend(chain,front){while(true){const point=front?chain[0]:chain[chain.length-1],choices=lookup.get(key(point))||[],choice=choices.find(([index])=>!used[index]);if(!choice)break;const [index,end]=choice;used[index]=1;const segment=segments[index],next=segment[end===0?1:0];if(front)chain.unshift(next);else chain.push(next)}}segments.forEach((segment,index)=>{if(used[index])return;used[index]=1;const chain=[segment[0],segment[1]];extend(chain,false);extend(chain,true);if(chain.length>3)chains.push(chain)});return chains}
function strokeSmooth(chain,nx,ny){const points=chain.map(([x,y])=>[x*W/(nx-1),y*H/(ny-1)]),closed=Math.hypot(points[0][0]-points[points.length-1][0],points[0][1]-points[points.length-1][1])<5;if(closed)points.pop();if(points.length<3)return;ctx.beginPath();if(closed){const first=points[0],last=points[points.length-1];ctx.moveTo((first[0]+last[0])/2,(first[1]+last[1])/2);for(let index=0;index<points.length;index++){const point=points[index],next=points[(index+1)%points.length];ctx.quadraticCurveTo(point[0],point[1],(point[0]+next[0])/2,(point[1]+next[1])/2)}ctx.closePath()}else{ctx.moveTo(points[0][0],points[0][1]);for(let index=1;index<points.length-1;index++){const point=points[index],next=points[index+1];ctx.quadraticCurveTo(point[0],point[1],(point[0]+next[0])/2,(point[1]+next[1])/2)}ctx.lineTo(points[points.length-1][0],points[points.length-1][1])}ctx.stroke()}
let terrainCache=null;function paintGrid(){if(theme!=='obsidian-atlas')return;const p=palette(),minor=60,major=minor*3;ctx.save();ctx.strokeStyle=p.grid;ctx.lineWidth=.62;ctx.globalAlpha=.095;for(let x=0;x<=W;x+=minor){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke()}for(let y=0;y<=H;y+=minor){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke()}ctx.lineWidth=.92;ctx.globalAlpha=.17;for(let x=0;x<=W;x+=major){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke()}for(let y=0;y<=H;y+=major){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke()}ctx.globalAlpha=.28;ctx.lineWidth=.88;for(let y=minor;y<H;y+=minor*2)for(let x=minor;x<W;x+=minor*2){ctx.beginPath();ctx.moveTo(x-5,y);ctx.lineTo(x+5,y);ctx.moveTo(x,y-5);ctx.lineTo(x,y+5);ctx.stroke()}ctx.restore()}
function paintNoise(){if(theme!=='obsidian-atlas')return;const p=palette();ctx.save();for(let i=0;i<520;i++){const x=seeded(`grain-x-${i}`,i+31)*W,y=seeded(`grain-y-${i}`,i+73)*H,r=.18+seeded(`grain-r-${i}`,i+127)*.48;ctx.fillStyle=i%3===0?p.line:'#050605';ctx.globalAlpha=.018+seeded(`grain-a-${i}`,i+173)*.045;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill()}ctx.restore()}
function paintDust(){if(theme!=='obsidian-atlas')return;const p=palette();ctx.save();ctx.fillStyle=p.dust;for(let i=0;i<320;i++){const x=seeded(`dust-x-${i}`,i)*W,y=seeded(`dust-y-${i}`,i+91)*H,r=.42+seeded(`dust-r-${i}`,i+181)*1.12;ctx.globalAlpha=.09+seeded(`dust-a-${i}`,i+271)*.21;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill()}ctx.restore()}
function paintRange(){const field=terrainCache||(terrainCache=terrainField()),rings=theme==='obsidian-atlas'?24:16,p=palette();ctx.save();ctx.strokeStyle=p.line;ctx.lineCap='round';ctx.lineJoin='round';for(let ring=1;ring<=rings;ring++){const t=ring/rings,level=field.max*((theme==='obsidian-atlas'?.022:.036)+Math.pow(t,1.48)*(theme==='obsidian-atlas'?.87:.83)),major=ring===1||ring===rings||ring%4===0,chains=connectSegments(levelSegments(field,level));ctx.globalAlpha=theme==='obsidian-atlas'?(major?.44+.20*t:.17+.22*t):(major?.58:.27);ctx.lineWidth=(theme==='obsidian-atlas'?(major?1.18+.80*t:.58+.46*t):(major?1.75:.78))/view.scale;chains.forEach((chain,index)=>{if(theme==='obsidian-atlas'){const fault=seeded(`fault-${ring}-${index}`,ring*47+index);if(fault>.66)ctx.setLineDash([72/view.scale,8/view.scale,28/view.scale,6/view.scale]);else if(fault>.48)ctx.setLineDash([132/view.scale,9/view.scale]);else ctx.setLineDash([]);ctx.lineDashOffset=-seeded(`offset-${ring}-${index}`,index*19)*150/view.scale}strokeSmooth(chain,field.nx,field.ny)});ctx.setLineDash([])}ctx.restore()}
function wrap(text,x,y,width,line){let row='';for(const ch of [...text]){const next=row+ch;if(ctx.measureText(next).width>width&&row){ctx.fillText(row,x,y);y+=line;row=ch}else row=next}if(row)ctx.fillText(row,x,y)}
function titleFont(text,maxWidth){let size=29;while(size>16){ctx.font=`650 ${size}px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif`;if(ctx.measureText(text).width<=maxWidth)break;size-=1}return size}
function evidenceOffsets(h){if(h.x<.22)return[[122,-76],[136,-14],[110,82]];if(h.x>.78)return[[-122,-76],[-136,-14],[-110,82]];if(h.y>.78)return[[-118,-76],[118,-48],[-104,-122]];return[[-120,-76],[120,-48],[-105,118]]}
function peripheralLabels(h,x,y,selected){if(theme!=='obsidian-atlas')return;const terms=(h.evidence_labels||[]).slice(0,3),p=palette(),offsets=evidenceOffsets(h);ctx.save();ctx.textAlign='center';ctx.fillStyle=p.title;ctx.strokeStyle=p.line;ctx.globalAlpha=selected ? .80 : .58;ctx.font='560 17px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';terms.forEach((term,index)=>{const text=language==='en'?(term.label_en||term.label):term.label,[dx,dy]=offsets[index];if(!text)return;ctx.fillText(text,x+dx,y+dy);const width=Math.min(96,Math.max(34,ctx.measureText(text).width*.76));ctx.lineWidth=.9/view.scale;ctx.beginPath();ctx.moveTo(x+dx-width/2,y+dy+11);ctx.lineTo(x+dx+width/2,y+dy+11);ctx.stroke()});ctx.restore()}
function label(h){const x=h.x*W,y=h.y*H,p=palette(),words=q(),text=copy(h),selected=active?.id===h.id,dense=hills.length>=7,titleWidth=dense?232:340;ctx.save();ctx.textAlign='center';ctx.globalAlpha=active&&!selected ? .55 : 1;ctx.fillStyle=p.count;ctx.font=`810 ${selected?31:dense?27:29}px ui-monospace,SFMono-Regular,Menlo,monospace`;ctx.strokeStyle=p.bg;ctx.lineWidth=4.2/view.scale;ctx.strokeText(words.pieces(h.count),x,y-52);ctx.fillText(words.pieces(h.count),x,y-52);ctx.fillStyle=p.dot;ctx.beginPath();ctx.moveTo(x,y-38);ctx.lineTo(x-22,y+14);ctx.lineTo(x+22,y+14);ctx.closePath();ctx.fill();ctx.strokeStyle=p.title;ctx.globalAlpha=active&&!selected ? .28 : .62;ctx.lineWidth=1/view.scale;ctx.beginPath();ctx.moveTo(x-19,y+15);ctx.lineTo(x+19,y+15);ctx.stroke();ctx.globalAlpha=active&&!selected ? .55 : 1;const size=titleFont(text.label,titleWidth),titleSize=selected?Math.min(size+5,34):dense?Math.min(size+2,29):size;ctx.fillStyle=p.title;ctx.font=`700 ${titleSize}px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif`;ctx.strokeStyle=p.bg;ctx.lineWidth=(theme==='obsidian-atlas'?4.4:5)/view.scale;ctx.strokeText(text.label,x,y+59);ctx.fillText(text.label,x,y+59);peripheralLabels(h,x,y,selected);if(!dense&&theme!=='obsidian-atlas'){ctx.fillStyle=p.muted;ctx.font='12px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';wrap(text.answer,x,y+89,310,19)}ctx.restore()}
function focusRing(hill){const x=hill.x*W,y=hill.y*H,r=Math.max(112,...hill.points.map(p=>Math.hypot(p.x*W-x,p.y*H-y)+32)),p=palette();ctx.save();ctx.strokeStyle=p.focus;ctx.globalAlpha=theme==='obsidian-atlas'?.70:.78;ctx.lineWidth=(theme==='obsidian-atlas'?1.25:1.7)/view.scale;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.stroke();ctx.restore()}
function draw(){const p=palette();ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle=p.bg;ctx.fillRect(0,0,W,H);paintGrid();paintNoise();ctx.save();ctx.translate(view.x,view.y);ctx.scale(view.scale,view.scale);paintDust();paintRange();for(const hill of hills){ctx.save();for(const point of hill.points){ctx.beginPath();ctx.arc(point.x*W,point.y*H,(theme==='obsidian-atlas'?2.55:3.1)/view.scale,0,Math.PI*2);ctx.fillStyle=p.dot;ctx.globalAlpha=active&&active.id!==hill.id?(theme==='obsidian-atlas'?.22:.38):(theme==='obsidian-atlas'?.58:.76);ctx.fill();ctx.strokeStyle=p.dotStroke;ctx.globalAlpha=active&&active.id!==hill.id?(theme==='obsidian-atlas'?.22:.48):(theme==='obsidian-atlas'?.68:.92);ctx.lineWidth=(theme==='obsidian-atlas'?.72:1.15)/view.scale;ctx.stroke()}ctx.restore()}if(active)focusRing(active);for(const hill of hills.filter(h=>h.id!==active?.id))label(hill);if(active)label(active);ctx.restore()}
function canvasPoint(event){const box=canvas.getBoundingClientRect();return{x:(event.clientX-box.left)*W/box.width,y:(event.clientY-box.top)*H/box.height}}
function worldPoint(event){const point=canvasPoint(event);return{x:(point.x-view.x)/view.scale,y:(point.y-view.y)/view.scale,screen:point}}
function nearest(event){const point=worldPoint(event);let best=null,d=Infinity;for(const hill of hills)for(const p of hill.points){const value=(p.x*W-point.x)**2+(p.y*H-point.y)**2;if(value<d){best={hill,p};d=value}}return d<(18/view.scale)**2?best:null}
function clampView(candidate=view){candidate.scale=Math.max(1,Math.min(3.2,candidate.scale));if(candidate.scale===1){candidate.x=0;candidate.y=0;return candidate}const marginX=W*.14,marginY=H*.42;candidate.x=Math.min(marginX,Math.max(W-W*candidate.scale-marginX,candidate.x));candidate.y=Math.min(marginY,Math.max(H-H*candidate.scale-marginY,candidate.y));return candidate}
function animateView(target){cancelAnimationFrame(animation);clampView(target);const start={...view},begin=performance.now(),duration=matchMedia('(prefers-reduced-motion: reduce)').matches?0:320;function frame(now){const raw=duration?Math.min(1,(now-begin)/duration):1,eased=1-Math.pow(1-raw,3);view.scale=start.scale+(target.scale-start.scale)*eased;view.x=start.x+(target.x-start.x)*eased;view.y=start.y+(target.y-start.y)*eased;draw();if(raw<1)animation=requestAnimationFrame(frame)}animation=requestAnimationFrame(frame)}
function focusHill(hill,animate=true){active=hill;const scale=1.48,target=clampView({scale,x:W*.5-hill.x*W*scale,y:H*.27-hill.y*H*scale});if(animate)animateView(target);else{Object.assign(view,target);draw()}detail(hill,false)}
function closeDetail(reset=false){active=null;inspector.classList.remove('show');if(reset)animateView({scale:1,x:0,y:0});else draw()}
function detail(hill,redraw=true){active=hill;const words=q(),text=copy(hill),ordered=[...hill.points].sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))),links=ordered.map(p=>`<a href="${esc(p.url)}"><time>${esc(p.date||'—')}</time><strong>${esc(p.title)}</strong><p>${esc(p.judgment||'')}</p></a>`).join(''),subpeaks=(hill.subpeaks||[]).map(p=>`${esc(language==='en'?(p.label_en||p.label):p.label)} · ${p.count}`).join(' / ');inspector.innerHTML=`<div><small class="evidence">${words.articles(hill.count)}</small><h2>${esc(text.label)}</h2>${subpeaks?`<div class="subpeaks">${subpeaks}</div>`:''}<p class="answer">${esc(text.answer)}</p></div><button class="close" type="button" aria-label="${words.close}">×</button><div class="articles">${links}</div>`;inspector.querySelector('.close').onclick=()=>closeDetail(false);inspector.classList.add('show');if(redraw)draw()}
function chrome(){const words=q(),articleCount=hills.reduce((n,h)=>n+h.count,0);document.body.className=theme;document.documentElement.lang=language==='zh'?'zh-CN':'en';document.title=words.pageTitle;document.querySelector('#wordmark').textContent=words.brand;document.querySelector('#slogan').textContent=words.slogan;document.querySelector('#meta').textContent=words.stat(articleCount,hills.length);document.querySelector('#nickname').textContent=settings.nickname||words.anonymous;document.querySelector('#timestamp').textContent=words.generatedAt(DATA.generated_at);document.querySelector('#language-label').textContent=language==='zh'?'EN':'中';document.querySelector('#theme-label').textContent=theme==='obsidian-atlas'?words.themeLight:words.themeDark;document.querySelector('#snapshot-label').textContent=words.shot;document.querySelector('#setup-label').textContent=words.setupLabel;document.querySelector('#context-title').textContent=words.brand;document.querySelector('#context-index').innerHTML=words.contextIndex;document.querySelector('#context-guide').innerHTML=words.contextGuide;document.querySelector('#map').setAttribute('aria-label',words.mapAria);document.querySelector('#tools').setAttribute('aria-label',words.toolsAria);document.querySelector('#setup-close').setAttribute('aria-label',words.close);document.querySelector('#setup-kicker').textContent=words.setupKicker;document.querySelector('#setup-title').textContent=words.setupTitle;document.querySelector('#nickname-field-label').textContent=words.nicknameField;document.querySelector('#collection-field-label').textContent=words.collectionField;document.querySelector('#nickname-input').placeholder=words.nicknamePlaceholder;document.querySelector('#collection-input').placeholder=words.collectionPlaceholder;document.querySelector('#setup-help').textContent=words.setupHelp;document.querySelector('#setup-submit').textContent=words.setupSubmit}
function openSetup(){document.querySelector('#nickname-input').value=settings.nickname||'';document.querySelector('#collection-input').value=settings.collection_url||'';document.querySelector('#setup-sheet').classList.add('show');document.querySelector('#setup-sheet').setAttribute('aria-hidden','false');document.querySelector('#nickname-input').focus()}function closeSetup(){document.querySelector('#setup-sheet').classList.remove('show');document.querySelector('#setup-sheet').setAttribute('aria-hidden','true')}
document.querySelector('#setup').onclick=openSetup;document.querySelector('#setup-close').onclick=closeSetup;document.querySelector('#setup-sheet').onclick=e=>{if(e.target===e.currentTarget)closeSetup()};document.querySelector('#setup-form').onsubmit=e=>{e.preventDefault();const fields=e.currentTarget.elements;settings.nickname=fields.namedItem('nickname').value.trim();settings.collection_url=fields.namedItem('collection').value.trim();try{localStorage.setItem(settingsKey,JSON.stringify(settings))}catch(_){/* ponytail: preview remains usable without persistence. */}chrome();closeSetup()};
document.querySelector('#language').onclick=()=>{language=language==='zh'?'en':'zh';chrome();if(active)detail(active,false);draw()};
document.querySelector('#theme').onclick=()=>{theme=theme==='obsidian-atlas'?'survey-parchment':'obsidian-atlas';chrome();draw()};
canvas.addEventListener('wheel',event=>{event.preventDefault();const point=canvasPoint(event),worldX=(point.x-view.x)/view.scale,worldY=(point.y-view.y)/view.scale,next=Math.max(1,Math.min(3.2,view.scale*Math.exp(-event.deltaY*.0012)));view.x=point.x-worldX*next;view.y=point.y-worldY*next;view.scale=next;clampView();draw()},{passive:false});
canvas.addEventListener('pointerdown',event=>{if(event.button!==0)return;cancelAnimationFrame(animation);const point=canvasPoint(event);drag={id:event.pointerId,x:point.x,y:point.y,viewX:view.x,viewY:view.y};didDrag=false;canvas.setPointerCapture(event.pointerId);canvas.style.cursor='grabbing'});
canvas.addEventListener('pointermove',event=>{if(drag&&drag.id===event.pointerId){const point=canvasPoint(event),dx=point.x-drag.x,dy=point.y-drag.y;if(Math.hypot(dx,dy)>4)didDrag=true;view.x=drag.viewX+dx;view.y=drag.viewY+dy;clampView();draw();return}hover=nearest(event);canvas.style.cursor=hover?'pointer':'grab'});
canvas.addEventListener('pointerup',event=>{if(!drag||drag.id!==event.pointerId)return;canvas.releasePointerCapture(event.pointerId);drag=null;canvas.style.cursor='grab';if(didDrag)return;const hit=nearest(event);if(hit&&hit.p.url){window.location.href=hit.p.url;return}const point=worldPoint(event),hill=hills.map(h=>[h,(h.x*W-point.x)**2+(h.y*H-point.y)**2]).sort((a,b)=>a[1]-b[1])[0];if(hill&&hill[1]<(150/view.scale)**2)focusHill(hill[0]);else closeDetail(false)});
canvas.addEventListener('pointercancel',()=>{drag=null;didDrag=false;canvas.style.cursor='grab'});
canvas.addEventListener('mouseleave',()=>{if(!drag){hover=null;canvas.style.cursor='grab'}});
canvas.addEventListener('dblclick',event=>{event.preventDefault();closeDetail(true)});
canvas.addEventListener('keydown',event=>{if(event.key==='Escape'){closeDetail(false);return}if(event.key==='0'){event.preventDefault();closeDetail(true);return}if(!['+','=','-','_'].includes(event.key))return;event.preventDefault();const factor=event.key==='-'||event.key==='_' ? .82 : 1.22,next=Math.max(1,Math.min(3.2,view.scale*factor)),worldX=(W/2-view.x)/view.scale,worldY=(H/2-view.y)/view.scale;view.x=W/2-worldX*next;view.y=H/2-worldY*next;view.scale=next;clampView();draw()});
document.querySelector('#snapshot').onclick=()=>{const button=document.querySelector('#snapshot'),label=document.querySelector('#snapshot-label'),share=document.createElement('canvas'),s=share.getContext('2d'),articleCount=hills.reduce((n,h)=>n+h.count,0),stat=q().stat(articleCount,hills.length),nickname=settings.nickname||q().anonymous,stamp=q().generatedAt(DATA.generated_at),dark=theme==='obsidian-atlas',page=dark?'#11120f':'#efede6',ink=dark?'#eadfc8':'#202521',muted=dark?'#a49680':'#61675f',border=dark?'#796b58':'#8e948f',inner=dark?'#4f483d':'#c2c4bd',mapBg=dark?'#10110f':'#e7e4dc';button.disabled=true;label.textContent=q().exporting;share.width=1080;share.height=1440;s.fillStyle=page;s.fillRect(0,0,1080,1440);s.strokeStyle=border;s.lineWidth=2;s.strokeRect(24,24,1032,1392);s.strokeStyle=inner;s.lineWidth=1;s.strokeRect(32,32,1016,1376);s.fillStyle=ink;s.textAlign='left';s.font='650 36px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';s.fillText(q().brand,60,74);s.fillStyle=muted;s.font='18px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';s.fillText(q().slogan,60,111);s.textAlign='right';s.fillStyle=ink;s.font='650 22px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';s.fillText(nickname,1020,70);s.font='650 27px ui-monospace,SFMono-Regular,Menlo,monospace';s.fillText(stat,1020,109);s.strokeStyle=inner;s.beginPath();s.moveTo(60,136);s.lineTo(1020,136);s.stroke();const mapX=86,mapY=164,mapW=908,mapH=1211;s.fillStyle=mapBg;s.fillRect(mapX-8,mapY-8,mapW+16,mapH+16);s.strokeStyle=border;s.lineWidth=2;s.strokeRect(mapX-8,mapY-8,mapW+16,mapH+16);s.strokeStyle=inner;s.lineWidth=1;s.strokeRect(mapX-2,mapY-2,mapW+4,mapH+4);const savedView={...view},savedActive=active;Object.assign(view,{scale:1,x:0,y:0});active=null;draw();s.drawImage(canvas,mapX,mapY,mapW,mapH);Object.assign(view,savedView);active=savedActive;draw();s.strokeStyle=border;s.lineWidth=1;for(let i=0;i<=12;i++){const y=mapY+i*mapH/12,len=i%3===0?10:5;s.beginPath();s.moveTo(mapX-8,y);s.lineTo(mapX-8+len,y);s.moveTo(mapX+mapW+8,y);s.lineTo(mapX+mapW+8-len,y);s.stroke()}s.textAlign='right';s.fillStyle=muted;s.font='500 12px ui-monospace,SFMono-Regular,Menlo,monospace';s.fillText(stamp,1020,1403);share.toBlob(blob=>{if(!blob){button.disabled=false;label.textContent=q().shot;return}const link=document.createElement('a'),safe=nickname.replace(/[^\p{L}\p{N}._-]+/gu,'-');link.href=URL.createObjectURL(blob);link.download=language==='zh'?`文山-${safe}-${articleCount}文.png`:`Wenshan-${safe}-${articleCount}-pieces.png`;link.click();label.textContent=q().saved;setTimeout(()=>{URL.revokeObjectURL(link.href);button.disabled=false;label.textContent=q().shot},1400)},'image/png')};chrome();canvas.style.cursor='grab';draw();const requestedFocus=new URLSearchParams(location.search).get('focus'),initialHill=hills.find(h=>h.id===requestedFocus);if(initialHill)focusHill(initialHill,false);
</script></body></html>'''


def main() -> None:
    args = parse_args()
    scope = args.scope.expanduser().resolve()
    atlas = scope / "Cognitive Map" / "Agent Atlas"
    preferred = atlas / "wenshan-terrain.json"
    legacy = atlas / "knowledge-peaks-demo-data.json"
    data_path = args.terrain_data.expanduser().resolve() if args.terrain_data else (preferred if preferred.exists() else legacy)
    data = read_json(data_path)
    payload = build_payload(scope, data, args.nickname, args.collection_url or str(scope), args.language, args.theme)
    basename = args.output_name or ("知识山峰-Demo" if args.language == "zh" else "Wenshan-Demo")
    html_language = "zh-CN" if args.language == "zh" else "en"
    page_title = "文山.skill · 知识山峰" if args.language == "zh" else "Wenshan.skill · Knowledge Peaks"
    paper_path = Path(__file__).resolve().parent.parent / "assets" / "obsidian-paper.jpg"
    paper_texture = (
        f"data:image/jpeg;base64,{base64.b64encode(paper_path.read_bytes()).decode('ascii')}"
        if paper_path.exists()
        else ""
    )
    html = (
        HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        .replace("__HTML_LANG__", html_language)
        .replace("__PAGE_TITLE__", page_title)
        .replace("__THEME__", args.theme)
        .replace("__PAPER_TEXTURE__", paper_texture)
    )
    (atlas / f"{basename}.html").write_text(html, encoding="utf-8")
    if args.language == "zh":
        titles = "、".join(f"{item['label']}（{item['count']}）" for item in payload["territories"])
        markdown = f"""---
tags: [knowledge-peaks, evidence-gated-demo]
generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
scope: {scope.name}
---

# 文山.skill · 知识山峰

[[{basename}.html|打开交互式地图]]

本图只显示由 Agent 从当前语料识别、且有至少 **3 篇独立 canonical 文章** 支撑的场景或行业山峰：{titles}。

未通过证据门槛的候选方向不会显示为占位、“待勘探”或虚构山体。
"""
    else:
        titles = ", ".join(f"{item['label_en']} ({item['count']})" for item in payload["territories"])
        markdown = f"""---
tags: [knowledge-peaks, evidence-gated-demo]
generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
scope: {scope.name}
---

# Wenshan.skill · Knowledge Peaks

[[{basename}.html|Open the interactive map]]

This map shows only Agent-identified scene or industry peaks supported by at least **three independent canonical articles**: {titles}.

Candidate directions below the evidence gate do not appear as placeholders, “to be explored” labels, or invented terrain.
"""
    (atlas / f"{basename}.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"html": str(atlas / f"{basename}.html"), "language": args.language, "mountains": [(x["id"], x["count"]) for x in payload["territories"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
