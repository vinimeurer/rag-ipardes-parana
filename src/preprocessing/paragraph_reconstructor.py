"""Etapa 5: Reconstituição de parágrafos."""

import re


def _is_section_or_title(line: str) -> bool:
    """
    Verifica se uma linha é seção/título e não deve ser juntada.
    
    Inclui:
    - Linhas totalmente em maiúsculas
    - Linhas que começam com número + ponto/parêntese (1. TÍTULO, 2.1 SEÇÃO)
    - Captions de tabelas/gráficos/figuras (TABELA 1, GRÁFICO 5, etc)
    - Linhas que parecem ser continuação de título (todas as palavras começam com maiúscula)
    """
    stripped = line.strip()
    
    if not stripped:
        return False
    
    # 1. Linha totalmente em maiúsculas
    if stripped.isupper() and any(c.isalpha() for c in stripped):
        return True
    
    # 2. Começa com numeração de seção (1. 2.1 3.4, etc)
    if re.match(r"^\d+[\.\)]\s+", stripped):
        return True
    
    # 3. Captions de elementos visuais
    if re.match(r"^(TABELA|GRÁFICO|FIGURA|QUADRO|IMAGEM|MAPA)\s+\d+", stripped, re.IGNORECASE):
        return True
    
    # 4. Continuação de título: todas as palavras principais começam com maiúscula
    # Exemplo: "DESENVOLVIMENTO PARANAENSE: CONTEXTO, TENDÊNCIAS E DESAFIOS"
    words = stripped.split()
    if len(words) >= 3:
        capitalized_count = sum(1 for w in words if w and w[0].isupper())
        if capitalized_count >= len(words) * 0.8:  # 80% das palavras com maiúscula
            return True
    
    return False


def reconstruct_paragraphs(text: str) -> str:
    """
    Junte linhas consecutivas que fazem parte do mesmo parágrafo.
    
    Estratégia CONSERVADORA:
    - NÃO junta se próxima linha é título/seção
    - NÃO junta se próxima linha começa com MAIÚSCULA
    - NÃO junta se próxima linha está vazia
    - Junta APENAS se: linha atual não termina com ponto E próxima começa com minúscula
    
    Args:
        text: Texto para processar.
    
    Returns:
        Texto com parágrafos reconstituídos (conservador).
    """
    lines = text.split("\n")
    result = []
    
    i = 0
    while i < len(lines):
        current_line = lines[i]
        
        # Se linha está vazia, manter como separador
        if current_line.strip() == "":
            result.append("")
            i += 1
            continue
        
        # Se é título/seção, não juntar
        if _is_section_or_title(current_line):
            result.append(current_line)
            i += 1
            continue
        
        # Tentar juntar com próximas linhas
        paragraph = current_line
        i += 1
        
        while i < len(lines):
            next_line = lines[i]
            
            # Parar se próxima linha está vazia
            if next_line.strip() == "":
                break
            
            # Parar se próxima linha é título/seção
            if _is_section_or_title(next_line):
                break
            
            # Parar se próxima linha começa com MAIÚSCULA (muito conservador)
            next_stripped = next_line.lstrip()
            if next_stripped and next_stripped[0].isupper():
                break
            
            # Juntar APENAS se:
            # - Linha atual não termina com pontuação forte (. ! ?)
            # - E próxima começa com minúscula
            current_stripped = paragraph.rstrip()
            
            ends_with_punctuation = current_stripped and current_stripped[-1] in ".!?:"
            starts_with_lowercase = next_stripped and next_stripped[0].islower()
            
            if not ends_with_punctuation and starts_with_lowercase:
                paragraph += " " + next_stripped
                i += 1
            else:
                break
        
        result.append(paragraph)
    
    return "\n".join(result)
