import re


class SectionParser:
    """Maintains state of active sections while traversing markdown lines.

    Detects markdown headers and infers hierarchy from section numbering
    (e.g. '3.', '3.1', '3.1.2') rather than markdown heading level (#, ##).
    This is necessary because docling often exports all headers at the same
    markdown level (#), losing the visual hierarchy of the original PDF.
    Falls back to markdown level when no numeric pattern is detected.
    """

    _HEADER_RE = re.compile(r"^(#+)\s+(.+)$")

    _NUMERIC_RE = re.compile(r"^(\d+(?:\.\d+)*\.?)\s+")

    def __init__(self):
        self._sections = []

    def _infer_level(self, title: str, markdown_level: int) -> int:
        """Infer section depth from numeric prefix, fallback to markdown level.

        '3.'     → depth 1
        '3.1'    → depth 2
        '3.1.2'  → depth 3
        """
        match = self._NUMERIC_RE.match(title)
        if not match:
            return markdown_level

        numeric_part = match.group(1).rstrip(".")
        return len(numeric_part.split("."))

    def update(self, line: str) -> bool:
        match = self._HEADER_RE.match(line.strip())
        if not match:
            return False

        markdown_level = len(match.group(1))
        title = match.group(2).strip()
        level = self._infer_level(title, markdown_level)

        while self._sections and self._sections[-1][0] >= level:
            self._sections.pop()

        self._sections.append((level, title))
        return True

    @property
    def current_sections(self) -> list[str]:
        return [title for _, title in self._sections]

    def reset(self):
        self._sections = []