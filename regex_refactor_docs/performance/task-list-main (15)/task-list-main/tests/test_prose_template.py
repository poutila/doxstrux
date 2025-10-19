from textwrap import dedent

from tasklist.prose_template import check_against_template, get_template, main


def test_get_template_contains_expected_sections():
    template = get_template()
    assert "Refactor Brief" in template
    assert "## Context" in template
    assert "## Goals / Non-Goals" in template
    assert "Verify:" in template


def test_check_against_template_accepts_template():
    report = check_against_template(get_template())
    assert report["ok"]
    assert report["errors"] == []
    assert report["warnings"] == []
    assert report["grade"] == "ok"


def test_check_against_template_reports_issues():
    prose = dedent(
        """\
        # Example — Refactor Brief

        ## Context
        - Placeholder

        ## Goals / Non-Goals
        - **Goals**
          - Goal

        ## Phase 0 — Start
        **Time estimate:** 1 d

        ### Step 1: Do work
        Rationale: because
        ```bash
        echo hi
        ```
        """
    )

    report = check_against_template(prose)
    assert not report["ok"]
    assert report["grade"] == "fail"
    assert any("risks" in err.lower() for err in report["errors"])
    assert any("verify" in warn.lower() for warn in report["warnings"])


def test_cli_new_prints_template(capsys):
    exit_code = main(["new"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Refactor Brief" in captured.out


def test_cli_check_detects_errors(tmp_path, capsys):
    prose_path = tmp_path / "brief.md"
    prose_path.write_text("## Missing header", encoding="utf-8")

    exit_code = main(["check", str(prose_path)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "❌ Issues detected" in captured.out


def test_cli_check_returns_zero_on_warning(tmp_path, capsys):
    prose_path = tmp_path / "brief.md"
    prose_path.write_text(
        dedent(
            """\
            # Demo — Refactor Brief

            ## Context
            - Background

            ## Goals / Non-Goals
            - Goals

            ## Risks & Mitigations
            - Risk: None
            - Mitigation: None

            ## Phase 0 — Setup
            **Time estimate:** 1 d
            **Success criteria:**
            - Example

            ### Step 1: Do work
            Rationale: why

            ```sh
            echo ok
            ```
            """
        ),
        encoding="utf-8",
    )

    exit_code = main(["check", str(prose_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "⚠️" in captured.out
