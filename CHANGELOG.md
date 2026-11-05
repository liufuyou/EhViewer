# 变更记录

面向维护者，记录"哪天核对过、改了什么"。README 的正文不在这里，因为它是自动生成的。

## 2026-11-05 · 第二轮：正文补全与状态口径

- 去掉 README 里面向维护者的提示（「本页由清单自动生成」、页脚、单独成节的「提问前」），改由 `render-check` 工作流兜底
- 补「下载安全」3 条与「常见问题」4 问；文案放在 `data/versions.yaml` 的 `safety` / `faq` 里
- 补录 HarmonyOS-EhViewer（`MinamiJogen/HarmonyOS-EhViewer`，v1.1.0 / 2026-10-08，ArkTS 原生）
- 彩 E（UjuiUjuMandan）移入新增的「已停更」分组，最后版本 1.14.6（2025-12-17）
- 移除指向 `tree/References` 的「参考资料存档」链接（该分支已删除）
- 顶部徽章换成 `github/last-commit` 动态徽章（显示「最近更新 · 今天 / 3 天前」），由 shields.io 实时取数，不用人工维护
- 新增 `scripts/expire.py` 与 `maintenance.yml`：带到期日的字段（目前是 README 顶部的「最后核对」行）到期后由云端定时任务自动摘掉并开 PR
- 状态改为三档自动判定：≤60 天活跃、60–180 天更新较少、>180 天停更；`status` 只允许手写 `taken_down` / `archived`
- `render.py` 新增 `--check`，并加 `render-check` 工作流校验生成物一致性

## 2026-11-05 · 恢复维护

停滞 8.7 个月后的第一次全面核对。

**内容**

- 恢复中文版 README，正文自 `284d0d4` 取回并重排为表格。此前中文版被整段英文覆盖，语言切换链接指向已不存在的文件
- 补上 SXJ 版本的真实链接，填平 4 处 `insert_link_here` 占位符
- 标注两个已下架项目：`FooIbar/EhViewer`、`honjow/FEhViewer`（均 HTTP 451）
- 修正 SXJ 版本信息：原写"半停更，最新 1.9.4.4"，实际已发布 `2.0.2.7`（2026-11-02）
- 修复 `e-hentai.org` 的 Markdown 链接语法错误
- 替换两个失效徽章（`badges.toozhao.com` 返回 404、`hits.seeyoufarm.com` 无法访问），改用 shields.io 静态徽章
- 删除空文件 `E-Hentai Viewer`（2022-11-20 首次提交遗留）

**结构**

- 新增 `data/versions.yaml` 作为唯一数据源，中英双版 README 由脚本生成，避免两份正文再次漂移
- 新增 `scripts/render.py`、`scripts/check_links.py`
- 新增每日链接巡检 workflow，出现坏链时自动开 issue
- 新增 `MAINTAINING.md`、`CONTRIBUTING.md`

**数据与校验**

- EhPanda 补记 3.0.0 预发布（2026-08-20），稳定版仍为 v2.8.1
- UjuiUjuMandan 备注区分"未发版"与"未维护"：近一年没发版，但仓库在 2026-10-07 仍在提交
- `render.py` 支持可选的 `prerelease` 字段，在版本号下方渲染为一行小字，不影响滞后判定
- `render.py` 新增校验：必填字段、`id` 唯一性、`released` 不得晚于 `last_checked`、`prerelease` 字段完整性
- `check_links.py` 仅对连接失败重试一次，404/451 不重试，减少网络抖动造成的误报

**许可**

- `LICENSE` 由 GPL-3.0 换为 **CC BY-NC-SA 4.0**，内容为官方法律文本原文，未作任何改动，以便 GitHub 正确识别
- 新增 `NOTICE.md`：版权归属、授权范围、"不覆盖第三方 App"的说明、历史版本 GPL-3.0 声明、商业授权方式
- 变更不追溯：`5c584b9` 及之前的提交仍为 GPL-3.0

**自动同步**

- 新增 `scripts/sync_releases.py`：比对清单内各仓库的最新 Release，检测到新版本时更新 `version` / `released` / `latest_summary`
  - 按行改写 `data/versions.yaml` 而非整体反序列化回写，保留原有注释与字段顺序
  - 默认 dry-run，`--apply` 才落盘；支持 `--only` 单条目调试与 `--report` 输出 Markdown 报告
- 安全检测分两级：上游 GHSA 公告命中为 `confirmed`，发布说明关键词命中为 `suspected`（有误报，需人工确认）
- 新增 `sync-releases` workflow：每 6 小时轮询，有变化时开 PR 而不是直接推 `main`
- README 新增「最近更新」与「安全提示」两个区块，带安全标记的版本在表格中显示 ⚠️
- 新增可选字段 `latest_summary` / `security_level` / `security_note` / `security_note_en` / `security_checked`，不写则输出与之前完全一致

**已知限制**

GitHub 的 `schedule` 在高峰期会延迟十几分钟甚至丢弃某次触发，且没有官方 SLA，所以同步的定位是"准实时"。真正的秒级只能上 webhook + 公网接收端，属于新增基础设施，暂不做。

**待决定**

- `References` 分支去留：目前是 3 个文件的旧状态副本
- 是否做 GitHub Pages 单页导航
