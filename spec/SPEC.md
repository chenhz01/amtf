# AMTF — Agent Memory Transfer Format Specification v1.0

> Status: **public draft v1.0**（首次公开发布）。本规范是 SDK、adapters、conformance 套件的唯一真相源。
> Spec text and code in this repository are licensed under MIT (see LICENSE).

## 0. 一句话

AMTF 是 AI Agent 长期记忆的统一导出格式：让用户换平台时能带走记忆（AI 版 GDPR 第 20 条）。核心 = 薄 schema；生态 = 每家记忆框架一个导出适配器。

## 1. 设计原则

1. **字段显式，禁静默补值**——缺失必须置 `null` 并在校验时点名，绝不悄悄填默认值（默认值是记忆迁移中最危险的谎言）。
2. **时效是一等公民**——每条记忆必须带生效期（`valid_from`/`valid_until`），"永久"用 `null` 显式表达而非省略。
3. **溯源必须存在**——每条记忆声明它从哪个通道来、可信度几级；无溯源记忆允许迁移但必须被标红。
4. **拒绝可见**——迁移中被拒的记忆必须逐条列出原因，禁静默丢弃。

## 2. 记忆条目 schema（单条）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `schema_version` | string | ✅ | 恒为 `"amtf/1.0"` |
| `content` | string | ✅ | 记忆正文（自然语言事实/偏好/教训） |
| `created_at` | string\|null | ✅ | 首次写入时间，ISO 8601 日期或日期时间；未知置 null |
| `valid_from` | string\|null | ✅ | 生效起始时间；未知置 null |
| `valid_until` | string\|null | ✅ | 失效时间；**null=仍然有效**（显式声明，非省略） |
| `provenance` | object\|null | ✅ | `{channel, origin, trust}`；channel=来源通道枚举，origin=源标识，trust∈{high,medium,low}；整体未知置 null |
| `confidence` | number\|null | ✅ | 置信度 0-1；未知置 null（禁编造 0.8） |

## 3. 导出文件封装

```json
{
  "format": "amtf/1.0",
  "exported_at": "2026-09-29T18:00:00+08:00",
  "exporter": "mem0-adapter/0.1",
  "entries": [ { ...第 2 节单条 schema... } ]
}
```

## 4. 校验规则（conformance 套件逐条对应）

- V1：七个必填字段全部存在（缺任何一个都要独立报错，聚合不短路）
- V2：`schema_version == "amtf/1.0"`
- V3：`confidence` 为 null 或 0-1 浮点
- V4：`valid_from <= valid_until`（两者非空时）
- V5：`provenance.trust ∈ {high, medium, low}`（provenance 非空时）
- V6：`created_at`/`valid_from`/`valid_until` 非 null 时必须可解析为 ISO 8601
- W1（警告级）：`valid_until=null` → "永久记忆，请确认是有意为之"

## 5. 兼容性承诺

v1.0 之后新增字段只增不改不删；消费方必须忽略未知字段（forward-compatible）。

## 6. 治理（Governance）

本规范的治理遵循"**审计清单公开，签发权锁住**"原则，分三层：

| 层 | 内容 | 位置 |
|---|---|---|
| 公开 | 认证审计准则 A1–A9、证书字段定义、边界声明 | [`docs/AUDIT-CRITERIA.md`](../docs/AUDIT-CRITERIA.md) |
| 锁定（哈希承诺） | 签发与裁定程序：阈值、签署人、争议与吊销流程、台账结构 | [`docs/GOVERNANCE-COMMITMENTS.md`](../docs/GOVERNANCE-COMMITMENTS.md)（仅 SHA-256 摘要，本体随签约交付） |
| 永不公开 | 裁定台账、标定记录、语料本体 | 不存在于任何公开仓库 |

认证证书并不由本仓库签发——本仓库只提供可复跑的 conformance 套件与准则；"由谁签发"见 GOVERNANCE-COMMITMENTS.md 的承诺记录。
