# bank 模式真实跑：前置检查、执行、验收

本文件记录 `thin_scan.py --bank-manifest` 的完整可复现流程，以及 2026-10-22 排查出的
陷阱。所有命令离线可验证的部分不需要凭证；只有最后一步真实跑需要 API key。

## 0. 凭证（Windows 用户作用域）

本机 API key 存放在 `HKCU\Environment`，**已运行的进程不会继承**。两种办法：

```powershell
# A. 新开终端（会自动继承用户作用域）
python -B -X utf8 scripts\thin_scan.py ...

# B. 从用户作用域注入当前进程
$env:DEEPSEEK_API_KEY = [Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')
```

涉及变量：`DEEPSEEK_API_KEY`（搜索 + deepseek 模型）、`MIMO_API_KEY`、`MINIMAX_API_KEY`。
检查是否齐全（离线）：

```powershell
python -B -X utf8 scripts\bank_manifest_preflight.py `
  --manifest runs\<run>\composed\manifest.json --check-credentials --user-scope-env
```

## 1. 组装 profile → compose

profile 必填（缺一个 compose 就拒绝，且不会留下半成品）：

| 字段 | 说明 |
|------|------|
| `company` `ticker` `exchange` `as_of` | 身份与截止日 |
| `company_type` | 必须是 `types` 类模块 ID（`operating`/`bank`/`insurer`/…） |
| `stage` | 必须是 `stages` 类模块 ID（`mature`/`scaling`/…），不能填 `cyclical` |
| `industry_modules` | `operating`/`pre_revenue` **至少 1 个**，不匹配用 `other`；最多 2 个 |
| `routing_confidence` | 只接受 `high` / `medium` |
| `routing_rationale` | 非空，写分类依据 |
| `routing_sources` | 非空数组，每项有合法 HTTP(S) `url`；`published_at` 不能晚于 `as_of` |

```powershell
python -B -X utf8 scripts\question_sets.py compose `
  --profile runs\<run>\profile.json --mode full `
  --out-dir runs\<run>\composed --now-utc <ISO8601Z>
```

成功输出 `question_count` / `modules` / `module_package_id`。**空目录 = compose 失败**，
不要当成"在后台跑"。

## 2. 前置检查（必须，零成本）

```powershell
python -B -X utf8 scripts\bank_manifest_preflight.py --manifest runs\<run>\composed\manifest.json
```

校验：题数非空、必填字段、三个 sha256、`prompt_sha256` 与 prompt 文本实算一致、
无重复 id、每个模块都有锁、`comparison_role` 齐全且至少 1 个 core、包/发布身份存在。
exit 0 才继续；exit 2 是清单不可跑。

## 3. 真实跑

```powershell
python -B -X utf8 scripts\thin_scan.py `
  --company "<公司名>" `
  --bank-manifest runs\<run>\composed\manifest.json `
  --out runs\<run>\final
```

预算与行为（2026-10-22 修复后）：

- `BANK_MAX_TOKENS=12000`：推理模型的思考也算在 max_tokens 里，预算不足时 `content`
  为空、`finish_reason=length`，会被报成 `model_truncated_no_content` 并**翻倍预算重试一次**。
- 每题最多 1 次搜索（`--max-searches-per-question`），搜索失败记入 `problems` 不再静默。
- 传输层超时/断连不会中断整轮，只影响当前题。
- 推理内容（`reasoning_content`）永不当作答案。

## 4. 验收（必须）

```powershell
python -B -X utf8 scripts\scan_result_check.py --run runs\<run>\final
```

| exit | 含义 |
|------|------|
| 0 | 可用：有 scored 答案且每题证据完整 |
| 1 | 跑完了但 0 分（诚实产出，但不是有效数据） |
| 2 | 不可用：缺产物、scored 无证据、搜索了但 0 次模型调用、每题同一个失败 |

**退出码 0 不等于有数据** —— 2026-10-22 的多次运行都 exit 0 但 0 分。

## 5. 已知陷阱（按出现顺序）

1. `model_config.search()` / `models()` 未把 `api_key_env` 映射成 `key_env` → `KeyError` 崩溃。
2. `search()` 把非 200 归一化成空列表 → 凭证缺失静默降级、exit 0。
3. `post_json()` 让 `TimeoutError` 逃逸 → 整轮崩溃、已收答案全丢。
4. `build_prompt()` 把来源截到 300 字 → 关键数据被砍，模型正确判"证据不足"。
5. `BANK_MAX_TOKENS` 太小 → 推理吃光预算、`content` 为空。
6. `normalize_bank_answer()` 吞掉 error → 截断重试永不触发。

以上 6 项均已修复并有 RED 反例测试锁住（见 `tests/test_thin_scan_*.py`、
`tests/test_model_config.py`、`tests/test_bank_manifest_preflight.py`、
`tests/test_scan_result_check.py`）。
