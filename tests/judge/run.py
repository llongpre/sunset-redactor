"""CLI: run all three LLM judges against redacted output files.

Usage:
    python -m tests.judge.run                          # judge both output dirs (default)
    python -m tests.judge.run tests/data/provided/outputs/
    python -m tests.judge.run tests/data/synthetic/outputs/
    python -m tests.judge.run <file>                   # judge a single file

Results are saved as judge_report.json in each directory that is judged.

Judges run per file:
  1. re-identification  — can a redacted person be named from context?
  2. missed PII         — is there still identifying information in the text?
  3. over-redaction     — was non-PII content incorrectly removed?
                          (requires a matching original in the sibling inputs/ dir)
"""
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from tests.judge import judge, JudgeResult
from tests.judge.missed_pii import judge_missed_pii, MissedPIIResult
from tests.judge.over_redaction import judge_over_redaction, OverRedactionResult

_SUPPORTED_SUFFIXES = {".txt", ".md", ".json"}
_REPORT_FILENAME = "judge_report.json"
_BINARY_SUFFIXES = {".pdf"}  # originals we can't read as plain text
_DEFAULT_OUTPUT_DIRS = [
    Path("tests/data/provided/outputs"),
    Path("tests/data/synthetic/outputs"),
]


def _collect_paths(directory: Path) -> list[Path]:
    return sorted(
        p for p in directory.rglob("*")
        if p.is_file()
        and p.suffix in _SUPPORTED_SUFFIXES
        and p.name != _REPORT_FILENAME
    )


def _find_original(redacted_path: Path, inputs_dir: Path) -> Path | None:
    """Return the original input file for a redacted output, or None if not found."""
    name = redacted_path.name
    if not name.startswith("redacted_"):
        return None
    original_stem = Path(name[len("redacted_"):]).stem
    for candidate in inputs_dir.iterdir():
        if candidate.stem == original_stem and candidate.suffix not in _BINARY_SUFFIXES:
            return candidate
    return None


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def _print_reid(result: JudgeResult) -> None:
    for v in result.verdicts:
        flag = "✗" if v.identifiable else "✓"
        inf = f", inferred={v.inferred_identity}" if v.inferred_identity else ""
        print(f"    {flag} {v.placeholder}: confidence={v.confidence}{inf}")
        if v.identifiable:
            print(f"      {v.reasoning}")


def _print_missed_pii(result: MissedPIIResult) -> None:
    for f in result.findings:
        print(f"    ✗ [{f.confidence}] {f.text!r}")
        print(f"      {f.reason}")


def _print_over_redaction(result: OverRedactionResult) -> None:
    for issue in result.issues:
        print(f"    ✗ {issue.location!r}")
        print(f"      {issue.concern}")


def _print_file_results(
    path: Path,
    reid: JudgeResult,
    missed: MissedPIIResult,
    over: OverRedactionResult | None,
) -> None:
    all_passed = reid.passed and missed.passed and (over is None or over.passed)
    status = "PASS" if all_passed else "FAIL"
    print(f"\n  [{status}] {path.name}")

    print(f"    re-identification: {'pass' if reid.passed else 'FAIL'}")
    if not reid.passed:
        _print_reid(reid)

    print(f"    missed PII:        {'pass' if missed.passed else 'FAIL'}")
    if not missed.passed:
        _print_missed_pii(missed)

    if over is not None:
        print(f"    over-redaction:    {'pass' if over.passed else 'FAIL'}")
        if not over.passed:
            _print_over_redaction(over)
    else:
        print(f"    over-redaction:    skipped (no original available)")


# ---------------------------------------------------------------------------
# Report saving
# ---------------------------------------------------------------------------

def _save_report(
    file_results: list[tuple[Path, JudgeResult, MissedPIIResult, OverRedactionResult | None]],
    report_path: Path,
) -> None:
    def _count_failed(results, key):
        return sum(1 for _, r, m, o in results if not getattr(
            {"reid": r, "missed": m, "over": o}[key], "passed", True
        ))

    n_reid_failed = sum(1 for _, r, _, _ in file_results if not r.passed)
    n_missed_failed = sum(1 for _, _, m, _ in file_results if not m.passed)
    n_over_failed = sum(1 for _, _, _, o in file_results if o is not None and not o.passed)

    payload = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_files": len(file_results),
            "reidentification_failed": n_reid_failed,
            "missed_pii_failed": n_missed_failed,
            "over_redaction_failed": n_over_failed,
        },
        "files": [
            {
                "source": str(path),
                "reidentification": {
                    "passed": reid.passed,
                    "verdicts": [asdict(v) for v in reid.verdicts],
                },
                "missed_pii": {
                    "passed": missed.passed,
                    "findings": [asdict(f) for f in missed.findings],
                },
                "over_redaction": (
                    {"passed": over.passed, "issues": [asdict(i) for i in over.issues]}
                    if over is not None else None
                ),
            }
            for path, reid, missed, over in file_results
        ],
    }
    report_path.write_text(json.dumps(payload, indent=2))
    print(f"\n  report → {report_path}")


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def _judge_dir(output_dir: Path) -> int:
    """Run all judges on an output directory. Returns total failure count."""
    inputs_dir = output_dir.parent / "inputs"
    paths = _collect_paths(output_dir)
    if not paths:
        print("  (no files to judge)")
        return 0

    file_results = []
    for path in paths:
        redacted_text = path.read_text(encoding="utf-8")

        reid = judge(redacted_text, source=str(path))
        missed = judge_missed_pii(redacted_text, source=str(path))

        over = None
        if inputs_dir.exists():
            original_path = _find_original(path, inputs_dir)
            if original_path:
                over = judge_over_redaction(
                    original_path.read_text(encoding="utf-8"),
                    redacted_text,
                    source=str(path),
                )

        _print_file_results(path, reid, missed, over)
        file_results.append((path, reid, missed, over))

    _save_report(file_results, output_dir / _REPORT_FILENAME)

    return sum(
        1 for _, r, m, o in file_results
        if not r.passed or not m.passed or (o is not None and not o.passed)
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2:
        dirs = [d for d in _DEFAULT_OUTPUT_DIRS if d.exists()]
        if not dirs:
            print("no output directories found; run the pipeline first")
            return 1
        total_failed = 0
        for d in dirs:
            print(f"\n{'═' * 50}")
            print(f"Judging {d}")
            total_failed += _judge_dir(d)
        return 1 if total_failed else 0

    target = Path(sys.argv[1])
    if target.is_dir():
        n_failed = _judge_dir(target)
        return 1 if n_failed else 0
    if target.is_file():
        redacted_text = target.read_text(encoding="utf-8")
        reid = judge(redacted_text, source=str(target))
        missed = judge_missed_pii(redacted_text, source=str(target))
        _print_file_results(target, reid, missed, over=None)
        _save_report([(target, reid, missed, None)], target.parent / _REPORT_FILENAME)
        return 0 if (reid.passed and missed.passed) else 1

    print(f"error: {target} does not exist")
    return 1


if __name__ == "__main__":
    sys.exit(main())
