"""Etapa 1: Filtragem de páginas irrelevantes."""

import re
from src.core.preprocessing_config import DEFAULT_PREPROCESSING_CONFIG


def is_page_empty(text: str, min_chars: int = None) -> bool:
    """
    Verifica se página tem conteúdo útil.
    
    Critério a) Texto vazio ou com menos de 150 caracteres úteis após strip.
    """
    if min_chars is None:
        min_chars = DEFAULT_PREPROCESSING_CONFIG.filters.min_useful_characters
    return len(text.strip()) < min_chars


def is_institutional_credit_page(text: str) -> bool:
    """
    Detecta páginas de créditos institucionais.
    
    Critério b) Contém padrões como "GOVERNO DO ESTADO DO PARANÁ", "Governador",
    "Secretário de Estado", "Vice-Governador" e variações.
    """
    patterns = DEFAULT_PREPROCESSING_CONFIG.filters.institutional_patterns
    text_upper = text.upper()
    for pattern in patterns:
        if re.search(pattern, text_upper):
            return True
    return False


def is_index_page(text: str) -> bool:
    """
    Detecta páginas de sumário/índice.
    
    Critério c) Contém 3 ou mais linhas com sequência de 5+ pontos consecutivos
    (padrão de índice: "Tópico..................página").
    """
    lines = text.split("\n")
    config = DEFAULT_PREPROCESSING_CONFIG.filters
    
    dotted_pattern = r"\.{" + str(config.min_consecutive_dots) + r",}"
    dotted_lines = sum(1 for line in lines if re.search(dotted_pattern, line))
    
    return dotted_lines >= config.min_dotted_lines_for_index


def filter_pages(pages: list[dict]) -> tuple[list[dict], dict]:
    """
    Filtra páginas irrelevantes e retorna relatório de remoções.
    
    Args:
        pages: Lista de dicts com chaves 'page', 'text', 'document', etc.
    
    Returns:
        (páginas filtradas, relatório de filtragem)
    """
    filtered = []
    report = {
        "total_input": len(pages),
        "removed_empty": 0,
        "removed_institutional": 0,
        "removed_index": 0,
        "total_output": 0,
    }
    
    for page_data in pages:
        text = page_data.get("text", "")
        page_num = page_data.get("page")
        
        if is_page_empty(text):
            report["removed_empty"] += 1
            continue
        
        if is_institutional_credit_page(text):
            report["removed_institutional"] += 1
            continue
        
        if is_index_page(text):
            report["removed_index"] += 1
            continue
        
        filtered.append(page_data)
    
    report["total_output"] = len(filtered)
    return filtered, report
