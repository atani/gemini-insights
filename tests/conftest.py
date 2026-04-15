"""Shared pytest fixtures — build a fake ~/.gemini/ tree for tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _session(session_id: str, project_hash: str, messages: list[dict]) -> dict:
    return {
        "sessionId": session_id,
        "projectHash": project_hash,
        "startTime": "2026-04-01T10:00:00.000Z",
        "lastUpdated": "2026-04-01T10:30:00.000Z",
        "messages": messages,
    }


@pytest.fixture
def fake_gemini_dir(tmp_path: Path) -> Path:
    gemini = tmp_path / ".gemini"
    gemini.mkdir()

    project_path = "/fake/workspace/demo-project"
    project_hash = hashlib.sha256(project_path.encode()).hexdigest()
    (gemini / "projects.json").write_text(
        json.dumps({"projects": {project_path: "demo-project"}}),
        encoding="utf-8",
    )

    chats_dir = gemini / "tmp" / project_hash / "chats"
    chats_dir.mkdir(parents=True)

    session_1 = _session(
        "s-1",
        project_hash,
        [
            {
                "id": "m1",
                "timestamp": "2026-04-01T10:00:00.000Z",
                "type": "user",
                "content": "Investigate the <script>alert(1)</script> bug",
            },
            {
                "id": "m2",
                "timestamp": "2026-04-01T10:00:05.000Z",
                "type": "gemini",
                "content": "",
                "model": "gemini-2.5-pro",
                "toolCalls": [
                    {"name": "read_file", "args": {"file_path": "app/main.py"}, "status": "success"},
                    {
                        "name": "read_file",
                        "args": {"file_path": "missing.py"},
                        "status": "error",
                        "resultDisplay": "File not found: missing.py",
                    },
                ],
            },
        ],
    )
    (chats_dir / "session-2026-04-01T10-00-s-1.json").write_text(json.dumps(session_1), encoding="utf-8")

    session_2 = _session(
        "s-2",
        project_hash,
        [
            {
                "id": "m1",
                "timestamp": "2026-04-01T11:00:00.000Z",
                "type": "user",
                "content": [{"text": "What does this project do?"}],
            },
            {
                "id": "m2",
                "timestamp": "2026-04-01T11:00:02.000Z",
                "type": "gemini",
                "model": "gemini-2.5-flash",
                "toolCalls": [],
            },
        ],
    )
    (chats_dir / "session-2026-04-01T11-00-s-2.json").write_text(json.dumps(session_2), encoding="utf-8")

    return gemini
