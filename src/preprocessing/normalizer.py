"""Etapa 7: Normalização de texto."""

import re
import unicodedata
from src.core.preprocessing_config import DEFAULT_PREPROCESSING_CONFIG
import ftfy


def normalize_text(text: str) -> str:
    """
    Normaliza texto aplicando etapas em ordem:
    
    a) ftfy.fix_text() para corrigir encoding
    b) unicodedata.normalize("NFC", text)
    c) Substituir múltiplos espaços por um único espaço
    d) Substituir múltiplas quebras de linha (\n{3,}) por \n\n
    
    Args:
        text: Texto para processar.
    
    Returns:
        Texto normalizado.
    """
    config = DEFAULT_PREPROCESSING_CONFIG.normalization
    
    # a) Corrigir encoding com ftfy se disponível e configurado
    if config.use_ftfy:
        text = ftfy.fix_text(text)
    
    # b) Normalizar Unicode para NFC (ou NFD conforme config)
    text = unicodedata.normalize(config.unicode_form, text)
    
    # c) Substituir múltiplos espaços por um único
    if config.normalize_spaces:
        text = re.sub(r" {2,}", " ", text)
    
    # d) Substituir múltiplas quebras de linha por número máximo configurado
    if config.normalize_newlines:
        min_breaks = config.min_consecutive_newlines
        max_breaks = config.max_newlines_after_normalize
        pattern = r"\n{" + str(min_breaks) + r",}"
        replacement = "\n" * max_breaks
        text = re.sub(pattern, replacement, text)
    
    return text
