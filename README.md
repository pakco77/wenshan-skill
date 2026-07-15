# 文山.skill

**用山脉展示你的篇章。**

![文山.skill 中英双语效果](knowledge-peak-map/assets/demo-bilingual.png)

文山让本地 Agent 阅读你选定的 Markdown 或 Obsidian 篇章，清理脏数据、归并草稿与成稿，再把反复出现且证据充足的场景、行业、角色、实践或知识领域，生成一张可追溯的个人知识山脉地图。

它不按文件夹照抄分类，不用词频冒充洞察，也不依赖 embedding 猜测文章距离。每座山都必须回到原文证据。

> Wenshan turns a reviewed Markdown corpus into a bilingual, evidence-gated contour map. No embeddings, vector database, or API key.

## 一座山怎么读

| 地图元素 | 含义 |
|---|---|
| 山名 | Agent 从当前语料识别出的具体关键词，例如 `AI工具`、`产品经理`、`CNC` |
| 副标题 | 这批文章对该关键词形成的共同回答或判断 |
| `35篇` | 35 篇独立、有效、归并后的文章，也是这座山的海拔 |
| 证据点 | 一篇原始文章，可点击返回 Markdown 或 Obsidian 原文 |
| 等高线 | 文章证据形成的山体，而不是相似度距离 |

至少 3 篇独立文章才能形成一座山。没有证据，就没有山，也不会出现“待勘探”占位符。

## 它做了什么

1. **语义审阅**：排除提示词、模板、操作说明、第三方样例、空文件和无效数据。
2. **版本归并**：识别草稿、成稿和改写，每个版本族只保留一个 canonical 代表。
3. **山峰识别**：从有效文章中提炼具体领域关键词和证据支持的回答。
4. **确定性渲染**：以独立文章数作为海拔，生成中英双语等高线地图和传播截图。

## 安装 / Install

```bash
npx skills add pakco77/wenshan-skill \
  --skill knowledge-peak-map \
  --agent '*' \
  --global \
  --yes \
  --full-depth
```

同一份 Skill 可供 Codex、Claude Code、CodeWhale、CodeBuddy、WorkBuddy，以及其他支持 [Agent Skills](https://agentskills.io/) 的宿主使用。手动安装时，复制完整的 `knowledge-peak-map/` 文件夹。

## 使用 / Use

对 Agent 说：

> 使用 `$knowledge-peak-map` 分析这个 Markdown 文章集合，作者昵称是 Pakco，生成中文文山地图。

输入只有三个：作者昵称、用户选定的文章集合、界面语言。文山不会默认扫描整个 Vault。

输出包括逐篇判断卡、可审计的山峰数据，以及中文或英文 HTML 地图。所有派生文件都写入文章集合内的 `Cognitive Map/Agent Atlas/`，原始文章不会被修改。

如果已经准备好 `cards/` 与 `wenshan-terrain.json`，可直接渲染：

```bash
python3 knowledge-peak-map/scripts/render_territory_demo.py \
  --scope "/absolute/path/to/collection" \
  --nickname "Pakco" \
  --language zh \
  --output-name "文山"
```

## 可信边界

- 只读取用户明确选择的集合；渲染器不上传文章，也不另需 API key。语义审阅遵循所用 Agent 的隐私策略。
- 只有 `include: true`、`canonical: true` 的唯一原文路径才能增加海拔。
- 山名必须是具体领域关键词，不能是金句、抽象规律或用户预设愿望。
- 同一篇文章只增加一座主山的高度；跨山关系不重复计数。
- 中英文页面共享同一份证据数据，文章标题始终保留原文。

完整 Agent 指令与数据契约见 [`knowledge-peak-map/SKILL.md`](knowledge-peak-map/SKILL.md)。

## License

[MIT](LICENSE) © 2026 Pakco
