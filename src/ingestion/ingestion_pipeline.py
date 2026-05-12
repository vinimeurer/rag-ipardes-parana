"""
Pipeline de ingestão de PDFs.

Orquestra a extração (Docling), limpeza (TextCleaner) e
serialização (ExtractionSerializer) para cada PDF configurado.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .pdf_extractor import DoclingPDFExtractor, ExtractionResult
from .serializer import ExtractionSerializer
from .text_cleaner import CleaningStats, TextCleaner
from ..core.ingestion_config import IngestionPipelineConfig
from ..core.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class PipelineDocumentResult:
    """Resultado do processamento de um único documento no pipeline."""

    pdf_key: str
    success: bool
    extraction: Optional[ExtractionResult] = None
    cleaning_stats_text: Optional[CleaningStats] = None
    cleaning_stats_md: Optional[CleaningStats] = None
    saved_artifacts: dict = field(default_factory=dict)
    error: Optional[str] = None
    skipped: bool = False


@dataclass
class PipelineRunResult:
    """Resultado completo de uma execução do pipeline."""

    documents: list[PipelineDocumentResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total de documentos processados."""
        return len(self.documents)

    @property
    def successes(self) -> int:
        """Total de documentos extraídos com sucesso."""
        return sum(1 for d in self.documents if d.success and not d.skipped)

    @property
    def skipped(self) -> int:
        """Total de documentos pulados por já existirem."""
        return sum(1 for d in self.documents if d.skipped)

    @property
    def failures(self) -> int:
        """Total de documentos com falha na extração."""
        return sum(1 for d in self.documents if not d.success and not d.skipped)

    def summary(self) -> str:
        """Retorna um resumo textual da execução do pipeline."""
        return (
            f"Pipeline concluído: {self.total} docs | "
            f"{self.successes} OK | {self.skipped} pulados | {self.failures} falhas"
        )


class IngestionPipeline:
    """
    Pipeline completo de ingestão de PDFs.

    Sequência para cada documento:
    1. Verifica se extração já existe (skip opcional)
    2. Extrai conteúdo com DoclingPDFExtractor
    3. Limpa o texto com TextCleaner
    4. Serializa os artefatos com ExtractionSerializer

    Attributes:
        config: Configuração do pipeline.
        extractor: Instância do extrator de PDFs.
        cleaner: Instância do limpador de texto.
        serializer: Instância do serializador de artefatos.
    """

    def __init__(self, config: Optional[IngestionPipelineConfig] = None):
        """
        Inicializa o pipeline com a configuração fornecida.

        Args:
            config: Configuração do pipeline. Se None, usa defaults.
        """
        self.config = config or IngestionPipelineConfig()
        self.config.ensure_dirs()

        self.extractor = DoclingPDFExtractor(self.config)
        self.cleaner = TextCleaner(self.config.cleaning)
        self.serializer = ExtractionSerializer(self.config)

    def run(self, pdf_keys: Optional[list[str]] = None) -> PipelineRunResult:
        """
        Executa o pipeline para os PDFs especificados ou todos configurados.

        Args:
            pdf_keys: Lista de chaves de PDFs a processar.
                      Se None, processa todos em PDF_SOURCES.

        Returns:
            PipelineRunResult com resultado de cada documento.
        """
        keys = pdf_keys or list(self.config.pdf_sources.keys())
        run_result = PipelineRunResult()

        logger.info("Iniciando pipeline de ingestão para %d PDF(s).", len(keys))

        for key in keys:
            doc_result = self._process_document(key)
            run_result.documents.append(doc_result)

        logger.info(run_result.summary())
        return run_result

    def _process_document(self, pdf_key: str) -> PipelineDocumentResult:
        """
        Processa um único documento pelo pipeline completo.

        Args:
            pdf_key: Chave do PDF em PDF_SOURCES.

        Returns:
            PipelineDocumentResult com o estado do processamento.
        """
        if self.serializer.already_extracted(pdf_key):
            logger.info("'%s' já extraído. Pulando (overwrite=False).", pdf_key)
            return PipelineDocumentResult(
                pdf_key=pdf_key, success=True, skipped=True
            )

        extraction = self.extractor.extract(pdf_key)

        if not extraction.success:
            logger.error("Falha na extração de '%s': %s", pdf_key, extraction.error)
            return PipelineDocumentResult(
                pdf_key=pdf_key,
                success=False,
                extraction=extraction,
                error=extraction.error,
            )

        cleaned_text, stats_text = self.cleaner.clean(
            extraction.full_text, source_id=pdf_key
        )
        cleaned_md, stats_md = self.cleaner.clean_markdown(
            extraction.full_markdown, source_id=f"{pdf_key}(md)"
        )

        saved = self.serializer.save(extraction, cleaned_text, cleaned_md)

        return PipelineDocumentResult(
            pdf_key=pdf_key,
            success=True,
            extraction=extraction,
            cleaning_stats_text=stats_text,
            cleaning_stats_md=stats_md,
            saved_artifacts=saved,
        )
