# REPORT

## 为什么选择 SQLite

MVP 阶段我选择 SQLite，原因是样例数据量很小，启动链路需要尽量简单，而且题目要求 `docker compose up` 能低成本直接跑起来。当前实现仍然使用 async SQLAlchemy，因此后续如果要切换到 Postgres，代码改动会比较有限。

## 为什么这样设计 `/ask` 和 `/chat`

当前版本里，我把 `/ask` 和 `/chat` 都切换成了实时 LLM 调用，同时保留后端的安全边界与状态控制：

- `/ask` 第一次调用 LLM 生成单条 `SELECT`，第二次调用 LLM 基于结果生成 grounded answer
- `sql_guard.py` 在 SQL 执行前拒绝危险 SQL 和多语句执行
- `/chat` 第一次调用 LLM 解析多轮意图、筛选条件和引用关系，第二次调用 LLM 基于查询结果生成回答
- `session_state` 仍由后端持久化到 SQLite，保证筛选累积、预算偏好和上下文延续可控

我把编排逻辑集中在 service 层，这样 API 层保持稳定，Prompt 和模型接入也能独立迭代。

## Prompt / 翻译器迭代

### v1

第一版使用确定性意图判断，像 `Just the top 3`、`Tell me more about the second one` 这种追问很依赖手写规则，扩展性差，也容易漏掉自然表达。

### v2

我把 `/ask` 和 `/chat` 都迁移到实时 LLM 调用，并把输出限制成结构化 JSON：

- `/ask` 的第一跳 LLM 只允许输出 `{"out_of_scope": ..., "sql": ...}`
- `/chat` 的第一跳 LLM 只允许输出固定字段的意图对象，例如 `mode`、`resolved_asin`、`filters_to_set`
- 第二跳 LLM 只负责生成 grounded answer，不直接决定 SQL 执行

这样既提高了自然语言理解能力，也把真正高风险的执行权限保留在后端。

## AI 工具说明

- 使用的 AI 工具：Trae coding agent，底层模型为 GPT-5.4
- AI 生成的部分：初始项目骨架、路由处理器、服务层骨架、README/REPORT 初稿
- 人工主导的部分：架构选择、任务拆解、取舍判断，以及对状态处理和 eligibility 返回行为的迭代修正

## 如果继续完善

- 给 LLM 增加更严格的 JSON schema 校验和重试策略
- 在 `/chat` 中加入更丰富的结果摘要，提升序数引用和代词引用准确率
- 补强 Keepa 字段解析，并用真实 API 返回进一步校准索引映射
- 在 ETL 阶段直接存储更完整的 eligibility 解释结果，减少接口层重复计算
- 增加基于 mock Keepa 响应的异步接口测试
- 基于 `/token` 做更细粒度的 token 感知批处理和退避策略
- 继续增强 `/upc` 的 normalization，覆盖更多 GTIN / ISBN 边界情况
