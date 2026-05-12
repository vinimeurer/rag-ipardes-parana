import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..core.logger import setup_logger
from ..core.preprocessing_config import TableProcessingConfig


@dataclass
class ProcessedTable:
    """Represents a processed table with content and metadata."""

    table_index: int
    page_number: int | None
    caption: str | None
    content: str
    document: str


class TableProcessor:
    """Process extracted tables and prepare them for RAG pipeline.

    Reads markdown and JSON files from extracted directory, extracts
    metadata, and saves processed tables with embedded content and
    metadata in JSON format.

    Args:
        config: Table processing configuration.
    """

    def __init__(self, config: Optional[TableProcessingConfig] = None):
        self.config = config or TableProcessingConfig()
        self.logger = setup_logger(__name__)

    def process_document_tables(
        self, pdf_key: str, extracted_dir: Path, processed_dir: Path
    ) -> List[ProcessedTable]:
        """Process all tables for a single document.

        Args:
            pdf_key: Document identifier.
            extracted_dir: Root directory containing extracted data.
            processed_dir: Root directory for processed outputs.

        Returns:
            List of ProcessedTable objects.
        """
        tables_src = extracted_dir / pdf_key / "tables"
        if not tables_src.exists():
            return []

        tables_list: List[ProcessedTable] = []
        tables_index_path = tables_src / "tables_index.json"

        if not tables_index_path.exists():
            self.logger.warning(
                "[%s] tables_index.json não encontrado em %s",
                pdf_key,
                tables_src,
            )
            return []

        index_payload = tables_index_path.read_text(encoding="utf-8")
        tables_index = json.loads(index_payload)

        for table_info in tables_index.get("tables", []):
            try:
                processed = self._process_single_table(
                    pdf_key, tables_src, table_info
                )
                if processed:
                    tables_list.append(processed)
            except Exception as e:
                table_idx = table_info.get("table_index", "?")
                self.logger.error(
                    "[%s] Falha ao processar tabela (index=%s): %s",
                    pdf_key,
                    table_idx,
                    str(e),
                )
                continue

        self.save_processed_tables(
            pdf_key, tables_list, extracted_dir, processed_dir
        )

        return tables_list

    def _process_single_table(
        self, pdf_key: str, tables_dir: Path, table_info: dict
    ) -> ProcessedTable | None:
        """Process a single table from extracted files.

        Args:
            pdf_key: Document identifier.
            tables_dir: Directory containing table files.
            table_info: Metadata from tables_index.json.

        Returns:
            ProcessedTable or None if extraction fails.
        """
        table_index = table_info.get("table_index")
        if table_index is None:
            self.logger.warning(
                "[%s] Tabela sem table_index em tables_index.json",
                pdf_key,
            )
            return None

        page_number = table_info.get("page_number")
        caption = table_info.get("caption") if self.config.include_caption else None

        markdown_file = tables_dir / self.config.markdown_file_pattern.format(
            table_index
        )

        if not markdown_file.exists():
            self.logger.warning(
                "[%s] Arquivo de tabela não encontrado: %s",
                pdf_key,
                markdown_file.name,
            )
            return None

        content = markdown_file.read_text(encoding="utf-8")

        return ProcessedTable(
            table_index=table_index,
            page_number=page_number,
            caption=caption,
            content=content,
            document=pdf_key,
        )

    def save_processed_tables(
        self,
        pdf_key: str,
        tables: List[ProcessedTable],
        extracted_dir: Path,
        processed_dir: Path,
    ) -> None:
        """Save processed tables to JSON files in processed directory.

        Creates processed/[pdf_key]/tables/ with individual JSON files
        containing table content and metadata.

        Args:
            pdf_key: Document identifier.
            tables: List of ProcessedTable objects.
            extracted_dir: Root directory containing extracted data.
            processed_dir: Root directory for processed outputs.
        """
        if not tables:
            return

        tables_out_dir = processed_dir / pdf_key / "tables"
        tables_out_dir.mkdir(parents=True, exist_ok=True)

        for table in tables:
            output_file = tables_out_dir / self.config.json_output_pattern.format(
                table.table_index
            )

            payload = {
                "table_index": table.table_index,
                "page_number": table.page_number,
                "caption": table.caption,
                "content": table.content,
                "document": table.document,
            }

            if self.config.extract_metadata:
                tables_index_path = (
                    extracted_dir / pdf_key / "tables" / "tables_index.json"
                )
                if tables_index_path.exists():
                    index_data = json.loads(
                        tables_index_path.read_text(encoding="utf-8")
                    )
                    for table_info in index_data.get("tables", []):
                        if table_info.get("table_index") == table.table_index:
                            payload["metadata"] = {
                                "title": table_info.get("caption"),
                                "num_rows": table_info.get("num_rows"),
                                "num_cols": table_info.get("num_cols"),
                            }
                            break

            output_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
