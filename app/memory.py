from __future__ import annotations

import json
import math
import re
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class MemoryItem:
    id: str
    user_id: str
    kind: str
    content: str
    keywords: list[str]
    importance: int
    version: int
    created_at: float
    updated_at: float


class MemoryStore:
    """Demo store: STM is process memory, LTM can persist to a JSON file."""

    def __init__(self, persistence_path: str | Path | None = None) -> None:
        self._lock = threading.RLock()
        self._short_term: dict[str, list[dict[str, str]]] = {}
        self._long_term: dict[str, list[MemoryItem]] = {}
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self._load()

    def append_short_term(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            history = self._short_term.setdefault(session_id, [])
            history.append({"role": role, "content": content, "created_at": time.time()})
            if len(history) > 24:
                self._short_term[session_id] = history[-24:]

    def get_short_term(self, session_id: str, max_messages: int = 16) -> list[dict[str, str]]:
        with self._lock:
            rows = self._short_term.get(session_id, [])
            return [{"role": row["role"], "content": row["content"]} for row in rows[-max_messages:]]

    def write_long_term(
        self, user_id: str, content: str, *, kind: str = "fact", importance: int = 3
    ) -> tuple[MemoryItem, bool]:
        """Write a memory. Returns (item, created). Similar preference updates in place."""

        content = content.strip()
        if not content:
            raise ValueError("memory content cannot be empty")
        now = time.time()
        keywords = extract_keywords(content)
        with self._lock:
            items = self._long_term.setdefault(user_id, [])
            normalized = normalize_text(content)
            for item in items:
                if item.kind == kind and normalize_text(item.content) == normalized:
                    item.updated_at = now
                    self._save()
                    return item, False

                if kind == "preference" and item.kind == "preference":
                    overlap = len(set(item.keywords) & set(keywords))
                    if overlap >= max(1, min(2, len(keywords))):
                        item.content = content
                        item.keywords = keywords
                        item.importance = max(item.importance, importance)
                        item.version += 1
                        item.updated_at = now
                        self._save()
                        return item, False

            item = MemoryItem(
                id=f"mem_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                kind=kind,
                content=content,
                keywords=keywords,
                importance=importance,
                version=1,
                created_at=now,
                updated_at=now,
            )
            items.append(item)
            self._save()
            return item, True

    def search_long_term(self, user_id: str, query: str, top_k: int = 3) -> list[MemoryItem]:
        query_keywords = set(extract_keywords(query))
        now = time.time()
        with self._lock:
            items = list(self._long_term.get(user_id, []))

        scored: list[tuple[float, MemoryItem]] = []
        for item in items:
            overlap = len(query_keywords & set(item.keywords))
            contains = normalize_text(query) in normalize_text(item.content)
            age_days = max((now - item.updated_at) / 86400, 0)
            recency = 1.0 / (1.0 + math.log1p(age_days))
            score = overlap * 3.0 + (5.0 if contains else 0.0)
            score += item.importance * 0.7 + recency * 0.5
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda pair: (-pair[0], -pair[1].updated_at), reverse=False)
        return [item for _, item in scored[:top_k]]

    def list_long_term(self, user_id: str) -> list[MemoryItem]:
        with self._lock:
            return list(self._long_term.get(user_id, []))

    def _load(self) -> None:
        if not self.persistence_path or not self.persistence_path.exists():
            return
        raw = json.loads(self.persistence_path.read_text(encoding="utf-8"))
        with self._lock:
            for row in raw.get("long_term", []):
                item = MemoryItem(**row)
                self._long_term.setdefault(item.user_id, []).append(item)

    def _save(self) -> None:
        if not self.persistence_path:
            return
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            rows = [asdict(item) for items in self._long_term.values() for item in items]
        self.persistence_path.write_text(
            json.dumps({"long_term": rows}, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def extract_keywords(text: str) -> list[str]:
    normalized = normalize_text(text)
    words = re.findall(r"[a-z0-9]+", normalized)
    chinese_runs = re.findall(r"[\u4e00-\u9fff]+", normalized)
    bigrams: list[str] = []
    for run in chinese_runs:
        bigrams.extend(run[i : i + 2] for i in range(max(len(run) - 1, 0)))
    return dedupe(words + bigrams)


def dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
