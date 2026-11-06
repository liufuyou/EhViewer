# 维护手册

这份文档只解决一个问题：**隔了很久回来，怎么在 10 分钟内把仓库更新完。**

---

## 30 秒版

```bash
# 1. 改清单（只改这一个文件）
vim data/versions.yaml

# 2. 重新生成两份 README
python scripts/render.py

# 3. 检查链接
python scripts/check_links.py

# 4. 确认生成物与清单一致（CI 也会跑这一步）
python scripts/render.py --check

# 5. 提交
git add -A && git commit -m "chore: 核对至 2026-11"
```

就这五步。不要直接编辑 `README.md` 或 `README.en.md`——它们下次运行脚本就会被覆盖，
`render-check` 工作流也会因为「生成物与清单不一致」直接失败。

---

## 仓库结构

```
data/versions.yaml          唯一数据源。所有版本信息都在这里
scripts/render.py           从 yaml 生成两份 README
scripts/check_links.py      检查所有链接是否还活着
scripts/expire.py           按日期清理到期字段
.github/workflows/link-check.yml   每天自动巡检
.github/workflows/maintenance.yml  每天处理到期字段（云端跑，不靠本地）
.github/workflows/render-check.yml 校验 README 与清单一致
README.md                   中文版（自动生成）
README.en.md                英文版（自动生成）
```

**一个原则**：人和代码只改 `data/versions.yaml`，README 永远由脚本产出。

---

## 每月例行（约 10 分钟）

1. 打开 `data/versions.yaml`，把 `meta.last_checked` 改成今天
2. 跑一遍 `python scripts/check_links.py`
3. 对"活跃"的版本，去 release 页面看有没有新版本，顺手改 `version` 和 `released`
4. 跑 `python scripts/render.py`
5. 提交，提交信息写清楚这次核对到什么日期

CI 每天会自动巡检，真有链接挂了会开 issue 通知你——所以第 2 步失败也不会拖太久。

---

## 发现链接挂了怎么办

| 情况 | 怎么做 |
| --- | --- |
| 只是改了仓库名 | 把 `url` 改成新地址 |
| 转到新项目继续维护 | `url` 指向新项目，`zh_note` 写明"已迁移" |
| 彻底没了 / 被 DMCA 下架 | `status: taken_down`，并写清核实时间 |
| 作者停更但仓库还在 | `status: archived`，保留版本号供查证 |

把 `status` 改成 `taken_down` 后，脚本就不再检查这条链接了——避免每天重复报警。

---

## 状态字段的含义

**活跃程度不用手写**，脚本按 `released` 与 `meta.last_checked` 的差值自动分三档：

| 距上次发版 | 显示 | 放哪个组（按平台，不按活跃度） |
| --- | --- | --- |
| ≤ `active_within_days`（默认 60 天） | 活跃 | 推荐版本 / 全平台/桌面端 / iOS / 鸿蒙 |
| 60 ~ `dormant_after_days`（默认 180 天） | 更新较少 | 同上，按平台归组 |
| > `dormant_after_days` | 停更 | 已停更 |

只有下面两种状态必须手写，因为无法从日期推断：

| status | 什么时候用 | 页面上的显示 |
| --- | --- | --- |
| `taken_down` | 仓库打不开了（DMCA / 删除 / 私有化） | 已下架，标题加删除线，链接置为 — |
| `archived` | 官方或社区已归档，仅供查证 | 已归档 |

> `status: active` / `low` / `dormant` 会被校验直接拒绝——状态是算出来的，写死了就会和日期打架。
> 分组（`group`）仍然是手写的，所以条目停更之后要记得把它移到 `dormant` 组；放错时脚本会打印提示（不报错）。
> 组上加 `collapsed: true` 会整组收进 `<details>`，标题和说明一起折叠；不写就是展开。

---

## 预发布版本（可选字段）

如果某个项目有 beta / rc 之类的预发布，用 `prerelease` 单独记录，**不要**把它写进 `version`：

```yaml
  - id: ehpanda
    version: v2.8.1          # 稳定版，这条进"最新版本"列
    released: 2026-07-20
    prerelease:              # 可选；写了会在版本号下面加一行小字
      version: 3.0.0
      released: 2026-08-20
```

这样做的好处是：稳定版仍然参与"活跃 / 更新较少 / 停更"的计算，预发布只作为参考信息展示，不会让一个长期只发 beta 的项目看起来"很活跃"。

`prerelease` 必须同时给出 `version` 和 `released`，否则生成时会直接报错。

---

## 自动同步上游版本

`scripts/sync_releases.py` 会读清单里每个条目的 GitHub 仓库，取最新 Release，判断是否比清单里的 `version` 新。默认只看不改：

```bash
python scripts/sync_releases.py              # 只检查，打印将要发生什么
python scripts/sync_releases.py --apply      # 写入 data/versions.yaml
python scripts/sync_releases.py --only sxj   # 只查一个条目（调试用）
```

`.github/workflows/sync-releases.yml` 每 6 小时自动跑一次，有新版本就**开一个 PR**，不会直接推 `main`。这样做是因为版本号是自动写入的，让人过一眼再合并，比让机器人直接改主干安全。

脚本只改已存在的条目，**不会新增或删除条目**——新出现的分支仍需你手动加进清单。

## 最近更新与安全提示（自动写入的字段）

同步脚本会在条目里写入以下几个字段，`render.py` 据此生成 README 的「最近更新」和「安全提示」区块：

```yaml
    latest_summary: "添加本地导入筛选功能"        # 一句话摘要，取发布说明第一条有效内容
    security_level: suspected                    # 可选：confirmed / suspected
    security_note: "发布说明提及 CVE-2026-1234，需人工确认影响范围"
    security_note_en: "Release notes mention CVE-2026-1234; impact needs manual review"
    security_checked: 2026-11-05
```

判定规则，按优先级：

1. **`confirmed`**——上游仓库发布了 GHSA 安全公告。这是硬信号。
2. **`suspected`**——发布说明里出现 `CVE-xxxx` 或安全相关词（security / 漏洞 / RCE / 提权…）。**这是关键词命中，不等于真的有问题**，比如「修复崩溃」也可能被误判。

所以 `suspected` 的正确用法是「提醒你去看一眼」，确认无关后把 `security_level` 和两个 `security_note` 删掉即可，README 里的警告随之消失。

`latest_summary` 取发布说明的第一行有效内容，不调用模型，所以可能有误报，`suspected` 需要自己看一遍。

---

## 下载安全与常见问题（写在 YAML 里）

README 的「下载安全」和「常见问题」不是硬编码在 Python 里的，而是 `data/versions.yaml` 末尾的两个列表：

```yaml
safety:
  - zh: 一句话
    en: one sentence

faq:
  - zh_q: 问题？
    en_q: Question?
    zh_a: 答案
    en_a: Answer
```

加一条就多一行，改文案不用碰 `scripts/render.py`。四个字段缺一个会直接报错——宁可生成失败，也不要中英两版缺一段。

> 英文文案里不要出现半角冒号加空格，YAML 会把它当键值分隔符。

---

## 带期限的字段（自动过期）

有些内容只想挂一段时间，比如 README 顶部的「最后核对」行——它的作用是让访客一眼看出仓库最近动过，但挂太久反而显得像是很久没更新。

这类东西不写死在代码里，而是在 `meta` 里给一个到期日：

```yaml
meta:
  checked_line_until: 2027-02-05   # 到期后这行自动消失
```

`scripts/expire.py` 每天跑一次（由 `maintenance.yml` 触发）：当天超过这个日期，就把该字段从 `versions.yaml` 里删掉，再重新生成 README，然后开一个 PR。**不需要记日期，也不依赖本地机器。**

要加同类字段，照着 `checked_line_until` 在 `expire.py` 里补一段判断；`render.py` 靠「字段在不在」决定要不要输出。

> 注意：GitHub 会在仓库连续 60 天没有任何推送后停掉定时任务。所以这个 workflow 同时挂在 `push` 上——推迟到下次真实更新时补做，不会漏。

---

## 数据出错时会发生什么

`render.py` 会在生成前做校验，以下情况直接报错退出，不会产出半成品 README：

- 必填字段缺失（`id` / `group` / `name` / `platform`）
- `id` 重复（每条清单项必须唯一，否则增删时容易改错行）
- `group` 未在 `groups` 中定义
- `status` 取值非法
- 在架条目缺少 `url`
- 在架条目缺少 `released`（没有日期就算不出状态）
- `released` 晚于 `meta.last_checked`（发布日期不可能晚于核对日期）
- `prerelease` 字段不全
- `meta.active_within_days` ≥ `dormant_after_days`（「更新较少」这一档会被吞掉）
- `safety` / `faq` 的某一条缺中文或缺英文

---


## 断更很久之后怎么重启

1. **别先读 README**。直接跑 `python scripts/check_links.py`，让机器告诉你哪里烂了
2. 只处理红色的（`DEAD` / `TAKEN_DOWN`），黄色的先放着
3. 改完 `last_checked`，跑生成脚本，提交
4. 一次只做这一件事，不要顺手改文案或配色

---

## 已知待决定的事

- [x] **许可证**：2026-11-05 已从 GPL-3.0 改为 **CC BY-NC-SA 4.0**。`LICENSE` 存放官方原文（未改动任何一字，保证 GitHub 能识别），授权范围、历史版本与商业授权说明写在 `NOTICE.md`。
  - 变更不追溯：`5c584b9` 及之前的提交仍是 GPL-3.0
  - 注意：GitHub 公开仓库的服务条款本身允许他人查看与 fork，许可证管不住这一层
- [x] **`References` 分支**：2026-11-05 已删除（连同 `E-Hentai-Viewer`、`feat/release-sync` 一并清理），README 里的"参考资料存档"链接同步移除。删除前打了完整镜像与 bundle 备份；需要旧快照就 `git bundle` 还原，或从备份里 `git push origin <sha>:refs/heads/archive-2022`。
- [x] **删掉 README 顶部的「最后核对」行**：改由 `maintenance.yml` + `scripts/expire.py` 在 2027-02-05 之后自动完成（见「带期限的字段」一节），不再需要人工记日期。
- [ ] **GitHub Pages**：把清单渲染成可搜索的单页，需要额外模板和部署流程。
- [ ] **真·实时**：现在 6 小时轮询，要秒级得上 webhook + 公网接收端。
- [ ] **摘要接模型**：现在取发布说明第一行，接模型能真正归纳，但要 key 和费用。
- [ ] **托管 APK**：结论是不托管。真要改，先读 `NOTICE.md` 的「不覆盖的范围」。
