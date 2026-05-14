import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.logger import setup_logger
from ..core.preprocessing_config import PreprocessingConfig
from .section_parser import SectionParser
from .table_processor import TableProcessor
from .text_cleaner import TextCleaner


@dataclass
class ProcessResult:
    pdf_key: str
    output_path: Path
    total_pages: int
    total_text_items: int
    total_table_items: int
    has_sections: bool
    used_page_fallback: bool = False

    @property
    def total_items(self) -> int:
        """Total content items (text + tables)."""
        return self.total_text_items + self.total_table_items


class Preprocessor:
    """Run preprocessing over extracted documents.

    Converts extracted markdown files to processed JSON format compatible
    with the chunking pipeline. Handles text cleaning, section detection,
    and table integration.

    Args:
        config: Optional preprocessing configuration. If omitted, defaults
            are used.
    """

    _PAGE_TAG_RE = re.compile(r"<!--\s*PAGE:\s*(\d+)\s*-->")

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.in_dir = Path(self.config.paths.extracted_dir)
        self.out_dir = Path(self.config.paths.processed_dir)
        self.cleaner = TextCleaner(self.config.cleaning)
        self.table_processor = TableProcessor()
        self.logger = setup_logger(__name__)

    def run_document(self, pdf_key: str) -> ProcessResult:
        """Preprocess a single extracted document identified by `pdf_key`.

        Reads the markdown source, processes text by page with section
        tracking, integrates tables, and saves as unified JSON format.

        Args:
            pdf_key: Identifier of the document (matches folder name in
                the extracted directory).

        Returns:
            A ProcessResult with processing statistics.
        """
        src_md = self.in_dir / pdf_key / f"{pdf_key}.md"
        if not src_md.exists():
            raise FileNotFoundError(f"Markdown source not found: {src_md}")

        md_content = src_md.read_text(encoding="utf-8")
        pages_data = self._parse_pages_from_markdown(md_content)

        has_sections = pdf_key != "analise_conjuntural"
        content_items = []

        if has_sections:
            content_items = self._process_with_section_detection(pdf_key, pages_data)
        else:
            content_items = self._process_with_page_fallback(pdf_key, pages_data)

        tables = self.table_processor.load_tables_for_document(pdf_key, self.in_dir)
        content_items = self._merge_content_and_tables(content_items, tables)

        metadata = {
            "pdf_key": pdf_key,
            "description": self._get_document_description(pdf_key),
            "total_pages": len(pages_data),
            "processed_at": self._get_timestamp(),
            "has_sections": has_sections,
        }

        output = {
            "metadata": metadata,
            "content": content_items,
        }

        out_path = self.out_dir / f"{pdf_key}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        text_items = sum(1 for i in content_items if i.get("type") == "text")
        table_items = sum(1 for i in content_items if i.get("type") == "table")
        used_fallback = not has_sections

        result = ProcessResult(
            pdf_key=pdf_key,
            output_path=out_path,
            total_pages=len(pages_data),
            total_text_items=text_items,
            total_table_items=table_items,
            has_sections=has_sections,
            used_page_fallback=used_fallback,
        )

        self._log_processing_summary(result)
        return result

    def run_all(self, keys: Optional[list[str]] = None) -> list[ProcessResult]:
        """Preprocess all documents found in the extracted directory.

        Args:
            keys: Optional explicit list of `pdf_key` values to process.

        Returns:
            List of ProcessResult for each processed document.
        """
        keys = keys or [p.name for p in self.in_dir.iterdir() if p.is_dir()]
        results = []

        self.logger.info("Starting preprocessing for %d document(s).", len(keys))

        for k in keys:
            try:
                res = self.run_document(k)
                results.append(res)
            except Exception:
                self.logger.exception("Failed to preprocess '%s'", k)
                continue

        self.logger.info("Preprocessing completed: %d document(s).", len(results))
        return results

    def _parse_pages_from_markdown(self, content: str) -> list[dict]:
        """Parse markdown content into pages using PAGE tags.

        Each page is extracted between consecutive PAGE tags. The first
        page starts from the beginning of the document.

        Args:
            content: Full markdown content from source file.

        Returns:
            List of dicts with 'page_number' and 'text' keys.
        """
        pages = []
        tag_positions = [(m.start(), int(m.group(1))) for m in self._PAGE_TAG_RE.finditer(content)]

        if not tag_positions:
            return [{"page_number": 0, "text": content}]

        for idx, (pos, page_num) in enumerate(tag_positions):
            end_pos = tag_positions[idx + 1][0] if idx + 1 < len(tag_positions) else len(content)
            page_content = content[pos:end_pos]
            page_content = self._PAGE_TAG_RE.sub("", page_content, count=1).strip()

            pages.append({"page_number": page_num, "text": page_content})

        return pages

    def _process_with_section_detection(
        self, pdf_key: str, pages_data: list[dict]
    ) -> list[dict]:
        """Process pages with markdown header detection, breaking each page into multiple items per section.

        Detects markdown headers (#, ##, ###, etc.) and maintains active
        section state across pages using SectionParser. When a new header
        is detected, the current block is finalized and a new block starts.
        Each block inherits the sections that were active BEFORE the header
        that initiates it, ensuring the block captures its surrounding context.

        Args:
            pdf_key: Document identifier.
            pages_data: List of page dicts with page_number and text.

        Returns:
            List of content items ordered by page, with multiple items per page
            when headers are detected.
        """
        content_items = []
        section_parser = SectionParser()

        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]

            if not text.strip():
                continue

            cleaned_text, _ = self.cleaner.clean_markdown(
                text, source_id=f"{pdf_key}:p{page_num}"
            )

            if not cleaned_text.strip():
                continue

            lines = cleaned_text.split("\n")
            current_block_lines = []
            current_block_sections = section_parser.current_sections.copy()

            for line in lines:
                sections_before_update = section_parser.current_sections.copy()

                is_header = section_parser.update(line)

                if is_header:

                    if current_block_lines:
                        block_text = "\n".join(current_block_lines).strip()
                        if block_text:
                            if not current_block_sections:
                                current_block_sections = [f"pagina_{page_num}"]
                            content_items.append({
                                "document": pdf_key,
                                "page": page_num,
                                "sections": current_block_sections,
                                "type": "text",
                                "content": block_text,
                            })

                    current_block_lines = [line]
                    current_block_sections = section_parser.current_sections.copy() 
                else:
                    current_block_lines.append(line)

            if current_block_lines:
                block_text = "\n".join(current_block_lines).strip()
                if block_text:

                    if not current_block_sections:
                        current_block_sections = [f"pagina_{page_num}"]

                    content_items.append({
                        "document": pdf_key,
                        "page": page_num,
                        "sections": current_block_sections,
                        "type": "text",
                        "content": block_text,
                    })

        return content_items

    def _process_with_page_fallback(
        self, pdf_key: str, pages_data: list[dict]
    ) -> list[dict]:
        """Process pages with page-number-only sections (for analise_conjuntural).

        Documents without true section hierarchy use page numbers as pseudo-sections.
        This preserves document structure for retrieval without inferring sections.

        Args:
            pdf_key: Document identifier.
            pages_data: List of page dicts with page_number and text.

        Returns:
            List of content items with page-based sections.
        """
        content_items = []

        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]

            if not text.strip():
                continue

            cleaned_text, _ = self.cleaner.clean_markdown(
                text,
                source_id=f"{pdf_key}:p{page_num}",
            )

            if not cleaned_text.strip():
                continue

            content_items.append(
                {
                    "document": pdf_key,
                    "page": page_num,
                    "sections": [f"pagina_{page_num}"],
                    "type": "text",
                    "content": cleaned_text,
                }
            )

        return content_items

    def _merge_content_and_tables(
        self, text_items: list[dict], table_items: list[dict]
    ) -> list[dict]:
        """Merge text and table items maintaining page order.

        Combines text and table content into a single ordered array,
        then sorts by page number. Within each page, text appears before
        tables. Fills in section information for tables based on active
        sections at their page or nearest preceding page with sections.

        Args:
            text_items: List of text content items.
            table_items: List of table content items (with empty sections).

        Returns:
            Merged and sorted list of content items.
        """
        all_items = text_items + table_items
        all_items.sort(key=lambda x: (x.get("page", 0), x.get("type") == "table"))

        section_map = {}
        for item in text_items:
            page = item.get("page")
            if page and item.get("sections"):
                section_map[page] = item.get("sections")

        last_sections = None
        for item in all_items:
            page = item.get("page")
            if page in section_map:
                last_sections = section_map[page]
            
            if item.get("type") == "table":
                if page in section_map:
                    item["sections"] = section_map[page]
                elif last_sections:
                    item["sections"] = last_sections
                else:
                    item["sections"] = []

        return all_items

    def _get_document_description(self, pdf_key: str) -> str:
        """Get human-readable description for a document.

        Args:
            pdf_key: Document identifier.

        Returns:
            Description string.
        """
        descriptions = {
            "desenvolvimento_paranaense": "Desenvolvimento Paranaense - Análise socioeconômica do Estado",
            "analise_conjuntural": "Análise Conjuntural - Julho/Agosto 2025",
            "avaliacoes_politicas": "Avaliações Políticas Públicas Brasil",
        }
        return descriptions.get(pdf_key, pdf_key)

    def _get_timestamp(self) -> str:
        """Return current timestamp in ISO format."""
        return datetime.now().isoformat()

    def _log_processing_summary(self, result: ProcessResult) -> None:
        """Log summary statistics after processing a document.

        Args:
            result: Processing result object.
        """
        fallback_note = " (página fallback)" if result.used_page_fallback else ""
        self.logger.info(
            "[%s] páginas=%d | itens_texto=%d | tabelas=%d | total=%d%s | saída=%s",
            result.pdf_key,
            result.total_pages,
            result.total_text_items,
            result.total_table_items,
            result.total_items,
            fallback_note,
            result.output_path.name,
        )

