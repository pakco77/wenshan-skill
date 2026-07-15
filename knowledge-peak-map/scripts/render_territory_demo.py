#!/usr/bin/env python3
"""Render the evidence-gated 文山.skill demo without embeddings.

Terrain position is a stable visual layout. A mountain exists only when an
Agent-identified scene or industry label has three or more independent canonical articles.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode


ANCHORS = {
    "ai-tools": (0.30, 0.50),
    "product-manager": (0.56, 0.72),
    "cnc": (0.25, 0.74),
    "smart-hardware": (0.76, 0.46),
    "ai-cognition": (0.70, 0.24),
    "parenting-life": (0.75, 0.76),
}
LABEL_KINDS = {"scene", "industry", "role", "practice", "knowledge_domain"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render evidence-gated Knowledge Peaks demo.")
    parser.add_argument("--scope", type=Path, required=True)
    parser.add_argument("--nickname", default="Pakco", help="Name shown in the map header.")
    parser.add_argument("--collection-url", default="", help="Article collection URL or local collection reference.")
    parser.add_argument("--language", choices=("zh", "en"), default="zh", help="Initial interface and export language.")
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
        if len(label) > 40 or any(mark in label for mark in "，。！？；：,.!?;:"):
            raise SystemExit(f"{territory.get('id', '<unknown>')}: label must be a compact scene or industry keyword, not a sentence")


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


def unit_jitter(identifier: str, index: int, total: int) -> tuple[float, float]:
    """Stable sunflower-like spread: visual only, never semantic geometry."""
    digest = hashlib.sha256(identifier.encode("utf-8")).digest()
    angle = (int.from_bytes(digest[:4], "big") / 2**32) * math.tau + index * 2.399963
    radius = (0.028 + 0.115 * math.sqrt((index + 0.45) / max(total, 1))) * (0.78 + digest[4] / 255 * 0.42)
    return radius * math.cos(angle), radius * math.sin(angle)


def build_payload(scope: Path, data: dict, nickname: str, collection_url: str, language: str) -> dict:
    validate_peak_labels(data)
    vault = vault_for(scope)
    candidates = [
        territory for territory in data.get("territories", [])
        if territory.get("status") == "evidenced" and len(territory.get("cards", [])) >= 3
    ]
    if not candidates:
        raise SystemExit("No territory has the minimum three independent canonical cards.")
    presets_apply = all(territory.get("id") in ANCHORS for territory in candidates)
    anchors = [ANCHORS[territory["id"]] for territory in candidates] if presets_apply else generic_anchors(len(candidates))
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
                "url": source_url(vault, scope, record),
            })
        territories.append({
            "id": ident,
            "label": first_text(territory, "label", "domain", "title", "rule"),
            "label_en": first_text(territory, "label_en", "domain_en", "title_en", "label", "domain", "title", "rule_en", "rule"),
            "answer": first_text(territory, "answer", "explanation", "llm_answer"),
            "answer_en": first_text(territory, "answer_en", "explanation_en", "llm_answer_en", "answer", "explanation", "llm_answer"),
            "count": len(points),
            "x": ax,
            "y": ay,
            "points": points,
        })
    if not territories:
        raise SystemExit("No territory has the minimum three independent canonical cards.")
    return {
        "territories": territories,
        "profile": {
            "nickname": nickname.strip() or ("匿名" if language == "zh" else "Anonymous"),
            "collection_url": collection_url.strip(),
            "language": language,
        },
    }


HTML = r'''<!doctype html>
<html lang="__HTML_LANG__"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__PAGE_TITLE__</title>
<style>
:root{--ink:#232721;--muted:#73766d;--paper:#f1efe8;--paper-2:#e9e6dc;--line:#c9c5b9;--night:#26302c}*{box-sizing:border-box}html{background:#dcd9d0}body{min-height:100vh;margin:0;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans CJK SC",sans-serif;background:radial-gradient(ellipse at 50% 10%,#f3f1ea 0,#dfddd5 46%,#d3d0c7 100%)}button,a{font:inherit}.workspace{width:min(1120px,calc(100% - 48px));min-height:100vh;margin:auto;display:grid;grid-template-columns:minmax(156px,1fr) 570px 76px;gap:24px;align-items:center}.context{align-self:center;border-top:1px solid var(--ink);padding-top:13px;color:var(--muted);font-size:11px;letter-spacing:.11em;text-transform:uppercase}.context strong{display:block;color:var(--ink);font-size:13px;font-weight:650;letter-spacing:.16em;margin-bottom:9px}.context p{margin:0;line-height:1.8;letter-spacing:.06em;text-transform:none}.context .rule{width:44px;height:1px;margin:22px 0;background:#98988d}.poster{position:relative;display:grid;grid-template-rows:auto 1fr auto;gap:12px;width:570px;padding:18px;background:var(--paper);border:1px solid #bcb9ad;box-shadow:0 28px 56px #4c4a421f,0 3px 9px #4c4a4218}.poster::after{content:"";position:absolute;inset:7px;pointer-events:none;border:1px solid #d6d2c7}.head,.foot{position:relative;z-index:1;display:flex;justify-content:space-between;align-items:flex-end;gap:14px}.wordmark{font-size:17px;font-weight:680;letter-spacing:.22em;line-height:1}.slogan{margin:6px 0 0;color:#666a61;font-size:11px;letter-spacing:.03em}.index{font-size:10px;color:#6d7169;letter-spacing:.10em;white-space:nowrap}.map-shell{position:relative;isolation:isolate;aspect-ratio:3/4;overflow:hidden;background:#e8e5dc;border:1px solid #cfcbc0}.map-shell::before{content:"";position:absolute;inset:0;z-index:1;pointer-events:none;background-image:linear-gradient(#a8a79e16 1px,transparent 1px),linear-gradient(90deg,#a8a79e16 1px,transparent 1px);background-size:42px 42px}canvas{position:relative;z-index:0;display:block;width:100%;height:100%;cursor:crosshair}.inspector{position:absolute;z-index:2;left:12px;right:12px;bottom:12px;display:grid;grid-template-columns:1fr auto;gap:10px;padding:13px 14px;background:#f4f2eaeF;border:1px solid #767970;box-shadow:0 12px 24px #292d2820;opacity:0;transform:translateY(14px);pointer-events:none;transition:opacity .18s ease,transform .22s ease}.inspector.show{opacity:1;transform:none;pointer-events:auto}.inspector h2{margin:0 0 5px;font-size:18px;letter-spacing:.08em;font-weight:650}.inspector p{margin:0;color:#4e534b;font-size:12px;line-height:1.6}.inspector .close{border:0;background:none;color:#5e625a;font-size:18px;line-height:1;cursor:pointer}.articles{grid-column:1/-1;display:flex;gap:7px;overflow:auto;padding-top:5px;border-top:1px solid #d0cdc2}.articles a{flex:0 0 auto;max-width:190px;overflow:hidden;color:#363a34;font-size:11px;line-height:1.35;text-decoration:none;white-space:nowrap;text-overflow:ellipsis}.articles a:hover{text-decoration:underline}.foot{font-size:11px;letter-spacing:.08em;color:#60645c}.meta{font-size:15px;font-weight:650;letter-spacing:.05em;color:var(--ink)}.author{font-size:11px;letter-spacing:.14em}.tools{display:flex;flex-direction:column;gap:8px;align-self:center}.tool{width:76px;min-height:60px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px;border:1px solid #a8a69b;background:#eeece4cc;color:#3e433c;text-decoration:none;font-size:10px;letter-spacing:.08em;cursor:pointer;transition:transform .16s ease,background .16s ease,box-shadow .16s ease}.tool:hover{transform:translateX(3px);background:#f8f6ef;box-shadow:5px 6px 0 #96958b33}.tool:focus-visible{outline:2px solid #45534c;outline-offset:3px}.tool .icon{font-size:16px;line-height:1}.desktop-note{display:none}@media(max-width:900px){.workspace{grid-template-columns:570px 76px;width:max-content;max-width:calc(100% - 28px)}.context{display:none}}@media(max-width:680px){body{background:var(--paper)}.workspace{width:100%;max-width:none;display:block;min-height:100vh}.poster{width:100%;min-height:100vh;padding:12px;border:0;box-shadow:none}.tools{display:none}.map-shell{margin-top:auto}.desktop-note{display:block;margin:0 0 8px;font-size:10px;color:var(--muted);letter-spacing:.04em}.inspector{left:9px;right:9px;bottom:9px}.wordmark{font-size:15px}.slogan{font-size:10px}.meta{font-size:13px}}
</style><style>
/* Header identity and the explicit setup step belong to the product shell, not the terrain. */
:root{--poster-w:570px}.poster{width:var(--poster-w)}@media(min-width:681px) and (max-height:860px){:root{--poster-w:min(570px,calc((100dvh - 74px)*.72))}.workspace{gap:clamp(12px,2vw,24px);padding:12px 0}}@media(min-width:681px) and (max-width:900px){.workspace{grid-template-columns:var(--poster-w) 76px;width:max-content;max-width:calc(100% - 28px)}}
.profile{display:grid;justify-items:end;gap:6px;text-align:right}.profile strong{font-size:12px;font-weight:650;letter-spacing:.08em}.profile .meta{font-size:14px}.foot{justify-content:space-between}.foot span:last-child{max-width:46%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right}.setup-sheet{position:fixed;z-index:20;inset:0;display:grid;place-items:center;padding:24px;background:#29312b55;opacity:0;visibility:hidden;transition:opacity .18s ease,visibility .18s}.setup-sheet.show{opacity:1;visibility:visible}.setup-card{position:relative;width:min(450px,100%);padding:27px;background:#f4f1e8;border:1px solid #777b72;box-shadow:0 28px 70px #262b261f}.setup-kicker{margin:0 0 12px;color:#6b6f67;font-size:10px;letter-spacing:.14em}.setup-card h2{margin:0 34px 22px 0;font-size:22px;line-height:1.35;font-weight:650;letter-spacing:.03em}.setup-card label{display:grid;gap:7px;margin:15px 0}.setup-card label span{font-size:11px;color:#4c524a;letter-spacing:.06em}.setup-card input{width:100%;border:0;border-bottom:1px solid #92968d;border-radius:0;padding:9px 0;background:transparent;color:#242a23;font-size:14px;outline:none}.setup-card input:focus{border-bottom:2px solid #46564c}.setup-help{margin:18px 0;color:#6a6e66;font-size:11px;line-height:1.65}.setup-submit{width:100%;padding:12px;border:1px solid #3f4b42;background:#3f4b42;color:#f7f4ec;font-size:12px;letter-spacing:.08em;cursor:pointer}.setup-submit:hover{background:#2d3930}.setup-close{position:absolute;top:14px;right:14px;width:30px;height:30px;border:1px solid #aaa99f;background:transparent;color:#4e534b;font-size:19px;cursor:pointer}
/* Map annotation card: deliberately denser and quieter than a generic modal. */
.inspector{left:14px;right:14px;bottom:14px;padding:16px 17px 13px;border-color:#4a5048;border-top:3px solid #4a5048;background:#f5f2e9f5;box-shadow:0 18px 30px #292d2830}.inspector h2{margin:5px 0 8px;font-size:20px}.inspector p{max-width:440px;font-size:13px;line-height:1.65}.inspector .evidence{display:block;color:#6a6e66;font-size:10px;letter-spacing:.13em}.inspector .close{width:28px;height:28px;border:1px solid #aaa99f;background:transparent}.articles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 16px;margin-top:6px;padding-top:9px}.articles a{max-width:none;padding:3px 0}.articles a::before{content:'↗';margin-right:5px;color:#777b72}@media(max-width:680px){.inspector{padding:13px}.articles{grid-template-columns:1fr}.inspector p{font-size:12px}}
/* Precision-instrument shell. Terrain stays light; controls carry the machine character. */
html,body{overflow-x:hidden}body{background:radial-gradient(ellipse at 50% 5%,#e8e6de 0,#d6d4cc 48%,#c7c6bf 100%)}.workspace{grid-template-columns:minmax(120px,1fr) var(--poster-w) 66px;gap:16px}.poster{grid-template-rows:auto 1fr;gap:10px;padding:14px;background:#efede6;border-color:#9d9f98;box-shadow:0 26px 62px #30363020,0 1px 0 #fff9}.poster::after{inset:6px;border-color:#cac9c1}.head{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;padding:4px 4px 11px;border-bottom:1px solid #b8bab2}.wordmark{font-size:20px;font-weight:650;letter-spacing:.08em}.slogan{margin-top:7px;font-size:10px;letter-spacing:.04em}.profile{gap:5px;padding-left:18px}.profile strong{font-size:12px}.profile .meta{font-size:13px;font-variant-numeric:tabular-nums}.map-shell{border:1px solid #969b94;box-shadow:inset 0 0 0 5px #e4e2da,inset 0 0 0 6px #c7c8c0;background:#e7e4dc}.tools{width:66px;gap:0;padding:5px;background:#202724;border:1px solid #5d6861;box-shadow:0 18px 36px #2a302b30;color:#dbe0dc}.control-head{display:grid;gap:5px;padding:7px 5px 10px;color:#919b95;font:600 7px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.12em;border-bottom:1px solid #4a544e}.control-head i{color:#8ba999;font-style:normal;font-size:7px}.tool{position:relative;width:100%;min-height:62px;display:grid;grid-template-columns:auto 1fr;grid-template-rows:auto auto;align-content:center;justify-items:start;gap:3px 6px;padding:9px 7px;border:0;border-bottom:1px solid #414a45;background:transparent;color:#d9dfdb;text-align:left;transition:background .16s ease,color .16s ease;text-decoration:none}.tool b{grid-row:1/3;color:#77827b;font:500 8px ui-monospace,SFMono-Regular,Menlo,monospace}.tool span{font:600 9px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.08em}.tool small{color:#929c96;font-size:8px;letter-spacing:.04em}.tool:hover{transform:none;background:#303a35;color:#fff;box-shadow:inset 2px 0 #9ab2a4}.tool:disabled{cursor:wait;background:#303a35;color:#a9c2b4;box-shadow:inset 2px 0 #a9c2b4}.tool:focus-visible{outline:1px solid #a9c2b4;outline-offset:-3px}.desktop-note{display:none!important}@media(min-width:681px) and (max-width:900px){.workspace{grid-template-columns:var(--poster-w) 66px;gap:12px}}@media(max-width:680px){body{background:#c9c8c1}.workspace{width:100%;max-width:none;min-height:100vh;display:grid;grid-template-columns:minmax(0,1fr) 58px;gap:7px;align-items:start;padding:7px}.poster{width:100%;min-height:0;padding:9px}.tools{display:flex;position:sticky;top:7px;width:58px;align-self:start}.control-head{padding-inline:3px}.tool{min-height:58px;padding-inline:5px;gap:2px 4px}.tool b{font-size:7px}.tool span{font-size:8px}.tool small{font-size:7px}.head{padding:3px 3px 9px}.wordmark{font-size:16px}.slogan{font-size:9px}.profile{padding-left:8px}.profile strong{font-size:10px}.profile .meta{font-size:11px}.map-shell{margin:0}.inspector{left:8px;right:8px;bottom:8px}}@media(max-width:410px){.head{grid-template-columns:1fr;gap:7px}.profile{display:flex;justify-content:space-between;padding-left:0;text-align:left}.profile strong,.profile .meta{font-size:10px}}
</style></head><body>
<main class="workspace"><aside class="context" id="context" aria-label="地图索引"><strong id="context-title">文山.skill</strong><p id="context-index"></p><div class="rule"></div><p id="context-guide"></p></aside>
<article class="poster" id="poster"><header class="head"><div><div class="wordmark" id="wordmark">文山.skill</div><p class="slogan" id="slogan"></p></div><div class="profile"><strong id="nickname"></strong><span class="meta" id="meta"></span></div></header><section class="map-shell"><canvas id="map" width="900" height="1200" aria-label="知识山峰地图"></canvas><aside class="inspector" id="inspector" aria-live="polite"></aside></section></article>
<nav class="tools" id="tools" aria-label="地图控制台"><div class="control-head"><span>CONTROL</span><i>ON</i></div><button class="tool" id="setup" type="button"><b>01</b><span>SET</span><small id="setup-label">设置</small></button><button class="tool" id="language" type="button"><b>02</b><span>LANG</span><small id="language-label">EN</small></button><a class="tool" href="https://github.com/pakco77/wenshan-skill/tree/main/knowledge-peak-map" target="_blank" rel="noopener"><b>03</b><span>SOURCE</span><small>GitHub</small></a><button class="tool" id="snapshot" type="button"><b>04</b><span>EXPORT</span><small id="snapshot-label">截图</small></button></nav>
<section class="setup-sheet" id="setup-sheet" aria-hidden="true"><form class="setup-card" id="setup-form"><button class="setup-close" id="setup-close" type="button" aria-label="关闭">×</button><p class="setup-kicker" id="setup-kicker">文山.skill / SETUP</p><h2 id="setup-title">先确定这张图属于谁，分析什么。</h2><label><span id="nickname-field-label">01 · 当前用户昵称</span><input id="nickname-input" name="nickname" required maxlength="40" placeholder="例如：Pakco"></label><label><span id="collection-field-label">02 · 文章集合 URL</span><input id="collection-input" name="collection" required maxlength="500" placeholder="粘贴 Obsidian 文件夹、本地集合或文章库 URL"></label><p class="setup-help" id="setup-help">保存后更新地图署名与材料引用。真正的文章读取、证据筛选与重新生成，由本地 Agent 在此集合上执行。</p><button class="setup-submit" id="setup-submit" type="submit">保存此地图设置</button></form></section></main>
<script>
const DATA=__DATA__,canvas=document.querySelector('#map'),ctx=canvas.getContext('2d'),W=canvas.width,H=canvas.height,inspector=document.querySelector('#inspector');
const PALETTE=[{rgb:[149,104,55],line:'#765b35',dot:'#5a4226'},{rgb:[57,101,98],line:'#3e6864',dot:'#30514e'},{rgb:[119,78,71],line:'#714b45',dot:'#51332e'},{rgb:[83,92,119],line:'#4e5875',dot:'#384057'},{rgb:[113,105,60],line:'#6b6438',dot:'#4f4929'},{rgb:[92,73,105],line:'#594765',dot:'#40334a'},{rgb:[70,104,116],line:'#456872',dot:'#334e56'},{rgb:[128,89,62],line:'#76523a',dot:'#563b2a'}],COLORS={};DATA.territories.forEach((territory,index)=>COLORS[territory.id]=PALETTE[index%PALETTE.length]);
const WORDS={zh:{brand:'文山.skill',slogan:'用山脉展示你的篇章',pageTitle:'文山.skill · 知识山峰',anonymous:'匿名',mapAria:'知识山峰地图',toolsAria:'地图控制台',contextIndex:'KNOWLEDGE PEAKS<br>EVIDENCE-GATED ATLAS<br>LOCAL AGENT',contextGuide:'选择一座山<br>阅读它的回答<br>回到原始文章',setupLabel:'设置',setupKicker:'文山.skill / 设置',setupTitle:'先确定这张图属于谁，分析什么。',nicknameField:'01 · 当前用户昵称',collectionField:'02 · 文章集合 URL',nicknamePlaceholder:'例如：Pakco',collectionPlaceholder:'粘贴 Obsidian 文件夹、本地集合或文章库 URL',setupHelp:'保存后更新地图署名与材料引用。真正的文章读取、证据筛选与重新生成，由本地 Agent 在此集合上执行。',setupSubmit:'保存此地图设置',stat:(articles,mountains)=>`${articles}文 ≈ ${mountains}山`,pieces:n=>`${n}篇`,articles:n=>`${n} 篇独立文章`,source:'查看文章',close:'关闭',shot:'截图',exporting:'生成中',saved:'已导出'},en:{brand:'Wenshan.skill',slogan:'Map your writing as mountains.',pageTitle:'Wenshan.skill · Knowledge Peaks',anonymous:'Anonymous',mapAria:'Knowledge mountain map',toolsAria:'Map controls',contextIndex:'KNOWLEDGE PEAKS<br>EVIDENCE-GATED ATLAS<br>LOCAL AGENT',contextGuide:'Choose a mountain<br>Read its answer<br>Return to the source',setupLabel:'Setup',setupKicker:'Wenshan.skill / SETUP',setupTitle:'Define whose map this is and which writing to analyze.',nicknameField:'01 · Author nickname',collectionField:'02 · Article collection URL',nicknamePlaceholder:'For example: Pakco',collectionPlaceholder:'Paste an Obsidian folder, local collection, or article-library URL',setupHelp:'Saving updates attribution and the collection reference. Your local Agent performs article reading, evidence review, and regeneration on that collection.',setupSubmit:'Save map settings',stat:(articles,mountains)=>`${articles} pieces ≈ ${mountains} peaks`,pieces:n=>`${n} pieces`,articles:n=>`${n} independent pieces`,source:'Open article',close:'Close',shot:'Capture',exporting:'Rendering',saved:'Exported'}};
let language=DATA.profile?.language==='en'?'en':'zh',hover=null,active=null;const q=()=>WORDS[language],copy=h=>language==='en'?{label:h.label_en||h.label,answer:h.answer_en||h.answer}:{label:h.label,answer:h.answer},esc=s=>String(s).replace(/[&<>'"]/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[x]));
const settingsKey='wenshan.skill.setup.v1';let settings={...(DATA.profile||{})};try{settings={...settings,...JSON.parse(localStorage.getItem(settingsKey)||'{}')}}catch(_){/* ponytail: file previews may not expose persistent storage. */}
const all=DATA.territories.flatMap(t=>[{x:t.x,y:t.y},...t.points]),loX=Math.min(...all.map(p=>p.x)),hiX=Math.max(...all.map(p=>p.x)),loY=Math.min(...all.map(p=>p.y)),hiY=Math.max(...all.map(p=>p.y));
const fit=(v,a,b,start,span)=>start+(v-a)/Math.max(.0001,b-a)*span;
const hills=DATA.territories.map(t=>({...t,x:fit(t.x,loX,hiX,.24,.52),y:fit(t.y,loY,hiY,.18,.58),points:t.points.map(p=>({...p,x:fit(p.x,loX,hiX,.24,.52),y:fit(p.y,loY,hiY,.18,.58)}))}));
function field(points){const nx=110,ny=150,g=new Float32Array(nx*ny),blur=5.6+Math.min(3,Math.sqrt(points.length)/2),r=Math.ceil(blur*3);for(const p of points){const px=p.x*(nx-1),py=p.y*(ny-1);for(let y=Math.max(0,Math.floor(py-r));y<=Math.min(ny-1,Math.ceil(py+r));y++)for(let x=Math.max(0,Math.floor(px-r));x<=Math.min(nx-1,Math.ceil(px+r));x++){const d=(x-px)**2+(y-py)**2;if(d<r*r)g[y*nx+x]+=Math.exp(-d/(2*blur*blur))}}return{g,nx,ny,max:Math.max(...g)}}
const CASES={1:[[3,0]],2:[[0,1]],3:[[3,1]],4:[[1,2]],5:[[0,3],[1,2]],6:[[0,2]],7:[[3,2]],8:[[2,3]],9:[[0,2]],10:[[0,1],[2,3]],11:[[1,2]],12:[[1,3]],13:[[0,1]],14:[[3,0]]};
function edgePoint(edge,x,y,a,b,d,z,level){const between=(u,v)=>u===v?.5:Math.max(0,Math.min(1,(level-u)/(v-u)));if(edge===0)return[x+between(a,b),y];if(edge===1)return[x+1,y+between(b,d)];if(edge===2)return[x+between(z,d),y+1];return[x,y+between(a,z)]}
function paintTerrain(h){const {g,nx,ny,max}=field(h.points),off=document.createElement('canvas'),o=off.getContext('2d'),c=COLORS[h.id];off.width=nx;off.height=ny;const im=o.createImageData(nx,ny);for(let i=0;i<g.length;i++){const value=Math.pow(g[i]/max,.66),p=i*4;if(value>.03){im.data[p]=c.rgb[0];im.data[p+1]=c.rgb[1];im.data[p+2]=c.rgb[2];im.data[p+3]=Math.round(14+value*102)}}o.putImageData(im,0,0);ctx.save();ctx.globalAlpha=.18;ctx.filter='blur(8px)';ctx.drawImage(off,10,14,W,H);ctx.restore();ctx.save();ctx.globalAlpha=.68;ctx.drawImage(off,0,0,W,H);ctx.restore();const rings=Math.min(10,Math.max(4,Math.round(Math.sqrt(h.count)+3)));ctx.save();ctx.strokeStyle=c.line;ctx.lineCap='round';for(let ring=1;ring<=rings;ring++){const level=max*(.12+ring/rings*.72);ctx.globalAlpha=.24+ring/rings*.34;ctx.lineWidth=1+ring*.1;ctx.beginPath();for(let y=0;y<ny-1;y++)for(let x=0;x<nx-1;x++){const a=g[y*nx+x],b=g[y*nx+x+1],d=g[(y+1)*nx+x+1],z=g[(y+1)*nx+x],mask=(a>=level?1:0)|(b>=level?2:0)|(d>=level?4:0)|(z>=level?8:0);for(const pair of CASES[mask]||[]){const u=edgePoint(pair[0],x,y,a,b,d,z,level),v=edgePoint(pair[1],x,y,a,b,d,z,level);ctx.moveTo(u[0]*W/(nx-1),u[1]*H/(ny-1));ctx.lineTo(v[0]*W/(nx-1),v[1]*H/(ny-1))}}ctx.stroke()}ctx.restore()}
function wrap(text,x,y,width,line){let row='';for(const ch of [...text]){const next=row+ch;if(ctx.measureText(next).width>width&&row){ctx.fillText(row,x,y);y+=line;row=ch}else row=next}if(row)ctx.fillText(row,x,y)}
function titleFont(text,maxWidth){let size=37;while(size>22){ctx.font=`650 ${size}px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif`;if(ctx.measureText(text).width<=maxWidth)break;size-=1}return size}
function label(h){const x=h.x*W,y=h.y*H,c=COLORS[h.id],words=q(),text=copy(h);ctx.save();ctx.textAlign='center';ctx.fillStyle=c.line;ctx.font='650 22px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';ctx.fillText(words.pieces(h.count),x,y-31);ctx.fillStyle=c.dot;ctx.beginPath();ctx.moveTo(x,y-22);ctx.lineTo(x-12,y+8);ctx.lineTo(x+12,y+8);ctx.closePath();ctx.fill();ctx.fillStyle='#242722';const size=titleFont(text.label,330);ctx.font=`650 ${size}px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif`;ctx.fillText(text.label,x,y+52);ctx.fillStyle='#575a53';ctx.font='12px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';wrap(text.answer,x,y+81,310,19);ctx.restore()}
function draw(){ctx.fillStyle='#e8e5dc';ctx.fillRect(0,0,W,H);ctx.save();ctx.strokeStyle='#73776d';ctx.globalAlpha=.035;for(let i=0;i<12;i++){ctx.beginPath();ctx.arc((i*193)%W,(i*257)%H,84+i*24,0,Math.PI*2);ctx.stroke()}ctx.restore();for(const hill of hills)paintTerrain(hill);for(const hill of hills){ctx.save();for(const p of hill.points){ctx.beginPath();ctx.arc(p.x*W,p.y*H,3.7,0,Math.PI*2);ctx.fillStyle=COLORS[hill.id].dot;ctx.globalAlpha=.92;ctx.fill();ctx.strokeStyle='#e8e5dc';ctx.globalAlpha=.9;ctx.lineWidth=1.2;ctx.stroke()}ctx.restore();label(hill)}}
function nearest(event){const box=canvas.getBoundingClientRect(),x=(event.clientX-box.left)*W/box.width,y=(event.clientY-box.top)*H/box.height;let best=null,d=Infinity;for(const hill of hills)for(const p of hill.points){const value=(p.x*W-x)**2+(p.y*H-y)**2;if(value<d){best={hill,p};d=value}}return d<18**2?best:null}
function detail(hill){active=hill;const words=q(),text=copy(hill),links=hill.points.slice(0,6).map(p=>`<a href="${esc(p.url)}">${esc(p.title)}</a>`).join('');inspector.innerHTML=`<div><small class="evidence">${words.articles(hill.count)}</small><h2>${esc(text.label)}</h2><p>${esc(text.answer)}</p></div><button class="close" type="button" aria-label="${words.close}">×</button><div class="articles">${links}</div>`;inspector.querySelector('.close').onclick=()=>{active=null;inspector.classList.remove('show')};inspector.classList.add('show')}
function chrome(){const words=q(),articleCount=hills.reduce((n,h)=>n+h.count,0);document.documentElement.lang=language==='zh'?'zh-CN':'en';document.title=words.pageTitle;document.querySelector('#wordmark').textContent=words.brand;document.querySelector('#slogan').textContent=words.slogan;document.querySelector('#meta').textContent=words.stat(articleCount,hills.length);document.querySelector('#nickname').textContent=settings.nickname||words.anonymous;document.querySelector('#language-label').textContent=language==='zh'?'EN':'中';document.querySelector('#snapshot-label').textContent=words.shot;document.querySelector('#setup-label').textContent=words.setupLabel;document.querySelector('#context-title').textContent=words.brand;document.querySelector('#context-index').innerHTML=words.contextIndex;document.querySelector('#context-guide').innerHTML=words.contextGuide;document.querySelector('#map').setAttribute('aria-label',words.mapAria);document.querySelector('#tools').setAttribute('aria-label',words.toolsAria);document.querySelector('#setup-close').setAttribute('aria-label',words.close);document.querySelector('#setup-kicker').textContent=words.setupKicker;document.querySelector('#setup-title').textContent=words.setupTitle;document.querySelector('#nickname-field-label').textContent=words.nicknameField;document.querySelector('#collection-field-label').textContent=words.collectionField;document.querySelector('#nickname-input').placeholder=words.nicknamePlaceholder;document.querySelector('#collection-input').placeholder=words.collectionPlaceholder;document.querySelector('#setup-help').textContent=words.setupHelp;document.querySelector('#setup-submit').textContent=words.setupSubmit}
function openSetup(){document.querySelector('#nickname-input').value=settings.nickname||'';document.querySelector('#collection-input').value=settings.collection_url||'';document.querySelector('#setup-sheet').classList.add('show');document.querySelector('#setup-sheet').setAttribute('aria-hidden','false');document.querySelector('#nickname-input').focus()}function closeSetup(){document.querySelector('#setup-sheet').classList.remove('show');document.querySelector('#setup-sheet').setAttribute('aria-hidden','true')}
document.querySelector('#setup').onclick=openSetup;document.querySelector('#setup-close').onclick=closeSetup;document.querySelector('#setup-sheet').onclick=e=>{if(e.target===e.currentTarget)closeSetup()};document.querySelector('#setup-form').onsubmit=e=>{e.preventDefault();const fields=e.currentTarget.elements;settings.nickname=fields.namedItem('nickname').value.trim();settings.collection_url=fields.namedItem('collection').value.trim();try{localStorage.setItem(settingsKey,JSON.stringify(settings))}catch(_){/* ponytail: preview remains usable without persistence. */}chrome();closeSetup()};
document.querySelector('#language').onclick=()=>{language=language==='zh'?'en':'zh';chrome();draw();if(active)detail(active)};canvas.onmousemove=e=>{hover=nearest(e);canvas.style.cursor=hover?'pointer':'crosshair'};canvas.onmouseleave=()=>{hover=null;canvas.style.cursor='crosshair'};canvas.onclick=e=>{if(hover){window.location.href=hover.p.url;return}const box=canvas.getBoundingClientRect(),x=(e.clientX-box.left)*W/box.width,y=(e.clientY-box.top)*H/box.height;const hill=hills.map(h=>[h,(h.x*W-x)**2+(h.y*H-y)**2]).sort((a,b)=>a[1]-b[1])[0];if(hill&&hill[1]<180**2)detail(hill[0]);else{active=null;inspector.classList.remove('show')}};
document.querySelector('#snapshot').onclick=()=>{const button=document.querySelector('#snapshot'),label=document.querySelector('#snapshot-label'),share=document.createElement('canvas'),s=share.getContext('2d'),articleCount=hills.reduce((n,h)=>n+h.count,0),stat=q().stat(articleCount,hills.length),nickname=settings.nickname||q().anonymous;button.disabled=true;label.textContent=q().exporting;share.width=1080;share.height=1440;s.fillStyle='#efede6';s.fillRect(0,0,1080,1440);s.strokeStyle='#8e948f';s.lineWidth=2;s.strokeRect(24,24,1032,1392);s.strokeStyle='#c2c4bd';s.lineWidth=1;s.strokeRect(32,32,1016,1376);s.fillStyle='#202521';s.textAlign='left';s.font='650 36px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';s.fillText(q().brand,60,74);s.fillStyle='#61675f';s.font='18px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';s.fillText(q().slogan,60,111);s.textAlign='right';s.fillStyle='#252b26';s.font='650 22px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif';s.fillText(nickname,1020,70);s.font='650 27px ui-monospace,SFMono-Regular,Menlo,monospace';s.fillText(stat,1020,109);s.strokeStyle='#a8aca6';s.beginPath();s.moveTo(60,136);s.lineTo(1020,136);s.stroke();const mapX=86,mapY=164,mapW=908,mapH=1211;s.fillStyle='#e7e4dc';s.fillRect(mapX-8,mapY-8,mapW+16,mapH+16);s.strokeStyle='#929991';s.lineWidth=2;s.strokeRect(mapX-8,mapY-8,mapW+16,mapH+16);s.strokeStyle='#c4c7c0';s.lineWidth=1;s.strokeRect(mapX-2,mapY-2,mapW+4,mapH+4);s.drawImage(canvas,mapX,mapY,mapW,mapH);s.strokeStyle='#6f7871';s.lineWidth=1;for(let i=0;i<=12;i++){const y=mapY+i*mapH/12,len=i%3===0?10:5;s.beginPath();s.moveTo(mapX-8,y);s.lineTo(mapX-8+len,y);s.moveTo(mapX+mapW+8,y);s.lineTo(mapX+mapW+8-len,y);s.stroke()}share.toBlob(blob=>{if(!blob){button.disabled=false;label.textContent=q().shot;return}const link=document.createElement('a'),safe=nickname.replace(/[^\p{L}\p{N}._-]+/gu,'-');link.href=URL.createObjectURL(blob);link.download=language==='zh'?`文山-${safe}-${articleCount}文.png`:`Wenshan-${safe}-${articleCount}-pieces.png`;link.click();label.textContent=q().saved;setTimeout(()=>{URL.revokeObjectURL(link.href);button.disabled=false;label.textContent=q().shot},1400)},'image/png')};chrome();draw();
</script></body></html>'''


def main() -> None:
    args = parse_args()
    scope = args.scope.expanduser().resolve()
    atlas = scope / "Cognitive Map" / "Agent Atlas"
    preferred = atlas / "wenshan-terrain.json"
    legacy = atlas / "knowledge-peaks-demo-data.json"
    data_path = args.terrain_data.expanduser().resolve() if args.terrain_data else (preferred if preferred.exists() else legacy)
    data = read_json(data_path)
    payload = build_payload(scope, data, args.nickname, args.collection_url or str(scope), args.language)
    basename = args.output_name or ("知识山峰-Demo" if args.language == "zh" else "Wenshan-Demo")
    html_language = "zh-CN" if args.language == "zh" else "en"
    page_title = "文山.skill · 知识山峰" if args.language == "zh" else "Wenshan.skill · Knowledge Peaks"
    html = (
        HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        .replace("__HTML_LANG__", html_language)
        .replace("__PAGE_TITLE__", page_title)
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
