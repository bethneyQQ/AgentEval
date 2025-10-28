# Agent Evaluation System - 数据库设计

**版本**: 1.0
**日期**: 2025-01-28
**数据库**: PostgreSQL 14+ with TimescaleDB 2.10+

---

## 📋 概述

本文档详细定义了 Agent Evaluation System 的数据库 Schema，包括：

1. **PostgreSQL + TimescaleDB**：时序数据（Traces, Spans, Metrics）
2. **Redis**：缓存、实时指标、会话映射
3. **S3/MinIO**：对象存储（归档数据、报告文件）

---

## 🗄️ PostgreSQL Schema

### 1. Traces 表（主表）

```sql
-- traces 表：存储完整的追踪记录
CREATE TABLE traces (
    -- 主键
    trace_id VARCHAR(32) PRIMARY KEY,

    -- 基本信息
    service_name VARCHAR(100) NOT NULL DEFAULT 'agenteval',
    agent_type VARCHAR(50),              -- ClaudeCodeAgent, DevAgent 等
    model VARCHAR(100),                   -- gpt-4-turbo, claude-3.5-sonnet 等

    -- 用户与项目
    user_id VARCHAR(100),
    project_id VARCHAR(100),
    task_id VARCHAR(100),

    -- 时间
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_ms FLOAT,

    -- 聚合统计
    total_spans INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,

    -- Token 与成本
    total_prompt_tokens INTEGER DEFAULT 0,
    total_completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost FLOAT DEFAULT 0.0,

    -- 状态
    status VARCHAR(20) CHECK (status IN ('running', 'completed', 'error', 'timeout')),
    termination_reason VARCHAR(50),      -- success, max_turns, timeout, error 等

    -- 元数据（JSONB 灵活存储）
    metadata JSONB,

    -- 审计字段
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 转换为 TimescaleDB 时序表（按 start_time 分区，每天一个 chunk）
SELECT create_hypertable('traces', 'start_time',
                        chunk_time_interval => INTERVAL '1 day');

-- 索引
CREATE INDEX idx_traces_user_id ON traces(user_id, start_time DESC);
CREATE INDEX idx_traces_agent_type ON traces(agent_type, start_time DESC);
CREATE INDEX idx_traces_model ON traces(model, start_time DESC);
CREATE INDEX idx_traces_status ON traces(status);
CREATE INDEX idx_traces_project_id ON traces(project_id, start_time DESC);
CREATE INDEX idx_traces_metadata ON traces USING GIN(metadata);

-- 数据保留策略：自动删除 7 天前的数据
SELECT add_retention_policy('traces', INTERVAL '7 days');
```

### 2. Spans 表（子表）

```sql
-- spans 表：存储 Trace 中的每个 Span
CREATE TABLE spans (
    -- 主键
    span_id VARCHAR(16) PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    parent_span_id VARCHAR(16),

    -- 基本信息
    name VARCHAR(200) NOT NULL,          -- agent.run, tool.call, llm.generate 等
    kind VARCHAR(20),                     -- internal, server, client, producer, consumer
    status VARCHAR(20),                   -- ok, error, unset

    -- 时间
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_ms FLOAT,

    -- 属性（JSONB 存储 OpenTelemetry 属性）
    attributes JSONB,
    /*
    示例 attributes:
    {
      "agent.type": "ClaudeCodeAgent",
      "llm.model": "gpt-4-turbo",
      "llm.prompt_tokens": 1500,
      "llm.completion_tokens": 500,
      "llm.cost": 0.025,
      "tool.name": "Read",
      "tool.success": true
    }
    */

    -- 事件（Span 内的关键事件）
    events JSONB,
    /*
    示例 events:
    [
      {
        "name": "thinking_start",
        "timestamp": 1704067200.123,
        "attributes": {"content_length": 256}
      }
    ]
    */

    -- 资源信息
    resource JSONB,

    -- 审计
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 转换为时序表
SELECT create_hypertable('spans', 'start_time',
                        chunk_time_interval => INTERVAL '1 day');

-- 索引
CREATE INDEX idx_spans_trace_id ON spans(trace_id, start_time);
CREATE INDEX idx_spans_parent_span_id ON spans(parent_span_id);
CREATE INDEX idx_spans_name ON spans(name, start_time DESC);
CREATE INDEX idx_spans_kind ON spans(kind);
CREATE INDEX idx_spans_status ON spans(status);
CREATE INDEX idx_spans_attributes ON spans USING GIN(attributes jsonb_path_ops);

-- GIN 索引优化：可快速查询 attributes 中的字段
-- 示例查询：WHERE attributes @> '{"llm.model": "gpt-4-turbo"}'

-- 保留策略
SELECT add_retention_policy('spans', INTERVAL '7 days');
```

### 3. Realtime Metrics 表（实时指标）

```sql
-- realtime_metrics 表：存储预聚合的实时指标
CREATE TABLE realtime_metrics (
    metric_id SERIAL PRIMARY KEY,

    -- 指标名称
    metric_name VARCHAR(100) NOT NULL,   -- success_rate, avg_duration, p95_latency 等
    metric_type VARCHAR(20),              -- counter, gauge, histogram

    -- 维度（JSONB 存储多维度分组）
    dimensions JSONB,
    /*
    示例 dimensions:
    {
      "model": "gpt-4-turbo",
      "agent_type": "ClaudeCodeAgent",
      "task_type": "coding"
    }
    */

    -- 指标值
    value FLOAT,
    count INTEGER,                        -- 样本数量
    sum FLOAT,                            -- 累加值（用于计算平均）
    min FLOAT,
    max FLOAT,

    -- 时间窗口
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    window_size_sec INTEGER,              -- 60, 300, 3600, 86400 (1m, 5m, 1h, 1d)

    -- 审计
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 转换为时序表
SELECT create_hypertable('realtime_metrics', 'window_start',
                        chunk_time_interval => INTERVAL '1 hour');

-- 索引
CREATE INDEX idx_realtime_metrics_name ON realtime_metrics(metric_name, window_start DESC);
CREATE INDEX idx_realtime_metrics_dimensions ON realtime_metrics USING GIN(dimensions jsonb_path_ops);
CREATE INDEX idx_realtime_metrics_window ON realtime_metrics(window_start, window_end);

-- 保留策略：保留 30 天
SELECT add_retention_policy('realtime_metrics', INTERVAL '30 days');
```

### 4. Continuous Aggregates（连续聚合视图）

TimescaleDB 的连续聚合功能，自动预计算聚合数据。

```sql
-- 按小时聚合 Agent 性能指标
CREATE MATERIALIZED VIEW hourly_agent_metrics
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', start_time) AS hour,
    agent_type,
    model,

    -- 数量统计
    COUNT(*) as total_traces,
    COUNT(*) FILTER (WHERE status = 'completed') as success_count,
    COUNT(*) FILTER (WHERE status = 'error') as error_count,

    -- 持续时间统计
    AVG(duration_ms) as avg_duration_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) as p50_duration,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99_duration,
    MIN(duration_ms) as min_duration,
    MAX(duration_ms) as max_duration,

    -- Token 与成本
    SUM(total_tokens) as total_tokens,
    AVG(total_tokens) as avg_tokens_per_trace,
    SUM(total_cost) as total_cost,
    AVG(total_cost) as avg_cost_per_trace,

    -- 工具调用
    AVG(tool_call_count) as avg_tool_calls

FROM traces
GROUP BY hour, agent_type, model;

-- 刷新策略：每小时刷新一次
SELECT add_continuous_aggregate_policy('hourly_agent_metrics',
    start_offset => INTERVAL '3 hours',   -- 从 3 小时前开始
    end_offset => INTERVAL '1 hour',      -- 到 1 小时前结束
    schedule_interval => INTERVAL '1 hour' -- 每小时执行
);

-- 按天聚合（用于长期趋势分析）
CREATE MATERIALIZED VIEW daily_agent_metrics
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', start_time) AS day,
    agent_type,
    model,

    COUNT(*) as total_traces,
    COUNT(*) FILTER (WHERE status = 'completed') as success_count,
    (COUNT(*) FILTER (WHERE status = 'completed'))::FLOAT / COUNT(*) as success_rate,

    AVG(duration_ms) as avg_duration_ms,
    SUM(total_cost) as total_cost,
    SUM(total_tokens) as total_tokens

FROM traces
GROUP BY day, agent_type, model;

SELECT add_continuous_aggregate_policy('daily_agent_metrics',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);
```

### 5. Session Mappings 表（会话映射）

```sql
-- session_mappings 表：映射 adeworker 会话到评估 Trace
CREATE TABLE session_mappings (
    mapping_id SERIAL PRIMARY KEY,

    -- 会话 ID
    user_session_id VARCHAR(100) NOT NULL UNIQUE,
    agent_session_id VARCHAR(100),        -- Claude Code 会话 ID
    trace_id VARCHAR(32) REFERENCES traces(trace_id),

    -- 用户与项目
    user_id VARCHAR(100),
    project_id VARCHAR(100),
    task_id VARCHAR(100),

    -- Agent 信息
    agent_type VARCHAR(50),
    workspace_path VARCHAR(500),

    -- 元数据
    metadata JSONB,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_session_user_session_id ON session_mappings(user_session_id);
CREATE INDEX idx_session_trace_id ON session_mappings(trace_id);
CREATE INDEX idx_session_user_id ON session_mappings(user_id, created_at DESC);
```

### 6. Alerts 表（告警记录）

```sql
-- alerts 表：存储告警历史
CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 规则信息
    rule_name VARCHAR(100) NOT NULL,
    rule_version INTEGER,

    -- 严重程度
    severity VARCHAR(20) CHECK (severity IN ('info', 'warning', 'critical')),

    -- 消息
    message TEXT NOT NULL,
    template_data JSONB,                  -- 模板渲染使用的数据

    -- 维度
    dimensions JSONB,

    -- 状态
    status VARCHAR(20) DEFAULT 'triggered', -- triggered, acknowledged, resolved
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,

    -- 通知状态
    notifications_sent JSONB,
    /*
    示例:
    [
      {"channel": "slack", "sent_at": "2025-01-28T10:00:00Z", "success": true},
      {"channel": "email", "sent_at": "2025-01-28T10:00:05Z", "success": false, "error": "..."}
    ]
    */

    -- 时间
    triggered_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 转换为时序表
SELECT create_hypertable('alerts', 'triggered_at',
                        chunk_time_interval => INTERVAL '1 day');

-- 索引
CREATE INDEX idx_alerts_rule_name ON alerts(rule_name, triggered_at DESC);
CREATE INDEX idx_alerts_severity ON alerts(severity, triggered_at DESC);
CREATE INDEX idx_alerts_status ON alerts(status);

-- 保留策略：保留 90 天
SELECT add_retention_policy('alerts', INTERVAL '90 days');
```

---

## 🔴 Redis Data Structures

### 1. 实时指标缓存

```
# Key 格式: metrics:{window}:{timestamp}:{hash(dimensions)}
# 类型: Hash

Key: metrics:1m:1704067200:a3f2e8c1
Hash:
  trace_count: 125
  success_count: 112
  error_count: 13
  total_duration: 156780.5  # 毫秒
  total_tokens: 245000
  total_cost: 12.35

# TTL: 2 * window_size (例如 1m 窗口保留 2 分钟)
```

### 2. 百分位数数据

```
# Key 格式: metrics:{window}:{timestamp}:{hash}:durations
# 类型: List

Key: metrics:1m:1704067200:a3f2e8c1:durations
List: [1234.5, 2345.6, 3456.7, ...]  # 持续时间列表

# TTL: 2 * window_size
```

### 3. 会话映射缓存

```
# Key 格式: session:{user_session_id}
# 类型: Hash

Key: session:usr_123_sess_456
Hash:
  trace_id: abc123def456
  agent_session_id: cc_sess_789
  user_id: user_123
  agent_type: ClaudeCodeAgent
  created_at: 1704067200

# TTL: 24 小时
```

### 4. 事件队列（Redis Stream）

```
# Stream Key: agenteval:events
# 消费组: trace-ingestion-workers

XADD agenteval:events * \
  trace_id abc123 \
  event_type tool_call \
  timestamp 1704067200.123 \
  data '{"tool_name": "Read", "tool_input": "..."}'

# Consumer 读取
XREADGROUP GROUP trace-ingestion-workers consumer-1 \
  COUNT 100 BLOCK 5000 STREAMS agenteval:events >
```

### 5. 去重缓存（告警降噪）

```
# Key 格式: alert:dedup:{grouping_key}
# 类型: String
# Value: 最后一次告警时间戳

Key: alert:dedup:low-success-rate-gpt4-coding
Value: 1704067200

# TTL: alert window (如 300 秒)
```

---

## 📦 S3/MinIO Object Storage

### 目录结构

```
s3://agenteval-data/
├── archives/                    # 归档数据
│   ├── traces/
│   │   ├── 2025-01/
│   │   │   ├── 01.parquet      # 每天一个 Parquet 文件
│   │   │   ├── 02.parquet
│   │   │   └── ...
│   │   └── 2025-02/
│   └── spans/
│       └── 2025-01/
│           └── ...
│
├── reports/                     # 评估报告
│   ├── offline/
│   │   ├── swe-bench-lite-2025-01-28.html
│   │   ├── humaneval-comparison.pdf
│   │   └── ...
│   └── custom/
│       └── ...
│
├── exports/                     # 导出数据
│   ├── csv/
│   │   ├── eval_results_2025-01.csv
│   │   └── ...
│   └── json/
│       └── ...
│
└── backups/                     # 数据库备份
    ├── postgres/
    │   ├── 2025-01-28.dump
    │   └── ...
    └── redis/
        └── ...
```

### Parquet Schema（归档格式）

```python
# traces.parquet schema
{
    "trace_id": "string",
    "agent_type": "string",
    "model": "string",
    "user_id": "string",
    "start_time": "timestamp[ms]",
    "end_time": "timestamp[ms]",
    "duration_ms": "double",
    "total_tokens": "int64",
    "total_cost": "double",
    "status": "string",
    "metadata": "string"  # JSON encoded
}

# 优点：
# 1. 列式存储，压缩率高（通常 10:1）
# 2. 支持谓词下推，查询快
# 3. 生态兼容性好（Spark, Athena, BigQuery）
```

---

## 🔧 Migration Scripts

### 001_initial_schema.sql

```sql
-- 初始化 Schema
BEGIN;

-- 启用 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 创建 traces 表
CREATE TABLE traces (...);  -- 如上定义

-- 转换为时序表
SELECT create_hypertable('traces', 'start_time', chunk_time_interval => INTERVAL '1 day');

-- 创建索引
CREATE INDEX idx_traces_user_id ON traces(user_id, start_time DESC);
-- ...

COMMIT;
```

### 002_add_continuous_aggregates.sql

```sql
-- 添加连续聚合视图
CREATE MATERIALIZED VIEW hourly_agent_metrics
WITH (timescaledb.continuous) AS
SELECT ...;

SELECT add_continuous_aggregate_policy(...);
```

### Migration 管理（使用 Alembic）

```bash
# 安装
pip install alembic

# 初始化
alembic init migrations

# 创建 migration
alembic revision -m "add alerts table"

# 执行 migration
alembic upgrade head

# 回滚
alembic downgrade -1
```

---

## 📊 查询示例

### 1. 查询某用户最近的 Traces

```sql
SELECT
    trace_id,
    agent_type,
    model,
    start_time,
    duration_ms,
    total_cost,
    status
FROM traces
WHERE user_id = 'user_123'
  AND start_time >= NOW() - INTERVAL '7 days'
ORDER BY start_time DESC
LIMIT 20;
```

### 2. 查询某模型的成功率（近 24 小时）

```sql
SELECT
    hour,
    model,
    total_traces,
    success_count,
    (success_count::FLOAT / total_traces) as success_rate,
    avg_duration_ms,
    total_cost
FROM hourly_agent_metrics
WHERE hour >= NOW() - INTERVAL '24 hours'
  AND model = 'gpt-4-turbo'
ORDER BY hour DESC;
```

### 3. 查询某 Trace 的完整 Span 树

```sql
WITH RECURSIVE span_tree AS (
    -- 根 Span
    SELECT
        s.*,
        0 as level,
        ARRAY[s.span_id] as path
    FROM spans s
    WHERE s.trace_id = 'abc123'
      AND s.parent_span_id IS NULL

    UNION ALL

    -- 递归查找子 Span
    SELECT
        s.*,
        st.level + 1,
        st.path || s.span_id
    FROM spans s
    INNER JOIN span_tree st ON s.parent_span_id = st.span_id
)
SELECT
    REPEAT('  ', level) || name as span_name,
    duration_ms,
    status,
    attributes
FROM span_tree
ORDER BY path;
```

### 4. 查询最消耗成本的任务（Top 10）

```sql
SELECT
    trace_id,
    task_id,
    model,
    total_cost,
    total_tokens,
    duration_ms
FROM traces
WHERE start_time >= NOW() - INTERVAL '7 days'
ORDER BY total_cost DESC
LIMIT 10;
```

### 5. 查询某工具的使用频率

```sql
SELECT
    attributes->>'tool.name' as tool_name,
    COUNT(*) as call_count,
    AVG(duration_ms) as avg_duration_ms,
    COUNT(*) FILTER (WHERE status = 'error') as error_count
FROM spans
WHERE name = 'tool.call'
  AND start_time >= NOW() - INTERVAL '24 hours'
GROUP BY attributes->>'tool.name'
ORDER BY call_count DESC;
```

---

## 🔒 安全与权限

### 数据库用户角色

```sql
-- 只读用户（Dashboard、查询）
CREATE ROLE agenteval_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agenteval_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO agenteval_readonly;

-- 读写用户（API、后台任务）
CREATE ROLE agenteval_readwrite;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO agenteval_readwrite;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO agenteval_readwrite;

-- 创建具体用户
CREATE USER dashboard_user WITH PASSWORD 'xxx' IN ROLE agenteval_readonly;
CREATE USER api_user WITH PASSWORD 'xxx' IN ROLE agenteval_readwrite;
```

### 敏感数据加密

```sql
-- 使用 pgcrypto 扩展加密敏感字段
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 加密 API Key
INSERT INTO credentials (service, api_key_encrypted)
VALUES ('openai', pgp_sym_encrypt('sk-xxx', 'encryption-key'));

-- 解密
SELECT pgp_sym_decrypt(api_key_encrypted, 'encryption-key')
FROM credentials WHERE service = 'openai';
```

---

## ⚡ 性能优化

### 1. 分区策略

```sql
-- TimescaleDB 自动按时间分区
-- 手动调整 chunk 大小（默认 7 天 → 改为 1 天）
SELECT set_chunk_time_interval('traces', INTERVAL '1 day');
```

### 2. 索引优化

```sql
-- 查看索引使用情况
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,  -- 索引扫描次数
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 删除未使用的索引
DROP INDEX IF EXISTS idx_unused_index;
```

### 3. 查询优化

```sql
-- 使用 EXPLAIN ANALYZE 分析查询
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM traces
WHERE user_id = 'user_123'
  AND start_time >= NOW() - INTERVAL '7 days';

-- 优化建议：
-- 1. 确保有复合索引 (user_id, start_time)
-- 2. 使用时间范围限制（利用时序分区）
-- 3. 避免 SELECT *，只查询需要的列
```

### 4. 连接池

```python
# 使用 PgBouncer 连接池
# pgbouncer.ini
[databases]
agenteval = host=localhost dbname=agenteval

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

---

## 📈 监控指标

### 关键数据库指标

```sql
-- 数据库大小
SELECT pg_size_pretty(pg_database_size('agenteval'));

-- 表大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 缓存命中率（应 >95%）
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;

-- 活跃连接数
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
```

---

**相关文档**：
- [总体架构](./00_architecture_overview.md)
- [Milestone 3 设计](./03_milestone3_online_tracing.md)
- [实施计划](./06_implementation_timeline.md)
