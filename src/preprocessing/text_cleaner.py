"""
Limpeza e normalização de texto extraído de PDFs.

Aplica heurísticas para remover artefatos de extração,
normalizar espaçamento e filtrar conteúdo de baixa qualidade.
"""
import re
import unicodedata
from dataclasses import dataclass

from ..core.preprocessing_config import CleaningConfig
from ..core.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class CleaningStats:
    """Estatísticas produzidas pelo processo de limpeza."""

    original_chars: int = 0
    cleaned_chars: int = 0
    lines_removed: int = 0
    paragraphs_removed: int = 0

    @property
    def reduction_pct(self) -> float:
        """Percentual de redução de caracteres."""
        if self.original_chars == 0:
            return 0.0
        return round((1 - self.cleaned_chars / self.original_chars) * 100, 2)


class TextCleaner:
    """
    Limpador de texto pós-extração de PDFs.

    Aplica as seguintes transformações na ordem:
    1. Normalização Unicode (NFC)
    2. Remoção de hifenização artificial
    3. Normalização de espaços e quebras de linha
    4. Remoção de números de página isolados
    5. Filtragem de linhas muito curtas
    6. Remoção de parágrafos com poucos tokens
    7. Deduplicação de linhas em branco consecutivas
    """

    _PAGE_NUMBER_RE = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)
    _HYPHENATION_RE = re.compile(r"(\w+)-\n(\w+)")
    _MULTI_BLANK_RE = re.compile(r"\n{3,}")
    _MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
    _CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

    def __init__(self, config: CleaningConfig):
        """
        Inicializa o limpador com a configuração de limpeza.

        Args:
            config: Parâmetros de limpeza de texto.
        """
        self.config = config

    def clean(self, text: str, source_id: str = "") -> tuple[str, CleaningStats]:
        """
        Aplica o pipeline completo de limpeza em um texto.

        Args:
            text: Texto bruto extraído do PDF.
            source_id: Identificador opcional para logging.

        Returns:
            Tupla (texto limpo, estatísticas de limpeza).
        """
        stats = CleaningStats(original_chars=len(text))

        text = self._normalize_unicode(text)
        text = self._remove_control_chars(text)

        if self.config.remove_hyphenation:
            text = self._fix_hyphenation(text)

        if self.config.normalize_whitespace:
            text = self._normalize_whitespace(text)

        if self.config.remove_page_numbers:
            text, n_removed = self._remove_page_numbers(text)
            stats.lines_removed += n_removed

        lines, n_short = self._filter_short_lines(text)
        stats.lines_removed += n_short
        text = "\n".join(lines)

        paragraphs, n_para = self._filter_short_paragraphs(text)
        stats.paragraphs_removed += n_para
        text = "\n\n".join(paragraphs)

        if self.config.dedup_empty_lines:
            text = self._dedup_blank_lines(text)

        text = text.strip()
        stats.cleaned_chars = len(text)

        if source_id:
            logger.debug(
                "[%s] Limpeza: %d → %d chars (%.1f%% redução)",
                source_id,
                stats.original_chars,
                stats.cleaned_chars,
                stats.reduction_pct,
            )

        return text, stats

    def clean_markdown(self, markdown: str, source_id: str = "") -> tuple[str, CleaningStats]:
        """
        Limpeza adaptada para texto em formato Markdown.

        Preserva estrutura de títulos e listas enquanto remove artefatos.

        Args:
            markdown: Texto em Markdown extraído pelo Docling.
            source_id: Identificador opcional para logging.

        Returns:
            Tupla (markdown limpo, estatísticas).
        """
        stats = CleaningStats(original_chars=len(markdown))

        markdown = self._normalize_unicode(markdown)
        markdown = self._remove_control_chars(markdown)

        if self.config.remove_hyphenation:
            markdown = self._fix_hyphenation(markdown)

        if self.config.normalize_whitespace:
            markdown = self._normalize_whitespace(markdown)

        if self.config.dedup_empty_lines:
            markdown = self._dedup_blank_lines(markdown)

        markdown = markdown.strip()
        stats.cleaned_chars = len(markdown)

        return markdown, stats

    def clean_table_content(self, content: str) -> str:
        """Clean table content with minimal processing.

        Applies only unicode normalization and control character removal
        without line or paragraph filtering. Table cells are naturally
        short and would be incorrectly removed by heuristic filters
        designed for body text. Filtering short lines would destroy
        table structure, removing valuable data cells and headers.

        Args:
            content: Raw table content from extraction.

        Returns:
            Minimally processed table content.
        """
        content = self._normalize_unicode(content)
        content = self._remove_control_chars(content)
        return content.strip()

    def _normalize_unicode(self, text: str) -> str:
        """Normaliza o texto para forma Unicode NFC."""
        return unicodedata.normalize("NFC", text)

    def _remove_control_chars(self, text: str) -> str:
        """Remove caracteres de controle exceto tabulações e quebras de linha."""
        return self._CONTROL_CHARS_RE.sub("", text)

    def _fix_hyphenation(self, text: str) -> str:
        """Remove hifenização artificial de quebra de linha."""
        return self._HYPHENATION_RE.sub(r"\1\2", text)

    def _normalize_whitespace(self, text: str) -> str:
        """Colapsa múltiplos espaços em um único espaço."""
        text = text.replace('\xa0', ' ')
        text = self._MULTI_SPACE_RE.sub(" ", text)
        lines = [line.rstrip() for line in text.splitlines()]
        return "\n".join(lines)

    def _remove_page_numbers(self, text: str) -> tuple[str, int]:
        """
        Remove linhas que contêm apenas números de página.

        Returns:
            Tupla (texto sem números de página, quantidade de linhas removidas).
        """
        original_lines = text.splitlines()
        filtered = [l for l in original_lines if not self._PAGE_NUMBER_RE.fullmatch(l + "\n")]
        return "\n".join(filtered), len(original_lines) - len(filtered)

    def _filter_short_lines(self, text: str) -> tuple[list[str], int]:
        """
        Filtra linhas abaixo do comprimento mínimo configurado.

        Lines que iniciam com '#' (títulos Markdown) são preservadas.

        Returns:
            Tupla (lista de linhas válidas, quantidade removida).
        """
        lines = text.splitlines()
        filtered = []
        removed = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                filtered.append(line)
            elif len(stripped) >= self.config.min_line_length:
                filtered.append(line)
            else:
                removed += 1
        return filtered, removed

    def _filter_short_paragraphs(self, text: str) -> tuple[list[str], int]:
        """
        Filtra parágrafos com menos tokens que o mínimo configurado.

        Returns:
            Tupla (lista de parágrafos válidos, quantidade removida).
        """
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text)]
        filtered = []
        removed = 0
        for para in paragraphs:
            if not para:
                continue
            token_count = len(para.split())
            if token_count >= self.config.min_paragraph_tokens:
                filtered.append(para)
            else:
                removed += 1
        return filtered, removed

    def _dedup_blank_lines(self, text: str) -> str:
        """Colapsa sequências de mais de duas linhas em branco para duas."""
        return self._MULTI_BLANK_RE.sub("\n\n", text)
