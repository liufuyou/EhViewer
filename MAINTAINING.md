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

- [ ] **许可证**：现在是 GPL-3.0，但本仓库只有文档和链接，没有代码。GPL 是软件许可证，对纯内容索引并不合适。可考虑改为 `CC0-1.0`（最省事）或 `MIT`。改动涉及法律含义，需仓库所有者决定。
- [ ] **`References` 分支**：目前是 3 个文件的旧状态副本，与 README 里的"参考资料存档"链接对应。要么保留并在里面放真正有价值的资料，要么删除分支并去掉链接。
- [ ] **是否做 GitHub Pages**：把清单渲染成可搜索的单页，比 README 更好用，但需要额外的模板和部署流程。
