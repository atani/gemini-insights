"""Collect rich stats from `~/.gemini/tmp/<hash>/chats/session-*.json`."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_GEMINI_DIR = Path(os.environ.get("GEMINI_HOME", str(Path.home() / ".gemini")))

EXT_TO_LANG = {
    ".py": "Python",
    ".rb": "Ruby",
    ".go": "Go",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".sh": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".php": "PHP",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++",
    ".scss": "SCSS",
    ".vue": "Vue",
    ".dart": "Dart",
    ".erb": "ERB",
    ".dockerfile": "Docker",
}


@dataclass
class ToolCall:
    name: str
    status: str  # "success" | "error" | ""
    args: dict
    error_message: str = ""


@dataclass
class Session:
    session_id: str
    project_hash: str
    project_name: str
    start_time: datetime | None
    last_updated: datetime | None
    models_used: set[str] = field(default_factory=set)
    user_messages: list[tuple[datetime | None, str]] = field(default_factory=list)
    gemini_messages: int = 0
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def duration_minutes(self) -> float:
        if self.start_time and self.last_updated:
            return max(0.0, (self.last_updated - self.start_time).total_seconds() / 60.0)
        return 0.0

    @property
    def total_messages(self) -> int:
        return len(self.user_messages) + self.gemini_messages

    @property
    def first_user_prompt(self) -> str:
        for _, text in self.user_messages:
            if text:
                return text.strip().splitlines()[0][:200]
        return ""

    @property
    def session_type(self) -> str:
        m = len(self.user_messages)
        if m <= 1:
            return "single_task"
        if m <= 5:
            return "multi_task"
        if m <= 20:
            return "iterative_refinement"
        return "exploration"


def parse_ts(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return ""


def load_project_hash_map(gemini_dir: Path) -> dict[str, str]:
    """Map projectHash (sha256 of absolute path) -> friendly project name.

    Gemini CLI stores projects.json as `{"projects": {path: name}}`, so we
    sha256 each path to get the same hash used for `~/.gemini/tmp/<hash>/`.
    """
    mapping: dict[str, str] = {}
    projects_json = gemini_dir / "projects.json"
    if not projects_json.exists():
        return mapping
    try:
        data = json.loads(projects_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return mapping
    projects = data.get("projects") if isinstance(data, dict) and "projects" in data else data
    if not isinstance(projects, dict):
        return mapping
    for path, name in projects.items():
        if not isinstance(path, str):
            continue
        h = hashlib.sha256(path.encode()).hexdigest()
        if isinstance(name, str) and name:
            mapping.setdefault(h, name)
        else:
            mapping.setdefault(h, Path(path).name)
    return mapping


def parse_session_file(path: Path, project_map: dict[str, str]) -> Session | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    project_hash = data.get("projectHash") or path.parent.parent.name
    name = project_map.get(project_hash) or project_hash[:12]

    s = Session(
        session_id=data.get("sessionId") or path.stem,
        project_hash=project_hash,
        project_name=name,
        start_time=parse_ts(data.get("startTime")),
        last_updated=parse_ts(data.get("lastUpdated")),
    )

    for msg in data.get("messages") or []:
        mtype = msg.get("type")
        ts = parse_ts(msg.get("timestamp"))
        if mtype == "user":
            s.user_messages.append((ts, extract_text(msg.get("content"))))
        elif mtype == "gemini":
            s.gemini_messages += 1
            model = msg.get("model")
            if isinstance(model, str) and model:
                s.models_used.add(model)
            for tc in msg.get("toolCalls") or []:
                status = tc.get("status") or ""
                err = ""
                if status == "error":
                    display = tc.get("resultDisplay")
                    if isinstance(display, str):
                        err = display[:200]
                s.tool_calls.append(
                    ToolCall(
                        name=tc.get("name") or "unknown",
                        status=status,
                        args=tc.get("args") or {},
                        error_message=err,
                    )
                )
    return s


def collect_sessions(gemini_dir: Path) -> list[Session]:
    tmp_dir = gemini_dir / "tmp"
    if not tmp_dir.is_dir():
        return []
    project_map = load_project_hash_map(gemini_dir)
    out: list[Session] = []
    for chat_file in sorted(tmp_dir.glob("*/chats/session-*.json")):
        s = parse_session_file(chat_file, project_map)
        if s:
            out.append(s)
    return out


# ---------------------------------------------------------------------------
# Derived metrics
# ---------------------------------------------------------------------------


def detect_language_from_args(args: dict) -> str | None:
    for key in ("file_path", "absolute_path", "path", "file"):
        v = args.get(key) if isinstance(args, dict) else None
        if isinstance(v, str):
            ext = Path(v).suffix.lower()
            if ext in EXT_TO_LANG:
                return EXT_TO_LANG[ext]
    return None


def categorize_tool_error(msg: str) -> str:
    low = msg.lower()
    if not msg:
        return "Other"
    if "file not found" in low or "no such file" in low or "not a file" in low:
        return "File Not Found"
    if "not in workspace" in low or "outside the allowed workspace" in low:
        return "Path Outside Workspace"
    if "command failed" in low or "exit code" in low or "non-zero" in low:
        return "Command Failed"
    if "could not find" in low or "did not match" in low:
        return "Edit Mismatch"
    if "timeout" in low or "timed out" in low:
        return "Timeout"
    if "permission" in low or "denied" in low:
        return "Permission Denied"
    if "too large" in low:
        return "File Too Large"
    return "Other"


def compute_response_time_buckets(sessions: list[Session]) -> dict[str, int]:
    buckets = {
        "2-10s": 0,
        "10-30s": 0,
        "30s-1m": 0,
        "1-2m": 0,
        "2-5m": 0,
        "5-15m": 0,
        ">15m": 0,
    }
    for s in sessions:
        prev: datetime | None = None
        for ts, _ in s.user_messages:
            if prev and ts:
                delta = (ts - prev).total_seconds()
                if delta < 2:
                    pass
                elif delta < 10:
                    buckets["2-10s"] += 1
                elif delta < 30:
                    buckets["10-30s"] += 1
                elif delta < 60:
                    buckets["30s-1m"] += 1
                elif delta < 120:
                    buckets["1-2m"] += 1
                elif delta < 300:
                    buckets["2-5m"] += 1
                elif delta < 900:
                    buckets["5-15m"] += 1
                else:
                    buckets[">15m"] += 1
            prev = ts
    return buckets


def compute_overlap(sessions: list[Session]) -> dict[str, int]:
    intervals = [
        (s.start_time, s.last_updated, s.session_id)
        for s in sessions
        if s.start_time and s.last_updated and s.last_updated > s.start_time
    ]
    intervals.sort(key=lambda x: x[0])
    overlap_events = 0
    involved: set[str] = set()
    # Intervals sorted by start_time; when intervals[j].start >= end[i] no later
    # j can overlap intervals[i], so we break the inner loop early.
    for i, (_, end_i, sid_i) in enumerate(intervals):
        for j in range(i + 1, len(intervals)):
            start_j, _, sid_j = intervals[j]
            if start_j >= end_i:
                break
            overlap_events += 1
            involved.add(sid_i)
            involved.add(sid_j)
    total_messages = sum(s.total_messages for s in sessions)
    msgs_in_overlap = sum(s.total_messages for s in sessions if s.session_id in involved)
    pct = round(100 * msgs_in_overlap / total_messages) if total_messages else 0
    return {
        "overlap_events": overlap_events,
        "sessions_involved": len(involved),
        "pct_messages": pct,
    }


def compute_hour_histogram(sessions: list[Session]) -> dict[int, int]:
    counter: Counter[int] = Counter()
    for s in sessions:
        for ts, _ in s.user_messages:
            if ts:
                counter[ts.astimezone().hour] += 1
    return {h: counter.get(h, 0) for h in range(24)}


def aggregate(sessions: list[Session]) -> dict:
    totals_user_msgs = sum(len(s.user_messages) for s in sessions)
    totals_gemini_msgs = sum(s.gemini_messages for s in sessions)
    tools: Counter[str] = Counter()
    tool_errors: Counter[str] = Counter()
    error_categories: Counter[str] = Counter()
    models: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    session_types: Counter[str] = Counter()
    per_day: Counter[str] = Counter()
    per_project: dict[str, dict] = defaultdict(
        lambda: {
            "sessions": 0,
            "user_messages": 0,
            "gemini_messages": 0,
            "tool_calls": 0,
            "errors": 0,
            "last_activity": None,
        }
    )

    for s in sessions:
        for m in s.models_used:
            models[m] += 1
        if s.start_time:
            per_day[s.start_time.date().isoformat()] += 1
        session_types[s.session_type] += 1
        for tc in s.tool_calls:
            tools[tc.name] += 1
            if tc.status == "error":
                tool_errors[tc.name] += 1
                error_categories[categorize_tool_error(tc.error_message)] += 1
            lang = detect_language_from_args(tc.args)
            if lang:
                languages[lang] += 1
        p = per_project[s.project_name]
        p["sessions"] += 1
        p["user_messages"] += len(s.user_messages)
        p["gemini_messages"] += s.gemini_messages
        p["tool_calls"] += len(s.tool_calls)
        p["errors"] += sum(1 for tc in s.tool_calls if tc.status == "error")
        if s.last_updated:
            cur = p["last_activity"]
            if cur is None or s.last_updated > cur:
                p["last_activity"] = s.last_updated

    starts = [s.start_time for s in sessions if s.start_time]
    date_range = None
    if starts:
        date_range = (min(starts).date().isoformat(), max(starts).date().isoformat())

    projects_sorted = sorted(
        per_project.items(),
        key=lambda kv: (kv[1]["sessions"], kv[1]["last_activity"] or datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True,
    )

    long_sessions = sorted(sessions, key=lambda s: (s.total_messages, s.duration_minutes), reverse=True)[:10]

    return {
        "totals": {
            "sessions": len(sessions),
            "user_messages": totals_user_msgs,
            "gemini_messages": totals_gemini_msgs,
            "total_messages": totals_user_msgs + totals_gemini_msgs,
            "tool_calls": sum(tools.values()),
            "tool_errors": sum(tool_errors.values()),
        },
        "date_range": date_range,
        "days_active": len(per_day),
        "tools": tools.most_common(15),
        "tool_errors_by_tool": dict(tool_errors),
        "tool_error_categories": error_categories.most_common(),
        "models": models.most_common(),
        "languages": languages.most_common(10),
        "session_types": session_types.most_common(),
        "per_day": sorted(per_day.items()),
        "per_project": projects_sorted,
        "long_sessions": long_sessions,
        "response_time_buckets": compute_response_time_buckets(sessions),
        "overlap": compute_overlap(sessions),
        "hour_histogram": compute_hour_histogram(sessions),
    }


def aggregate_to_jsonable(agg: dict) -> dict:
    """Convert aggregate output to a JSON-serialisable form."""
    return {
        "totals": agg["totals"],
        "date_range": agg["date_range"],
        "days_active": agg["days_active"],
        "tools": agg["tools"],
        "tool_errors_by_tool": agg["tool_errors_by_tool"],
        "tool_error_categories": agg["tool_error_categories"],
        "models": agg["models"],
        "languages": agg["languages"],
        "session_types": agg["session_types"],
        "per_day": agg["per_day"],
        "per_project": [
            {
                "name": name,
                "sessions": data["sessions"],
                "user_messages": data["user_messages"],
                "gemini_messages": data["gemini_messages"],
                "tool_calls": data["tool_calls"],
                "errors": data["errors"],
                "last_activity": data["last_activity"].isoformat() if data["last_activity"] else None,
            }
            for name, data in agg["per_project"]
        ],
        "long_sessions": [
            {
                "session_id": s.session_id,
                "project": s.project_name,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "total_messages": s.total_messages,
                "tool_calls": len(s.tool_calls),
                "duration_minutes": round(s.duration_minutes, 1),
                "first_prompt": s.first_user_prompt,
            }
            for s in agg["long_sessions"]
        ],
        "response_time_buckets": agg["response_time_buckets"],
        "overlap": agg["overlap"],
        "hour_histogram": agg["hour_histogram"],
    }
