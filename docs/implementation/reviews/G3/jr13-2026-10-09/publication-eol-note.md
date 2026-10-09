# JR1/JR3 同次集中审查：发布换行双域附记

**仅 `tests/test_quick_scan_delivery.py` 的 Git 文本序列化差异可以接受。** 独立直接读取当前 staged blob，确认它恰等受审 CRLF 原件的 `replace(b"\r\n", b"\n")`，不是近似 diff；Python AST（包括字面量值、不含位置属性）完全相等。此结论属于原集中审查的发布附记，不新增测试或审查门，不回写旧签收。

| 域 | SHA-256 | 字节 / 换行 |
|---|---|---|
| 受审执行原件及当前源工作树 | `b50ef0e46cc2a335a93f72eeb3fde6f76b1838ebbc0f637d6df6ae81ee4faeab` | 19,991 bytes，496 CRLF |
| 当前 staged Git blob | `bda18d2e691fc037d955136f80f1e7cb9bed4bdaed95d693f5ac89867fbba4aa` | 19,495 bytes，0 CRLF |

这两个 SHA 不能混称。原 113P/18P 和兼容复核仍绑定执行域 `b50…`；发布 Git 内容域为 `bda…`，其语义等价依据是本附记的精确换行比较与静态源码检查。这里的 Git blob SHA 是内容的 SHA-256，不是 Git object OID。

## 必要静态核查

完整阅读该文件并检查 AST，没有 `__file__`/`__cached__`/loader/spec、自身 source 读取、inspect/linecache/tokenize/importlib、源文件散列或 raw 源字节断言。文件中的 payload_sha256 属观察/ACK业务值；原 ledger JSON 字节保真断言检查数据库回执，不读取或散列测试源码。空数据库的 `write_bytes(b"")` 和 synthetic workspace 删除也与自身源码换行无关。本轮没有导入或执行测试模块。

直接独立读取源工作树与最终快照五件原文，全部工作树 SHA 仍精确等于受审执行 SHA。其余四条 staged 路径与受审执行原件**逐字节完全相同**：quick_scan_import、quick_scan_observations、quick_scan_backup_manifest、test_quick_scan_observations。对这四条不接受换行、格式或其他字节差异；此附记不放松任何产品字节要求。

源 HEAD 仍为 `c40de21403720306ba21edbf71b9634a40ee58f8`。独立 `git diff --cached --name-only -z` 恰有五个获授权路径；326 项已冻结非秘密保护文件实际 SHA 全相同。Git index 在核查前后 SHA 均为 `08c2d16c914020141d75951f909821a4f2bc324a9535648d99d373eefee343ee`，HEAD 和完整 status 前后亦相同。本轮未修改源、stage、Git 或已有报告，未 commit/push。

只读 Git 设置 `GIT_OPTIONAL_LOCKS=0`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=NUL`，避免读取个人 Git 配置。该配置域 status 对 delivery 显示 `MM`，前后相同；总控原 diagnostic 为 `M `。不把不同配置域的状态缩写当作字节改写证据：实际工作树始终是受审 `b50…`，实际 index 是上述仅 LF 的 `bda…`。

机器记录见 [publication-eol-note.json](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/reviews/G3/jr13-2026-10-09/publication-eol-note.json)。原发布诊断和 input 的 SHA 分别为 `ec7c25c2c23be3b584d157a39aa2dd037e1989cadb23362a3a2136818c9200ed`、`4f0a37264330d5aed1feb5f62dcc99dc74b41a9ddb8ac080a2e53abf1aafb7c1`，原件不改。

可以按以上两个明确内容域继续原批正常 Git hooks/发布；如 hook 或后续步骤改变任何受保护字节，需按实际差异重新核发布范围，不能引用本附记作一般格式豁免。无需重跑已通过 113/18 或运行新探针。测试/API/数据库操作均为 0；全局 G3/F05/L03、真实 golden 与金融准确性边界不变。
