"""Tests for gemini_insights.render."""

from __future__ import annotations

import json
import re

from gemini_insights.collect import aggregate, aggregate_to_jsonable, collect_sessions
from gemini_insights.demo import DEMO_INSIGHTS, DEMO_STATS, FORBIDDEN_DEMO_TOKENS
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
        "Suggested slash commands",
        "/read-home",
        "~/.gemini/commands/read-home.toml",
        "Global GEMINI.md tweaks",
        "backend-api",
        "Weekly self-critique",
    ]:
        assert marker in html, f"missing {marker}"


def test_render_command_suggestions_block_absent_when_empty(fake_gemini_dir):
    html = render(_jsonable_stats(fake_gemini_dir), insights={"command_suggestions": []})
    assert "Suggested slash commands" not in html


def test_render_command_suggestions_escapes_user_controlled_fields(fake_gemini_dir):
    insights = {
        "command_suggestions": [
            {
                "name": "safe<xss>",
                "description": "<script>alert(1)</script>",
                "prompt": "</code><script>evil()</script>",
                "why": "legit reason",
            }
        ]
    }
    html = render(_jsonable_stats(fake_gemini_dir), insights=insights)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_command_suggestion_without_name_is_skipped(fake_gemini_dir):
    insights = {
        "command_suggestions": [
            {"name": "", "description": "no name", "prompt": "p", "why": "w"},
            {"name": "ok", "description": "d", "prompt": "p", "why": "w"},
        ]
    }
    html = render(_jsonable_stats(fake_gemini_dir), insights=insights)
    assert "/ok" in html
    assert "no name" not in html


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
    tokens we explicitly want to keep out of the published screenshot.

    Both this test and the CI `demo-pii-guard` job consume the same
    `FORBIDDEN_DEMO_TOKENS` list from `gemini_insights.demo`, so they can't
    drift apart.
    """
    html = render(DEMO_STATS, DEMO_INSIGHTS)
    # Build one alternation regex; tokens are lowercased so match is i-case.
    pattern = r"(?:" + "|".join(re.escape(t) for t in FORBIDDEN_DEMO_TOKENS) + r")"
    forbidden = re.compile(pattern, re.IGNORECASE)
    match = forbidden.search(html)
    assert match is None, f"demo HTML contains forbidden token: {match.group(0)}"


def test_demo_data_totals_reconcile():
    """Synthetic demo numbers should be internally consistent so the
    README screenshot doesn't display a paradox."""
    totals = DEMO_STATS["totals"]
    per_project = DEMO_STATS["per_project"]
    assert sum(p["sessions"] for p in per_project) == totals["sessions"]
    assert sum(p["user_messages"] for p in per_project) == totals["user_messages"]
    assert sum(p["gemini_messages"] for p in per_project) == totals["gemini_messages"]
    assert sum(p["tool_calls"] for p in per_project) == totals["tool_calls"]
    hist_sum = sum(int(v) for v in DEMO_STATS["hour_histogram"].values())
    assert hist_sum == totals["user_messages"]
