# 文山.skill · Wenshan.skill

![文山.skill 中英双语效果](knowledge-peak-map/assets/demo-bilingual.png)

把一组经过语义审阅与版本归并的 Markdown 篇章，生成证据门槛驱动的个人知识山脉地图。

主标题是 Agent 从当前语料识别出的场景、行业、角色、实践或知识领域关键词；副标题是这批文章对该关键词的共同回答。每座山至少需要 3 篇独立 canonical 文章，篇数就是海拔。没有证据，就没有山。

> Turn a reviewed Markdown corpus into a bilingual, evidence-gated contour map. Mountain titles are concrete corpus-derived domains; subtitles are evidence-backed answers. No embeddings.

## 安装 / Install

```bash
npx skills add pakco77/wenshan-skill \
  --skill knowledge-peak-map \
  --agent '*' \
  --global \
  --yes \
  --full-depth
```

同一份 Skill 可供 Codex、Claude Code、CodeWhale、CodeBuddy 与支持 Agent Skills 的宿主使用。手动安装时，复制完整的 `knowledge-peak-map/` 文件夹。

## 输入与输出 / Input & output

输入：作者昵称、用户选定的 Markdown/Obsidian 文章集合、界面语言。文山不会默认扫描整个 Vault。

输出写入文章集合内的 `Cognitive Map/Agent Atlas/`：

- `cards/*.json`：逐篇语义判断与版本决策
- `wenshan-terrain.json`：可审计山峰数据
- `文山.html` / `Wenshan.html`：中英双语地图

原始文章不会被修改。渲染器只使用 Python 标准库，不需要 embedding、向量库或 API key。

## 使用 / Use

对 Agent 说：

> 使用 `$knowledge-peak-map` 分析这个 Markdown 文章集合，作者昵称是 Pakco，生成中文文山地图。

已准备好 `cards/` 与 `wenshan-terrain.json` 后，也可以直接渲染：

```bash
python3 knowledge-peak-map/scripts/render_territory_demo.py \
  --scope "/absolute/path/to/collection" \
  --nickname "Pakco" \
  --language zh \
  --output-name "文山"
```

## 核心规则 / Core rules

- 山名必须是具体关键词，例如 `AI工具`、`产品经理`、`CNC`、`智能硬件`；不能是金句、结论或抽象规律。
- `include: true`、`canonical: true`、唯一源路径才增加海拔。
- 同一文章只属于一座主山；跨山关系不重复计数。
- 证据文章标题保留原文，中英页面共享同一份地形数据。

完整 Agent 指令见 [`knowledge-peak-map/SKILL.md`](knowledge-peak-map/SKILL.md)。
