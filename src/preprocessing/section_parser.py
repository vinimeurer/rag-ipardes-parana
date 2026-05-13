import re


class SectionParser:
    """Maintains state of active sections while traversing markdown lines.

    Detects markdown headers (#, ##, ###, etc.) and maintains a stack
    of active sections that reflects the current document hierarchy.

    The stack is updated using the following logic: when a header of
    level N is detected, all headers of level >= N are removed from
    the stack before adding the new header. This ensures proper nesting
    without accumulating sibling sections.
    """

    _HEADER_RE = re.compile(r"^(#+)\s+(.+)$")

    def __init__(self):
        """Initialize parser with empty section stack."""
        self._sections = []

    def update(self, line: str) -> bool:
        """Process a line and update section stack if it is a header.

        Args:
            line: A line from the markdown document.

        Returns:
            True if the line was a header, False otherwise.
        """
        match = self._HEADER_RE.match(line.strip())
        if not match:
            return False

        level = len(match.group(1))
        title = match.group(2).strip()

        while self._sections and self._sections[-1][0] >= level:
            self._sections.pop()

        self._sections.append((level, title))
        return True

    @property
    def current_sections(self) -> list[str]:
        """Return a copy of the currently active sections list.

        Returns:
            List of section titles in hierarchy order.
        """
        return [title for _, title in self._sections]

    def reset(self):
        """Reset parser state for processing a new document."""
        self._sections = []
