# LR-02B 一次集中有限独立审查

日期：2026-10-08。复用既有 `evid_lab_remediation_review` agent；只读静态审查，不运行测试、写文件或调用 API。对象是 IQS 独占副本中的接收 HEAD `2c0efb6370e401ca84d5f23cd5047de2bbfdec0a`，软件结果 `cef3d95969671d10b42138ed97010c9c164b5118`。

收到的结论：**静态审查未发现 LR-02B 软件阻断，可以在总控同快照动态复验通过后有限签收。**

- `inputs.py:184` 在实际读取的 IQS 根先核原锁、index 与绑定文件，再返回该根内受锁覆盖的归档路径。原锁不变、同改副本归档与 fixture 时，归档 SHA 漂移先触发 `InputDriftError`，公开 CLI exit 2。
- 历史 replay 在 `cli.py:270` 先核验，再构建记录和 payload；catalog 在 `fixtures.py:339` 同样先核验。缺锁、缺归档、index 或绑定文件漂移不得产出最终目录、已验证历史结果或 `verified_before_write=true` summary。
- synthetic/uncollected 不依赖历史锁；完整历史答案省略可选 `answer_sha256` 仍可接受，答案与归档仍无条件比较。整份锁的无关绑定文件漂移也拒绝历史入口，是原卡允许的选择。
- 软件版本统一为 0.2.2、structure-rules/4；diagnostic 1.2.0、fixture 1.1.0 兼容。新增测试 `test_archive_binding.py:226` 保持原锁/index不变，通过真实子进程验证同改拒绝和无 final/staging/已验证 summary；另覆盖缺锁/归档/catalog/synthetic。

worker 的 118 测试、公开 CLI 和清理回执属于交付方证据，不能替代总控复验；软件结果提交与交接 HEAD 分别归因。交接 `isolation.md:52` 保留之前的 `nul` 越界事故，`external_writes=false` 仅描述对应测试和 CLI，不能扩成全会话无外写。

此结论只覆盖来源字节绑定与拒绝发布。proposal、人类 gold、事实准确性、L02 整体、G3、F05、TH/IN、L03 均未签收。动态执行、路径适配和本轮清理由总控在验收报告另记，不额外增加小节点审查。
