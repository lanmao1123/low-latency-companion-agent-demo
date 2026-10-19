from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前时间。当用户询问现在时间、日期，或回答需要时间事实时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA 时区，Demo 固定使用 Asia/Shanghai。",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "保存用户的稳定偏好、重要事件或明确要求记住的信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "kind": {"type": "string", "enum": ["preference", "event", "fact"]},
                    "importance": {"type": "integer", "minimum": 1, "maximum": 5},
                },
                "required": ["content", "kind", "importance"],
            },
        },
    },
]


@dataclass
class PlannedTool:
    name: str
    arguments: dict[str, Any]
    reason: str


class ToolPlanner:
    """Deterministic planner for the offline demo.

    Production replaces this with model-native tool calling. Keeping the planner
    behind this interface makes the harness independent of a model vendor.
    """

    def plan(self, query: str) -> PlannedTool | None:
        text = query.strip().lower()
        if any(word in text for word in ("几点", "现在时间", "当前时间", "今天日期", "今天几号", "what time")):
            return PlannedTool(
                name="get_current_time",
                arguments={"timezone": "Asia/Shanghai"},
                reason="用户询问客观时间事实，需要工具提供，不能让模型猜测。",
            )

        remember_match = re.search(r"(?:请?记住|帮我记住|以后记住)[，,：:\s]*(.+)", query)
        if remember_match:
            return PlannedTool(
                name="save_memory",
                arguments={
                    "content": remember_match.group(1).strip(),
                    "kind": "preference",
                    "importance": 4,
                },
                reason="用户显式要求长期记住信息。",
            )
        return None


class ToolExecutor:
    def __init__(self, memory_store) -> None:
        self.memory_store = memory_store

    def execute(self, planned: PlannedTool, user_id: str) -> dict[str, Any]:
        if planned.name == "get_current_time":
            now = datetime.now().astimezone()
            return {
                "timezone": "Asia/Shanghai",
                "iso8601": now.isoformat(timespec="seconds"),
                "display": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
            }

        if planned.name == "save_memory":
            content = str(planned.arguments.get("content", "")).strip()
            if not content:
                raise ValueError("content is empty")
            kind = str(planned.arguments.get("kind", "fact"))
            importance = int(planned.arguments.get("importance", 3))
            item, created = self.memory_store.write_long_term(
                user_id, content, kind=kind, importance=importance
            )
            return {
                "memory_id": item.id,
                "created": created,
                "version": item.version,
                "content": item.content,
            }

        raise KeyError(f"unknown tool: {planned.name}")
