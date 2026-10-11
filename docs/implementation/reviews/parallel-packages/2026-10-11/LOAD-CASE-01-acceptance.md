# LOAD-CASE-01 验收：需要集中整改

实际分支`codex/load-case-01`、HEAD`d232965e48a67aec7d528097ea3ce574c942596e`，无remote、工作树干净。产品提交是`54038475c0a3ce8b6097a11322cf24c5f09b585f`；handoff.result_commit所写`1496c7545b6e92d4abb151ead432b9f270e4c91a`是交接树提交，需修角色。143源文件、15锁内快照及60工件条目实际字节匹配，不能称这些工件hash损坏。

原稳定测试实际77P/exit0，PID67152。四个独立手算控制的算术均吻合：并发峰值2、五小时半开窗口1/2、搜索与模型结算0.23及held0.2/剩余0.57、重启同hash ACK重投0新增发送。公开generate可复现；显式2000只是synthetic容量声明，没有跑真实2000家公司或第二调度器。事件冲突/未来事件/未来schema与乱序处理的有效边界保留。

20次独立CLI加一次生成SHA比较，共21条鉴别检查，13满足、8未满足，不与77测试相加。真实缺口归为四组：预发送reservation被丢、相同settlement重复计费、未知价格仍输出完整额度和守恒；peak超显式cap无违规且五小时请求限额误借并发字段；全部blocked仍进入公平性分母/无first eligible仍判断饥饿、信息日期与TTL混淆；case锁SHA与真实锁未绑定、collection假source SHA及不存在跨包member仍valid。

全部归入[同包R1施工卡](LOAD-CASE-01-R1.md)，另在同包交接中准确记录产品/交接/最终HEAD、真实changed_paths及review快照。只做声明轨迹的归约和诊断，不实现新调度/预算引擎、不猜真实quota、未知费用不填0。

两次pytest控制器错误（随机cwd选错父配置、Windows NUL空设备被误挡）原样保留，最终完整77P与它们分开记载；20个CLI未重复。自有lc01根经精确清单/SHA/lstat清除，源字节前后不变。API/生产库/名单0。证据在`docs/implementation/intake/parallel-acceptance-2026-10-11/load-case/`；这次验收不关闭O02/L03/X09/G3、金融准确性或全池门，也不自动派发整改。
