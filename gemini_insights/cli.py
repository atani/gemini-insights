"""gemini-insights CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from . import __version__
from .collect import DEFAULT_GEMINI_DIR, aggregate, aggregate_to_jsonable, collect_sessions
from .demo import DEMO_INSIGHTS, DEMO_STATS
from .render import load_insights, render


def _default_output_dir(gemini_dir: Path) -> Path:
    return (gemini_dir / "usage-data").expanduser()


def _print_summary(jsonable: dict) -> None:
    t = jsonable["totals"]
    print(f"Sessions analyzed : {t['sessions']:,}")
    print(f"User messages     : {t['user_messages']:,}")
    print(f"Gemini messages   : {t['gemini_messages']:,}")
    print(f"Tool calls        : {t['tool_calls']:,} ({t['tool_errors']:,} errors)")
    if jsonable["date_range"]:
        print(f"Period            : {jsonable['date_range'][0]} ~ {jsonable['date_range'][1]}")
    if jsonable["per_project"]:
        print("\nTop projects:")
        for p in jsonable["per_project"][:5]:
            print(f"  - {p['name']}: {p['sessions']} sessions, {p['user_messages']} user msgs")
    if jsonable["tools"]:
        print("\nTop tools:")
        for name, count in jsonable["tools"][:5]:
            errs = jsonable["tool_errors_by_tool"].get(name, 0)
            print(f"  - {name}: {count} calls ({errs} errors)")


def cmd_collect(args: argparse.Namespace) -> int:
    gemini_dir: Path = args.gemini_dir.expanduser()
    if not gemini_dir.exists():
        print(f"error: Gemini directory not found: {gemini_dir}", file=sys.stderr)
        return 1
    sessions = collect_sessions(gemini_dir)
    if not sessions:
        print(f"No Gemini sessions under {gemini_dir}/tmp/.", file=sys.stderr)
        return 1
    jsonable = aggregate_to_jsonable(aggregate(sessions))
    out = (args.output or (_default_output_dir(gemini_dir) / "stats.json")).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(jsonable, indent=2, ensure_ascii=False), encoding="utf-8")
    _print_summary(jsonable)
    print(f"\nStats written to: {out}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    stats_path: Path = args.stats.expanduser()
    if not stats_path.exists():
        print(f"error: stats file not found: {stats_path}", file=sys.stderr)
        return 1
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    insights = load_insights(args.insights.expanduser() if args.insights else None)
    html = render(stats, insights)
    out = args.output.expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Report written to: {out}")
    if not args.no_open:
        # webbrowser.open can fail in headless envs; the file is on disk, so swallow.
        try:
            webbrowser.open(out.as_uri())
        except Exception:
            pass
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Render a sample report from the package's built-in synthetic data.

    This is what we use for the README screenshot — it never touches
    `~/.gemini/` and is fully reproducible.
    """
    html = render(DEMO_STATS, DEMO_INSIGHTS)
    out = args.output.expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Demo report written to: {out}")
    if not args.no_open:
        try:
            webbrowser.open(out.as_uri())
        except Exception:
            pass
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    gemini_dir: Path = args.gemini_dir.expanduser()
    if not gemini_dir.exists():
        print(f"error: Gemini directory not found: {gemini_dir}", file=sys.stderr)
        return 1
    sessions = collect_sessions(gemini_dir)
    if not sessions:
        print(f"No Gemini sessions under {gemini_dir}/tmp/.", file=sys.stderr)
        return 1

    jsonable = aggregate_to_jsonable(aggregate(sessions))

    usage_dir = _default_output_dir(gemini_dir)
    usage_dir.mkdir(parents=True, exist_ok=True)
    stats_path = (args.stats_output or (usage_dir / "stats.json")).expanduser()
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(json.dumps(jsonable, indent=2, ensure_ascii=False), encoding="utf-8")

    insights_path = args.insights or (usage_dir / "insights.json")
    insights = load_insights(insights_path.expanduser()) if insights_path else None

    html = render(jsonable, insights)
    out_path = (args.output or (usage_dir / "report.html")).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    _print_summary(jsonable)
    print(f"\nStats : {stats_path}")
    print(f"Report: {out_path}")
    if insights is None:
        print(f"\nTip: run `/insights` inside Gemini CLI to populate {insights_path} with AI narrative sections.")

    if not args.no_open:
        try:
            webbrowser.open(out_path.as_uri())
        except Exception:
            pass
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gemini-insights",
        description="Generate a usage report from your Gemini CLI sessions.",
    )
    parser.add_argument("--version", action="version", version=f"gemini-insights {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_report = sub.add_parser("report", help="Collect stats and render report (default).")
    p_report.add_argument("--gemini-dir", type=Path, default=DEFAULT_GEMINI_DIR)
    p_report.add_argument("--output", "-o", type=Path, default=None, help="HTML output path.")
    p_report.add_argument("--stats-output", type=Path, default=None, help="Stats JSON output path.")
    p_report.add_argument("--insights", type=Path, default=None, help="Insights JSON (AI narrative) path.")
    p_report.add_argument("--no-open", action="store_true")
    p_report.set_defaults(func=cmd_report)

    p_col = sub.add_parser("collect", help="Compute stats JSON only (no HTML).")
    p_col.add_argument("--gemini-dir", type=Path, default=DEFAULT_GEMINI_DIR)
    p_col.add_argument("--output", "-o", type=Path, default=None)
    p_col.set_defaults(func=cmd_collect)

    p_ren = sub.add_parser("render", help="Render HTML from existing stats (+ optional insights) JSON.")
    p_ren.add_argument("--stats", type=Path, required=True)
    p_ren.add_argument("--insights", type=Path, default=None)
    p_ren.add_argument("--output", "-o", type=Path, required=True)
    p_ren.add_argument("--no-open", action="store_true")
    p_ren.set_defaults(func=cmd_render)

    p_demo = sub.add_parser(
        "demo",
        help="Render a sample report from built-in synthetic data (for README screenshots).",
    )
    p_demo.add_argument("--output", "-o", type=Path, required=True)
    p_demo.add_argument("--no-open", action="store_true")
    p_demo.set_defaults(func=cmd_demo)

    # Legacy top-level flags routed to `report` when no subcommand is given.
    parser.add_argument("--gemini-dir", type=Path, default=DEFAULT_GEMINI_DIR, help=argparse.SUPPRESS)
    parser.add_argument("--output", "-o", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--stats-output", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--insights", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--no-open", action="store_true", help=argparse.SUPPRESS)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) is None:
        return cmd_report(args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
