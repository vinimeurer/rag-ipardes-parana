from dataclasses import dataclass, field
from pathlib import Path

from .constants import EXTRACTED_DATA_DIR, PROCESSED_DATA_DIR


@dataclass
class PreprocessingPaths:
    extracted_dir: Path = EXTRACTED_DATA_DIR
    processed_dir: Path = PROCESSED_DATA_DIR


@dataclass
class CleaningConfig:
    remove_hyphenation: bool = True
    remove_headers_footers: bool = True
    remove_page_numbers: bool = True
    normalize_whitespace: bool = True
    dedup_empty_lines: bool = True
    min_line_length: int = 15
    min_paragraph_tokens: int = 5


@dataclass
class TableProcessingConfig:
    extract_metadata: bool = True
    include_caption: bool = True
    markdown_file_pattern: str = "table_{:03d}.md"
    json_output_pattern: str = "table_{:03d}.json"


@dataclass
class PreprocessingConfig:
    paths: PreprocessingPaths = field(default_factory=PreprocessingPaths)
    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    tables: TableProcessingConfig = field(default_factory=TableProcessingConfig)
