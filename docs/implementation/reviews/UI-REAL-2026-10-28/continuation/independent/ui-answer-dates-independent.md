# UI 原答案日期展示独立终审

结论：passed；open_findings=[]。本审查不是实现作者的自签。

实际审查了 product.js 与 test_product_ui.py 当前 diff、presentationRow 字段来源、answerTable 的摘要/展开详情，以及 dom.js 的文本节点行为。没有发现未解决问题。

独立运行 6 个定向真实 ESM 场景，6P，1.366 秒。独立新增反例覆盖：原嵌套 information_as_of=null 不被扁平旧日期或取证截止日替换；明确 null 的 cutoff 不继承 payload 旧截止日；coverage/confidence=0 与 missing_fields=[] 不丢失，且区别于未提供；历史扁平行兼容。结果、历史、信息三种页面都分别显示取证截止与答案信息日期。

XSS 反例在 DOM innerHTML setter 上直接抛异常，向 coverage/confidence/missing_fields 注入 SVG 字符串；实际模块只产生文本，没有 script/img/svg 节点，没有执行标志。原记录、分数/null 与元数据均保持不变，模拟请求全部 GET。

命令：`C:/Miniconda/python.exe runs/resume-recovery-2026-10-28/independent/review_ui_answer_dates.py`。

执行前后 SHA-256 均稳定：

- product.js：4f586595b1d9cd817997ef40d3bcbd198c5a9022198a9912fd9c2808f6798c4c
- test_product_ui.py：95c87275a9df07a7acc99118af72f8b09895f4078cbc1f11e1ecdd7a40b28182

测试在自动清理的临时工作目录运行，直接导入原 ESM，不复制生产源码；API/DOM 全为夹具。没有接触真实数据库、真实 HTTP、收费 API、UI 服务进程、浏览器、源码、PWF 或提交。此结论仅覆盖展示逻辑和兼容边界，不授予金融核验资格，也不代替最终真实页面查看。
