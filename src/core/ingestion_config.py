"""
Configurações centralizadas para o pipeline de ingestão de PDFs.

Todas as opções de extração, serialização e controle de pipeline
são definidas aqui, sem duplicação nos módulos de ingestão.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from .constants import (
    RAW_DATA_DIR,
    EXTRACTED_DATA_DIR,
    LOGS_DIR,
    PDF_SOURCES,
)


@dataclass
class DoclingBackendConfig:
    """Configurações do backend de parsing do Docling."""

    do_ocr: bool = False
    do_table_structure: bool = True
    generate_page_images: bool = False
    images_scale: float = 1.0
    ocr_lang: list = field(default_factory=lambda: ["pt", "en"])


@dataclass
class ExtractionOutputConfig:
    """Configurações de saída da extração."""

    save_markdown: bool = True
    save_json: bool = True
    save_raw_text: bool = True
    output_dir: Path = EXTRACTED_DATA_DIR
    overwrite_existing: bool = False


@dataclass
class IngestionPipelineConfig:
    """Configuração completa do pipeline de ingestão."""

    raw_data_dir: Path = RAW_DATA_DIR
    extracted_data_dir: Path = EXTRACTED_DATA_DIR
    logs_dir: Path = LOGS_DIR
    pdf_sources: dict = field(default_factory=lambda: PDF_SOURCES)
    timeout_seconds: int = 300
    max_pages: Optional[int] = None
    num_workers: int = 1
    backend: DoclingBackendConfig = field(default_factory=DoclingBackendConfig)
    output: ExtractionOutputConfig = field(default_factory=ExtractionOutputConfig)

    def ensure_dirs(self) -> None:
        """Cria os diretórios de saída se não existirem."""
        self.extracted_data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.output.output_dir.mkdir(parents=True, exist_ok=True)

    def pdf_output_dir(self, pdf_key: str) -> Path:
        """
        Retorna o diretório de saída para um PDF específico.

        Args:
            pdf_key: Chave do PDF em PDF_SOURCES.

        Returns:
            Path do diretório de saída.
        """
        return self.extracted_data_dir / pdf_key