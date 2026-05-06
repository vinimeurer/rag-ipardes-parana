"""
Extrator textual estrutural com coordenadas completas.
"""

from typing import Any

import pdfplumber


class PDFTextExtractor:
    """
    Extrator estrutural de texto.
    """

    HEADER_LIMIT = 50
    FOOTER_LIMIT = 760

    def extract_text_blocks(
        self,
        page: pdfplumber.page.Page,
    ) -> list[dict[str, Any]]:
        """
        Extrai blocos textuais estruturados.

        Args:
            page: Página PDF.

        Returns:
            Lista de blocos estruturados.
        """

        words = page.extract_words(
            keep_blank_chars=False,
            use_text_flow=True,
            extra_attrs=[
                "fontname",
                "size",
            ],
        )

        if not words:
            return []

        lines = self._group_words_into_lines(words)

        blocks = []

        for line in lines:
            if not line:
                continue

            line_top = line.get("top", 0)

            # Remove header
            if line_top < self.HEADER_LIMIT:
                continue

            # Remove footer
            if line_top > self.FOOTER_LIMIT:
                continue

            text = line.get("text", "").strip()

            if not text:
                continue

            x0 = line.get("x0", 0)
            x1 = line.get("x1", 0)
            top = line.get("top", 0)
            bottom = line.get("bottom", 0)

            blocks.append(
                {
                    "text": text,
                    "x0": round(x0, 2),
                    "x1": round(x1, 2),
                    "top": round(top, 2),
                    "bottom": round(bottom, 2),
                    "line_top": round(top, 2),
                    "width": round(
                        x1 - x0,
                        2,
                    ),
                    "height": round(
                        bottom - top,
                        2,
                    ),
                    "font_size": round(
                        line.get("font_size", 0),
                        2,
                    ),
                    "font_name": line.get(
                        "font_name",
                        "",
                    ),
                    "is_upper": text.isupper(),
                    "word_count": len(text.split()),
                }
            )

        return blocks

    def _group_words_into_lines(
        self,
        words: list[dict[str, Any]],
        tolerance: float = 3,
    ) -> list[dict[str, Any]]:
        """
        Agrupa palavras em linhas.

        Args:
            words: Lista de palavras.
            tolerance: Tolerância vertical.

        Returns:
            Linhas estruturadas.
        """

        if not words:
            return []

        sorted_words = sorted(
            words,
            key=lambda w: (
                w.get("top", 0),
                w.get("x0", 0),
            ),
        )

        lines = []
        current_line = []

        current_top = sorted_words[0].get(
            "top",
            0,
        )

        for word in sorted_words:
            word_top = word.get("top", 0)

            if abs(word_top - current_top) <= tolerance:
                current_line.append(word)

            else:
                if current_line:
                    lines.append(
                        self._build_line(
                            current_line
                        )
                    )

                current_line = [word]
                current_top = word_top

        if current_line:
            lines.append(
                self._build_line(current_line)
            )

        return lines

    def _build_line(
        self,
        words: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Constrói estrutura da linha.

        Args:
            words: Palavras da linha.

        Returns:
            Linha estruturada.
        """

        if not words:
            return {}

        sorted_words = sorted(
            words,
            key=lambda w: w.get("x0", 0),
        )

        text = " ".join(
            word.get("text", "")
            for word in sorted_words
        ).strip()

        valid_sizes = [
            w.get("size", 0)
            for w in sorted_words
            if w.get("size") is not None
        ]

        avg_font_size = (
            sum(valid_sizes) / len(valid_sizes)
            if valid_sizes
            else 0
        )

        return {
            "text": text,
            "x0": min(
                w.get("x0", 0)
                for w in sorted_words
            ),
            "x1": max(
                w.get("x1", 0)
                for w in sorted_words
            ),
            "top": min(
                w.get("top", 0)
                for w in sorted_words
            ),
            "bottom": max(
                w.get("bottom", 0)
                for w in sorted_words
            ),
            "font_size": round(
                avg_font_size,
                2,
            ),
            "font_name": sorted_words[0].get(
                "fontname",
                "",
            ),
        }