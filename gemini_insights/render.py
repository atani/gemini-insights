"""HTML renderer matching Claude Code's /insights visual style."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from . import __version__

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; color: #334155; line-height: 1.65; padding: 48px 24px; }
.container { max-width: 800px; margin: 0 auto; }
h1 { font-size: 32px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
h2 { font-size: 20px; font-weight: 600; color: #0f172a; margin-top: 48px; margin-bottom: 16px; }
.subtitle { color: #64748b; font-size: 15px; margin-bottom: 32px; }
.nav-toc { display: flex; flex-wrap: wrap; gap: 8px; margin: 24px 0 32px 0; padding: 16px; background: white; border-radius: 8px; border: 1px solid #e2e8f0; }
.nav-toc a { font-size: 12px; color: #64748b; text-decoration: none; padding: 6px 12px; border-radius: 6px; background: #f1f5f9; transition: all 0.15s; }
.nav-toc a:hover { background: #e2e8f0; color: #334155; }
.stats-row { display: flex; gap: 24px; margin-bottom: 40px; padding: 20px 0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; flex-wrap: wrap; }
.stat { text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: #0f172a; }
.stat-label { font-size: 11px; color: #64748b; text-transform: uppercase; }
.at-a-glance { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #f59e0b; border-radius: 12px; padding: 20px 24px; margin-bottom: 32px; }
.glance-title { font-size: 16px; font-weight: 700; color: #92400e; margin-bottom: 16px; }
.glance-sections { display: flex; flex-direction: column; gap: 12px; }
.glance-section { font-size: 14px; color: #78350f; line-height: 1.6; }
.glance-section strong { color: #92400e; }
.see-more { color: #b45309; text-decoration: none; font-size: 13px; white-space: nowrap; }
.see-more:hover { text-decoration: underline; }
.placeholder { color: #78350f; font-style: italic; }
.project-areas { display: flex; flex-direction: column; gap: 12px; margin-bottom: 32px; }
.project-area { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
.area-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.area-name { font-weight: 600; font-size: 15px; color: #0f172a; }
.area-count { font-size: 12px; color: #64748b; background: #f1f5f9; padding: 2px 8px; border-radius: 4px; }
.area-desc { font-size: 14px; color: #475569; line-height: 1.5; }
.narrative { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 24px; }
.narrative p { margin-bottom: 12px; font-size: 14px; color: #475569; line-height: 1.7; }
.key-insight { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px 16px; margin-top: 12px; font-size: 14px; color: #166534; }
.section-intro { font-size: 14px; color: #64748b; margin-bottom: 16px; }
.big-wins { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
.big-win { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; }
.big-win-title { font-weight: 600; font-size: 15px; color: #166534; margin-bottom: 8px; }
.big-win-desc { font-size: 14px; color: #15803d; line-height: 1.5; }
.friction-categories { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
.friction-category { background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 16px; }
.friction-title { font-weight: 600; font-size: 15px; color: #991b1b; margin-bottom: 6px; }
.friction-desc { font-size: 13px; color: #7f1d1d; margin-bottom: 10px; }
.friction-examples { margin: 0 0 0 20px; font-size: 13px; color: #334155; }
.friction-examples li { margin-bottom: 4px; }
.gemini-md-section { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
.gemini-md-section h3 { font-size: 14px; font-weight: 600; color: #1e40af; margin: 0 0 12px 0; }
.gemini-md-item { padding: 10px 0; border-bottom: 1px solid #dbeafe; }
.gemini-md-item:last-child { border-bottom: none; }
.cmd-code { background: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; color: #1e40af; border: 1px solid #bfdbfe; font-family: monospace; display: block; white-space: pre-wrap; word-break: break-word; }
.cmd-why { font-size: 12px; color: #64748b; margin-top: 4px; }
.features-section, .patterns-section { display: flex; flex-direction: column; gap: 12px; margin: 16px 0; }
.feature-card { background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 16px; }
.pattern-card { background: #f0f9ff; border: 1px solid #7dd3fc; border-radius: 8px; padding: 16px; }
.feature-title, .pattern-title { font-weight: 600; font-size: 15px; color: #0f172a; margin-bottom: 6px; }
.feature-oneliner, .pattern-summary { font-size: 14px; color: #475569; margin-bottom: 8px; }
.feature-why, .pattern-detail { font-size: 13px; color: #334155; line-height: 1.5; }
.example-code, .copyable-prompt { background: #f1f5f9; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #334155; overflow-x: auto; white-space: pre-wrap; display: block; margin-top: 8px; }
.prompt-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: #64748b; margin-top: 12px; margin-bottom: 6px; }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 24px 0; }
.chart-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
.chart-title { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 12px; }
.bar-row { display: flex; align-items: center; margin-bottom: 6px; }
.bar-label { width: 140px; font-size: 11px; color: #475569; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 6px; background: #f1f5f9; border-radius: 3px; margin: 0 8px; }
.bar-fill { height: 100%; border-radius: 3px; }
.bar-value { width: 36px; font-size: 11px; font-weight: 500; color: #64748b; text-align: right; }
.empty { color: #94a3b8; font-size: 13px; font-style: italic; padding: 8px 0; }
.horizon-section { display: flex; flex-direction: column; gap: 16px; }
.horizon-card { background: linear-gradient(135deg, #faf5ff 0%, #f5f3ff 100%); border: 1px solid #c4b5fd; border-radius: 8px; padding: 16px; }
.horizon-title { font-weight: 600; font-size: 15px; color: #5b21b6; margin-bottom: 8px; }
.horizon-possible { font-size: 14px; color: #334155; margin-bottom: 10px; line-height: 1.5; }
.horizon-tip { font-size: 13px; color: #6b21a8; background: rgba(255,255,255,0.6); padding: 8px 12px; border-radius: 4px; margin-bottom: 8px; }
.fun-ending { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #fbbf24; border-radius: 12px; padding: 24px; margin-top: 40px; text-align: center; }
.fun-headline { font-size: 18px; font-weight: 600; color: #78350f; margin-bottom: 8px; }
.fun-detail { font-size: 14px; color: #92400e; }
footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 12px; text-align: center; }
footer a { color: #64748b; }
@media (max-width: 640px) { .charts-row { grid-template-columns: 1fr; } .stats-row { justify-content: center; } .bar-label { width: 100px; } }
"""

PALETTE = {
    "projects": "#2563eb",
    "tools": "#0891b2",
    "languages": "#10b981",
    "session_types": "#8b5cf6",
    "response_times": "#6366f1",
    "hours": "#8b5cf6",
    "errors": "#dc2626",
    "models": "#a78bfa",
}


def _esc(val: Any) -> str:
    return escape(str(val), quote=True)


def _bar_row(label: str, value: int, max_value: int, color: str) -> str:
    pct = (value / max_value * 100) if max_value else 0
    return (
        f'<div class="bar-row">'
        f'<div class="bar-label">{_esc(label)}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.2f}%;background:{color}"></div></div>'
        f'<div class="bar-value">{value:,}</div>'
        f"</div>"
    )


def _chart(title: str, items: list[tuple[str, int]], color: str) -> str:
    if not items:
        body = '<div class="empty">No data.</div>'
    else:
        max_v = max(v for _, v in items) or 1
        body = "".join(_bar_row(k, v, max_v, color) for k, v in items)
    return f'<div class="chart-card"><div class="chart-title">{_esc(title)}</div>{body}</div>'


def _cards_row(items: list[str]) -> str:
    return '<div class="charts-row">' + "".join(items) + "</div>"


def _stat(value: str, label: str) -> str:
    return f'<div class="stat"><div class="stat-value">{_esc(value)}</div><div class="stat-label">{_esc(label)}</div></div>'


def _glance_section(label: str, body: str, anchor: str, anchor_label: str) -> str:
    return (
        f'<div class="glance-section"><strong>{_esc(label)}:</strong> {body} '
        f'<a href="#{anchor}" class="see-more">{_esc(anchor_label)} →</a></div>'
    )


def _toc() -> str:
    sections = [
        ("section-work", "What You Work On"),
        ("section-usage", "How You Use Gemini"),
        ("section-wins", "Impressive Things"),
        ("section-friction", "Where Things Go Wrong"),
        ("section-features", "Features to Try"),
        ("section-patterns", "New Usage Patterns"),
        ("section-horizon", "On the Horizon"),
    ]
    return '<nav class="nav-toc">' + "".join(f'<a href="#{a}">{_esc(label)}</a>' for a, label in sections) + "</nav>"


def _placeholder(section: str) -> str:
    return (
        f'<div class="narrative"><p class="placeholder">'
        f"Narrative for “{_esc(section)}” will appear once you run `/insights` "
        f"inside Gemini CLI (the skill prompt fills <code>insights.json</code> with AI analysis)."
        f"</p></div>"
    )


def build_at_a_glance(insights: dict | None) -> str:
    glance = (insights or {}).get("at_a_glance") or {}

    def fmt(text: str | None, anchor: str, anchor_label: str, label: str) -> str:
        if text:
            return _glance_section(label, _esc(text), anchor, anchor_label)
        return f'<div class="glance-section"><strong>{_esc(label)}:</strong> <span class="placeholder">(fill via /insights)</span></div>'

    body = (
        fmt(glance.get("working"), "section-wins", "Impressive Things You Did", "What's working")
        + fmt(glance.get("hindering"), "section-friction", "Where Things Go Wrong", "What's hindering you")
        + fmt(glance.get("quick_wins"), "section-features", "Features to Try", "Quick wins to try")
        + fmt(glance.get("ambitious"), "section-horizon", "On the Horizon", "Ambitious workflows")
    )
    return (
        '<div class="at-a-glance">'
        '<div class="glance-title">At a Glance</div>'
        f'<div class="glance-sections">{body}</div>'
        "</div>"
    )


def build_project_areas(stats: dict, insights: dict | None) -> str:
    areas = (insights or {}).get("project_areas") or []
    if not areas:
        items = []
        for p in stats.get("per_project", [])[:5]:
            items.append(
                '<div class="project-area">'
                '<div class="area-header">'
                f'<span class="area-name">{_esc(p["name"])}</span>'
                f'<span class="area-count">{p["sessions"]} sessions</span>'
                "</div>"
                '<div class="area-desc">'
                f"{p['user_messages']:,} user messages &middot; {p['gemini_messages']:,} gemini messages &middot; "
                f"{p['tool_calls']:,} tool calls ({p['errors']:,} errors). "
                '<span class="placeholder">Run /insights in Gemini to replace this with a narrative description.</span>'
                "</div>"
                "</div>"
            )
        return '<div class="project-areas">' + "".join(items) + "</div>"
    blocks = []
    for a in areas:
        name = a.get("name", "?")
        count_raw = a.get("session_count")
        desc = a.get("description", "")
        count_html = ""
        if isinstance(count_raw, (int, float)):
            count_html = f'<span class="area-count">~{int(count_raw)} sessions</span>'
        elif isinstance(count_raw, str) and count_raw.strip():
            count_html = f'<span class="area-count">{_esc(count_raw)}</span>'
        blocks.append(
            '<div class="project-area">'
            '<div class="area-header">'
            f'<span class="area-name">{_esc(name)}</span>{count_html}'
            "</div>"
            f'<div class="area-desc">{_esc(desc)}</div>'
            "</div>"
        )
    return '<div class="project-areas">' + "".join(blocks) + "</div>"


def build_narrative(insights: dict | None) -> str:
    nar = (insights or {}).get("narrative") or {}
    paragraphs = nar.get("paragraphs") or []
    if not paragraphs:
        return _placeholder("How You Use Gemini")
    body = "".join(f"<p>{_esc(p)}</p>" for p in paragraphs)
    insight_text = nar.get("key_insight")
    insight_html = (
        f'<div class="key-insight"><strong>Key pattern:</strong> {_esc(insight_text)}</div>' if insight_text else ""
    )
    return f'<div class="narrative">{body}{insight_html}</div>'


def build_wins(insights: dict | None) -> str:
    wins = (insights or {}).get("wins") or []
    if not wins:
        return _placeholder("Impressive Things You Did")
    cards = []
    for w in wins:
        cards.append(
            '<div class="big-win">'
            f'<div class="big-win-title">{_esc(w.get("title", ""))}</div>'
            f'<div class="big-win-desc">{_esc(w.get("description", ""))}</div>'
            "</div>"
        )
    return '<div class="big-wins">' + "".join(cards) + "</div>"


def build_friction(insights: dict | None) -> str:
    items = (insights or {}).get("friction") or []
    if not items:
        return _placeholder("Where Things Go Wrong")
    cards = []
    for f in items:
        examples = f.get("examples") or []
        ex_html = ""
        if examples:
            ex_html = "<ul class='friction-examples'>" + "".join(f"<li>{_esc(e)}</li>" for e in examples) + "</ul>"
        cards.append(
            '<div class="friction-category">'
            f'<div class="friction-title">{_esc(f.get("title", ""))}</div>'
            f'<div class="friction-desc">{_esc(f.get("description", ""))}</div>'
            f"{ex_html}"
            "</div>"
        )
    return '<div class="friction-categories">' + "".join(cards) + "</div>"


def build_gemini_md_section(insights: dict | None) -> str:
    items = (insights or {}).get("gemini_md_additions") or []
    if not items:
        return ""
    cards = []
    for it in items:
        text = it.get("text", "")
        why = it.get("why", "")
        cards.append(
            '<div class="gemini-md-item">'
            f'<code class="cmd-code">{_esc(text)}</code>'
            f'<div class="cmd-why">{_esc(why)}</div>'
            "</div>"
        )
    return '<div class="gemini-md-section"><h3>Suggested GEMINI.md additions</h3>' + "".join(cards) + "</div>"


def build_features(insights: dict | None) -> str:
    items = (insights or {}).get("features") or []
    if not items:
        return _placeholder("Features to Try")
    cards = []
    for it in items:
        code = it.get("example_code", "")
        code_html = f'<code class="example-code">{_esc(code)}</code>' if code else ""
        cards.append(
            '<div class="feature-card">'
            f'<div class="feature-title">{_esc(it.get("title", ""))}</div>'
            f'<div class="feature-oneliner">{_esc(it.get("oneliner", ""))}</div>'
            f'<div class="feature-why"><strong>Why for you:</strong> {_esc(it.get("why", ""))}</div>'
            f"{code_html}"
            "</div>"
        )
    return '<div class="features-section">' + "".join(cards) + "</div>"


def build_patterns(insights: dict | None) -> str:
    items = (insights or {}).get("patterns") or []
    if not items:
        return _placeholder("New Usage Patterns")
    cards = []
    for it in items:
        prompt = it.get("prompt", "")
        prompt_html = (
            f'<div class="prompt-label">Paste into Gemini CLI:</div><code class="copyable-prompt">{_esc(prompt)}</code>'
            if prompt
            else ""
        )
        cards.append(
            '<div class="pattern-card">'
            f'<div class="pattern-title">{_esc(it.get("title", ""))}</div>'
            f'<div class="pattern-summary">{_esc(it.get("summary", ""))}</div>'
            f'<div class="pattern-detail">{_esc(it.get("detail", ""))}</div>'
            f"{prompt_html}"
            "</div>"
        )
    return '<div class="patterns-section">' + "".join(cards) + "</div>"


def build_horizon(insights: dict | None) -> str:
    items = (insights or {}).get("horizon") or []
    if not items:
        return _placeholder("On the Horizon")
    cards = []
    for it in items:
        tip = it.get("tip", "")
        tip_html = f'<div class="horizon-tip"><strong>Getting started:</strong> {_esc(tip)}</div>' if tip else ""
        prompt = it.get("prompt", "")
        prompt_html = (
            f'<div class="prompt-label">Paste into Gemini CLI:</div><code class="copyable-prompt">{_esc(prompt)}</code>'
            if prompt
            else ""
        )
        cards.append(
            '<div class="horizon-card">'
            f'<div class="horizon-title">{_esc(it.get("title", ""))}</div>'
            f'<div class="horizon-possible">{_esc(it.get("possible", ""))}</div>'
            f"{tip_html}{prompt_html}"
            "</div>"
        )
    return '<div class="horizon-section">' + "".join(cards) + "</div>"


def build_fun_ending(insights: dict | None) -> str:
    fun = (insights or {}).get("fun_ending") or {}
    if not fun.get("headline"):
        return ""
    return (
        '<div class="fun-ending">'
        f'<div class="fun-headline">“{_esc(fun.get("headline", ""))}”</div>'
        f'<div class="fun-detail">{_esc(fun.get("detail", ""))}</div>'
        "</div>"
    )


def build_charts(stats: dict) -> str:
    project_items = [(p["name"], p["sessions"]) for p in stats.get("per_project", [])[:6]]
    tool_items = stats.get("tools", [])
    chart1 = _cards_row(
        [
            _chart("Projects (by sessions)", project_items, PALETTE["projects"]),
            _chart("Top tools used", tool_items, PALETTE["tools"]),
        ]
    )

    lang_items = stats.get("languages", [])
    type_items = [(k.replace("_", " ").title(), v) for k, v in stats.get("session_types", [])]
    chart2 = _cards_row(
        [
            _chart("Languages (by file-touching tool calls)", lang_items, PALETTE["languages"]),
            _chart("Session types", type_items, PALETTE["session_types"]),
        ]
    )

    rtb = stats.get("response_time_buckets", {}) or {}
    rt_items = [(k, rtb[k]) for k in ["2-10s", "10-30s", "30s-1m", "1-2m", "2-5m", "5-15m", ">15m"] if k in rtb]
    chart3 = _cards_row(
        [
            _chart("Response time between prompts", rt_items, PALETTE["response_times"]),
            _chart("Models used (sessions)", stats.get("models", []), PALETTE["models"]),
        ]
    )

    hh = stats.get("hour_histogram", {}) or {}
    hh = {int(k): v for k, v in hh.items()}
    periods = [
        ("Morning (6-12)", range(6, 12)),
        ("Afternoon (12-18)", range(12, 18)),
        ("Evening (18-24)", range(18, 24)),
        ("Night (0-6)", range(0, 6)),
    ]
    period_items = [(label, sum(hh.get(h, 0) for h in rng)) for label, rng in periods]
    chart4 = _cards_row(
        [
            _chart("User messages by time of day", period_items, PALETTE["hours"]),
            _chart("Tool error categories", stats.get("tool_error_categories", []), PALETTE["errors"]),
        ]
    )

    overlap = stats.get("overlap", {}) or {}
    overlap_html = (
        '<div class="chart-card">'
        '<div class="chart-title">Multi-gemini (parallel sessions)</div>'
        '<div style="display:flex;gap:24px;flex-wrap:wrap;">'
        f'<div style="text-align:center;"><div style="font-size:24px;font-weight:700;color:#7c3aed;">{overlap.get("overlap_events", 0):,}</div>'
        '<div style="font-size:11px;color:#64748b;text-transform:uppercase;">Overlap events</div></div>'
        f'<div style="text-align:center;"><div style="font-size:24px;font-weight:700;color:#7c3aed;">{overlap.get("sessions_involved", 0):,}</div>'
        '<div style="font-size:11px;color:#64748b;text-transform:uppercase;">Sessions involved</div></div>'
        f'<div style="text-align:center;"><div style="font-size:24px;font-weight:700;color:#7c3aed;">{overlap.get("pct_messages", 0)}%</div>'
        '<div style="font-size:11px;color:#64748b;text-transform:uppercase;">Of messages</div></div>'
        "</div>"
        '<p style="font-size:13px;color:#475569;margin-top:12px;">Sessions whose time windows overlap with at least one other session.</p>'
        "</div>"
    )

    return chart1 + chart2 + chart3 + chart4 + overlap_html


def render(stats: dict, insights: dict | None = None) -> str:
    totals = stats.get("totals", {})
    date_range = stats.get("date_range")
    generated = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    subtitle_parts = [f"{totals.get('total_messages', 0):,} messages across {totals.get('sessions', 0):,} sessions"]
    if date_range:
        subtitle_parts.append(f"{date_range[0]} to {date_range[1]}")
    subtitle = " | ".join(subtitle_parts)

    stats_row = "".join(
        [
            _stat(f"{totals.get('total_messages', 0):,}", "Messages"),
            _stat(f"{totals.get('sessions', 0):,}", "Sessions"),
            _stat(f"{totals.get('tool_calls', 0):,}", "Tool calls"),
            _stat(f"{totals.get('tool_errors', 0):,}", "Tool errors"),
            _stat(f"{stats.get('days_active', 0):,}", "Days active"),
        ]
    )

    sections = [
        build_at_a_glance(insights),
        _toc(),
        f'<div class="stats-row">{stats_row}</div>',
        '<h2 id="section-work">What You Work On</h2>',
        build_project_areas(stats, insights),
        build_charts(stats),
        '<h2 id="section-usage">How You Use Gemini</h2>',
        build_narrative(insights),
        '<h2 id="section-wins">Impressive Things You Did</h2>',
        build_wins(insights),
        '<h2 id="section-friction">Where Things Go Wrong</h2>',
        build_friction(insights),
        '<h2 id="section-features">Features to Try</h2>',
        build_gemini_md_section(insights),
        build_features(insights),
        '<h2 id="section-patterns">New Ways to Use Gemini CLI</h2>',
        build_patterns(insights),
        '<h2 id="section-horizon">On the Horizon</h2>',
        build_horizon(insights),
        build_fun_ending(insights),
        f'<footer>Generated by <a href="https://github.com/atani/gemini-insights">gemini-insights</a> v{_esc(__version__)} &middot; {_esc(generated)}</footer>',
    ]

    body = "".join(sections)
    return (
        "<!doctype html>\n"
        '<html lang="en"><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Gemini CLI Insights</title>"
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'
        f"<style>{CSS}</style>"
        "</head><body>"
        '<div class="container">'
        f"<h1>Gemini CLI Insights</h1>"
        f'<p class="subtitle">{_esc(subtitle)}</p>'
        f"{body}"
        "</div>"
        "</body></html>"
    )


def load_insights(path: Path | None) -> dict | None:
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
