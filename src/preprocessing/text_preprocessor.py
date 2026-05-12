import re
import unicodedata
from typing import Pattern

from ..core.preprocessing_config import CleaningConfig


class TextPreprocessor:
    """Normalize and clean extracted page text.

    Args:
        config: Cleaning configuration controlling cleaning behaviour.
    """

    def __init__(self, config: CleaningConfig):
        self.config = config
        self._page_num_re: Pattern[str] = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)
        self._multi_space_re: Pattern[str] = re.compile(r"[ \t]{2,}")
        self._blank_re: Pattern[str] = re.compile(r"\n{3,}")

    def process_page(self, text: str) -> str:
        """Process a single page of extracted text.

        The method applies Unicode normalization, control character removal,
        optional page-number removal, whitespace normalization, line-break
        joining inside paragraphs, note/footnote standardization and empty-line
        deduplication.

        Args:
            text: Raw page text as extracted from the PDF.

        Returns:
            Cleaned page text.
        """
        text = self._normalize_unicode(text)
        text = self._remove_control_chars(text)
        if self.config.remove_page_numbers:
            text = self._remove_page_numbers(text)
        if self.config.normalize_whitespace:
            text = self._normalize_whitespace(text)
        text = self._fix_line_breaks(text)
        text = self._standardize_notes(text)
        if self.config.dedup_empty_lines:
            text = self._dedup_blank_lines(text)
        return text.strip()

    def _normalize_unicode(self, text: str) -> str:
        """Normalize text to Unicode NFC form.

        Args:
            text: Input text.

        Returns:
            Normalized text.
        """
        return unicodedata.normalize("NFC", text)

    def _remove_control_chars(self, text: str) -> str:
        """Remove ASCII control characters except tab and newline.

        Args:
            text: Input text.

        Returns:
            Text without control characters.
        """
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    def _remove_page_numbers(self, text: str) -> str:
        """Remove lines that contain only a page number.

        Args:
            text: Input text.

        Returns:
            Text without isolated page numbers.
        """
        lines = text.splitlines()
        filtered = [l for l in lines if not self._page_num_re.fullmatch(l.strip())]
        return "\n".join(filtered)

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse repeated spaces/tabs and rstrip each line.

        Args:
            text: Input text.

        Returns:
            Text with normalized whitespace.
        """
        text = self._multi_space_re.sub(" ", text)
        lines = [line.rstrip() for line in text.splitlines()]
        return "\n".join(lines)

    def _fix_line_breaks(self, text: str) -> str:
        """Join internal line breaks inside paragraphs while preserving paragraphs.

        Args:
            text: Input text.

        Returns:
            Text where paragraph internal breaks are joined.
        """
        paragraphs = re.split(r"\n{2,}", text)
        fixed = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            p = re.sub(r"\n", " ", p)
            p = re.sub(r"\s+", " ", p)
            fixed.append(p)
        return "\n\n".join(fixed)

    def _standardize_notes(self, text: str) -> str:
        """Standardize common note and source markers.

        Args:
            text: Input text.

        Returns:
            Text with standardized 'FONTE:' and 'NOTA:' markers.
        """
        text = re.sub(r"(?i)fonte[:\s]*", "FONTE: ", text)
        text = re.sub(r"(?i)nota[s]?:[:\s]*", "NOTA: ", text)
        return text

    def _dedup_blank_lines(self, text: str) -> str:
        """Collapse sequences of more than two blank lines into two.

        Args:
            text: Input text.

        Returns:
            Text with deduplicated blank lines.
        """
        return self._blank_re.sub("\n\n", text)
