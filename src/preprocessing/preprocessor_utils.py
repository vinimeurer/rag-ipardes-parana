"""
Módulo com utilitários e helpers para o preprocessador.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..core.logger import setup_logger
from ..core.pdf_config import PDF_SOURCES


@dataclass
class ProcessResult:
    """
    Resultado do processamento de um documento.
    
    Atributos:
        pdf_key: Identificador do documento.
        output_path: Caminho do arquivo de saída.
        total_pages: Número total de páginas processadas.
        total_text_items: Número de itens de texto.
        total_table_items: Número de itens de tabela.
        has_sections: Se o documento tem seções detectadas.
        used_page_fallback: Se foi usado fallback de página.
        items_filtered: Número de itens filtrados.
    """
    
    pdf_key: str
    output_path: Path
    total_pages: int
    total_text_items: int
    total_table_items: int
    has_sections: bool
    used_page_fallback: bool = False
    items_filtered: int = 0

    @property
    def total_items(self) -> int:
        """Total content items (text + tables)."""
        return self.total_text_items + self.total_table_items


class PreprocessorUtils:
    """
    Utilitários para o preprocessador.
    """
    
    @staticmethod
    def get_document_description(pdf_key: str) -> str:
        """
        Obtém uma descrição legível para um documento.
        
        Args:
            pdf_key: Identificador do documento.
        
        Returns:
            String de descrição.
        """
        pdf_config = PDF_SOURCES.get(pdf_key)
        return pdf_config.description if pdf_config else pdf_key
    
    @staticmethod
    def get_timestamp() -> str:
        """
        Retorna o timestamp atual em formato ISO.
        
        Returns:
            String com timestamp ISO.
        """
        return datetime.now().isoformat()
    
    @staticmethod
    def build_metadata(pdf_key: str, total_pages: int, has_sections: bool) -> dict:
        """
        Constrói o dicionário de metadata para o documento.
        
        Args:
            pdf_key: Identificador do documento.
            total_pages: Número total de páginas.
            has_sections: Se o documento tem seções.
        
        Returns:
            Dicionário com metadados.
        """
        return {
            "pdf_key": pdf_key,
            "description": PreprocessorUtils.get_document_description(pdf_key),
            "total_pages": total_pages,
            "processed_at": PreprocessorUtils.get_timestamp(),
            "has_sections": has_sections,
        }
    
    @staticmethod
    def log_processing_summary(result: ProcessResult) -> None:
        """
        Registra estatísticas resumidas após processar um documento.
        
        Args:
            result: Objeto de resultado do processamento.
        """
        logger = setup_logger(__name__)
        fallback_note = " (página fallback)" if result.used_page_fallback else ""
        logger.info(
            "[%s] páginas=%d | itens_texto=%d | tabelas=%d | total=%d | filtrados=%d%s | saída=%s",
            result.pdf_key,
            result.total_pages,
            result.total_text_items,
            result.total_table_items,
            result.total_items,
            result.items_filtered,
            fallback_note,
            result.output_path.name,
        )
