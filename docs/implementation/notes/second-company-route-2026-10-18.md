# 第二家公司（000026）路由现状与阻塞

日期：2026-10-18

## 已具备

- analysis subject：ASJ_67a1f0d0-f1b4-4d78-9969-f439e5aac617@1（revision 1）
- primary issuer：ENT_a87249c5-f020-4246-89d8-9f2d9eac1b7a
- perimeter：b5ec90015803216fd33add74470a3482e94c416011c188987a7e87b7f124caba
- 导入回执：PRC_cce87da49d0fe024b69b6ebe47f52d1a

## 尝试

```
python -B -m stockwiki.quick_scan_routes_cli --root <ws> quick-scan-route-refresh \
  --subject-key ASJ_67a1...@1 --scope entity --scope-id ENT_a872... \
  --now-utc 2026-10-18T19:30:00Z --provider mimo --model mimo-v2.6-pro --ttl-hours 24
```

结果：`route_current_unavailable`（exit 2）。在 workspace 副本上执行，未改真实 owner 状态。

## 结论

`quick-scan-route-refresh` 只能刷新**已存在**的 current route；000026 没有 route。

建 route 需要先 `quick-scan-route-record`：

- `--expected-decision-id`（route decision id）
- `--route`（route 决策文档）
- `--manifest`（公司 manifest/identity bundle）

这些是 CATL 早期由 native task/owner 流程生成的对象，目前没有为 000026 生成它们的工具或输入。因此第二家公司的 admission 仍被 route 前置件阻塞，而不是 search/observation 环节。

## 下一步（若继续）

1. 为 000026 生成 manifest/identity bundle（需要 IQS native task 的 company profile 输入）；
2. 由 owner 生成 route decision，再用 route-record 落库；
3. route-refresh → preview/confirm/admit → driver。
