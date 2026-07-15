# 文章进入 Markdown / Obsidian 的前置链路

## 结论

文山.skill 不应该自己再造网页抓取器、PDF 转换器或 Obsidian 写入器。把导入作为独立前置链路，复用现有转换 Skill；文山只接收边界明确的 Markdown 文章集合。

当前建议组合：

- `$huashu-md-html`：把网页、微信公众号、PDF、DOCX、PPTX、表格、图片或其他文件转为 Markdown。
- `$obsidian`：把转换后的 Markdown 创建或整理到用户指定的 Vault 文件夹。
- `$knowledge-peak-map`：只对用户确认的文章集合做语义审阅、版本归并、场景/行业山峰识别和地图生成。

## 输入路由

| 原始材料 | 转换能力 | 结果 |
|---|---|---|
| 已经是 `.md` 的文件夹 | 不转换 | 直接作为候选集合 |
| 普通文章 URL / HTML | `huashu-md-html/scripts/html_to_md.py` | 清理后的 Markdown |
| 微信公众号文章 URL | `huashu-md-html/scripts/wechat_to_md.py` | 保留正文结构的 Markdown |
| PDF / DOCX / PPTX / XLSX / 图片等 | `huashu-md-html/scripts/any_to_md.py` | 可审阅 Markdown |
| 需要进入 Obsidian | `$obsidian` | 写入用户明确选择的文件夹 |

不要把 MD → HTML 的排版能力混入导入阶段。导入目标是忠实、可追溯的 Markdown，不是漂亮页面。

## 最小元数据

导入时保留原始标题和正文，并添加最少量 frontmatter：

```yaml
---
title: 原始文章标题
source_url: https://example.com/article
source_type: article
imported_at: 2026-07-15T12:00:00+08:00
language: zh
---
```

本地文件可用 `source_path` 代替 `source_url`。`source_type` 可取 `article`、`wechat`、`pdf`、`docx`、`pptx`、`image` 或 `markdown`。

## 集合边界

在导入目录旁生成 `wenshan-collection.json`：

```json
{
  "version": 1,
  "nickname": "作者昵称",
  "collection": "绝对路径或 Obsidian 文件夹",
  "documents": [
    {
      "path": "相对路径/文章.md",
      "source_url": "https://example.com/article",
      "sha256": "内容哈希",
      "authorship": "self"
    }
  ]
}
```

这个清单负责回答“这次到底分析哪些文章”。文山默认只接受 `authorship: self`；第三方参考资料必须显式标记为 `reference`，并在语义审阅阶段默认排除，不得悄悄抬高个人山峰。

## 去重与保真

- 优先用规范化 `source_url` 去重；没有 URL 时用正文内容哈希。
- 同一文章的草稿、成稿和改写先全部保留，交给版本归并阶段选择 canonical。
- 导入阶段不改写观点，不总结正文，不生成“更好”的标题。
- 图片可以保留本地相对链接，但不能让图片缺失阻塞纯文本分析。
- 抓取失败、正文为空或仅有导航广告时，记录错误并跳过，不制造占位文章。

## 是否再做一个 Skill

第一版不需要第三个转换 Skill。现有 `$huashu-md-html` 加 `$obsidian` 已覆盖转换和落库。

只有当用户需要“一条命令批量接收 URL、生成集合清单并写入 Vault”时，才值得增加一个很薄的 `markdown-corpus-import` 编排 Skill。它只负责路由、去重、元数据和清单，不复制任何解析器。
