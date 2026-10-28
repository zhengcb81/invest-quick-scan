# UI 答案日期与原元数据最小修复（待独立审查）

仅修改 UI 外仓的 `src/app/ui/product.js` 和 `tests/test_product_ui.py`，未提交或推送。原 `product_core.js` 的 `flattenFields` 已保留完整row/payload，因此无需改投影核心文件。

卡片及展开详情分别显示“取证截止”和“答案信息日期”。嵌套 `payload.answer.information_as_of` 显式null会保留并显示“未提供”，不会用cutoff或扁平旧日期遮盖；没有嵌套字段时继续支持标准扁平row原值。coverage/confidence/missing_fields只显示对应原值（包括0和空数组）或“未提供”，不推导资格、覆盖或缺口结论。评分与scored/null原逻辑未改。

所有新显示都使用现有textContent/kv文本节点，未采用HTML渲染。回归包含恶意HTML字串、null与缺省、原日期、扁平row兼容、0/空数组、原DTO不变和score/null不变。

红测先于产品修复：在原product.js上，新实际DOM/ESM案例因 `Card must distinguish collection cutoff from the original answer information date` 失败。修复后，仅运行现有 `tests/test_product_ui.py`，**47 passed in 13.37s**。`git diff --check`退出0。

源码pin：

| 文件 | 修复后SHA256 |
|---|---|
| product.js | 4f586595b1d9cd817997ef40d3bcbd198c5a9022198a9912fd9c2808f6798c4c |
| test_product_ui.py | 95c87275a9df07a7acc99118af72f8b09895f4078cbc1f11e1ecdd7a40b28182 |
| product_core.js（未改） | 90b5cc50a0898e463db1abbb5508a954cc68c2e5a903282ae27f8502bd7a291d |

外仓HEAD：`bd5595863110c5e79e9d30a5432a712fb90e14eb`。完整before/after pin、两文件diff、红绿测试输出、工作区状态及UTF-8核验均在相邻 `ui-answer-dates-author.json`；diff SHA256为 `7627ac4146080e380c03ce27fa5c4c7be9b81d1da14ffed1d3b3e4aa6dc8bc29`。

修改前后仅上述两tracked文件有变化；预先已有的未跟踪 `.codegraph/` 保留未动。未控制浏览器、服务、进程、配置或真实数据库，未调用模型。测试使用原隔离DOM/API fixtures。静态资产等待下一次正常reload即可，当前三个准备任务未受干预。请root或另一agent独立审查后再决定提交。
