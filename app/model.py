from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator


class MockStreamingModel:
    """Vendor-neutral streaming model used by the offline API demo."""

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        reply = self._compose_reply(messages)
        await asyncio.sleep(0.012)
        start = 0
        while start < len(reply):
            end = min(start + 5, len(reply))
            yield reply[start:end]
            start = end
            await asyncio.sleep(0.006)

    def _compose_reply(self, messages: list[dict[str, str]]) -> str:
        user_message = next(
            (row["content"] for row in reversed(messages) if row["role"] == "user"), ""
        )
        observation = next(
            (row["content"] for row in reversed(messages) if row["role"] == "tool"), ""
        )
        memory_context = next(
            (
                row["content"]
                for row in messages
                if row["role"] == "system" and "长期记忆" in row["content"]
            ),
            "",
        )

        if "TOOL_RESULT:" in observation and "get_current_time" in observation:
            import json

            raw = observation.split("TOOL_RESULT:", 1)[1].strip()
            result = json.loads(raw)
            return (
                f"当前时间是{result['display']}，{result['weekday']}。"
                "这个时间来自时间工具，不是我的猜测。若有后续安排，我可以继续帮你拆解下一步。"
            )

        if "TOOL_RESULT:" in observation and "save_memory" in observation:
            import json

            raw = observation.split("TOOL_RESULT:", 1)[1].strip()
            result = json.loads(raw)
            action = "新增" if result["created"] else "更新"
            return (
                f"我已{action}这条长期记忆：{result['content']}。"
                "后续对话中我会优先使用它，但不会让它覆盖我作为阿澄的基本设定。"
            )

        if memory_context:
            memory_text = memory_context.split("：", 1)[-1].split("。", 1)[0]
            return (
                f"我理解你的输入：{user_message}。"
                f"结合我记住的信息，{memory_text}。"
                "我会按这个背景给出冷静、可靠的建议；如果记忆有变化，你可以直接告诉我。"
            )

        return (
            f"我理解你的输入：{user_message}。"
            "我会保持冷静、克制的陪伴方式，先确认事实，再给下一步建议。"
        )
