# 变更记录

记录使用者能感知的变化。README 正文不在这里，它是自动生成的。

## 2026-11-07 · 单页

- 新增 `docs/index.html`：可按平台和状态筛、能搜关键词、中英可切，与 README 同源生成
- 上线 GitHub Pages：<https://liufuyou.github.io/EhViewer/>，README 顶部加了入口

## 2026-11-07 · 文档收敛

- `CONTRIBUTING.md` 只留提交规则，操作步骤移到 `scripts/render.py` 与 `data/versions.yaml` 的注释里
- 删除 `MAINTAINING.md`

## 2026-11-05 · 第二轮：正文补全与状态口径

- 补「下载安全」3 条、「常见问题」4 问
- 补录 HarmonyOS-EhViewer（`MinamiJogen/HarmonyOS-EhViewer`，v1.1.0 / 2026-10-08，ArkTS 原生）
- 彩 E（UjuiUjuMandan）移入「已停更」分组，最后版本 1.14.6（2025-12-17）
- 移除指向 `tree/References` 的「参考资料存档」链接（该分支已删除）
- 顶部徽章换成动态的「最近更新」，靠 shields.io 取数，不用人工维护
- 状态改为按日期自动分三档：≤60 天活跃、60–180 天更新较少、>180 天停更

## 2026-11-05 · 恢复维护

停滞 8.7 个月后的第一次全面核对。

**内容**

- 恢复中文版 README，正文自 `284d0d4` 取回并重排为表格。此前中文版被整段英文覆盖，语言切换链接指向已不存在的文件
- 补上 SXJ 版本的真实链接，填平 4 处 `insert_link_here` 占位符
- 标注两个已下架项目：`FooIbar/EhViewer`、`honjow/FEhViewer`（均 HTTP 451）
- 修正 SXJ 版本信息：原写"半停更，最新 1.9.4.4"，实际已发布 `2.0.2.7`（2026-11-02）
- 修复 `e-hentai.org` 的 Markdown 链接语法错误
- 替换两个失效徽章（`badges.toozhao.com`、`hits.seeyoufarm.com`），改用 shields.io
- 删除空文件 `E-Hentai Viewer`（2022-11-20 首次提交遗留）

**结构**

- 新增 `data/versions.yaml` 作为唯一数据源，中英双版 README 由脚本生成，避免两份正文再次漂移
- 新增每日链接巡检，出现坏链时自动开 issue
- 新增 `MAINTAINING.md`、`CONTRIBUTING.md`

**数据**

- EhPanda 补记 3.0.0 预发布（2026-08-20），稳定版仍为 v2.8.1
- UjuiUjuMandan 备注区分"未发版"与"未维护"：近一年没发版，但仓库在 2026-10-07 仍在提交

**自动同步**

- 每 6 小时比对清单内各仓库的最新 Release，有新版本时开 PR 等人过一眼，不直接改主干
- 上游发了安全公告、或发布说明里提到安全问题，表格里会标 ⚠️，悬疑的需人工确认

**许可**

- `LICENSE` 由 GPL-3.0 换为 **CC BY-NC-SA 4.0**，内容为官方法律文本原文，未作任何改动，以便 GitHub 正确识别
- 新增 `NOTICE.md`：版权归属、授权范围、"不覆盖第三方 App"的说明、历史版本 GPL-3.0 声明、商业授权方式
- 变更不追溯：`5c584b9` 及之前的提交仍为 GPL-3.0
