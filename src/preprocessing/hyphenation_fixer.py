"""Etapa 3: Correção de hifenização."""

import re
from src.core.preprocessing_config import DEFAULT_PREPROCESSING_CONFIG


def fix_hyphenation(text: str) -> str:
    """
    Detecta e une palavras hifenizadas no fim de linha.
    
    Padrão: r'(\w+)-\n(\w+)' substituído por r'\1\2'
    
    Args:
        text: Texto para processar.
    
    Returns:
        Texto com hifenizações corrigidas.
    """
    config = DEFAULT_PREPROCESSING_CONFIG.hyphenation
    pattern = config.pattern
    replacement = config.replacement
    fixed = re.sub(pattern, replacement, text)
    return fixed
