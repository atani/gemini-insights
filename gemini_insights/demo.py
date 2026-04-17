"""Synthetic demo data used to render a shareable sample report.

This is the ONLY source of data for the README screenshot. Do NOT run
`gemini-insights report` against a real `~/.gemini/` tree and commit the
resulting HTML or screenshots — always regenerate from `DEMO_STATS` +
`DEMO_INSIGHTS` via `gemini-insights demo`.

All project names, session IDs, and narrative text below are invented.
"""

from __future__ import annotations

# Single source of truth for the demo PII guard. Both the unit test and the
# CI workflow check that the rendered demo HTML contains none of these
# tokens — real project / service / customer / user names that must never
# leak via the shipped demo or screenshot.
#
# Keep the list in lowercase; both consumers match case-insensitively.
FORBIDDEN_DEMO_TOKENS: tuple[str, ...] = (
    # personal / host identifiers that have leaked before
    "lolipop",
    "heteml",
    "hetemail",
    "pepabo",
    "taniwaki",
    "atanit",
    "tech.pepabo.com",
    "git.pepabo.com",
    # past project/service codenames from the author's real ~/.gemini/
    "tsudanuma",
    "archives-server",
    "qrunner",
    "puppetserver",
    "customer-reliability",
    # Pepabo brand names — defence-in-depth against future leaks
    "muumuu",
    "minne",
    "suzuri",
    "colorme",
    "color-me",
    "goope",
    "booth",
    "kouin",
    "stores.jp",
)

DEMO_STATS: dict = {
    "totals": {
        "sessions": 72,
        "user_messages": 318,
        "gemini_messages": 1184,
        "total_messages": 1502,
        "tool_calls": 876,
        "tool_errors": 24,
    },
    "date_range": ["2026-02-01", "2026-03-15"],
    "days_active": 28,
    "tools": [
        ["run_shell_command", 412],
        ["read_file", 203],
        ["replace", 98],
        ["search_file_content", 52],
        ["google_web_search", 38],
        ["ask_user", 21],
        ["write_file", 18],
    ],
    "tool_errors_by_tool": {"read_file": 11, "replace": 7, "run_shell_command": 4, "write_file": 2},
    "tool_error_categories": [
        ["File Not Found", 10],
        ["Path Outside Workspace", 6],
        ["Edit Mismatch", 5],
        ["Command Failed", 2],
        ["Other", 1],
    ],
    "models": [["gemini-2.5-pro", 48], ["gemini-2.5-flash", 24]],
    "languages": [
        ["Python", 84],
        ["TypeScript", 61],
        ["Markdown", 43],
        ["YAML", 27],
        ["Go", 22],
        ["JSON", 18],
        ["SQL", 9],
    ],
    "session_types": [
        ["single_task", 31],
        ["multi_task", 23],
        ["iterative_refinement", 14],
        ["exploration", 4],
    ],
    "per_day": [],
    "per_project": [
        {
            "name": "backend-api",
            "sessions": 18,
            "user_messages": 96,
            "gemini_messages": 362,
            "tool_calls": 258,
            "errors": 8,
            "last_activity": "2026-03-15T14:20:00+00:00",
        },
        {
            "name": "frontend-web",
            "sessions": 12,
            "user_messages": 54,
            "gemini_messages": 198,
            "tool_calls": 141,
            "errors": 5,
            "last_activity": "2026-03-14T09:30:00+00:00",
        },
        {
            "name": "data-pipelines",
            "sessions": 10,
            "user_messages": 43,
            "gemini_messages": 167,
            "tool_calls": 118,
            "errors": 3,
            "last_activity": "2026-03-13T17:45:00+00:00",
        },
        {
            "name": "infra-terraform",
            "sessions": 8,
            "user_messages": 38,
            "gemini_messages": 154,
            "tool_calls": 109,
            "errors": 4,
            "last_activity": "2026-03-10T11:10:00+00:00",
        },
        {
            "name": "docs-site",
            "sessions": 7,
            "user_messages": 29,
            "gemini_messages": 102,
            "tool_calls": 74,
            "errors": 1,
            "last_activity": "2026-03-08T15:00:00+00:00",
        },
        {
            "name": "tooling-scripts",
            "sessions": 6,
            "user_messages": 24,
            "gemini_messages": 85,
            "tool_calls": 60,
            "errors": 2,
            "last_activity": "2026-03-05T13:25:00+00:00",
        },
        # Catch-all "misc" row so per-project totals reconcile with the
        # top-level `totals` block. `aggregate_to_jsonable` emits every
        # project it saw, so the two always sum exactly in real output.
        {
            "name": "misc-sandboxes",
            "sessions": 11,
            "user_messages": 34,
            "gemini_messages": 116,
            "tool_calls": 116,
            "errors": 1,
            "last_activity": "2026-02-28T10:15:00+00:00",
        },
    ],
    "long_sessions": [],
    "response_time_buckets": {
        "2-10s": 28,
        "10-30s": 74,
        "30s-1m": 91,
        "1-2m": 68,
        "2-5m": 42,
        "5-15m": 12,
        ">15m": 3,
    },
    "overlap": {"overlap_events": 34, "sessions_involved": 28, "pct_messages": 41},
    # Hand-tuned so the 24 per-hour values sum to totals.user_messages (318).
    # `compute_hour_histogram` in collect.py counts exactly one entry per user
    # message, so sums must match in real data.
    "hour_histogram": {
        "0": 1,
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0,
        "6": 3,
        "7": 9,
        "8": 16,
        "9": 28,
        "10": 39,
        "11": 34,
        "12": 14,
        "13": 30,
        "14": 36,
        "15": 33,
        "16": 29,
        "17": 21,
        "18": 11,
        "19": 6,
        "20": 4,
        "21": 2,
        "22": 1,
        "23": 1,
    },
}

DEMO_INSIGHTS: dict = {
    "at_a_glance": {
        "working": (
            "Sample-project work dominates (backend-api + frontend-web ≈ 42% of sessions), "
            "and Gemini handles a shell-first workflow well: run_shell_command (412) drives "
            "most exploration, and error rate stays under 3%."
        ),
        "hindering": (
            "File access outside the workspace causes the top two error categories "
            "(File Not Found + Path Outside Workspace = 16/24). The agent also retries "
            "replace calls when the target file has drifted since the last read."
        ),
        "quick_wins": (
            "Turn the two recurring friction patterns into named slash commands "
            "(/read-home, /safe-replace) under ~/.gemini/commands/. That pulls the context "
            "in only when you need it — and keeps GEMINI.md lean."
        ),
        "ambitious": (
            "Let Gemini self-review a week of transcripts each Monday and file a PR that "
            "updates GEMINI.md where it would have cut friction. This turns the feedback "
            "loop into a code-owned process."
        ),
    },
    "project_areas": [
        {
            "name": "backend-api",
            "session_count": 18,
            "description": (
                "API endpoint development and debugging — schema validation, request/response "
                "shapes, and rate-limit tuning dominate the sessions."
            ),
        },
        {
            "name": "frontend-web",
            "session_count": 12,
            "description": (
                "Component refactors, accessibility tweaks, and a handful of CSS regressions "
                "investigated with Gemini as a pair-programmer."
            ),
        },
        {
            "name": "data-pipelines",
            "session_count": 10,
            "description": (
                "ETL job authoring and backfill scripts, usually a single prompt followed by 15–30 shell calls."
            ),
        },
        {
            "name": "infra-terraform",
            "session_count": 8,
            "description": (
                "Module refactors and plan/apply diffing sessions, often escalated to "
                "ask_user when a plan looked dangerous."
            ),
        },
        {
            "name": "docs-site",
            "session_count": 7,
            "description": "Markdown authoring and link-check runs across the documentation site.",
        },
    ],
    "narrative": {
        "paragraphs": [
            (
                "You use Gemini CLI as a focused investigation tool. Prompts start concrete "
                "('why does the /users endpoint 500 on empty payloads?') and the agent takes "
                "it from there with a shell-heavy cadence: run_shell_command, read_file, "
                "replace, repeat."
            ),
            (
                "Sessions cluster around single_task and multi_task types, which tracks with "
                "a short-burst style. Exploration sessions are rare but contain the most "
                "tool calls — those are where the friction concentrates."
            ),
            (
                "Model mix is pragmatic: gemini-2.5-pro on the long, cross-file work and "
                "gemini-2.5-flash for one-shot shell tasks. Language distribution (Python > "
                "TypeScript > Markdown > YAML) matches the project mix exactly."
            ),
        ],
        "key_insight": (
            "Gemini works best when the target file is inside the workspace; every boundary "
            "crossing is an error waiting to happen."
        ),
    },
    "wins": [
        {
            "title": "Clean investigation loop",
            "description": (
                "backend-api sessions converge on a fix with the same run → read → replace "
                "rhythm and rarely need you to bail out mid-session."
            ),
        },
        {
            "title": "Balanced pro/flash usage",
            "description": (
                "48 pro vs 24 flash sessions — you don't overuse the expensive model for one-shot shell tasks."
            ),
        },
    ],
    "friction": [
        {
            "title": "Out-of-workspace paths hit read_file",
            "description": (
                "11 of 24 tool errors are read_file failing because the target lives outside "
                "the configured workspace (typically $HOME dotfiles)."
            ),
            "examples": [
                "Multiple retries on ~/.config/*/config.toml lookups in infra-terraform sessions",
                "A replace call aborted after the preliminary read was rejected",
            ],
        },
        {
            "title": "replace loses sync on fast-moving files",
            "description": (
                "7 replace errors classified as Edit Mismatch — old_string no longer matches "
                "because the file changed since the agent last read it."
            ),
        },
    ],
    "command_suggestions": [
        {
            "name": "read-home",
            "description": "Read a file under $HOME that lives outside the workspace.",
            "prompt": "!{cat {{args}}}",
            "why": (
                "11/24 tool errors were read_file refusing paths outside the workspace. "
                "A named slash command makes the shell-cat fallback one keystroke away — "
                "no GEMINI.md bloat that every session pays for."
            ),
        },
        {
            "name": "safe-replace",
            "description": "Re-read the target file, then replace old_string with new_string.",
            "prompt": (
                "Re-read {{args.file}} with `read_file`, then call `replace` with "
                "old_string={{args.old}} and new_string={{args.new}}. Abort and ask if "
                "old_string no longer matches after the re-read."
            ),
            "why": (
                "7 Edit Mismatch errors came from stale context. Encoding the re-read as a "
                "command removes the class without adding rules to GEMINI.md."
            ),
        },
        {
            "name": "api-triage",
            "description": "Triage a backend-api 5xx with a fixed run → read → replace playbook.",
            "prompt": (
                "Reproduce {{args}} against the dev server, collect the first failing "
                "stack frame, read the handler + its immediate dependencies, then propose a "
                "minimal patch. Stop before writing any change."
            ),
            "why": (
                "backend-api's 18 sessions all follow the same rhythm — codifying it as a "
                "slash command cuts the 20+ shell rounds exploration sessions need today."
            ),
        },
    ],
    "gemini_md_additions": [
        {
            "text": (
                "## Replace discipline\n"
                "- Before calling `replace`, always re-read the target file in the same turn "
                "so `old_string` is up to date."
            ),
            "why": (
                "Kept as a global GEMINI.md rule only because it applies everywhere — most "
                "other friction patterns are now covered by dedicated slash commands."
            ),
        },
    ],
    "features": [
        {
            "title": "Argument placeholders in slash commands",
            "oneliner": "Use {{args}} / {{args.name}} to pass context into TOML prompts.",
            "why": (
                "The suggested commands above all use {{args}} — worth knowing the full "
                "substitution surface so you can template richer workflows."
            ),
            "example_code": (
                "# inside ~/.gemini/commands/review.toml\n"
                'prompt = "Review the diff for {{args.pr}} focusing on {{args.focus}}."'
            ),
        },
        {
            "title": "Headless invocation with --prompt",
            "oneliner": "Run Gemini CLI non-interactively from cron or CI.",
            "why": (
                "Once workflows are captured as slash commands, piping them through "
                "`gemini --prompt '/api-triage ...'` unlocks scheduled runs."
            ),
            "example_code": "gemini --prompt '/api-triage /users endpoint 500s on empty payload'",
        },
    ],
    "patterns": [
        {
            "title": "Use exploration agents for broad questions",
            "summary": "Exploration sessions chain 20+ shell calls before converging.",
            "detail": (
                "For open-ended prompts, spawn a dedicated investigation agent that returns "
                "structure, dependencies, and CI state in one summary pass instead of shelling "
                "out repeatedly."
            ),
            "prompt": (
                "Spawn an exploration agent: investigate the current repo, summarise "
                "structure, dependencies, CI state, and top 3 next steps in under 200 words."
            ),
        },
    ],
    "horizon": [
        {
            "title": "Weekly self-critique over transcripts",
            "possible": (
                "Gemini analyses the last 7 days of sessions each Monday, diffs the friction "
                "patterns against GEMINI.md, and opens a PR with proposed updates."
            ),
            "tip": ("Combine /insights with gemini-cli's headless `--prompt` mode and a cron or launchd job."),
            "prompt": (
                "Every Monday at 08:00, run `/insights` over the last 7 days, diff the "
                "suggestions against ~/.gemini/GEMINI.md, and emit a patch file ready for "
                "git apply."
            ),
        },
    ],
    "fun_ending": {
        "headline": ("Gemini learned the art of saying “let me shell out” instead of panicking at sandbox denials."),
        "detail": (
            "When the workspace said no, it pivoted to cat/ls more than fifteen times before "
            "the user had to step in. A respectable humility-to-automation ratio."
        ),
    },
}
