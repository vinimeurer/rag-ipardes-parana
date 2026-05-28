"""
Extração de conteúdo de PDFs usando Docling (IBM).

Responsável por converter PDFs em representações estruturadas
(texto, markdown, JSON) preservando metadados de página, seção
e tabelas — tratadas como elementos de primeira classe.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import DoclingDocument
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from .pdf_splitter import split_pdf, cleanup_splits
from .table_extractor import ExtractedTable, TableExtractionResult, TableExtractor
from ..core.ingestion_config import IngestionPipelineConfig
from ..core.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class ExtractedPage:
    """Representa o conteúdo textual extraído de uma única página."""

    page_number: int
    text: str
    markdown: str


@dataclass
class ExtractionResult:
    """Resultado completo da extração de um PDF."""

    pdf_key: str
    pdf_path: Path
    pages: list[ExtractedPage] = field(default_factory=list)
    tables: list[ExtractedTable] = field(default_factory=list)
    full_text: str = ""
    full_markdown: str = ""
    metadata: dict = field(default_factory=dict)
    success: bool = False
    error: Optional[str] = None

    @property
    def has_tables(self) -> bool:
        """Indica se tabelas foram encontradas no documento."""
        return len(self.tables) > 0


class DoclingPDFExtractor:
    """
    Extrator de PDFs usando Docling com pipeline CPU-only.

    Converte PDFs em texto estruturado, markdown e JSON,
    sem requerer GPU ou serviços externos. Tabelas são extraídas
    como estruturas independentes pelo TableExtractor, preservando
    sua semântica matricial para uso diferenciado no pipeline RAG.
    """

    def __init__(self, config: IngestionPipelineConfig):
        """
        Inicializa o extrator com a configuração do pipeline.

        Args:
            config: Configuração completa do pipeline de ingestão.
        """
        self.config = config
        self._converter = self._build_converter()
        self._table_extractor = TableExtractor()

    def _build_converter(self) -> DocumentConverter:
        """
        Constrói o DocumentConverter do Docling com opções CPU-only.

        A extração de estrutura de tabelas (do_table_structure) é sempre
        habilitada quando configurada, pois é necessária para o
        TableExtractor produzir grades bem formadas.

        Returns:
            Instância configurada do DocumentConverter.
        """
        pipeline_options = PdfPipelineOptions(
            do_ocr=self.config.backend.do_ocr,
            do_table_structure=self.config.backend.do_table_structure,
            generate_page_images=self.config.backend.generate_page_images,
        )

        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def extract(self, pdf_key: str) -> ExtractionResult:
        """
        Extrai conteúdo completo de um PDF identificado pela sua chave.

        Executa em sequência:
        1. Conversão Docling -> DoclingDocument
        2. Exportação de texto e markdown completos
        3. Extração de conteúdo por página (somente texto, sem tabelas)
        4. Extração dedicada de tabelas via TableExtractor

        Args:
            pdf_key: Chave do PDF em PDF_SOURCES da configuração.

        Returns:
            ExtractionResult com conteúdo extraído, tabelas e metadados,
            ou resultado com success=False em caso de erro.
        """
        source_info = self.config.pdf_sources.get(pdf_key)
        if not source_info:
            return ExtractionResult(
                pdf_key=pdf_key,
                pdf_path=Path(),
                success=False,
                error=f"Chave '{pdf_key}' não encontrada em PDF_SOURCES.",
            )

        pdf_path: Path = source_info.local_path

        if not pdf_path.exists():
            return ExtractionResult(
                pdf_key=pdf_key,
                pdf_path=pdf_path,
                success=False,
                error=f"Arquivo não encontrado: {pdf_path}",
            )

        logger.info("Iniciando extração de '%s' (%s)", pdf_key, pdf_path.name)

        try:
            splits = split_pdf(pdf_path, self.config.batch_size)
            
            all_pages: list[ExtractedPage] = []
            all_tables: list[ExtractedTable] = []

            for split_path, page_offset in splits:
                conversion = self._converter.convert(str(split_path))
                docling_doc: DoclingDocument = conversion.document

                batch_pages = self._extract_pages(docling_doc)

                for page in batch_pages:
                    page.page_number += page_offset

                    page.markdown = f"<!-- PAGE: {page.page_number} -->\n\n{page.markdown}"

                all_pages.extend(batch_pages)

                table_result: TableExtractionResult = self._table_extractor.extract(
                    pdf_key, docling_doc
                )

                for idx, table in enumerate(table_result.tables):
                    table.page_number += page_offset
                    table.table_index = len(all_tables) + idx

                all_tables.extend(table_result.tables)

            cleanup_splits(splits)

            full_text = "\n\n".join(page.text for page in all_pages)
            full_markdown = "\n\n".join(page.markdown for page in all_pages)

            metadata = {
                "pdf_key": pdf_key,
                "source_path": str(pdf_path),
                "description": getattr(source_info, "description", ""),
                "total_pages": len(all_pages),
                "total_tables": len(all_tables),
                "tables_found": len(all_tables),
                "docling_schema_version": "2",
                "batch_size": self.config.batch_size,
                "num_batches": len(splits),
            }

            logger.info(
                "Extração concluída para '%s': %d páginas, %d tabelas, %d batches.",
                pdf_key,
                len(all_pages),
                len(all_tables),
                len(splits),
            )

            return ExtractionResult(
                pdf_key=pdf_key,
                pdf_path=pdf_path,
                pages=all_pages,
                tables=all_tables,
                full_text=full_text,
                full_markdown=full_markdown,
                metadata=metadata,
                success=True,
            )

        except Exception as exc:
            logger.error("Erro ao extrair '%s': %s", pdf_key, exc, exc_info=True)
            return ExtractionResult(
                pdf_key=pdf_key,
                pdf_path=pdf_path,
                success=False,
                error=str(exc),
            )

    def _extract_pages(self, docling_doc: DoclingDocument) -> list[ExtractedPage]:
        """
        Extrai conteúdo por página, preservando estrutura markdown do Docling.

        Tabelas são intencionalmente ignoradas aqui pois têm tratamento
        dedicado via TableExtractor. Isso evita que o conteúdo tabular
        seja duplicado no texto corrido das páginas.

        O campo 'text' é salvo puro (texto plano) para o JSON.
        O campo 'markdown' preserva a estrutura markdown do Docling.
        
        **Nota**: A tag `<!-- PAGE: X -->` será adicionada APÓS o offset ser
        aplicado na função extract(). Isso garante que os números de página
        sejam globais (considerando todos os batches) e não locais ao batch.

        Args:
            docling_doc: Documento convertido pelo Docling.

        Returns:
            Lista de ExtractedPage com texto por página, sem tabelas, sem tag PAGE.
        """
        from docling_core.types.doc import TableItem as _TableItem

        pages: list[ExtractedPage] = []

        if not (hasattr(docling_doc, "pages") and docling_doc.pages):
            full_text = docling_doc.export_to_text()
            full_markdown = f"<!-- PAGE: 1 -->\n\n{full_text}"
            return [ExtractedPage(page_number=1, text=full_text, markdown=full_markdown)]

        page_texts: dict[int, list[str]] = {p: [] for p in sorted(docling_doc.pages.keys())}
        page_markdowns: dict[int, list[str]] = {p: [] for p in sorted(docling_doc.pages.keys())}

        for item, _level in docling_doc.iterate_items():
            if isinstance(item, _TableItem):
                continue
            if not (hasattr(item, "prov") and item.prov):
                continue

            page_no = item.prov[0].page_no
            if page_no not in page_markdowns:
                continue

            if not hasattr(item, "text") or not item.text:
                continue

            text_content = item.text.strip()

            page_texts[page_no].append(text_content)

            item_type = type(item).__name__
            markdown_content = text_content
            
            if item_type in ("SectionHeaderItem", "TitleItem"):
                level = getattr(item, "level", 1)
                markdown_content = f"{'#' * level} {text_content}"

            page_markdowns[page_no].append(markdown_content)

        for page_no in sorted(page_markdowns.keys()):

            page_text = "\n\n".join(t for t in page_texts[page_no] if t)

            page_md_content = "\n\n".join(t for t in page_markdowns[page_no] if t)

            page_markdown = page_md_content

            pages.append(
                ExtractedPage(
                    page_number=page_no,
                    text=page_text,
                    markdown=page_markdown,
                )
            )

        return pages
