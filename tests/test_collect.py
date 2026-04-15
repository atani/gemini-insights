"""Tests for gemini_insights.collect."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from gemini_insights.collect import (
    Session,
    aggregate,
    aggregate_to_jsonable,
    categorize_tool_error,
    collect_sessions,
    compute_overlap,
    detect_language_from_args,
    parse_ts,
)


def test_collect_sessions_parses_fake_tree(fake_gemini_dir):
    sessions = collect_sessions(fake_gemini_dir)
    assert len(sessions) == 2
    assert sessions[0].project_name == "demo-project"


def test_aggregate_totals(fake_gemini_dir):
    agg = aggregate(collect_sessions(fake_gemini_dir))
    totals = agg["totals"]
    assert totals["sessions"] == 2
    assert totals["user_messages"] == 2
    assert totals["gemini_messages"] == 2
    assert totals["tool_calls"] == 2
    assert totals["tool_errors"] == 1


def test_aggregate_to_jsonable_is_serializable(fake_gemini_dir):
    agg = aggregate(collect_sessions(fake_gemini_dir))
    restored = json.loads(json.dumps(aggregate_to_jsonable(agg), ensure_ascii=False))
    assert restored["totals"]["sessions"] == 2
    assert all(isinstance(k, str) for k in restored["hour_histogram"])


def test_languages_detected(fake_gemini_dir):
    agg = aggregate(collect_sessions(fake_gemini_dir))
    langs = dict(agg["languages"])
    assert langs.get("Python", 0) >= 2


def test_parse_ts_accepts_and_rejects():
    ts = parse_ts("2026-04-01T10:00:00.000Z")
    assert ts is not None and ts.year == 2026 and ts.hour == 10
    assert parse_ts("not-a-date") is None
    assert parse_ts(None) is None
    assert parse_ts(12345) is None


def test_categorize_tool_error_matrix():
    assert categorize_tool_error("File not found: missing.py") == "File Not Found"
    assert categorize_tool_error("Path not in workspace: /etc/passwd") == "Path Outside Workspace"
    assert categorize_tool_error("Command failed with exit code 1") == "Command Failed"
    assert categorize_tool_error("could not find the old string") == "Edit Mismatch"
    assert categorize_tool_error("") == "Other"
    assert categorize_tool_error("some unmatched phrase") == "Other"


def test_detect_language_from_args():
    assert detect_language_from_args({"file_path": "foo.rb"}) == "Ruby"
    assert detect_language_from_args({"absolute_path": "/tmp/x.go"}) == "Go"
    assert detect_language_from_args({"unknown_key": "foo.py"}) is None
    assert detect_language_from_args({}) is None
    assert detect_language_from_args({"file": 42}) is None


def test_compute_overlap_detects_and_skips():
    def mk(sid: str, start_h: int, start_m: int, end_h: int, end_m: int) -> Session:
        s = Session(
            session_id=sid,
            project_hash="h",
            project_name="p",
            start_time=datetime(2026, 4, 1, start_h, start_m, tzinfo=timezone.utc),
            last_updated=datetime(2026, 4, 1, end_h, end_m, tzinfo=timezone.utc),
        )
        s.gemini_messages = 1
        return s

    overlap = compute_overlap([mk("A", 10, 0, 10, 30), mk("B", 10, 15, 10, 45), mk("C", 11, 0, 11, 10)])
    assert overlap["overlap_events"] == 1
    assert overlap["sessions_involved"] == 2  # A and B
