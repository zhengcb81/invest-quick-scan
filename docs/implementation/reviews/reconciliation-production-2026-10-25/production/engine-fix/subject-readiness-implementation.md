# 搜索前的原 subject 初始化检查

本次仅改 StockQA `src/utils/quick_scan_owner_research.py` 并新增 `tests/unit/test_owner_subject_readiness.py`；未改PWF、外部协议、正式库、生产名单、driver/pins，未提交或发起真实API。

根因：原 capabilities 查询对可读 observation schema2返回成功，但原 subject dispatch登记明确只支持schema3/4。原send次序为prepare attempt → external use intent → subject register → budget/model mark-send-intent，因此本次schema2拒绝只留下prepared，不能被解释为模型已发送。

新增公开 `OwnerResearchServices.preflight_subject_dispatch()`，构造时自动调用。它通过原配置根/工作区的固定 StockWiki 公共query CLI（1.1.0）读取原数据能力，并用配置IQS原schema校验，要求唯一available observations3/4、原subject登记接口、store watermark自洽以及API/database写入/dispatch零标志。子进程不继承API密钥，固定argv/cwd，stdout限8MiB读取，schema解析不允许隐式联网，240秒超时，TEMP/TMP及stdout放自有临时目录并始终清理。该能力只描述初始化，**不是授权或金融正确性**；原owner检查在前后执行，物理发送时原register/租约/预算/SDK守卫不变。schema2必须通过原owner备份/迁移工具由operator显式升级，本guard不会自动迁移。

测试：先保留22项RED（缺公开seam），最终23项新单元+原36项相关回归共59passed/8.02秒，见`subject-readiness-after-profile.xml`和同名txt。中间GREEN与格式变更日志独立保留，不把旧日志冒充最终字节。独立agent `/root/fix_bank21` 又跑23项全部通过3.93秒并审过最终两源hash，见`engine-review/prepared-failure-schema-review.json`的readiness_guard_review。未重复649秒软件E2E；真实已升级schema4原producer正例与schema2负例由root另行留证，不能把单元mock当真实生产资格。

精确命令（StockQA cwd，TEMP/TMP/--basetemp钉至每次独有 `TemporaryDirectory(prefix="iqs-ready25-",dir="C:/Temp")`，结束自动清理）：

```text
python -B -m isort --profile black src/utils/quick_scan_owner_research.py tests/unit/test_owner_subject_readiness.py
python -B -m black src/utils/quick_scan_owner_research.py tests/unit/test_owner_subject_readiness.py
python -B -m pytest -q -p no:cacheprovider tests/unit/test_owner_subject_readiness.py tests/unit/test_owner_finalization.py tests/unit/test_owner_native_inspection.py --basetemp <owned-temp>/pytest --junitxml=<engine-fix>/subject-readiness-after-profile.xml
```

准备下一真实尝试时必须镜像并锁住最终源码：owner_research SHA `ca46abca82630573d18dfdc4f5e10c1ab05f3c97daa311355dbd11d7eb6988bc`，新test SHA `9e1732f1c5b0a0a974d960d84f7684b0ab39ed3a607bccbe8c19f95f2b62caf2`。原prepared保留到真实租约到期，由原recover变为abandoned_unsent后同request_cache_key新ordinal；无需新增prepared恢复旁路。epoch3在成功缓存TTL内可复用retry1同query/policy/generation的已settled搜索结果，新use proof绑定新lease/attempt，保留旧记录，不重置预算或task。

## 正常提交hooks后的最终LF字节（追加）

正常mixed-line-ending hook仅将两文件CRLF规范成LF；black/isort/mypy/secrets已通过。此前独审23项的raw字节和59项after-profile记录保留，不能称与最终raw SHA相同。独立agent另以精确CRLF重构核实纯换行等价，见`engine-review/guard-line-ending-equivalence.json`。

最终仅对实际LF字节运行同59项回归，**59passed/14.61秒**，见`subject-readiness-final-lf.xml`及同名txt。`subject-readiness-final-lf-evidence.json`核实测试前后raw SHA相同：生产源`388e05b06196eb68c078196e60d044c06a31692d2110361107984977078c3ed9`，新测试`7327d2a17117399dd73dc920d8fd72d4f1e60d1412fd651eca1f319dd4b79f32`。精确自有临时根`C:/Temp/iqs-ready25-jfujajxk`结束后已清理，0API/0生产DB写。下一真实runtime与pins应锁本段最终LF源；上一段ca46/9e17是hooks前CRLF历史，勿混用。

真实摘要reporter已按总控明确将输入改为`r25-live/retry-2/result.json`，其他算法未改；结果尚未出现时实际运行返回not_ready/real_acceptance_result_missing/new_http0且没有生成summary。它不是本次真实acceptance成功证据。
