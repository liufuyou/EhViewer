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

# 4. 提交
git add -A && git commit -m "chore: 核对至 2026-11"
```

就这四步。不要直接编辑 `README.md` 或 `README.en.md`——它们下次运行脚本就会被覆盖。

---

## 仓库结构

```
data/versions.yaml          唯一数据源。所有版本信息都在这里
scripts/render.py           从 yaml 生成两份 README
scripts/check_links.py      检查所有链接是否还活着
.github/workflows/link-check.yml   每天自动巡检
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

| status | 什么时候用 | 页面上的显示 |
| --- | --- | --- |
| `active` | 正常维护，最近有发版 | 活跃 |
| `stale` | 还在，但很久没更新 | 滞后 |
| `archived` | 已归档，仅供查证 | 已归档 |
| `taken_down` | 仓库打不开了 | 已下架（并加删除线） |

`stale` 可以不用手写：脚本会对比 `released` 和 `meta.last_checked`，超过 `stale_after_days`（默认 180 天）自动标成滞后。

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

这样做的好处是：稳定版仍然参与"是否滞后"的计算，预发布只作为参考信息展示，不会让一个长期只发 beta 的项目看起来"很活跃"。

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

关于「实时」：GitHub 的 `schedule` 最短间隔是 5 分钟，但高峰期会延迟、甚至丢弃某次触发，没有 SLA。所以这里定位是**准实时**（发版后几小时内同步）。要秒级只能上 webhook + 自己的服务端，见文末「已知待决定的事」。

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

> 关键词扫描有误报，这是已知设计取舍：宁可多报一次让你花 30 秒确认，也不要漏掉一次真实的安全问题。

`latest_summary` 是**抽取式**的——取发布说明第一行有效内容，不调用任何模型。好处是零成本、可离线、结果稳定；代价是遇到「一堆琐碎修复」时概括性不够。想要真正的归纳，需要接一个模型 API，见「已知待决定的事」。

---

## 数据出错时会发生什么

`render.py` 会在生成前做校验，以下情况直接报错退出，不会产出半成品 README：

- 必填字段缺失（`id` / `group` / `name` / `platform`）
- `id` 重复（每条清单项必须唯一，否则增删时容易改错行）
- `group` 未在 `groups` 中定义
- `status` 取值非法
- 在架条目缺少 `url`
- `released` 晚于 `meta.last_checked`（发布日期不可能晚于核对日期）
- `prerelease` 字段不全

---

## 关于日期的设计（重要）

判断"是否滞后"用的是 `meta.last_checked`，**不是当天日期**。

这意味着：同一份数据，无论哪天运行脚本，产出都完全一样，不会产生无意义的 diff。想刷新状态，就更新 `last_checked` 再跑。

---

## 断更很久之后怎么重启

1. **别先读 README**。直接跑 `python scripts/check_links.py`，让机器告诉你哪里烂了
2. 只处理红色的（`DEAD` / `TAKEN_DOWN`），黄色的先放着
3. 改完 `last_checked`，跑生成脚本，提交
4. 一次只做这一件事，不要顺手改文案或配色

重建节奏靠"小步、可验证"，不靠意志力。

---

## 已知待决定的事

- [x] **许可证**：2026-11-05 已从 GPL-3.0 改为 **CC BY-NC-SA 4.0**。`LICENSE` 存放官方原文（未改动任何一字，保证 GitHub 能识别），授权范围、历史版本与商业授权说明写在 `NOTICE.md`。
  - 变更不追溯：`5c584b9` 及之前的提交仍是 GPL-3.0
  - 注意：GitHub 公开仓库的服务条款本身允许他人查看与 fork，许可证管不住这一层
- [ ] **`References` 分支**：目前是 3 个文件的旧状态副本，与 README 里的"参考资料存档"链接对应。要么保留并在里面放真正有价值的资料，要么删除分支并去掉链接。
- [ ] **是否做 GitHub Pages**：把清单渲染成可搜索的单页，比 README 更好用，但需要额外的模板和部署流程。
- [ ] **要不要「真·实时」**：现在是 6 小时轮询（准实时）。要秒级必须用 GitHub webhook，它需要一个能被公网访问的接收端——这是新增的基础设施，不是改配置能解决的。
- [ ] **摘要要不要接模型**：现在是抽取式（取发布说明第一行）。接模型能真正归纳，但需要 API key、每次发版产生费用，且模型可能改写原意。建议只有在条目多到人工看不过来时才考虑。
- [ ] **是否托管 APK**：目前结论是**不托管**，只放官方链接。若要改，先读 `NOTICE.md` 里「不覆盖的范围」一节——托管安装包会把免责声明里的「不托管、不再分发」直接推翻。
