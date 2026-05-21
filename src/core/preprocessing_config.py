"""
Configurações centralizadas para o pipeline de preprocessamento.

Define as classes de configuração usando dataclasses para organizar os parâmetros 
relacionados ao preprocessamento de documentos.
"""

from dataclasses import dataclass, field
from pathlib import Path

from .directory_config import EXTRACTED_DATA_DIR, PROCESSED_DATA_DIR
from .pdf_config import ContentFilterConfig


@dataclass
class PreprocessingPaths:
    extracted_dir: Path = EXTRACTED_DATA_DIR
    processed_dir: Path = PROCESSED_DATA_DIR


@dataclass
class CleaningConfig:
    remove_headers: bool = True
    header_patterns: list[str] | None = None
    remove_page_numbers: bool = True
    remove_hyphenation: bool = True
    min_line_length: int = 20
    min_paragraph_tokens: int = 5
    normalize_whitespace: bool = True
    dedup_empty_lines: bool = True


@dataclass
class TableProcessingConfig:
    include_caption: bool = True
    markdown_file_pattern: str = "table_{:03d}.md"
    json_output_pattern: str = "table{:03d}.json"
    extract_metadata: bool = False


@dataclass
class PreprocessingConfig:
    paths: PreprocessingPaths = field(default_factory=PreprocessingPaths)
    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    tables: TableProcessingConfig = field(default_factory=TableProcessingConfig)
    content_filter: ContentFilterConfig = field(default_factory=ContentFilterConfig)

