# src/ingestion/table_extractor.py

"""
Extração robusta de tabelas reais.
Ignora falso positivo de layout editorial.
"""

from __future__ import annotations

import re
from typing import Any

import pdfplumber


class PDFTableExtractor:
    """Extrator de tabelas reais."""

    MIN_ROWS = 3
    MIN_COLS = 2

    @staticmethod
    def is_broken_table(rows: list[list[str]]) -> bool:
        """
        Detecta tabelas quebradas.
        """

        text = " ".join(
            str(cell or "")
            for row in rows
            for cell in row
        )

        if not text:
            return True

        # excesso de fragmentação
        small_tokens = re.findall(r"\b[a-zA-Z]{1,2}\b", text)

        ratio = len(small_tokens) / max(len(text.split()), 1)

        return ratio > 0.35

    @staticmethod
    def normalize_rows(
        rows: list[list[Any]],
    ) -> list[list[str]]:
        """
        Limpa células.
        """

        normalized = []

        for row in rows:
            clean_row = []

            for cell in row:
                value = str(cell or "").strip()

                value = re.sub(r"\s+", " ", value)

                clean_row.append(value)

            normalized.append(clean_row)

        return normalized

    @staticmethod
    def table_to_text(
        rows: list[list[str]],
    ) -> str:
        """
        Converte tabela para texto semântico.
        Melhor para embedding.
        """

        if not rows:
            return ""

        headers = rows[0]

        lines = []

        for row in rows[1:]:
            parts = []

            for idx, value in enumerate(row):
                if not value:
                    continue

                header = (
                    headers[idx]
                    if idx < len(headers)
                    else f"coluna_{idx}"
                )

                parts.append(f"{header}: {value}")

            if parts:
                lines.append(" | ".join(parts))

        return "\n".join(lines)

    @classmethod
    def extract_tables(
        cls,
        page: pdfplumber.page.Page,
    ) -> list[dict[str, Any]]:
        """
        Extrai somente tabelas válidas.
        """

        extracted_tables = []

        # sem linhas gráficas = provavelmente não há tabela
        if len(page.lines) < 3 and len(page.rects) < 3:
            return []

        tables = page.find_tables()

        for idx, table in enumerate(tables):
            rows = table.extract()

            if not rows:
                continue

            rows = cls.normalize_rows(rows)

            row_count = len(rows)
            col_count = max(len(r) for r in rows)

            if row_count < cls.MIN_ROWS:
                continue

            if col_count < cls.MIN_COLS:
                continue

            if cls.is_broken_table(rows):
                continue

            semantic_text = cls.table_to_text(rows)

            extracted_tables.append(
                {
                    "table_id": f"table_{idx + 1}",
                    "rows": rows,
                    "row_count": row_count,
                    "column_count": col_count,
                    "semantic_text": semantic_text,
                }
            )

        return extracted_tables