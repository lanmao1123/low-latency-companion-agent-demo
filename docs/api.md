# API 说明

## 服务地址

```text
http://127.0.0.1:8765
```

## 健康检查

```bash
curl -i http://127.0.0.1:8765/health
```

返回：

```json
{
  "status": "ok",
  "service": "companion-agent-demo"
}
```

## 工具列表

```bash
curl http://127.0.0.1:8765/v1/tools
```

## 流式对话

```bash
curl -N -X POST http://127.0.0.1:8765/v1/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "现在几点了？",
    "user_id": "demo-user",
    "session_id": "demo-session",
    "memory_top_k": 3
  }'
```

### 请求字段

| 字段 | 必填 | 类型 | 说明 |
|---|---:|---|---|
| `query` | 是 | string | 用户文本输入 |
| `user_id` | 否 | string | 长期记忆归属用户 |
| `session_id` | 否 | string | 当前会话标识 |
| `stream` | 否 | boolean | 当前只支持 `true` |
| `memory_top_k` | 否 | integer | 长期记忆召回条数 |

### SSE 事件

| 事件 | 说明 |
|---|---|
| `meta` | 连接建立，返回 `turn_id`、角色 ID、会话 ID |
| `tool_call` | 工具调用意图、工具名、参数 |
| `tool_result` | 工具返回结果 |
| `tool_error` | 工具失败与降级说明 |
| `token` | 一段自然语言回复 |
| `memory_updated` | 本轮写入或更新长期记忆 |
| `done` | 本轮结束，返回耗时、TTFT 和统计 |
| `error` | 系统错误 |

### 示例事件流

```text
event: meta
data: {"type":"meta","turn_id":"turn_xxx","role_id":"calm_companion_v1","session_id":"demo-session","stream":true}

event: tool_call
data: {"type":"tool_call","tool_call_id":"call_xxx","name":"get_current_time","arguments":{"timezone":"Asia/Shanghai"},"intent":"用户询问客观时间事实。"}

event: tool_result
data: {"type":"tool_result","name":"get_current_time","result":{"timezone":"Asia/Shanghai","iso8601":"2026-10-19T09:00:45+08:00","display":"2026-10-19 09:00:45 CST","weekday":"周一"}}

event: token
data: {"type":"token","value":"当前时间是"}

event: done
data: {"type":"done","turn_id":"turn_xxx","elapsed_ms":109.32,"ttft_ms":14.0,"tool_called":true,"retrieved_memory_count":0}
```
