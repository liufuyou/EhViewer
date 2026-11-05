# 贡献说明

本仓库是一个**链接索引**，不是客户端源码。所有内容都由 `data/versions.yaml` 生成。

## 最重要的一条

**不要直接编辑 `README.md` 或 `README.en.md`。**

它们是生成产物，任何手改都会在下一次运行脚本时被覆盖。历史上中英文版本就是因为手写两份而出现不同步，请改清单。

## 修改流程

```bash
git clone https://github.com/liufuyou/EhViewer.git
cd EhViewer
python -m pip install -r scripts/requirements.txt

# 1. 编辑清单
#    data/versions.yaml

# 2. 重新生成
python scripts/render.py

# 3. 验证链接
python scripts/check_links.py

# 4. 确认生成物与清单一致（CI 也会跑）
python scripts/render.py --check

# 5. 提交（README 的改动请一并提交）
git add -A && git commit -m "data: 更新 XX 版本至 x.y.z"
```

## 常见提交类型

| 想做的事 | 改哪里 |
| --- | --- |
| 某个版本发了新版 | 该条目的 `version` 与 `released` |
| 链接换了地址 | 该条目的 `url` |
| 版本彻底没了 | `status: taken_down`，并在 `zh_note`/`en_note` 写明核实时间 |
| 作者停更、仓库还在 | 把条目移到 `dormant` 分组即可，状态由日期自动算成「停更」 |
| 仓库被作者归档 / 长期只读 | `status: archived` |
| 距上次发版超过 60 天 | 不用改，状态自动变「更新较少」；超过 180 天变「停更」 |
| 新增一个分支版本 | 在对应 group 下新增条目，必填 `id`、`group`、`name`、`platform`、`url`，以及在架条目的 `released` |

> `status` 只接受 `taken_down` / `archived`。写 `active` / `stale` 会被生成脚本直接拒绝——活跃程度是按 `released` 算的，写死就会和日期打架。

## 提 PR 时请说明

- 你核实的时间（例如"2026-11-05 确认可访问"）
- 版本号从哪看到的（release 页链接即可）
- 如果改了 `status`，说明依据

没有这些信息的 PR 不会合并——索引类仓库的价值全在准确性上。

## 不接受的内容

- 直接贴 APK 或网盘分流链接。本仓库只索引官方发布页，不分发文件。
- 在 README 里插入推广链接或第三方导航站。
- 大段主观评测。想要评测可以开 issue 讨论，不进正文。
