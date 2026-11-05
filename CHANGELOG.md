# 变更记录

面向维护者，记录"哪天核对过、改了什么"。README 的正文不在这里，因为它是自动生成的。

## 2026-11-05 · 恢复维护

停滞 8.7 个月后的第一次全面核对。

**内容修复**

- 恢复中文版 README。中文正文在 `5c584b9`（2026-02-13）那次提交里被英文内容整段覆盖，本次从 `284d0d4` 取回并重写为结构化表格
- 补上 SXJ 版本的真实链接。原 README 里 4 处 `insert_link_here` 占位符由此填平
- 核实并标注两个已下架项目：`FooIbar/EhViewer`、`honjow/FEhViewer` 均为 HTTP 451（DMCA 下架）
- 修正 SXJ 版本信息：原英文版写"半停更，最新 1.9.4.4"，实际已发布 `2.0.2.7`（2026-11-02）
- 标注 `UjuiUjuMandan/EhViewer` 已超过半年未发版（最新 1.14.6，2025-12-17）
- 修复 `e-hentai.org` 的错误 Markdown 链接语法
- 替换两个失效徽章（`badges.toozhao.com` 返回 404、`hits.seeyoufarm.com` 无法访问），改用 shields.io 静态徽章

**结构改动**

- 新增 `data/versions.yaml` 作为唯一数据源，中英文 README 由脚本生成，避免两份正文再次漂移
- 新增 `scripts/render.py`、`scripts/check_links.py`
- 新增每日链接巡检 workflow（含自动开 issue）
- 新增 `MAINTAINING.md`、`CONTRIBUTING.md`
- 删除空文件 `E-Hentai Viewer`（2022-11-20 首次提交遗留，2 字节）

**待决定**

- 许可证是否从 GPL-3.0 改为 CC0-1.0 / MIT（详见 `MAINTAINING.md`）
- `References` 分支去留
