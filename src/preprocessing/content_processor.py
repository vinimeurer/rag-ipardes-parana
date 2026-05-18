"""
Módulo responsável por processar o conteúdo das páginas com diferentes estratégias.
"""

from abc import ABC, abstractmethod

from .section_parser import SectionParser
from .text_cleaner import TextCleaner
from ..core.preprocessing_config import CleaningConfig


class ContentProcessingStrategy(ABC):
    """
    Interface abstrata para estratégias de processamento de conteúdo.
    """
    
    @abstractmethod
    def process(self, pdf_key: str, pages_data: list[dict]) -> list[dict]:
        """
        Processa as páginas e retorna itens de conteúdo.
        
        Args:
            pdf_key: Identificador do documento.
            pages_data: Lista de dicionários de páginas com page_number e text.
        
        Returns:
            Lista de itens de conteúdo com estrutura padronizada.
        """
        pass


class SectionDetectionStrategy(ContentProcessingStrategy):
    """
    Estratégia de processamento com detecção de cabeçalhos markdown.
    
    Quebra cada página em múltiplos itens por seção, detectando cabeçalhos
    markdown e mantendo o estado das seções ativas.
    """
    
    def __init__(self, cleaning_config: CleaningConfig = None):
        self.cleaner = TextCleaner(cleaning_config or CleaningConfig())
    
    def process(self, pdf_key: str, pages_data: list[dict]) -> list[dict]:
        """
        Processa as páginas com detecção de cabeçalhos markdown.
        
        Detecta cabeçalhos markdown (#, ##, ###, etc.) e mantém o estado das
        seções ativas usando SectionParser. Quando um novo cabeçalho é detectado,
        o bloco atual é finalizado e um novo bloco começa.
        
        Args:
            pdf_key: Identificador do documento.
            pages_data: Lista de dicionários de páginas com page_number e text.
        
        Returns:
            Lista de itens de conteúdo ordenados por página.
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


class PageFallbackStrategy(ContentProcessingStrategy):
    """
    Estratégia de processamento usando apenas números de página como seções.
    
    Documentos sem hierarquia de seções verdadeira usam números de página como
    pseudo-seções, preservando a estrutura do documento para recuperação.
    """
    
    def __init__(self, cleaning_config: CleaningConfig = None):
        self.cleaner = TextCleaner(cleaning_config or CleaningConfig())
    
    def process(self, pdf_key: str, pages_data: list[dict]) -> list[dict]:
        """
        Processa as páginas usando apenas números de página como seções.
        
        Args:
            pdf_key: Identificador do documento.
            pages_data: Lista de dicionários de páginas com page_number e text.
        
        Returns:
            Lista de itens de conteúdo com seções baseadas em páginas.
        """
        content_items = []
        
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
            
            content_items.append({
                "document": pdf_key,
                "page": page_num,
                "sections": [f"pagina_{page_num}"],
                "type": "text",
                "content": cleaned_text,
            })
        
        return content_items


def get_processing_strategy(pdf_key: str, cleaning_config: CleaningConfig = None) -> ContentProcessingStrategy:
    """
    Factory function para obter a estratégia apropriada para um documento.
    
    Args:
        pdf_key: Identificador do documento.
        cleaning_config: Configuração de limpeza opcional.
    
    Returns:
        Estratégia de processamento apropriada para o documento.
    """
    if pdf_key == "analise_conjuntural":
        return PageFallbackStrategy(cleaning_config)
    return SectionDetectionStrategy(cleaning_config)
