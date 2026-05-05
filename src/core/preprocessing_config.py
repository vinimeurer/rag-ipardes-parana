"""Configuração centralizada para todo o sistema RAG."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class FilterConfig:
    """Configurações da Etapa 1: Filtração de páginas."""
    
    min_useful_characters: int = 150
    institutional_patterns: List[str] = field(default_factory=lambda: [
        r"GOVERNO\s+DO\s+ESTADO\s+DO\s+PARANÁ",
        r"\bGOVERNADOR\b",
        r"SECRETÁR[IA]{2}\s+DE\s+ESTADO",
        r"VICE-GOVERNADOR",
        r"DIRETORIA\s+(EXECUTIVA|GERAL)",
        r"IPARDES",
        r"DECRETO\s+Nº",
    ])
    min_dotted_lines_for_index: int = 3
    min_consecutive_dots: int = 5


@dataclass
class HeaderFooterConfig:
    """Configurações da Etapa 2: Remoção de headers/footers."""
    
    repetition_threshold: float = 0.30


@dataclass
class HyphenationConfig:
    """Configurações da Etapa 3: Correção de hifenização."""
    
    pattern: str = r"(\w+)-\n(\w+)"
    replacement: str = r"\1\2"


@dataclass
class FootnoteConfig:
    """Configurações da Etapa 4: Remoção de superescritos."""
    
    pattern: str = r"(?<=\w)(\d{1,2})(?=[\s,\.;])"
    preserve_before: List[str] = field(default_factory=lambda: ["$"])
    preserve_after: List[str] = field(default_factory=lambda: ["%"])


@dataclass
class ParagraphConfig:
    """Configurações da Etapa 5: Reconstituição de parágrafos."""
    
    sentence_endings: List[str] = field(default_factory=lambda: [".", "!", "?"])
    list_pattern: str = r"^\s*\d+[\.\)]"


@dataclass
class SectionConfig:
    """Configurações da Etapa 6: Extração de seções."""
    
    min_title_length: int = 10


@dataclass
class NormalizationConfig:
    """Configurações da Etapa 7: Normalização de texto."""
    
    use_ftfy: bool = True
    unicode_form: str = "NFC"
    normalize_spaces: bool = True
    normalize_newlines: bool = True
    min_consecutive_newlines: int = 3
    max_newlines_after_normalize: int = 2


@dataclass
class OutputConfig:
    """Configurações de saída."""
    
    processed_dir: str = "data/processed"
    save_reports: bool = True
    include_timestamp: bool = True


@dataclass
class PreprocessingConfig:
    """Configuração completa do pipeline de pré-processamento."""
    
    filters: FilterConfig = field(default_factory=FilterConfig)
    header_footer: HeaderFooterConfig = field(default_factory=HeaderFooterConfig)
    hyphenation: HyphenationConfig = field(default_factory=HyphenationConfig)
    footnotes: FootnoteConfig = field(default_factory=FootnoteConfig)
    paragraphs: ParagraphConfig = field(default_factory=ParagraphConfig)
    sections: SectionConfig = field(default_factory=SectionConfig)
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    def to_dict(self) -> dict:
        """Converte configuração para dicionário."""
        return {
            "filters": self.filters.__dict__,
            "header_footer": self.header_footer.__dict__,
            "hyphenation": self.hyphenation.__dict__,
            "footnotes": self.footnotes.__dict__,
            "paragraphs": self.paragraphs.__dict__,
            "sections": self.sections.__dict__,
            "normalization": self.normalization.__dict__,
            "output": self.output.__dict__,
        }


# Instância global padrão
DEFAULT_PREPROCESSING_CONFIG = PreprocessingConfig()
