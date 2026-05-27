"""
Módulo de filtro de conteúdo para remover itens sem valor semântico.

Implementa filtros progressivos: blocos só-header, páginas institucionais,
sumários, referências bibliográficas, e marcação de conteúdo auxiliar.
"""

import re
from typing import Optional

from ..core.logger import setup_logger
from ..core.preprocessing_config import ContentFilterConfig, PreprocessingConfig
from ..core.pdf_config import PDF_SOURCES


def get_skip_until_page(pdf_key: str) -> int:
    """
    Obtém o número de página até a qual pular para um documento.
    
    Args:
        pdf_key: Identificador do documento.
    
    Returns:
        Número de páginas a pular (0 se não configurado).
    """
    pdf_config = PDF_SOURCES.get(pdf_key)
    return pdf_config.skip_until_page if pdf_config else 0


class ContentFilter:
    """
    Filtra itens de conteúdo removendo blocos sem valor semântico.

    Aplica filtros sequenciais apenas em itens de tipo 'text', deixando
    tabelas intactas. Marca itens auxiliares para diferenciação posterior.
    
    Args:
        config: Configuração de filtro opcional. Se omitida, usa a configuração padrão.
    """

    def __init__(self, config: Optional[ContentFilterConfig] = None):
        self.config = config or ContentFilterConfig()
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
        skip_until_page = get_skip_until_page(pdf_key)

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
                    if page > skip_until_page:
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
            if page <= skip_until_page:
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
        return any(s.strip().upper() in self.config.summary_sections for s in item.get("sections", []))

    def _is_reference(self, item: dict) -> bool:
        """
        Verifica se um item está em seção de referências bibliográficas.

        Args:
            item: Dicionário de item com campo 'sections'.

        Returns:
            True se qualquer seção corresponder a um termo de referências.
        """
        return any(s.strip().upper() in self.config.references_sections for s in item.get("sections", []))

    def _is_orphan_reference(self, item: dict) -> bool:
        """
        Verifica se um item curto é apenas uma referência solta a gráfico, figura,
        quadro ou tabela sem corpo de dados associado.

        Args:
            item: Dicionário de item com campo 'content' e 'sections'.
            
        Returns:
            True se o item parecer uma referência órfã, False caso contrário.
        """
        content = item.get("content", "").strip()
        if not content:
            return False

        token_count = len(content.split())
        if token_count >= 30:
            return False

        first_line = content.lstrip().splitlines()[0].strip().upper()
        if not first_line.startswith(self.config.orphan_reference_prefixes):
            return False

        if self._has_table_body(content):
            return False

        return True

    def _has_table_body(self, content: str) -> bool:
        """
        Detecta se o conteúdo já contém linhas de tabela Markdown.

        Args:
            content: Conteúdo a ser verificado.

        Returns:
            True se o conteúdo contiver linhas de tabela, False caso contrário.
        """
        return any(line.lstrip().startswith("|") for line in content.splitlines())

    def _is_short_caption(self, item: dict) -> bool:
        """
        Verifica se um item é um caption muito curto (10-50 tokens).

        Esses itens são legítimos como captions de tabelas, mas geram chunks
        minúsculos no chunker e não têm valor semântico suficiente por si só.

        Args:
            item: Dicionário de item com campo 'content'.

        Returns:
            True se o item parecer um caption curto, False caso contrário.
        """
        content = item.get("content", "").strip()
        if not content:
            return False

        token_count = len(content.split())
        return self.config.short_caption_min_tokens <= token_count <= self.config.short_caption_max_tokens

    def _mark_auxiliary(self, item: dict) -> dict:
        """
        Marca um item como auxiliar se estiver em seção de siglas ou abreviações.

        Args:
            item: Dicionário de item com campo 'sections'.

        Returns:
            Item com campo 'is_auxiliary' definido se aplicável.
        """
        if any(s.strip().upper() in self.config.auxiliary_sections for s in item.get("sections", [])):
            item["is_auxiliary"] = True
        return item
