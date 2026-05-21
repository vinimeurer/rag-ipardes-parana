"""
Configurações específicas para ingestão e processamento de PDFs.

Centraliza as definições de fontes de PDFs, configurações de parsing
e metadados relacionados aos documentos do IPARDES.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .directory_config import RAW_DATA_DIR


@dataclass
class PDFSourceConfig:
    """Configuração de uma fonte de PDF individual."""
    
    url: str
    local_path: Path
    description: str
    skip_until_page: int = 0


# ============================================================================
# PDF Sources - Os 3 documentos oficiais do IPARDES
# ============================================================================
PDF_SOURCES = {
    "desenvolvimento_paranaense": PDFSourceConfig(
        url="https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2023-09/desenvolvimento_paranaense.pdf",
        local_path=RAW_DATA_DIR / "desenvolvimento_paranaense.pdf",
        description="Desenvolvimento Paranaense - Análise socioeconômica do Estado",
        skip_until_page=5,
    ),
    "analise_conjuntural": PDFSourceConfig(
        url="https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2026-02/Analise_Conjuntural_julho_agosto_2025.pdf",
        local_path=RAW_DATA_DIR / "Analise_Conjuntural_julho_agosto_2025.pdf",
        description="Análise Conjuntural - Julho/Agosto 2025",
        skip_until_page=3,
    ),
    "avaliacoes_politicas": PDFSourceConfig(
        url="https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2025-12/Avaliacoes%20Politicas%20Publicas%20Brasil_revisao%20escopo.pdf",
        local_path=RAW_DATA_DIR / "Avaliacoes Politicas Publicas Brasil_revisao escopo.pdf",
        description="Avaliações de Políticas Públicas Brasil - Revisão de Escopo",
        skip_until_page=4,
    ),
}


@dataclass
class ContentFilterConfig:
    """Configurações para filtragem de conteúdo durante preprocessamento.
    
    Attributes:
        summary_sections: Seções de sumário/índice a serem removidas.
        references_sections: Seções de referências bibliográficas a serem removidas.
        auxiliary_sections: Seções auxiliares (siglas, abreviações) a serem removidas.
        orphan_reference_prefixes: Prefixos de referências órfãs a serem removidas.
        short_caption_min_tokens: Mínimo de tokens em uma caption.
        short_caption_max_tokens: Máximo de tokens para considerar como caption curta.
    """
    
    summary_sections: set[str] = field(default_factory=lambda: {
        "SUMÁRIO", "SUMARIO", "SUMARIO EXECUTIVO", "ÍNDICE"
    })
    references_sections: set[str] = field(default_factory=lambda: {
        "REFERÊNCIAS", "REFERENCIAS", "BIBLIOGRAPHY", "REFERÊNCIAS BIBLIOGRÁFICAS"
    })
    auxiliary_sections: set[str] = field(default_factory=lambda: {
        "LISTA DE SIGLAS", "SIGLAS", "ABREVIAÇÕES"
    })
    orphan_reference_prefixes: tuple[str, ...] = (
        "GRÁFICO", "FIGURA", "QUADRO", "TABELA"
    )
    short_caption_min_tokens: int = 1
    short_caption_max_tokens: int = 40
