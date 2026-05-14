"""
Módulo de filtro de conteúdo para remover itens sem valor semântico.

Implementa filtros progressivos: blocos só-header, páginas institucionais,
sumários, referências bibliográficas, e marcação de conteúdo auxiliar.
"""

import re
from typing import Optional

from ..core.logger import setup_logger


SKIP_UNTIL_PAGE = {
    "desenvolvimento_paranaense": 5,
    "analise_conjuntural": 3,
    "avaliacoes_politicas": 4,
}

SUMMARY_SECTIONS = {"SUMÁRIO", "SUMARIO", "SUMARIO EXECUTIVO", "ÍNDICE"}
REFERENCES_SECTIONS = {"REFERÊNCIAS", "REFERENCIAS", "BIBLIOGRAPHY", "REFERÊNCIAS BIBLIOGRÁFICAS"}
AUXILIARY_SECTIONS = {"LISTA DE SIGLAS", "SIGLAS", "ABREVIAÇÕES"}
ORPHAN_REFERENCE_PREFIXES = ("GRÁFICO", "FIGURA", "QUADRO", "TABELA")
SHORT_CAPTION_MIN_TOKENS = 1
SHORT_CAPTION_MAX_TOKENS = 40


class ContentFilter:
    """
    Filtra itens de conteúdo removendo blocos sem valor semântico.

    Aplica filtros sequenciais apenas em itens de tipo 'text', deixando
    tabelas intactas. Marca itens auxiliares para diferenciação posterior.
    """

    def __init__(self):
        self.logger = setup_logger(__name__)

    def filter(self, content_items: list[dict], pdf_key: str) -> list[dict]:
        """
        Filtra itens de conteúdo aplicando uma sequência de critérios.

        Retorna uma lista filtrada onde itens de tipo 'text' foram processados
        através de cinco filtros sequenciais e itens de tipo 'table' passam
        intactos, exceto pelo filtro de páginas institucionais.

        Args:
            content_items: Array de itens de conteúdo (texto e tabelas).
            pdf_key: Identificador do documento para buscar configurações.

        Returns:
            Array filtrado com estatísticas registradas em log.
        """
        original_count = len(content_items)
        items_before_filter = content_items.copy()

        filtered = []
        counts = {
            "header_only": 0,
            "institutional_pages": 0,
            "sumario": 0,
            "referencias": 0,
            "orphan_references": 0,
            "short_captions": 0,
            "auxiliary_marked": 0,
        }

        for item in items_before_filter:
            if item.get("type") != "text":
                if item.get("type") == "table":
                    page = item.get("page", 0)
                    if page > SKIP_UNTIL_PAGE.get(pdf_key, 0):
                        filtered.append(item)
                    else:
                        counts["institutional_pages"] += 1
                else:
                    filtered.append(item)
                continue

            if self._is_header_only(item):
                counts["header_only"] += 1
                continue

            page = item.get("page", 0)
            if page <= SKIP_UNTIL_PAGE.get(pdf_key, 0):
                counts["institutional_pages"] += 1
                continue

            if self._is_summary(item):
                counts["sumario"] += 1
                continue

            if self._is_reference(item):
                counts["referencias"] += 1
                continue

            if self._is_orphan_reference(item):
                counts["orphan_references"] += 1
                continue

            if self._is_short_caption(item):
                counts["short_captions"] += 1
                continue

            item = self._mark_auxiliary(item)
            if item.get("is_auxiliary"):
                counts["auxiliary_marked"] += 1

            filtered.append(item)

        items_filtered = original_count - len(filtered)

        self.logger.debug(
            "[%s] Filtrage concluída: %d → %d itens | "
            "header_only=%d | institutional=%d | sumario=%d | referencias=%d | orphan_references=%d | short_captions=%d | auxiliary_marked=%d",
            pdf_key,
            original_count,
            len(filtered),
            counts["header_only"],
            counts["institutional_pages"],
            counts["sumario"],
            counts["referencias"],
            counts["orphan_references"],
            counts["short_captions"],
            counts["auxiliary_marked"],
        )

        return filtered

    def _is_header_only(self, item: dict) -> bool:
        """
        Verifica se um item contém apenas cabeçalhos sem corpo de texto.

        Args:
            item: Dicionário de item com campo 'content'.

        Returns:
            True se o conteúdo, após remover linhas de cabeçalho, ficar vazio.
        """
        body = re.sub(r"^#+\s+.*$", "", item["content"], flags=re.MULTILINE).strip()
        return len(body) == 0

    def _is_summary(self, item: dict) -> bool:
        """
        Verifica se um item está em seção de sumário ou índice.

        Args:
            item: Dicionário de item com campo 'sections'.

        Returns:
            True se qualquer seção corresponder a um termo de sumário.
        """
        return any(s.strip().upper() in SUMMARY_SECTIONS for s in item.get("sections", []))

    def _is_reference(self, item: dict) -> bool:
        """
        Verifica se um item está em seção de referências bibliográficas.

        Args:
            item: Dicionário de item com campo 'sections'.

        Returns:
            True se qualquer seção corresponder a um termo de referências.
        """
        return any(s.strip().upper() in REFERENCES_SECTIONS for s in item.get("sections", []))

    def _is_orphan_reference(self, item: dict) -> bool:
        """
        Verifica se um item curto é apenas uma referência solta a gráfico, figura,
        quadro ou tabela sem corpo de dados associado.

        Esses blocos costumam ser títulos extraídos de imagens/tabelas e não
        contêm informação suficiente para responder perguntas.
        """
        content = item.get("content", "").strip()
        if not content:
            return False

        token_count = len(content.split())
        if token_count >= 30:
            return False

        first_line = content.lstrip().splitlines()[0].strip().upper()
        if not first_line.startswith(ORPHAN_REFERENCE_PREFIXES):
            return False

        if self._has_table_body(content):
            return False

        return True

    def _has_table_body(self, content: str) -> bool:
        """Detecta se o conteúdo já contém linhas de tabela Markdown."""
        return any(line.lstrip().startswith("|") for line in content.splitlines())

    def _is_short_caption(self, item: dict) -> bool:
        """
        Verifica se um item é um caption muito curto (10-50 tokens).

        Esses itens são legítimos como captions de tabelas, mas geram chunks
        minúsculos no chunker e não têm valor semântico suficiente por si só.
        """
        content = item.get("content", "").strip()
        if not content:
            return False

        token_count = len(content.split())
        return SHORT_CAPTION_MIN_TOKENS <= token_count <= SHORT_CAPTION_MAX_TOKENS

    def _mark_auxiliary(self, item: dict) -> dict:
        """
        Marca um item como auxiliar se estiver em seção de siglas ou abreviações.

        Args:
            item: Dicionário de item com campo 'sections'.

        Returns:
            Item com campo 'is_auxiliary' definido se aplicável.
        """
        if any(s.strip().upper() in AUXILIARY_SECTIONS for s in item.get("sections", [])):
            item["is_auxiliary"] = True
        return item
