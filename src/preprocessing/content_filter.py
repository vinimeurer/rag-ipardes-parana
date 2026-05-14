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

            if self._is_sumario(item):
                counts["sumario"] += 1
                continue

            if self._is_referencias(item):
                counts["referencias"] += 1
                continue

            item = self._mark_auxiliary(item)
            if item.get("is_auxiliary"):
                counts["auxiliary_marked"] += 1

            filtered.append(item)

        items_filtered = original_count - len(filtered)

        self.logger.debug(
            "[%s] Filtrage concluída: %d → %d itens | "
            "header_only=%d | institutional=%d | sumario=%d | referencias=%d | auxiliary_marked=%d",
            pdf_key,
            original_count,
            len(filtered),
            counts["header_only"],
            counts["institutional_pages"],
            counts["sumario"],
            counts["referencias"],
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
