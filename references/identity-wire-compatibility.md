# 真实身份导出的只读兼容规则

版本：`stockwiki-g2b/1.0.0`；公共校验CLI：`1.1.0`。适用已发布的身份包`2.2.0`和Entity`2.1.0`，不改变身份包版本或历史工件。

## 入口与版本

现有命令继续工作，默认使用这一兼容profile：

```powershell
python -B -X utf8 scripts/identity_contract_cli.py --input <owner-request.json> --schema-version 2.2.0
python -B -X utf8 scripts/identity_contract_cli.py --version
```

输出仍为单行JSON，新增`wire_profile`标记本次实际规则；`schema_version=2.2.0`、`validation_scope=contract_consistency_only`不变。成功exit0；结构或语义错误exit2；未知包版本或未知profile在读取输入前exit3。未知profile不回显原字符串。

需要重现旧词法边界时使用`--wire-profile legacy`。内部`contract_validation.validate_entity`默认仍走legacy；仅显式`wire_profile="stockwiki-g2b/1.0.0"`才启用兼容。这个参数不是写入或调度授权。

## 精确差异

冻结文件[identity.schema.json](../schemas/quick_scan/identity.schema.json)和[identity-cli-request.schema.json](../schemas/quick_scan/identity-cli-request.schema.json)保持原字节不变。新的[profile schema](../schemas/quick_scan/identity-wire-profile.schema.json)只用于在内存副本中替换`ListingV21.source_binding_ref`和`SourceBindingV21.binding_ref`，其他定义不变。

| 项目 | 兼容规则 | 拒绝条件 |
|---|---|---|
| 来源绑定ID | legacy `BND_` ID或精确小写`BIND_<UUIDv4>`；原值不变 | 非v4/variant错误、其他前缀、空后缀、空白或路径字符 |
| 资格回执生命周期 | 至少存在一个`status`或`effective_status`，所有出现的字段均严格为`active` | 任一字段撤销/退役/替代、未知、null、非字符串、两个字段冲突 |
| 修订 | 回执修订是非bool正整数，与Entity精确相同 | bool、float、字符串、旧修订 |
| 人工资格证据 | `user_exact_security_attestation`的`evidence_ref`可显式null，但必须有非空actor及完整精确挂牌/来源/属性 | 缺字段、缺actor、错entity/security/listing、错scope/source/known_attributes |
| 官方/verified证据 | 保持HTTPS来源和精确全部证券/挂牌属性覆盖 | 缺来源、HTTP、丢覆盖、错属性或同发行人标记 |

legacy模式同样拒绝明确的失效`effective_status`与不合法修订，不允许用历史`status=active`覆盖撤销生命周期。此处是失败关闭修复，不改变旧有效记录的字段解释。兼容规则不编造URL、状态、时间戳、source binding或verified资格。

## 真实样例与测试隔离

[真实样例索引](../docs/implementation/contracts/goldens/stockwiki-real-identity-2026-10-07.manifest.json)固定宁德时代、中信建投H及Alphabet的现有W04导出原字节、SHA和原归档来源。两份provisional保持provisional；Alphabet保留四条挂牌。源文件曾通过前置导入验收，本次只做原字节复制和IQS消费侧校验，没有重新导出或写真实身份库。索引中的producer commit是当前代码观察基线，历史生成命令为已归档子命令，不能解释为本次重跑或新producer签收。

运行定向测试：

```powershell
python -B -X utf8 -m unittest discover -s tests -p test_identity_wire_profile.py -v
```

测试只用本仓唯一自有临时根。真实子进程公开CLI加载启动audit hook，禁止socket调用及临时根外写入；隔离canary证明hook实际生效。测试比较输入原字节及冻结schema hash，覆盖三市场正例和一字段反例；结束断言临时根已删除。没有API、凭据、下载、生产DB访问或外仓写入。synthetic legacy fixture只作旧协议回归，不充当StockWiki正例。

原identity schema在Windows工作树为CRLF（raw SHA=671292a6…），Git冻结blob为LF（SHA=4924b5e3…）；旧CLI request schema为LF（d63afdf4…）。自动回归只容许Git的CRLF→LF转换，不容许内容变化；审查另复核当前原字节未改。三份producer golden以精确`-text` Git属性保存，不能因checkout平台改变原字节/hash。

## 尚未被证明的边界

CLI验证结构与交叉引用一致性，**不认证caller-supplied trusted_context的生产者身份，也不证明当前时点的准入有效性**。W04历史envelope未带可供IQS校验的as_of；不能据`effective_status=active`推断今天的挂牌/回执仍有效，当前权威状态和有效期仍须由owner公共读取/映射路径确认。

冻结`work.schema.json`仍有仅允许`BND_`的`source_binding_refs`词法边界。本批不会修改它；三份身份CLI通过不证明Work、Observation、C05派发或整条生产链均兼容BIND。后续集成必须由契约owner提出版本化加法演进，并在QA-NET-01/主线联调中验证。G3、F05与两个研究消费者的开工门均不因本规则关闭。
