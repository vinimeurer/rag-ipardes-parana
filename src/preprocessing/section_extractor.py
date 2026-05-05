"""Etapa 6: Extração de metadados de seção."""

from src.core.preprocessing_config import DEFAULT_PREPROCESSING_CONFIG


def extract_sections(pages: list[dict]) -> list[dict]:
    """
    Extrai metadados de seção de cada página.
    
    Varre páginas em ordem. Quando encontra linha toda em maiúsculas
    com mais de 10 caracteres (título de seção), registra como secao_atual.
    Propaga para todos os blocos seguintes até novo título.
    
    Args:
        pages: Lista de dicts com 'text', 'page', 'document'.
    
    Returns:
        Lista de páginas com campo 'section' adicionado.
    """
    processed = []
    current_section = "Unknown"
    config = DEFAULT_PREPROCESSING_CONFIG.sections
    
    for page in pages:
        text = page.get("text", "")
        lines = text.split("\n")
        
        # Procurar por títulos de seção em maiúsculas
        for line in lines:
            stripped = line.strip()
            
            # Critério: linha toda em maiúsculas com mais de min_title_length caracteres
            if (
                len(stripped) > config.min_title_length
                and stripped.isupper()
                and any(c.isalpha() for c in stripped)
            ):
                current_section = stripped
                break
        
        # Adicionar seção ao page data
        page_copy = page.copy()
        page_copy["section"] = current_section
        processed.append(page_copy)
    
    return processed
