"""Tests for gemini_insights.cli entry points."""

from __future__ import annotations

from pathlib import Path

from gemini_insights.cli import main


def test_demo_writes_valid_html(tmp_path: Path) -> None:
    out = tmp_path / "demo.html"
    rc = main(["demo", "--output", str(out), "--no-open"])
    assert rc == 0
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "<!doctype html>" in html
    assert "Gemini CLI Insights" in html
    # Sanity: the demo narrative should be present, not a placeholder.
    assert "At a Glance" in html
    assert "backend-api" in html
    assert "(fill via /insights)" not in html


def test_report_fails_cleanly_on_missing_gemini_dir(tmp_path: Path, capsys) -> None:
    nowhere = tmp_path / "nope"
    rc = main(["report", "--gemini-dir", str(nowhere), "--no-open"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Gemini directory not found" in err
