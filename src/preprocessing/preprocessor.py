import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..core.logger import setup_logger

from ..core.preprocessing_config import PreprocessingConfig
from .text_cleaner import TextCleaner
from .table_processor import TableProcessor


@dataclass
class ProcessResult:
    pdf_key: str
    pages: List[dict]
    metadata: dict
    original_chars: int
    cleaned_chars: int
    text_path: Path
    markdown_path: Path
    json_path: Path

    @property
    def reduction_pct(self) -> float:
        if self.original_chars == 0:
            return 0.0
        return round((1 - self.cleaned_chars / self.original_chars) * 100, 2)


class Preprocessor:
    """Run preprocessing over extracted documents.

    Args:
        config: Optional preprocessing configuration. If omitted, defaults
            are used.
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.in_dir = Path(self.config.paths.extracted_dir)
        self.out_dir = Path(self.config.paths.processed_dir)
        self.processor = TextCleaner(self.config.cleaning)
        self.logger = setup_logger(__name__)

    def run_document(self, pdf_key: str) -> ProcessResult:
        """Preprocess a single extracted document identified by `pdf_key`.

        The method reads the extracted JSON, runs page-level cleaning and
        writes cleaned artifacts to the configured processed directory.

        Args:
            pdf_key: Identifier of the document (matches folder name in
                the extracted directory).

        Returns:
            A ProcessResult with cleaned pages and preserved metadata.
        """
        src = self.in_dir / pdf_key / f"{pdf_key}.json"
        if not src.exists():
            raise FileNotFoundError(src)
        payload = src.read_text(encoding="utf-8")
        data = json.loads(payload)
        original_chars = sum(len(p.get("text", "")) for p in data.get("pages", []))
        pages = []
        total_lines_removed = 0
        total_paragraphs_removed = 0
        for p in data.get("pages", []):
            page_text = p.get("text", "")
            cleaned, stats = self.processor.clean(
                page_text,
                source_id=f"{pdf_key}:p{p.get('page_number', '?')}",
            )
            total_lines_removed += stats.lines_removed
            total_paragraphs_removed += stats.paragraphs_removed
            pages.append({"page_number": p.get("page_number"), "text": cleaned})
        result_payload = {
            "metadata": data.get("metadata", {}),
            "pages": pages,
            "tables_count": data.get("tables_count", 0),
            "tables_ref": data.get("tables_ref"),
        }
        out_dir = self.out_dir / pdf_key
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{pdf_key}.json"
        out_path.write_text(
            json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        text_out = out_dir / f"{pdf_key}.txt"
        full_text = "\n\n".join(p["text"] for p in pages)
        text_out.write_text(full_text, encoding="utf-8")
        md_out = out_dir / f"{pdf_key}.md"
        md_out.write_text(full_text, encoding="utf-8")
        cleaned_chars = len(full_text)

        result = ProcessResult(
            pdf_key=pdf_key,
            pages=pages,
            metadata=result_payload["metadata"],
            original_chars=original_chars,
            cleaned_chars=cleaned_chars,
            text_path=text_out,
            markdown_path=md_out,
            json_path=out_path,
        )

        self.logger.info(
            "[%s] páginas=%d | chars=%d→%d (%.1f%% redução) | linhas_removidas=%d | paragrafos_removidos=%d | arquivos: %s, %s, %s",
            pdf_key,
            len(pages),
            result.original_chars,
            result.cleaned_chars,
            result.reduction_pct,
            total_lines_removed,
            total_paragraphs_removed,
            result.json_path.name,
            result.text_path.name,
            result.markdown_path.name,
        )

        return result

    def run_all(self, keys: Optional[List[str]] = None) -> List[ProcessResult]:
        """Preprocess all documents found in the extracted directory.

        Args:
            keys: Optional explicit list of `pdf_key` values to process.

        Returns:
            List of ProcessResult for each processed document.
        """
        keys = keys or [p.name for p in self.in_dir.iterdir() if p.is_dir()]
        results: List[ProcessResult] = []
        self.logger.info("Iniciando pré-processamento para %d documento(s).", len(keys))
        for k in keys:
            try:
                res = self.run_document(k)
                results.append(res)
            except Exception:
                self.logger.exception("Falha ao pré-processar '%s'", k)
                continue
        self.logger.info("Pré-processamento concluído: %d documento(s).", len(results))
        return results

    def process_tables_for_all(self) -> dict:
        """Process extracted tables for all documents.

        Iterates through all documents in the extracted directory,
        processes their tables, and saves to processed directory.

        Returns:
            Dictionary with document counts and processing summary.
        """
        pdf_keys = self._get_all_pdf_keys()
        if not pdf_keys:
            self.logger.warning("Nenhum documento encontrado para processamento de tabelas.")
            return {"documents_with_tables": 0, "total_tables": 0}

        table_processor = TableProcessor(self.config.tables)
        total_tables = 0
        documents_with_tables = 0

        self.logger.info("Iniciando processamento de tabelas para %d documento(s).", len(pdf_keys))

        for pdf_key in pdf_keys:
            try:
                tables = table_processor.process_document_tables(
                    pdf_key, self.in_dir, self.out_dir
                )
                if tables:
                    documents_with_tables += 1
                    total_tables += len(tables)
                    self.logger.info(
                        "[%s] Tabelas processadas: %d", pdf_key, len(tables)
                    )
            except Exception:
                self.logger.exception(
                    "Falha ao processar tabelas do documento '%s'", pdf_key
                )
                continue

        self.logger.info(
            "Processamento de tabelas concluído: %d documento(s) com tabelas | total=%d tabelas",
            documents_with_tables,
            total_tables,
        )

        return {
            "documents_with_tables": documents_with_tables,
            "total_tables": total_tables,
        }

    def _get_all_pdf_keys(self) -> List[str]:
        """Get list of all available PDF keys in extracted directory.

        Returns:
            List of directory names representing PDF keys.
        """
        if not self.in_dir.exists():
            return []
        return [p.name for p in self.in_dir.iterdir() if p.is_dir()]
