"""
Módulo principal de pré-processamento dos documentos extraídos.
Lê os arquivos markdown gerados pelo extrator, processa o texto 
por página com detecção de seções, integra as tabelas, e salva 
em formato JSON unificado para o pipeline
"""

import json
from pathlib import Path
from typing import Optional

from ..core.logger import setup_logger
from ..core.preprocessing_config import PreprocessingConfig
from .content_filter import ContentFilter
from .content_merger import ContentMerger
from .content_processor import get_processing_strategy
from .page_parser import PageParser
from .preprocessor_utils import ProcessResult, PreprocessorUtils
from .table_processor import TableProcessor


class Preprocessor:
    """
    Converte os arquivos markdown extraídos para o formato JSON processado
    compatível com o pipeline de chunking. Lida com limpeza de texto, 
    detecção de seções e integração de tabelas.

    Args:
        config: Configuração de pré-processamento opcional. Se omitida, são usadas as configurações padrão.

    Métodos:
        run_document: Pré-processa um único documento identificado por `pdf_key`.
        run_all: Pré-processa todos os documentos encontrados no diretório de extração.
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.in_dir = Path(self.config.paths.extracted_dir)
        self.out_dir = Path(self.config.paths.processed_dir)
        self.content_filter = ContentFilter(self.config.content_filter)
        self.table_processor = TableProcessor()
        self.logger = setup_logger(__name__)

    def run_document(self, pdf_key: str) -> ProcessResult:
        """
        Pré-processa um único documento extraído identificado por `pdf_key`.

        Lê a fonte markdown, processa o texto por página com rastreamento 
        de seções, integra tabelas, e salva em formato JSON unificado.

        Args:
            pdf_key: Identificador do documento (corresponde ao nome da pasta no diretório de extração).
        
        Returns:
            Um ProcessResult com estatísticas do processamento.
        """
        src_md = self.in_dir / pdf_key / f"{pdf_key}.md"
        if not src_md.exists():
            raise FileNotFoundError(f"Markdown source not found: {src_md}")

        md_content = src_md.read_text(encoding="utf-8")
        pages_data = PageParser.parse_pages(md_content)

        has_sections = pdf_key != "analise_conjuntural"
        strategy = get_processing_strategy(pdf_key, self.config.cleaning)
        content_items = strategy.process(pdf_key, pages_data)

        tables = self.table_processor.load_tables_for_document(pdf_key, self.in_dir)
        content_items = ContentMerger.merge_content_and_tables(content_items, tables)
        items_before_filter = len(content_items)
        content_items = self.content_filter.filter(content_items, pdf_key)
        items_filtered = items_before_filter - len(content_items)

        metadata = PreprocessorUtils.build_metadata(pdf_key, len(pages_data), has_sections)

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
            items_filtered=items_filtered,
        )

        PreprocessorUtils.log_processing_summary(result)
        return result

    def run_all(self, keys: Optional[list[str]] = None) -> list[ProcessResult]:
        """
        Pré-processa todos os documentos encontrados no diretório de extração.

        Args:
            keys: Lista opcional de `pdf_key` explícitos para processar. Se omitida, processa todos os diretórios encontrados.

        Returns:
            Lista de ProcessResult para cada documento processado.
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

