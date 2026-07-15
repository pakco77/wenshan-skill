# Obsidian 插件方案

## 结论

可以做成 Obsidian 插件，但插件应该是 **文山.skill 的桌面入口与查看器**，不是第二套语义引擎。

## MVP 职责

插件只做五件事：

1. 选择要分析的 Vault 文件夹或文章清单。
2. 输入作者昵称并选择中文或 English。
3. 调用本地 Skill/Agent 生成或刷新地图。
4. 在 Obsidian View 中打开生成的 HTML 地图。
5. 点击证据文章时，用 Obsidian URI 打开对应笔记。

## 不放进插件的能力

- 不在插件内实现 LLM 供应商适配。
- 不把 API Key 存进地图 HTML。
- 不复制版本归并、证据门槛、主题判断和等高线算法。
- 不默认扫描整个 Vault。
- 不在移动端运行本地 Agent 或 Python。

这些能力保留在 Skill/CLI 中，CodeWhale、Codex 与 Obsidian 才能共享同一套语义真源。

## 命令与设置

建议命令：

- `文山：配置文章集合`
- `文山：生成或刷新地图`
- `文山：打开地图`
- `文山：导出传播图`

建议设置：

- `collectionPath`
- `nickname`
- `language: zh | en`
- `skillCommand`
- `outputPath`

## 数据契约

第一版沿用现有目录，避免迁移成本：

```text
Cognitive Map/Agent Atlas/
├── cards/*.json
├── wenshan-terrain.json
├── 文山.html
└── Wenshan.html
```

`knowledge-peaks-demo-data.json` 只作为旧版兼容输入保留一个发布周期。

插件只读取输出与触发命令，不直接改 `cards/*.json`。

## 迭代顺序

1. 桌面 MVP：设置页、三条命令、地图 View、Obsidian URI 回链。
2. 任务状态：显示收集、判断、归并、渲染的真实进度与错误。
3. 只读移动端：查看已经生成的静态地图。
4. 数据契约稳定后，再考虑把 Python 渲染器移植为 TypeScript。

先让 Skill 的输入、输出和失败状态稳定，再开发插件。这样插件工程是薄的，语义能力仍可独立演进。
