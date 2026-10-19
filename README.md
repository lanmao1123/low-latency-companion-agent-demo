# Low-Latency Companion Agent Demo

一个可本地运行的文本对话 Agent API Demo，重点验证长期陪伴场景中的四类基础能力：

- 固定角色与基础角色防护
- 多轮短期记忆
- 可持久化的简单长期记忆
- 工具调用与流式输出

Demo 默认使用本地 `MockStreamingModel`，因此不需要 API Key、不调用外部模型服务，也不会产生模型费用。

## 功能

- `POST /v1/chat/stream`：SSE 流式对话
- 多轮对话：同一 `user_id + session_id` 保留当前会话上下文
- 固定角色：冷静、克制、可靠的“阿澄”
- 短期记忆：最近会话窗口
- 长期记忆：JSON 持久化，支持写入、召回和偏好更新
- 工具调用：
  - `get_current_time`
  - `save_memory`
- SSE 事件：
  - `meta`
  - `tool_call`
  - `tool_result`
  - `tool_error`
  - `token`
  - `memory_updated`
  - `done`
  - `error`
- 用户隔离：相同 `session_id`、不同 `user_id` 不共享记忆

## 快速开始

```bash
cd low-latency-companion-agent-demo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
./run.sh
```

服务地址：

```text
http://127.0.0.1:8765
```

健康检查：

```bash
curl -i http://127.0.0.1:8765/health
```

流式工具调用：

```bash
curl -N -X POST http://127.0.0.1:8765/v1/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"query":"现在几点了？","user_id":"demo-user","session_id":"demo-session"}'
```

长期记忆写入：

```bash
curl -N -X POST http://127.0.0.1:8765/v1/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"query":"记住我喜欢早睡早起","user_id":"demo-user","session_id":"demo-session"}'
```

下一轮召回：

```bash
curl -N -X POST http://127.0.0.1:8765/v1/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"query":"我平时喜欢什么？","user_id":"demo-user","session_id":"demo-session"}'
```

## 验证

```bash
./scripts/verify.sh
```

当前包含 5 个单元测试：

- 流式输出与时间工具调用
- 多轮对话与长期记忆召回
- 角色诱导防护
- 相同 `session_id` 下不同用户隔离
- 偏好冲突更新版本

## 文档

- [架构设计](docs/architecture.md)
- [API 说明](docs/api.md)

## Demo 边界

这个仓库验证的是 Agent 工程编排链路，不声称已完成真实大模型评测：

- 模型层使用 `MockStreamingModel`，便于无 Key 本地复现。
- Demo 的工具选择使用确定性 Planner；生产环境应替换为模型原生 Tool Calling。
- 本地 `ttft_ms` 只代表 Mock 链路，不代表真实模型服务延时。
- 生产环境应将 JSON 长期记忆替换为向量数据库加业务数据库，并补充权限、审计、熔断、压测和线上监控。
