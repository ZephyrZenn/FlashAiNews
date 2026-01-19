import hashlib
import json
import time
from typing import Any, Callable


class ArtifactStore:
    """Boost 专用的轻量级 Artifact 存储。

    使用外部提供的 state getter，避免影响旧 workflow。
    提供 put/get/preview/sha 生成，返回 artifact_id。
    """

    def __init__(self, state_getter: Callable[[], dict]):
        self._state_getter = state_getter
        self._counter = 0

    def _state(self) -> dict:
        state = self._state_getter()
        if state is None:
            raise RuntimeError("ArtifactStore requires an active state")
        if "artifacts" not in state:
            state["artifacts"] = {}
        return state

    def _next_counter(self) -> int:
        self._counter += 1
        return self._counter

    def _calc_sha(self, content: Any) -> str:
        try:
            raw = (
                content
                if isinstance(content, (bytes, bytearray))
                else json.dumps(content, ensure_ascii=False, default=str)
            )
        except (TypeError, ValueError):
            raw = str(content)
        if not isinstance(raw, (bytes, bytearray)):
            raw = raw.encode("utf-8", errors="ignore")
        return hashlib.sha256(raw).hexdigest()

    def _content_len(self, content: Any) -> int:
        if isinstance(content, str):
            return len(content)
        try:
            return len(json.dumps(content, ensure_ascii=False, default=str))
        except (TypeError, ValueError):
            return len(str(content))

    def _build_preview(self, artifact_type: str, content: Any) -> Any:
        is_review = artifact_type.endswith("review_article")

        if isinstance(content, str):
            # 取头尾片段，避免过长
            head = content[:400]
            tail = content[-200:] if len(content) > 600 else ""
            return {"head": head, "tail": tail} if tail else {"head": head}

        if isinstance(content, dict):
            preview = {}
            if is_review:
                for key in ("status", "score", "overall_comment"):
                    if key in content:
                        preview[key] = content[key]
                if "findings" in content and isinstance(content["findings"], list):
                    preview["findings_preview"] = content["findings"][:3]
                return preview

            return content

        # 其他类型直接字符串化
        return str(content)

    def put(self, artifact_type: str, content: Any, meta: dict | None = None) -> dict:
        state = self._state()
        sha = self._calc_sha(content)
        artifact_id = f"{artifact_type}:{sha[:12]}:{self._next_counter()}"
        stats = {"len": self._content_len(content), "sha256": sha}
        entry = {
            "type": artifact_type,
            "content": content,
            "meta": meta or {},
            "stats": stats,
            "created_at": time.time(),
        }
        state["artifacts"][artifact_id] = entry
        return {
            "artifact_id": artifact_id,
            "type": artifact_type,
            "preview": self._build_preview(artifact_type, content),
            "stats": stats,
        }

    def get(self, artifact_id: str) -> dict | None:
        state = self._state()
        return state.get("artifacts", {}).get(artifact_id)

