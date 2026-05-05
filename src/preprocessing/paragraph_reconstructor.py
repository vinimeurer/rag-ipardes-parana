"""Etapa 5: Reconstituição de parágrafos."""

import re


def reconstruct_paragraphs(text: str) -> str:
    """
    Junte linhas consecutivas que fazem parte do mesmo parágrafo.
    
    Critério para NÃO juntar:
    - Linha em branco separando
    - Linha toda em maiúsculas (título/subtítulo)
    - Linha iniciando com número seguido de ponto ou parêntese (lista numerada)
    
    Critério para JUNTAR:
    - Linha termina sem ponto final e a próxima inicia com letra minúscula
    
    Args:
        text: Texto para processar.
    
    Returns:
        Texto com parágrafos reconstituídos.
    """
    lines = text.split("\n")
    result = []
    
    i = 0
    while i < len(lines):
        current_line = lines[i]
        
        # Se linha está vazia, manter como separador de parágrafo
        if current_line.strip() == "":
            result.append("")
            i += 1
            continue
        
        # Se linha está toda em maiúsculas, é título/subtítulo
        if current_line.strip().isupper() and len(current_line.strip()) > 0:
            result.append(current_line)
            i += 1
            continue
        
        # Se linha inicia com número + ponto/parêntese, é item de lista
        if re.match(r"^\s*\d+[\.\)]", current_line):
            result.append(current_line)
            i += 1
            continue
        
        # Juntar com próximas linhas se critérios forem atendidos
        paragraph = current_line
        i += 1
        
        while i < len(lines):
            next_line = lines[i]
            
            # Parar se próxima linha está vazia
            if next_line.strip() == "":
                break
            
            # Parar se próxima linha é título/subtítulo
            if next_line.strip().isupper() and len(next_line.strip()) > 0:
                break
            
            # Parar se próxima linha é item de lista
            if re.match(r"^\s*\d+[\.\)]", next_line):
                break
            
            # Juntar se:
            # - Linha atual não termina com ponto/interrogação/exclamação
            # - Próxima linha inicia com letra minúscula
            current_stripped = paragraph.rstrip()
            next_stripped = next_line.lstrip()
            
            ends_with_punctuation = current_stripped and current_stripped[-1] in ".!?"
            starts_with_lowercase = next_stripped and next_stripped[0].islower()
            
            if not ends_with_punctuation and starts_with_lowercase:
                paragraph += " " + next_stripped
                i += 1
            else:
                break
        
        result.append(paragraph)
    
    return "\n".join(result)
