"""Parses Markdown files into a MarkdownDocument struct, split by heading sections."""
import re
from pathlib import Path
from redactor.models import MarkdownDocument, MarkdownSection

_HEADING_RE = re.compile(r"(?m)^(#{1,6} .+)$")


def parse(md_path: str) -> MarkdownDocument:
    with open(md_path) as f:
        content = f.read()

    filename = Path(md_path).name
    # re.split with a capturing group interleaves the separators into the result:
    # [pre, heading, body, heading, body, ...]
    parts = _HEADING_RE.split(content)
    sections = []

    # content before the first heading
    if parts[0].strip():
        sections.append(MarkdownSection(heading="", level=0, text=parts[0].strip()))

    for i in range(1, len(parts), 2):
        heading_line = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        level = len(re.match(r"^(#+)", heading_line).group(1))
        sections.append(
            MarkdownSection(
                heading=heading_line,
                level=level,
                text=(heading_line + "\n" + body).strip(),
            )
        )

    return MarkdownDocument(filename=filename, sections=sections)
