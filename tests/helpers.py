"""Shared test helpers for loading pre-generated pipeline outputs."""
import json
from pathlib import Path

from redactor.parsers.slack_json import parse as parse_slack


def msg_out(input_dir: Path, output_dir: Path, json_file: str, contains: str) -> str:
    """Return the redacted text of the message whose original text contains `contains`."""
    export = parse_slack(str(input_dir / json_file))
    ts = next((msg.ts for msg in export.messages if contains in msg.text), None)
    if ts is None:
        raise ValueError(f"No message containing {contains!r} in {json_file}")
    data = json.loads((output_dir / f"redacted_{json_file}").read_text())
    for msg in data["messages"]:
        if msg.get("ts") == ts:
            return msg["text"]
    raise ValueError(f"ts={ts!r} not found in redacted output for {json_file}")


def md_block_out(output_dir: Path, md_file: str, contains: str) -> str:
    """Return the first double-newline block in a redacted markdown file that contains `contains`."""
    text = (output_dir / f"redacted_{md_file}").read_text()
    for block in text.split("\n\n"):
        if contains in block:
            return block
    raise ValueError(f"No block containing {contains!r} in redacted_{md_file}")


def page_out(output_dir: Path, pdf_stem: str, page_num: int) -> str:
    """Return the redacted text of a specific PDF page."""
    text = (output_dir / f"redacted_{pdf_stem}.txt").read_text()
    for section in text.split("\n\n"):
        if section.startswith(f"--- Page {page_num} ---"):
            return section[len(f"--- Page {page_num} ---\n"):]
    raise ValueError(f"Page {page_num} not found in redacted {pdf_stem}.txt")
