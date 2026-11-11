# UI 两仓未提交与未并线工作盘点

调查日期：2026-11-11；最后一次 canonical 只读状态核对约 20:11 UTC。审查人：总控独立子 agent `plan_ui_boundaries`。此文只记录观察、归属和总控待执行项，不代替 Dashboard D00 的总 PWF，不代表旧分支均须重新并线。

## 结论与本轮处理边界

- Dashboard 有 **3 个真正漏并的小提交**，分别修正公开 CWP 浏览参数、流式/缓冲读取测试和 FF reconcile 的部署配置。总控已在自有隔离树摘取，独立代码审查通过，总控短测 **29/29 通过**；最终并线由总控执行。三提交合计只涉及 **4 个不同文件**，与 canonical 的 **6 项功能 WIP 完全不重叠**。
- Dashboard 的其余未合祖先分支多数已经 patch 等价或后续重构吸收；另外一些只存旧研究/演练/失败证据。不能用 `git cherry` 的 `+` 直接认定产品漏并，更不能把旧单文件 adapter 整体覆盖现有包结构。
- 原 8766 UI 的实际仓库是 `iqs-question-bank-ui-lab`。未发现仍缺失的旧分支源码功能；canonical 两个脏 JSON 是本机生成快照，不应作为新功能并线。MC-UI 应把这些运行时快照迁往 IQS 自有状态目录。
- 可以明确归类为可重建缓存的是两个旧工作树中的 Node 编译缓存目录；删除前仍需总控确认当前没有写者、路径没有链接且严格落在该目录。个人配置、数据库、未提交脚本与失败证据都不按名字批量删除。
- Dashboard `main` 比实际远端 `origin/main` 多 19 个已提交节点。它们已经在本地主线，不是待 cherry-pick 分支；发布与新增 3 项小补丁须由总控/D00按同一最终版本核对，不能把“本地 main”与“已推送”混写。

本子 agent 没有修改外仓、运行外仓源码/测试、删除文件、checkout、merge、commit、push、读取密钥或生产数据库。Git 只读操作均设置 `GIT_OPTIONAL_LOCKS=0`；必要的外仓状态读取使用明确工作目录并在只读提权下执行。Git 字节输出按 UTF-8 解码，报告不继承先前 locale 解码造成的中文路径乱码。

## 1. 实际基线、分支与 D00 并发归属

| 仓库 | canonical 分支 / HEAD | upstream / remote | 工作树 |
|---|---|---|---|
| `C:/Users/郑曾波/Projects/investment-dashboard` | `main` / `b707473a1166d3f8740170dad77cb21aa09863ce` | `main` 没有配置 upstream；实际 `origin/main` 为 `0dcf61f59595ebe4b64d9bd8ea490087ed62f7fd` | 首轮 80 个；总控新建隔离树后 81 个。原 80 个中 70 clean、10 dirty |
| `C:/Users/郑曾波/Projects/iqs-question-bank-ui-lab` | `master` / `47d5354575b7561f278bed54e5eb29478574f103` | 没有 remote，也没有 upstream | 7 个；4 clean、3 dirty |

远端值来自 `git ls-remote origin refs/heads/main`，未 fetch/改本地引用。后续若总控合并或其他进程推进，以上是调查基线，不是永久断言。

Dashboard `AGENTS.md` 与 `.planning/unified-dashboard-2026-10-26/OWNERSHIP.md` 规定：D00 独占总 PWF/调度/串行集成；D03 管 adapters，D04 管 application/domain/transport/存储/UI/共享测试。OWNERSHIP 的历史工作树记录明确不继续代表当前活跃写域。大量旧 worktree 仍存在，不等于 80 个并行写者。canonical 四个原有跟踪源码/测试修改的 mtime 约 2026-11-10 02:49–03:04 UTC；但 **20:06→20:11 UTC 观察间有测试归位变化**：原 untracked `tests/unit/test_owner_port_error.py` 不再存在，现为 tracked M `tests/unit/m0-platform/test_owner_port_error.py`（mtime 20:09:45 UTC）。当前精确状态是 **5 tracked +1 untracked 功能 WIP**。因此不能宣称无活跃 writer；这 6 项 WIP 保留，总控在 fast-forward 前重新核对实际路径与 hash，不由本次小补丁顺手提交或清理。

## 2. Dashboard canonical 的 6 项功能 WIP

| 精确路径 | 状态与实际用途 | 处理 |
|---|---|---|
| `backend/dashboard/application/service.py` | tracked M；从 public ports 导入 `OriginalStream`/`OwnerPortError`，增加 application 公开 `open_original(...)` | 保留，纳入 MC-DASH 原有边界收口 |
| `backend/dashboard/ports/protocols.py` | tracked M；`OwnerPortError` 取消 frozen，保留 slots，使异步异常可正常附加 traceback | 保留，与回归测试作为一组 |
| `backend/dashboard/transport/http.py` | tracked M；原文路由经 `service.open_original(...)`，移除 transport 对 `service._port(...)` 的访问 | 保留，纳入 MC-DASH |
| `tests/support/factory.py` | tracked M；临时测试根支持 `DASHBOARD_TEST_RUNS_ROOT`，并创建父目录 | 保留，由 D04/MC-DASH 核对共享测试影响 |
| `tests/integration/test_module_boundaries.py` | untracked；模块方向/封装边界测试 | 保留，与上述 service/transport 改动一起测试 |
| `tests/unit/m0-platform/test_owner_port_error.py` | tracked M；验证 `OwnerPortError` 经过异步 context manager 后仍保留 owner/code/traceback；20:11 最新状态已在 m0 测试目录归位 | 保留，与 exception 改动一起测试 |

canonical 其余 untracked 的分类：

| 路径 | 观察 | 处理 |
|---|---|---|
| `.tmp_e07_adapter_probe.py` | 一次性本地 E07 adapter 探针脚本；有独立内容，不能由 tmp 前缀推定可丢 | 保留，由 D00 判断归档或补入原任务 |
| `.workbuddy-ai/memory/2026-11-07.md` | 个人 harness memory；未读取正文 | 保留，不进入产品提交 |
| `tmpbzf_cgmj/views.sqlite3` | 12,288 bytes | 未读数据库正文；没有足够 provenance 证明可删除 |
| `tmpc9wo1k66/v.sqlite3` | 20,480 bytes | 同上 |
| `tmpu5oe_zvo/u.sqlite3`、`tmpu5oe_zvo/v.sqlite3` | 12,288 / 20,480 bytes；四库 metadata 时间约 2026-11-09 12:00–12:03 UTC | 同上；名字像测试输出不是删除证据 |

## 3. 三个可独立摘取的小提交及独立审查

### 原提交与范围

| 原提交 | 分支 | 精确修改路径 | 内容 |
|---|---|---|---|
| `5d2a761ac75c19ada92a2a79c90e4ecf953055ad` | `codex/d03-e13-public-stream-test-20261107` | `tests/adapters/test_public_source_research.py` | 旧的整段 bytes mock 改为公开 `OwnerStreamTransfer` 流式测试，验证准确 reopen、SourceRef、metadata 与单次读取 |
| `4b30e1d938e77498c6d1c7e968b33a4249f2fac8` | `codex/dashboard-owner-adapter-contracts-20261109` | `backend/dashboard/adapters/cwp.py`；`tests/adapters/test_public_source_research.py` | `language` 按公开 owner 合同编码为单元素 list 或 null；另保留 `read_exact_source_ref` 缓冲读取测试 |
| `8e3231c319b0c845514d7a40036f8800795cf4f0` | 同上 | `backend/dashboard/adapters/m8_owner_jobs/ff_job.py`；`tests/integration/m8-jobs-integrate/test_ff_job_adapter.py` | `reconcile` 使用部署配置 `--config`；无配置时继续 owner 默认行为，其他动作不变化 |

`5d2a761` 与 `4b30e1d` 确实重写了同一旧测试方法，不能机械二选一。总控在隔离树将它们保留成 **streaming open_original** 和 **buffered read_exact_source_ref** 两个独立方法。4 个唯一修改路径与第 2 节 6 项 WIP 没有重叠。

### 总控当前候选与审查结论

- 隔离目录：`C:/Users/郑曾波/Projects/invest-quick-scan/runs/modularity-intake-20261111/dashboard-merge`。
- 分支：`codex/modularity-intake-fixes-20261111`。
- 候选：`0addea2`，提交顺序 `5a16ca7` → `c56e9ce` → `0addea2`。
- 审查范围：`b707473a1166d3f8740170dad77cb21aa09863ce..0addea2`，与三个原提交逐项对照。
- **独立静态审查通过**：两个生产 hunk 完整等价保留；两种原文读取测试均保留；语言过滤的存在/缺省分支和 reconcile 的配置/无配置分支都已覆盖；没有为了修复新增门禁、框架或私有 owner 访问。`git diff --check` 通过。
- 公开 owner 依据：company-wiki `src/company_wiki/source_catalog/public_document_browser.py` 的 `browse` 以 `_optional_text_list(request["language"], "language")` 读取语言；filing-fetch `scripts/ff_job.py` 的 `act` parser 明确声明 `--config` 用于 reconcile owner query，`_cmd_act` 把该路径传给公开 runner。
- 总控提供同一最终候选的短测结果：**29 passed，0 failed，3.86 秒**。本子 agent 独立检查代码与原提交完整性，没有自报运行该测试。两次沙箱内启动卡在首个异步 case、没有测试结论；总控精确停止自有 PID 后，用同一命令在沙箱外通过。没有把沙箱卡住计成产品失败或跳过产品断言。
- 结论：这 3 项小补丁可由总控合到 canonical；合前仍确认 HEAD/WIP 没有漂移。最终合并和推送由总控处理，此报告不是“已并线”断言。

总控执行的短测试入口：

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -B -m pytest -q tests/adapters/test_public_source_research.py tests/integration/m8-jobs-integrate/test_ff_job_adapter.py -p no:cacheprovider --confcutdir . --basetemp ../dash-test-temp -o faulthandler_timeout=30
```

独立审查还检查了相邻 `tests/adapters/cwp_original_stream/`。该套件虽使用临时合成目录、不下载原件，但依赖带 `source_stream_cli.py` 的特定 owner worktree；canonical company-wiki 与它默认尝试的旧兼容目录没有该入口，故没有假装运行成功，也没有为本次小补丁制造或重建 owner。三项改动不改变流传输实现；真实 owner stream 能力盘点交 company-wiki既有owner与Dashboard D00任务协调（不新增MC包），不扩展本轮摘取范围。

## 4. Dashboard 所有未合祖先的本地分支

下表的 `unique` 是 `git rev-list --count main..branch`；`+/-` 是 `git cherry main branch` 的非等价/等价 patch 数。merge 节点不会全部出现在 cherry 输出中，因此不强行让数字相等。共同基线是本次调查 `main=b707473`。

| 分支（均以 `codex/` 开头） | unique；+ / - | 判断与处理 |
|---|---:|---|
| `d03-e13-public-stream-test-20261107` | 1；1 / 0 | 真实测试缺口；第 3 节摘取 |
| `dashboard-owner-adapter-contracts-20261109` | 2；2 / 0 | 真实小修缺口；第 3 节摘取 |
| `modularity-intake-fixes-20261111` | 3；3 / 0 | 总控本轮隔离候选，不是新外包分支 |
| `dashboard-b-real-browser` | 7；0 / 5 | patch 等价吸收，无须重并 |
| `dashboard-b-real-code-audit` | 7；0 / 5 | 同上 |
| `dashboard-b-real-connections-fix` | 2；0 / 2 | 同上 |
| `dashboard-b-real-listing-plan` | 1；0 / 1 | 同上 |
| `dashboard-b-real-owner-packet-audit` | 2；0 / 2 | 同上 |
| `dashboard-b31-browser` | 1；0 / 1 | 同上 |
| `dashboard-b31-independent` | 1；0 / 1 | 同上 |
| `dashboard-b32-audit-bind` | 1；0 / 1 | 同上 |
| `dashboard-b32-audit-combined-transport` | 1；0 / 1 | 同上 |
| `dashboard-b32-audit-combined-universe` | 1；0 / 1 | 同上 |
| `dashboard-b32-audit-transport` | 1；0 / 1 | 同上 |
| `dashboard-b32-audit-universe` | 4；0 / 2 | 同上；另含 merge 节点 |
| `dashboard-b37-revision` | 4；0 / 4 | 同上 |
| `dashboard-c1-request-authority` | 2；0 / 2 | 消费者 C1 已吸收，不重复套旧 adapter |
| `dashboard-c38-integration` | 4；0 / 4 | 消费者 C38 已吸收 |
| `x-c04-cwp-original-stream-01` | 3；0 / 3 | Dashboard 流 adapter 已吸收；不表示 owner canonical 已有流 CLI |
| `x-c04-integrity-repair-01` | 6；0 / 6 | Dashboard 侧已吸收 |
| `dashboard-e14-capture-followup` | 3；1 / 2 | `3ca7378` 为旧 E14 capture 暂停/阻塞记录，保留历史；不自行重启 E14 |
| `dashboard-e14-d00-capture` | 3；1 / 2 | 与上一行同 head/相同历史新增 |
| `dashboard-iqs-b-read-projection` | 3；3 / 0 | 12 个 touched 路径为旧文档/探索，main 不含这些路径；保留分支供归档，不阻挡产品并线 |
| `dashboard-issuer-proof-contract` | 5；5 / 0 | 14 个旧文档路径；同上 |
| `dashboard-rf-provider-discovery` | 11；11 / 0 | 9 个旧文档路径；同上 |
| `dashboard-iqs-b03-company-result` | 19；19 / 0 | B03 功能已经后续集成/重构吸收；66 个 touched 路径中 1 相同、14 后续变化、51 主要为旧交付路径；禁止旧 monolith 覆盖现有 `adapters/iqs/` 包 |
| `x-b03-live-owner-verify-01` | 7；7 / 0 | 79 个历史 harness/演练证据路径，没有 production 源码；保留历史 |
| `x-c01-schema7-rehearsal` | 2；2 / 0 | 全部 81 个 touched 路径与 main 字节一致；已聚合吸收，无需重并 |
| `x-c02-ff-aggregate-context-01` | 11；11 / 0 | 45 个 touched 路径中 44 相同；剩余 service 是后续演进；`filing_fetch.py` 与 main 完全相同，集成见 `dc345e84` |
| `x-c02-ff-statements-read-01` | 7；7 / 0 | 前置已由 aggregate/context 及 `dc345e84` 吸收，不重复重并 |

B03 的实际 main 集成/演进记录包括 `6ea719ce`、`742bca59`、`dda77264`、`5d6495a2`，当前是 `backend/dashboard/adapters/iqs/` 包而非旧 monolith。CodeGraph 旧索引仍出现 monolith，因此此次具体 intake 以当前 Git tree 和已知实际文件为准，不用旧结构结果覆盖源树。

### C1/C38 与 IQS provider 未并线的关系

当前 Dashboard `backend/dashboard/adapters/iqs/universe.py` 已包含 `_require_request_authority`、`_verify_request_record`、preview/apply/request lookup，要求 owner public `membership_request` 协议并核对原请求身份、动作、版本和幂等 key。Dashboard 两个 C1/C38 分支均 patch 等价吸收。

若总控另行发现 IQS C1/C38 的两分支 tree 相同、membership request provider 约 830 行仍未入 IQS 主线，这应作为 **IQS 侧尚缺的公开 provider seam** 并线/验证。不能为迁就 provider 缺口删掉 Dashboard 消费者的幂等请求绑定，也无需再摘旧 Dashboard C1/C38 提交。提供者和消费者应以同一个公开合同做替换/真实接续测试。

### 本地 main 已提交但未推远端的 19 个节点

按时间序列：`37bc900`、`5f4d620`、`d733b3c`、`9e80329`、`93c2f0d`、`f12b237`、`3251efa`、`bde2fe1`、`cae2f3f`、`0755f69`、`441f5ca`、`c782013`、`f7fc984`、`5a42464`、`49b5e7d`、`73833ac`、`4ae1cde`、`212e234`、`b707473`。它们以 m0/m1/m2/m3/m5/m7/m8/m9 测试建设、测试修复和 PWF 为主；不应再 cherry-pick。D00/总控应结合原模块测试汇总及此次最终候选发布；本报告不替 owner 宣布这些产品模块整体已完成。

## 5. 所有 dirty 工作树及可清理范围

Dashboard 首轮 80 个 registered worktree 中，以下 10 个 dirty，其余 70 clean。总控后来增加 `runs/modularity-intake-20261111/dashboard-merge`，当前共 81 个；本报告不把该新候选算作旧遗留脏树。

| dirty 工作树 | 状态/归属 | 处理 |
|---|---|---|
| canonical `C:/Users/郑曾波/Projects/investment-dashboard` | 第 2 节所列 | 保留 6 项 WIP 与未知 provenance 文件 |
| `C:/Users/郑曾波/.codex/worktrees/dashboard-d03-adapters/investment-dashboard`，`dc345e84` | `.codegraph/config.json` 修改；`.tmp/e13-build-20261107/` 下 166 个 untracked，其中 165 个 Node compile-cache 与 1 个 esbuild 缓存 binary | CodeGraph 配置保留；精确 build 缓存目录可按下述规则清理 |
| 上一工作树内 `.worktrees/d06-e13-public-cli`，`0c60e5da` | 仅 `.codegraph/config.json` 修改 | 工具配置，不当产品功能、不删除 |
| `C:/Users/郑曾波/Projects/d00-b03-dashboard`，`6ea719ce` | 仅 `.codegraph/config.json` 修改 | 同上 |
| `C:/Users/郑曾波/Projects/dashboard-iqs-b03-company-result`，`8f126ed` | `.codegraph/config.json` 与旧 B03 `repair_chain.py` 修改；36 个 untracked 交接/证据文件 | 保留；不是垃圾，也不整包并回当前源码 |
| canonical 内 `.worktrees/all31-listing-preview-combo`，`e158288` | 120 个 staged 路径；存在 `MERGE_HEAD=475d44d133dfa781f7137cc292ad15d3e9660bf4`；包含 `OriginalPreview.tsx`、`Documents.tsx`、`transport/http.py` 和旧交接/测试证据 | **旧 merge 未收尾**，不能报 clean；不继续其旧 merge、不 reset，D00 以当前主线语义归档处理 |
| canonical 内 `.worktrees/b34-integration`，`0338c24` | 167 个 untracked，均为 `apps/web/.b34-build-temp/node-compile-cache/` 下编译缓存 | 精确 cache 目录可按下述规则清理 |
| canonical 内 `.worktrees/e14-d00-capture`，`3ca7378` | 3 个 `tests/e2e/evidence/e14-zoom-d00/.../platform-stop.json` | 用户暂停时的失败证据，保留 |
| canonical 内 `.worktrees/e14-d00-review`，`d360f` | `tests/audit/e14_capture_followup/audit_capture_bundle.py`、`original-replay.json` untracked | 独立脚本/历史证据，保留 |
| canonical 内 `.worktrees/m5-e05e06-ext-01`，`88063` | `.planning/unified-dashboard-2026-10-26/handoffs/m5-e05e06-extension-01/INDEPENDENT_AGENT_REVIEW.md` 修改 | 先保留交接审查内容，由 D00 对齐归档 |

B03 repair 文件的完整相对路径为 `.planning/unified-dashboard-2026-10-26/handoffs/external/X-IQS-B03-COMPANY-RESULT-REPAIR-01/repair_chain.py`。其 36 个 untracked 是同一施工包的 README/manifest、repair-chain JSON、输出 zip 与 stdout/stderr 等证据，不能因为 main 不跟踪就删除。

两个可重建缓存的 **精确候选根**：

1. `C:/Users/郑曾波/.codex/worktrees/dashboard-d03-adapters/investment-dashboard/.tmp/e13-build-20261107/`
2. `C:/Users/郑曾波/Projects/investment-dashboard/.worktrees/b34-integration/apps/web/.b34-build-temp/node-compile-cache/`

这不是整工作树清理授权清单。总控执行时先重新确认状态/无活跃写者/无 reparse point，解析绝对路径仍在上述候选根，使用 PowerShell `Remove-Item -LiteralPath`；不要拼接另一 shell 的删除命令。盘点 agent 没有执行删除。

`all31-listing-preview-combo` 的 staged index 相比旧 merge target 仍有 59 个差异，相比当前 main 涉及 2594 个路径；这些主要体现陈旧基线和后续演进，不能把“120 staged”误当作 120 个当前必需功能，也不能随意丢弃 staged 唯一内容。

## 6. 原 UI 的分支、生成物及处理

canonical `master=47d5354`：

| 路径 | 变化 | 处理 |
|---|---|---|
| `src/generated/manifest.json` | 本机 `data_root` 由 canonical IQS 指向 `C:/Users/郑曾波/Projects/iqs-job-facade-wt01`，sources 清单重生成 | 运行时输出；不作为源码功能提交，不在用户现有 UI 运行中盲目恢复 |
| `src/generated/versions.json` | current package hash 与 package/router 清单重生成 | 同上；MC-UI/C5 以 IQS-owned snapshot 替代写入 UI 源树 |
| `.codegraph/.gitignore`、`.codegraph/config.json` | untracked 工具索引配置 | 保留/按仓政策显式忽略；不属于产品修复 |

另外两个 dirty 工作树：

- `C:/Users/郑曾波/Projects/dashboard-iqs-ui-b03-company`，`c27e241`：只有上述 CodeGraph 两文件。
- `C:/Users/郑曾波/Projects/dashboard-iqs-ui-b03-pin-repair`，`d37488f`：只有上述 CodeGraph 两文件。

其余 4 个 registered worktree clean，包括 `_b03live/ui`、`d00-b03-iqs-ui`、旧 nested runtime UI 和 `dashboard-owner-iqs-ui`。没有删除这些工作树或分支。

全部未合祖先的 UI 分支：

| 分支 | head / unique | 结论 |
|---|---|---|
| `codex/d00-all31-universe-ui` | `7a3f44c` / 18 | 后续主线聚合吸收；不重并 |
| `codex/dashboard-iqs-deeplink` | 同上 / 18 | 同一 tree/head，非另一份缺口 |
| `codex/dashboard-iqs-ui-b03-company` | `c27e241` / 22 | B03/pin/return 功能后续聚合吸收 |
| `codex/d00-b03-pin-repair` | `d37488f` / 23 | 同上，当前 master 还有后续公司结果历史改进 |

以上分支 `git cherry` 都显示 `+`，但不是 81 个漏并功能。主线已经含相应演进：`265419f`（bound company return）、`63c4619`（原始边界/origin）、`3f7771f`（精确 result pin）、`5fac2fd`（pin/banner owner status）、`7d10232`（拒绝歧义 pin）、`47d5354`（history links 保持公司 scope）及 `46f86d5`（启动/草稿隔离）。

`d37488f` 与 master 的 `src/app/router.js`、`src/app/ui/deep_link.js`、`tests/test_result_pin.py` 字节一致；`scripts/serve.py`、`src/app/ui/product.js`、`tests/test_company_result_ui.py` 是后续产品化变化，不能反向覆写。未发现必须本轮摘取的原 UI 源码提交。

## 7. 剩余工作归回原 MC 卡，不增加新 gate

| 原卡/责任人 | 应带入内容 | 有限完成标准 |
|---|---|---|
| 总控 + Dashboard D00 | 第 3 节小补丁最终短测、保持 WIP 的 fast-forward、按实际范围发布 | 三项改动全部保留、短测通过、WIP 不变；最终 SHA/远端据实更新 |
| MC-DASH | 第 2 节 6 项 WIP；明确存储/ports/application/transport 方向；现有模块测试 | 合法 public port 可替换；不跨入 service 私有 `_port`；异常正常传播；不为此重开全部 m1–m9 |
| MC-IQS + MC-DASH | IQS membership request provider 与已存在消费者 C1/C38 配套 | provider/consumer 公开合同接通，保留请求幂等与未知状态接续，不重套旧 adapter |
| MC-UI + MC-IQS | canonical generated 两文件的运行时归属迁移 | UI 只读一次 `/generated/snapshot.json`；IQS 写自身 state root，不双向导入/执行 UI 脚本 |
| Dashboard D00 | 历史 merge/staged 内容、E14 暂停证据和独立脚本归档 | 不重启暂停功能；不因旧证据/分支存在阻止当前功能收口 |

本次没有提出新的审批回执、文档数门禁或全套测试要求。公开参数形状、幂等键、身份/作用域与调用方向属于功能合同；旧交接路径数量、harness receipt 和历史截图数量不作为业务运行条件。

## 总控处理结果（晚于本报告只读快照）

2026-11-11，已在canonical main核对base为b707473、目标4路径无WIP后快进至`0addea2f6eeddfd99119d7c6bee5abae6ee89d0f`。上列6项功能WIP在ff前后逐文件SHA-256一致。没有恢复旧all31暂存、删除SQLite、重建UI生成物或改D00总PWF。隔离工作树中的冲突解决保留两个读取测试；29项通过，独审结论不变。未推送既有19个未发布提交，发布范围仍由MC-DASH/D00收拢。本轮临时集成树完成用途后由正常git worktree remove清理，分支/提交保留。

### 并行writer的后续提交（总控收尾只读复核）

20:21:44 UTC产生`20493562f86b1351d97bc164bbc254efacddacdf`，原6项功能WIP及其README共7文件已提交，当前main tracked clean。本轮0addea2经merge-base确认仍为真祖先；本地origin/main缓存比较为0 behind/23 ahead，未联网核远端。2049356不属于本轮29项测试和上述代码独审范围，MC-DASH应以此新基线接续；不重新实现已提交改动，也不覆盖剩余untracked probe/记忆/四个SQLite。
