"""Tests for gemini_insights.render."""

from __future__ import annotations

import json
import re

from gemini_insights.collect import aggregate, aggregate_to_jsonable, collect_sessions
from gemini_insights.demo import DEMO_INSIGHTS, DEMO_STATS
from gemini_insights.render import render


def _jsonable_stats(gemini_dir):
    return json.loads(json.dumps(aggregate_to_jsonable(aggregate(collect_sessions(gemini_dir)))))


def test_render_smoke_no_insights(fake_gemini_dir):
    html = render(_jsonable_stats(fake_gemini_dir), insights=None)
    assert "<!doctype html>" in html
    assert "Gemini CLI Insights" in html


def test_render_empty_stats_does_not_crash():
    empty = {
        "totals": {
            "sessions": 0,
            "user_messages": 0,
            "gemini_messages": 0,
            "total_messages": 0,
            "tool_calls": 0,
            "tool_errors": 0,
        },
        "date_range": None,
        "days_active": 0,
        "tools": [],
        "tool_errors_by_tool": {},
        "tool_error_categories": [],
        "models": [],
        "languages": [],
        "session_types": [],
        "per_day": [],
        "per_project": [],
        "long_sessions": [],
        "response_time_buckets": {},
        "overlap": {"overlap_events": 0, "sessions_involved": 0, "pct_messages": 0},
        "hour_histogram": {},
    }
    html = render(empty, insights=None)
    assert "0 messages across 0 sessions" in html


def test_render_escapes_user_controlled_strings(fake_gemini_dir):
    stats = _jsonable_stats(fake_gemini_dir)
    stats["per_project"][0]["name"] = "<script>alert('xss')</script>"
    html = render(stats, insights=None)
    assert "<script>alert('xss')</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_with_insights_populates_sections(fake_gemini_dir):
    html = render(_jsonable_stats(fake_gemini_dir), insights=DEMO_INSIGHTS)
    for marker in [
        "At a Glance",
        "Suggested GEMINI.md additions",
        "backend-api",
        "Weekly self-critique",
    ]:
        assert marker in html, f"missing {marker}"


def test_render_tolerates_non_numeric_session_count(fake_gemini_dir):
    insights = {
        "project_areas": [
            {"name": "demo", "session_count": "several", "description": "d"},
            {"name": "demo2", "session_count": None, "description": "d"},
            {"name": "demo3", "session_count": 3, "description": "d"},
        ]
    }
    html = render(_jsonable_stats(fake_gemini_dir), insights=insights)
    assert "several" in html
    assert "~3 sessions" in html


def test_demo_output_has_no_placeholder_pii_tokens():
    """The built-in demo data ships with the repo; ensure it doesn't contain
    tokens we explicitly want to keep out of the published screenshot."""
    html = render(DEMO_STATS, DEMO_INSIGHTS)
    forbidden = re.compile(
        r"\b(lolipop|heteml|hetemail|pepabo|taniwaki|tsudanuma|archives-server|qrunner|puppetserver|customer-reliability)\b",
        re.IGNORECASE,
    )
    match = forbidden.search(html)
    assert match is None, f"demo HTML contains forbidden token: {match.group(0)}"
