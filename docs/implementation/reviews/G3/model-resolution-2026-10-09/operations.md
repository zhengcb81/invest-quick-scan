# 模型名称追溯与别名配置

本功能的有限软件范围已验收并交付StockQA `42a517c4bd6bc8219f926957c6c332944da3278a`，正常钩子提交／推送完成。最终14个受影响文件606项全部通过、原24路径精确发布，schema8／许可schema1.0.0／模型优先policy v2。本说明是该已交付源码的操作规范；真实厂商别名和收费扫描仍须按既有证据／启动门办理，不能用软件验收替答案准确性或G3。

## 用户配置

沿用StockQA既有配置和模型优先顺序，增加独立顶层`quick_scan_model_resolution`；不要往冻结v2模型route中加入新键。不填或aliases为空仍要求响应与请求同名。仅在确认服务端实际返回名与请求名对应时逐条登记，不能将任何同厂商模型互相放行。

以下只是合成软件例子，不是OpenAI或其他厂商真实别名：

```json
{
  "quick_scan_model_resolution": {
    "schema_version": "1.0.0",
    "aliases": [
      {
        "provider": "openai",
        "protocol": "responses",
        "requested_model": "model-a",
        "resolved_model": "model-b"
      }
    ]
  }
}
```

字段按精确名称匹配，不用通配符、前缀或猜测。请求／返回模型名各限160字符，与既有耐久保存边界一致；不允许首尾空白、控制字符或通配表达式。配置只包含非秘密许可；真实API key仍沿用既有环境变量/提供者配置，不写入这段配置、交接或日志。

允许的协议配对是`openai/responses`、`minimax/responses`、`minimax/anthropic_messages`、`mimo/mimo_chat_completions`。注册其中一对不能授权另一协议或提供者。现有provider配置名可能与canonical provider不同，许可必须依据已经验证的canonical协议提供者，不能用显示名混同服务。

## 扫描与恢复

请求模型仍决定路由顺序，实际模型来自HTTP envelope的model。每次HTTP调用在进入发送方法时固定requested值；异步等待连接期间修改client不改变已冻结请求、解析或回执。别名放行后两者分别保存；跨模型比较使用实际模型标记，别名不会改写实际模型名。模型生成的答案正文、思考过程或格式修复的合并历史不能成为模型身份来源。

非空许可进入策略指纹，在发送前和实际选中route一起冻结。修改配置只影响后续新派发，不能追认旧的未注册替换。已有结果恢复依耐久记录，不通过再问LLM补模型名，也不因缺记录自动重试付费请求。

实际返回模型未知、未注册、协议不符、解析非法JSON或耐久绑定失败时，不生成成功checkpoint。诊断要分别看请求名、真实响应名、HTTP状态、对应attempt和费用状态；没有费用数据就保留unknown和预留，不能认为失败免费。实际模型缺价格表时不能拿请求模型价格代替。

历史已保存的exact checkpoint可按旧来源读；旧裸attempt没有响应原件时不能从requested补actual或借当前配置新建成功结果。升级只加空来源表，不替旧数据补造证据。发送、响应、失败、重启和封包均保持同一attempt来源链。

repair和fallback每次HTTP各自保存来源。新checkpoint必须取同work最终attempt；较早的成功回执不能在新repair准备／拒绝／未知后抢占结果，读回和封包也核对这一点。若请求已发出而没有checkpoint，即使后来repair还未发送，租约到期也保持uncertain，保留来源和费用预留；不能借“最新请求未发”自动重问前一个付费请求。

数据库工作schema升到8，新许可schema为1.0.0，原模型优先policy v2与公共Observation／ExchangePackage／ImportAck不变。StockQA项目元数据版本仍0.1.0，不能用这个旧项目号判断本批是否安装；验收文档中的真实source commit才是交付版本。旧schema1–7升级添加空来源表；迁移失败保持原schema与数据。

## 隔离复验

不要直接重跑已清历史JR2根的helper。总控先按当前已签收源码/固定SHA建立新独占根；本批runner仅写其OWN和intake，移除真实key环境、禁止外网，并显式加载async测试插件。所有付费调用、生产库、真实名单和公司文档均不在离线测试中。

同一轮受影响测试与一次集中审查后才发布StockQA精确文件，正常提交钩子/推送，再按自有清单清理。模拟A→B通过只证明软件兼容，不证明厂商真实别名或答案准确性，不关闭G3/F05或授权200家公司运行。
