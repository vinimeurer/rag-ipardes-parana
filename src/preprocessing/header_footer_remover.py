"""Etapa 2: Remoção de cabeçalhos e rodapés repetidos."""

from collections import Counter
from src.core.preprocessing_config import DEFAULT_PREPROCESSING_CONFIG


def identify_repeated_lines(pages: list[dict], threshold: float = None) -> dict[str, set]:
    """
    Identifica linhas que aparecem em mais de N% das páginas por documento.
    
    Args:
        pages: Lista de dicts com 'text' e 'document'.
        threshold: Proporção mínima (0.3 = 30%) para considerar linha como repetida.
    
    Returns:
        Dict com chave=documento, valor=set de linhas a remover.
    """
    if threshold is None:
        threshold = DEFAULT_PREPROCESSING_CONFIG.header_footer.repetition_threshold
    
    pages_by_doc = {}
    for page in pages:
        doc = page.get("document", "unknown")
        if doc not in pages_by_doc:
            pages_by_doc[doc] = []
        pages_by_doc[doc].append(page)
    
    repeated_lines_per_doc = {}
    
    for doc, doc_pages in pages_by_doc.items():
        line_counts = Counter()
        total_pages = len(doc_pages)
        
        # Contar ocorrências de linhas
        for page in doc_pages:
            text = page.get("text", "")
            lines = text.split("\n")
            for line in lines:
                line_stripped = line.strip()
                if len(line_stripped) > 0:
                    line_counts[line_stripped] += 1
        
        # Identificar linhas que aparecem em mais de threshold% das páginas
        threshold_count = total_pages * threshold
        repeated = {line for line, count in line_counts.items() if count > threshold_count}
        repeated_lines_per_doc[doc] = repeated
    
    return repeated_lines_per_doc


def remove_repeated_lines(pages: list[dict], repeated_lines_per_doc: dict) -> tuple[list[dict], dict]:
    """
    Remove linhas repetidas de páginas e retorna relatório.
    
    Args:
        pages: Lista de dicts com 'text' e 'document'.
        repeated_lines_per_doc: Dict documento -> set de linhas a remover.
    
    Returns:
        (páginas processadas, relatório de remoções).
    """
    processed = []
    report = {
        "documents": {},
    }
    
    for page in pages:
        doc = page.get("document", "unknown")
        text = page.get("text", "")
        
        if doc not in report["documents"]:
            report["documents"][doc] = {
                "lines_removed": [],
                "pages_processed": 0,
            }
        
        lines_to_remove = repeated_lines_per_doc.get(doc, set())
        
        # Filtrar linhas
        new_lines = []
        for line in text.split("\n"):
            if line.strip() not in lines_to_remove:
                new_lines.append(line)
            else:
                if line.strip() not in report["documents"][doc]["lines_removed"]:
                    report["documents"][doc]["lines_removed"].append(line.strip())
        
        new_text = "\n".join(new_lines)
        page_copy = page.copy()
        page_copy["text"] = new_text
        processed.append(page_copy)
        
        report["documents"][doc]["pages_processed"] += 1
    
    return processed, report
