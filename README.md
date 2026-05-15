# Keepa Scout

一个基于 Keepa 数据的 Amazon 套利分析最小化 FastAPI 服务。

## 功能概览

- 从 `candidate_package/data/sample_asins.csv` 运行 ETL
- 批量请求 Keepa 商品数据
- 将 eligibility 和 ROI 计算结果写入 SQLite
- 提供 `/upc`、`/eligibility/{asin}`、`/eligibility/batch`、`/ask`、`/chat`
- 支持多轮对话中的状态筛选，例如 eligibility、ROI 阈值、排序和预算

## 技术栈

- Python 3.11+
- FastAPI
- async SQLAlchemy + SQLite
- httpx 调用 Keepa API
- `/ask` 和 `/chat` 通过实时 LLM 调用实现 NL -> SQL、意图解析和 grounded answer

## 启动方式

1. 复制环境变量模板。

```bash
cp candidate_package/env.example .env
```

2. 在 `.env` 中补充至少一个可用的 LLM key。

```bash
OPENAI_API_KEY=your_key
# 或
DEEPSEEK_API_KEY=your_key
# 或
MOONSHOT_API_KEY=your_key
```

3. 安装依赖。

```bash
pip install -r requirements.txt
```

4. 运行 ETL。

```bash
python -m app.etl
```

5. 启动 API。

```bash
uvicorn app.main:app --reload
```

本地也可以直接使用下面这条命令启动：

```bash
py -3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Docker

```bash
docker compose up --build
```

容器会先运行 ETL，再启动监听在 `:8000` 的 API 服务。

## 数据文件

- 输入 CSV：`candidate_package/data/sample_asins.csv`
- UPC 测试集：`candidate_package/data/upc_test_cases.json`
- SQLite 数据库：`data/scout.db`

## 接口示例

### 健康检查

```bash
curl http://localhost:8000/health
```

### UPC 查询

```bash
curl "http://localhost:8000/upc?upc=70537500052"
```

### Eligibility 单查

```bash
curl http://localhost:8000/eligibility/B00HEON30Y
```

### Eligibility 批量查询

```bash
curl -X POST http://localhost:8000/eligibility/batch \
  -H "Content-Type: application/json" \
  -d '{"asins": ["B00HEON30Y", "B006JVZXJM", "B000000000"]}'
```

### 自然语言问答

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many ASINs are eligible to resell?"}'
```

示例问题：

- `How many ASINs are eligible to resell?`
- `Show me ASINs with ROI over 25%`
- `Top 5 ROI ASINs that Amazon doesn't dominate`
- `Why is B006JVZXJM not eligible?`
- `Which eligible ASIN is the best opportunity right now?`

### 多轮聊天

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "message": "Show me eligible ASINs"}'

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "message": "Now only those with ROI over 25%"}'

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "message": "Sort by Amazon dominance, lowest first"}'
```

## 项目结构

```text
keepa_scout_challenge/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ config.py
│  ├─ db.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ etl.py
│  ├─ dependencies.py
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ upc.py
│  │  ├─ eligibility.py
│  │  ├─ ask.py
│  │  └─ chat.py
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ keepa_client.py
│  │  ├─ keepa_parser.py
│  │  ├─ eligibility.py
│  │  ├─ roi.py
│  │  ├─ upc_normalizer.py
│  │  ├─ llm_client.py
│  │  ├─ ask_service.py
│  │  ├─ chat_service.py
│  │  └─ sql_guard.py
│  ├─ repositories/
│  │  ├─ __init__.py
│  │  ├─ asin_repository.py
│  │  └─ session_repository.py
│  └─ prompts/
│     ├─ ask_sql.txt
│     ├─ ask_answer.txt
│     ├─ chat_intent.txt
│     └─ chat_answer.txt
├─ candidate_package/
│  ├─ data/
│  ├─ CHALLENGE.md
│  ├─ KEEPA_QUICKSTART.md
│  ├─ env.example
│  ├─ Dockerfile.example
│  └─ docker-compose.example.yml
├─ data/
├─ tests/
│  ├─ test_chat_service.py
│  ├─ test_eligibility.py
│  ├─ test_llm_client.py
│  ├─ test_sql_guard.py
│  └─ test_upc_normalizer.py
├─ Dockerfile
├─ docker-compose.yml
├─ pytest.ini
├─ requirements.txt
├─ README.md
└─ REPORT.md
```

### 文件职责说明

- `app/__init__.py`：标记 `app` 为 Python 包。
- `app/main.py`：应用入口、生命周期管理、首页、健康检查与路由注册。
- `app/config.py`：集中读取环境变量，生成数据库地址与 Keepa / LLM 配置。
- `app/db.py`：创建异步数据库引擎、Session 工厂和初始化函数。
- `app/models.py`：定义 `asins` 与 `chat_sessions` 两张核心表。
- `app/schemas.py`：定义请求体和响应体的 Pydantic 模型。
- `app/etl.py`：从样例 CSV 读取 ASIN，批量请求 Keepa，计算 eligibility 与 ROI 并写库。
- `app/dependencies.py`：集中管理 FastAPI 依赖注入，复用 Keepa、Ask、Chat 服务实例。

### API 层

- `app/api/__init__.py`：标记 `api` 目录为 Python 包。
- `app/api/upc.py`：实现 `/upc`，负责 UPC 输入接收、规整和 Keepa 查询。
- `app/api/eligibility.py`：实现 `/eligibility/{asin}` 和 `/eligibility/batch`。
- `app/api/ask.py`：实现 `/ask`，接收自然语言问题并返回 SQL + 答案。
- `app/api/chat.py`：实现 `/chat`，处理多轮、有状态的对话请求。

### 服务层

- `app/services/__init__.py`：标记 `services` 目录为 Python 包。
- `app/services/keepa_client.py`：封装 Keepa HTTP 请求、批量查询、重试和 key 轮换。
- `app/services/keepa_parser.py`：把 Keepa 原始商品对象解析成内部统一字段。
- `app/services/eligibility.py`：实现 5 条 eligibility 规则和首个失败原因判断。
- `app/services/roi.py`：实现题目指定的 payout / ROI 计算公式。
- `app/services/upc_normalizer.py`：处理 UPC 清洗、补零、ISBN 变体与候选码生成。
- `app/services/llm_client.py`：封装 OpenAI 兼容接口调用、JSON 解析和 Prompt 加载。
- `app/services/ask_service.py`：通过实时 LLM 调用生成 SQL，并对结果做 grounded answer。
- `app/services/chat_service.py`：通过实时 LLM 调用解析多轮意图、更新状态并生成回答。
- `app/services/sql_guard.py`：限制只允许单条安全 `SELECT` SQL。

### 仓储层

- `app/repositories/__init__.py`：标记 `repositories` 目录为 Python 包。
- `app/repositories/asin_repository.py`：封装 ASIN 数据的查询、批量 upsert 和 SQL 执行。
- `app/repositories/session_repository.py`：封装聊天 session 状态的读取与保存。

### Prompt 目录

- `app/prompts/ask_sql.txt`：约束 `/ask` 的 NL -> SQL 输出格式和字段范围。
- `app/prompts/ask_answer.txt`：约束 `/ask` 的 grounded 回答风格。
- `app/prompts/chat_intent.txt`：约束 `/chat` 的多轮意图解析 JSON 格式。
- `app/prompts/chat_answer.txt`：约束 `/chat` 的 grounded 回答风格。

### 题目与样例资料

- `candidate_package/data/`：题目提供的样例输入数据与 UPC 测试用例。
- `candidate_package/CHALLENGE.md`：完整题目说明、交付要求与评分标准。
- `candidate_package/KEEPA_QUICKSTART.md`：Keepa API 起手说明和字段提示。
- `candidate_package/env.example`：环境变量模板，包含 Keepa keys 示例。
- `candidate_package/Dockerfile.example`：官方给出的 Dockerfile 参考。
- `candidate_package/docker-compose.example.yml`：官方给出的 docker-compose 参考。

### 运行时与测试

- `data/`：运行期目录，用于保存 SQLite 数据库文件等本地状态。
- `tests/test_eligibility.py`：验证 eligibility 规则和 ROI 公式。
- `tests/test_chat_service.py`：验证多轮状态更新和 topic reset 行为。
- `tests/test_llm_client.py`：验证 LLM JSON 输出解析能力。
- `tests/test_sql_guard.py`：验证 SQL 安全校验逻辑。
- `tests/test_upc_normalizer.py`：验证 UPC 清洗与候选变体生成逻辑。

### 根目录文件

- `Dockerfile`：容器镜像构建文件，启动时先跑 ETL 再启动 API。
- `docker-compose.yml`：本地容器编排配置，暴露 `8000` 端口并挂载数据目录。
- `pytest.ini`：pytest 配置，约束异步测试的事件循环作用域。
- `requirements.txt`：项目依赖列表。
- `README.md`：项目说明、启动方式、接口示例和目录说明。
- `REPORT.md`：实现取舍、AI 工具说明和后续改进计划。

## 当前说明

- `/ask` 使用两次实时 LLM 调用：先生成 SQL，再基于 SQL 结果生成 grounded answer。
- `/chat` 使用实时 LLM 解析多轮意图与状态更新，再由后端执行 SQL，并通过第二次 LLM 调用生成最终回答。
- SQL 执行前仍会经过 `sql_guard.py` 校验，只允许单条安全 `SELECT`。
- Keepa 字段解析优先使用文档中的顶层字段，并用 `stats.current[]` 作为 Buy Box 和 sales rank 的兜底来源。
