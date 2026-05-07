# src/ingestion/pdf_extractor.py

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber

from src.core.constants import (
    EXTRACTED_DATA_DIR,
    PDF_SOURCES,
)
from src.ingestion.table_extractor import (
    PDFTableExtractor,
)
from src.ingestion.text_extractor import (
    PDFTextExtractor,
)


class PDFLayoutExtractor:
    """
    Pipeline principal de extração estrutural.
    """

    def __init__(self) -> None:
        self.text_extractor = PDFTextExtractor()
        self.table_extractor = PDFTableExtractor()

    def extract_single_pdf(
        self,
        pdf_key: str,
        pdf_path: Path,
    ) -> dict[str, Any]:

        pages_data = []

        with pdfplumber.open(pdf_path) as pdf:

            total_pages = len(pdf.pages)

            for page_number, page in enumerate(
                pdf.pages,
                start=1,
            ):

                blocks = (
                    self.text_extractor.extract_text_blocks(
                        page
                    )
                )

                text = "\n".join(
                    block["text"]
                    for block in blocks
                )

                tables = (
                    self.table_extractor.extract_tables(
                        page
                    )
                )

                pages_data.append(
                    {
                        "document": pdf_key,
                        "page": page_number,
                        "content": text,
                        "blocks": blocks,
                        "tables": tables,
                        "has_tables": len(tables) > 0,
                        "extracted_at": (
                            datetime.utcnow().isoformat()
                        ),
                    }
                )

        result = {
            "success": True,
            "pdf_key": pdf_key,
            "pages_extracted": len(pages_data),
            "total_pages": total_pages,
            "data": pages_data,
        }

        output_path = (
            EXTRACTED_DATA_DIR / f"{pdf_key}.json"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as fp:
            json.dump(
                result,
                fp,
                ensure_ascii=False,
                indent=2,
            )

        return result

    def extract_all_pdfs(self) -> dict[str, Any]:
        """
        Executa extração em todos PDFs.
        """

        results = {}

        for pdf_key, pdf_info in PDF_SOURCES.items():

            pdf_path = pdf_info["local_path"]

            try:
                result = self.extract_single_pdf(
                    pdf_key=pdf_key,
                    pdf_path=pdf_path,
                )

                results[pdf_key] = result

            except Exception as exc:

                print(exc)

                results[pdf_key] = {
                    "success": False,
                    "error": str(exc),
                }

        return results


def validate_extraction(
    results: dict[str, Any],
) -> dict[str, Any]:
    """
    Valida resultados da extração.
    """

    stats = {
        "total_pdfs": len(results),
        "successful": 0,
        "failed": 0,
        "total_pages": 0,
    }

    for result in results.values():

        if result.get("success"):

            stats["successful"] += 1

            stats["total_pages"] += result.get(
                "pages_extracted",
                0,
            )

        else:
            stats["failed"] += 1

    return stats