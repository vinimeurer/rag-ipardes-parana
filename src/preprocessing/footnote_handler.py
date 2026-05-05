"""Etapa 4: Remoção de superescritos de notas de rodapé."""

import re
from src.core.preprocessing_config import DEFAULT_PREPROCESSING_CONFIG


def remove_footnote_superscripts(text: str) -> str:
    """
    Remove números soltos imediatamente após palavras (superescritos).
    
    Padrão: r'(?<=\w)(\d{1,2})(?=[\s,\.;])' com cuidado para não remover:
    - Valores monetários (precedidos por R$)
    - Percentuais (seguidos de %)
    - Datas (dígito precedente)
    
    Args:
        text: Texto para processar.
    
    Returns:
        Texto com superescritos removidos.
    """
    # Não remover se precedido por R$, %, ou outro dígito
    # Padrão: palavra + 1-2 dígitos + espaço/vírgula/ponto/ponto-vírgula
    # mas não se o dígito for parte de um número monetário, percentual ou data
    
    def should_remove(match):
        """Verifica se o superscrito deve ser removido."""
        full_text = match.string
        pos = match.start()
        
        # Verificar se há R$ antes (monetário)
        if pos >= 2 and full_text[pos-2:pos].strip() == "R":
            return False
        
        # Verificar se há % depois (percentual)
        if match.end() < len(full_text) and full_text[match.end()] == "%":
            return False
        
        # Verificar se há dígito antes (data/número)
        if pos > 0 and full_text[pos-1].isdigit():
            return False
        
        return True
    
    # Procurar por padrão: palavra + 1-2 dígitos + símbolo de pontuação/espaço
    config = DEFAULT_PREPROCESSING_CONFIG.footnotes
    pattern = config.pattern
    
    result = []
    last_end = 0
    
    for match in re.finditer(pattern, text):
        if should_remove(match):
            result.append(text[last_end:match.start()])
        else:
            result.append(text[last_end:match.end()])
        last_end = match.end()
    
    result.append(text[last_end:])
    return "".join(result)
