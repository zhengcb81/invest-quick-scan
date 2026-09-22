# 接口、测试入口与现有行为基线报告（Task P00）

**记录日期**：2026-09-22  
**任务编号**：P00（Stage M0，Owner: `iqs`）  
**关口目标**：BASE-01、BASE-02 场景基线记录与核实  

---

## 1. 目标仓库版本与工作区状态

| 仓库名称 | 路径 | Commit Hash | 工作区状态 (Git Status) | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| **`invest-quick-scan`** | `C:/Users/郑曾波/Projects/invest-quick-scan` | `85162ec` | 干净（Clean） | 当前问题、契约与计划仓库 |
| **`StockQAbyLLM`** | `C:/Users/郑曾波/Projects/StockQAbyLLM` | `3c685dda28f67a00bd653ad257a121d3b8edebb8` | 干净（仅未跟踪测试/实验文件） | 承担 LLM 问答、搜索与调度拥有者 |
| **`StockWiki`** | `C:/Users/郑曾波/Projects/StockWiki` | `f5b8526c78ef0bc7df27885da043ce5a2534fffb` | 干净（仅本地生成wiki数据未跟踪） | 承担 SQLite 权威库、筛查与UI拥有者 |
| **`company-wiki`** | `C:/Users/郑曾波/Projects/company-wiki` | `f39bd5a64224cd0c7aa098f23f64bf3811fa8939` | 8 行已跟踪文件变更 | 仅提供证券主档只读关联 |

---

## 2. 外部依赖与替代核查方式（BASE-02）

* **CodeGraph 服务状态**：
  * 检测结果：本地 8080 端口不可达，返回 Transport Closed。
  * 替代方式：全面使用本地只读文本与代码结构检索（`view_file`、`run_command`），不依赖网络结构查询服务，不尝试重建已有索引。
* **目标仓库指令文件**：
  * `StockWiki`：已核实存在 [`AGENTS.md`](file:///C:/Users/郑曾波/Projects/StockWiki/AGENTS.md)，严格限定单一写入归属。
  * `company-wiki`：已核实存在 [`AGENTS.md`](file:///C:/Users/郑曾波/Projects/company-wiki/AGENTS.md)，确认其只读 export 与来源不可变边界。
  * `StockQAbyLLM`：无根目录 `AGENTS.md`，使用现有 `README.md` 与 `pyproject.toml` 作为调用与构建依据。

---

## 3. StockQA 关键调用链与已知上游缺陷核实（BASE-01）

经核实 `StockQAbyLLM/src` 源码，确认以下调用链与缺陷基线：

1. **问题加载 (`JSONConfigManager.load_questions`)**：
   * 位于 `src/config/json_config_manager.py`。
   * 接收格式：`[{category: str, questions: [str]}]`。
   * 现状：只能处理纯字符串列表，不能直接解析结构化题目对象。
2. **请求发送与搜索工具 (`LLMClient.send_request` / `AsyncLLMClient`)**：
   * 位于 `src/providers/llm_client.py` 第 37–45 行。
   * 请求体仅包含 `model`, `messages`, `temperature`, `max_tokens`；**未传递搜索工具或厂商搜索开关**，`SearchService` 处于占位状态。
3. **答案生成与分数硬编码缺陷 (`AnswerGenerator.generate_answer`)**：
   * 位于 `src/services/answer_generator.py` 第 58–61 行：
     ```python
     answer_text = first_result.snippet
     # 使用默认评分
     answer_score = 5
     ```
   * **已确认严重缺陷**：不论上游模型返回何种分数（如 `SearchResult.score = 8`），答案生成器均强制覆写为 `answer_score = 5`。
4. **多模型故障降级 (`ProviderCascade`)**：
   * 位于 `src/utils/llm_integration.py` 第 443 行。
   * 现状：仅在内存中维护 `_current_index` 与失败/成功计数，尚未具备跨进程持久化故障状态和 5 小时共享额度管理能力。

---

## 4. 本地题库与离线行为基线（BASE-01）

* **题库规模**：
  * 评分题库 3.0：48 个模块，共 222 道评分题（涵盖通用核心、类型替代、行业/生命周期/属性补充、恢复观察）。
  * 事实题库 1.0：61 道事实题（细分业务、关键设备、上游原材料、下游应用等）。
* **测试基线**：
  * 本地执行：`pytest -q`。
  * 结果：**97 项测试全部通过（101 个 subtests 全部通过，0 failed，0 skipped）**。
* **已知观察性断言记录**：
  * 在 [`tests/test_question_sets.py:282`](file:///C:/Users/郑曾波/Projects/invest-quick-scan/tests/test_question_sets.py#L282) 中：
    ```python
    self.assertIn(answer.score, (5, 8))
    ```
  * 说明：此断言系为了捕获并记录上游 StockQA 的“返回 8 但被生成器覆写为 5”的已知缺陷，属于防御性基线观察，**不能作为生产环境搜索和评分传递已就绪的证据**。后续在 Q01/S02 任务中必须收紧为严格断言。
