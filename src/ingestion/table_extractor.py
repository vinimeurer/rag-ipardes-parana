"""
Extração e representação de tabelas de documentos Docling.

Tabelas recebem tratamento dedicado porque sua semântica
se perde quando convertidas para texto corrido. Este módulo
as extrai como estruturas independentes, preservando:
- Cabeçalhos e dados em formato matricial (lista de listas)
- Representação em Markdown (para embedding e exibição)
- Representação em JSON estruturado (para recuperação precisa)
- Metadados de localização (página, índice sequencial no doc)
"""
from dataclasses import dataclass, field
from typing import Any, Optional

from docling.datamodel.document import DoclingDocument
from docling_core.types.doc import TableItem

from ..core.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class ExtractedTable:
    """
    Representa uma tabela extraída de um PDF.

    Attributes:
        table_index: Índice sequencial da tabela no documento (base 0).
        page_number: Número da página onde a tabela foi encontrada.
        caption: Legenda ou título da tabela, se disponível.
        headers: Lista de cabeçalhos da tabela (primeira linha, se detectada).
        rows: Linhas de dados como lista de listas de strings.
        markdown: Representação da tabela em Markdown pipe-table.
        num_rows: Quantidade de linhas de dados (excluindo cabeçalho).
        num_cols: Quantidade de colunas.
    """

    table_index: int
    page_number: int
    caption: str
    headers: list[str]
    rows: list[list[str]]
    markdown: str
    num_rows: int
    num_cols: int

    def to_dict(self) -> dict[str, Any]:
        """
        Serializa a tabela para um dicionário JSON-compatível.

        Returns:
            Dicionário com todos os campos da tabela.
        """
        return {
            "table_index": self.table_index,
            "page_number": self.page_number,
            "caption": self.caption,
            "headers": self.headers,
            "rows": self.rows,
            "markdown": self.markdown,
            "num_rows": self.num_rows,
            "num_cols": self.num_cols,
        }

    def to_text_block(self) -> str:
        """
        Gera uma representação textual da tabela para embedding.

        Combina legenda e markdown numa string única adequada para
        ser tratada como um chunk independente no pipeline RAG.

        Returns:
            Bloco de texto representando a tabela.
        """
        parts = []
        if self.caption:
            parts.append(f"Tabela: {self.caption}")
        parts.append(self.markdown)
        return "\n\n".join(parts)


@dataclass
class TableExtractionResult:
    """Resultado da extração de tabelas de um documento."""

    pdf_key: str
    tables: list[ExtractedTable] = field(default_factory=list)
    total_found: int = 0
    total_extracted: int = 0

    @property
    def has_tables(self) -> bool:
        """Indica se alguma tabela foi extraída."""
        return len(self.tables) > 0


class TableExtractor:
    """
    Extrator dedicado de tabelas de documentos Docling.

    Percorre os itens do DoclingDocument identificando TableItem,
    converte cada tabela para as representações matricial e Markdown,
    e descarta tabelas degeneradas (menos de 2 colunas ou 1 linha).

    A representação em Markdown pipe-table é gerada internamente
    para garantir compatibilidade independente da versão do Docling.
    """

    _MIN_COLS = 2
    _MIN_ROWS = 1

    def extract(self, pdf_key: str, docling_doc: DoclingDocument) -> TableExtractionResult:
        """
        Extrai todas as tabelas de um DoclingDocument.

        Args:
            pdf_key: Chave do PDF para identificação nos logs.
            docling_doc: Documento já convertido pelo Docling.

        Returns:
            TableExtractionResult com todas as tabelas encontradas.
        """
        result = TableExtractionResult(pdf_key=pdf_key)

        for idx, (item, _level) in enumerate(docling_doc.iterate_items()):
            if not isinstance(item, TableItem):
                continue

            result.total_found += 1
            page_no = self._get_page_number(item)
            caption = self._get_caption(item, docling_doc)

            grid = self._item_to_grid(item, docling_doc)
            if not self._is_valid_grid(grid):
                logger.debug(
                    "[%s] Tabela %d (pág. %d) ignorada: grade inválida %s",
                    pdf_key, idx, page_no, self._grid_shape(grid),
                )
                continue

            headers, rows = self._split_headers_rows(grid)
            markdown = self._grid_to_markdown(headers, rows)

            table = ExtractedTable(
                table_index=result.total_extracted,
                page_number=page_no,
                caption=caption,
                headers=headers,
                rows=rows,
                markdown=markdown,
                num_rows=len(rows),
                num_cols=len(headers) if headers else (len(rows[0]) if rows else 0),
            )

            result.tables.append(table)
            result.total_extracted += 1

        logger.info(
            "[%s] Tabelas: %d encontradas, %d extraídas.",
            pdf_key, result.total_found, result.total_extracted,
        )
        return result

    def _get_page_number(self, item: TableItem) -> int:
        """
        Obtém o número de página de um TableItem.

        Args:
            item: Item de tabela do Docling.

        Returns:
            Número de página ou 0 se não disponível.
        """
        if item.prov:
            return item.prov[0].page_no
        return 0

    def _get_caption(self, item: TableItem, docling_doc: DoclingDocument) -> str:
        """
        Extrai a legenda associada à tabela, se existir.

        O Docling associa captions via referências no item ou como
        texto vizinho. Tenta múltiplas estratégias em ordem de
        confiabilidade.

        Args:
            item: Item de tabela do Docling.
            docling_doc: Documento completo para busca de captions.

        Returns:
            Texto da legenda ou string vazia.
        """
        if hasattr(item, "caption_text") and callable(item.caption_text):
            try:
                caption = item.caption_text(docling_doc)
                if caption:
                    return caption.strip()
            except Exception:
                pass

        if hasattr(item, "captions") and item.captions:
            for cap_ref in item.captions:
                try:
                    cap_item = docling_doc.get_item(cap_ref)
                    if cap_item and hasattr(cap_item, "text") and cap_item.text:
                        return cap_item.text.strip()
                except Exception:
                    pass

        return ""

    def _item_to_grid(self, item: TableItem, docling_doc: DoclingDocument) -> list[list[str]]:
        """
        Converte um TableItem em uma grade 2D de strings.

        Usa a representação em DataFrame do Docling quando disponível,
        e cai para a exportação direta de células como fallback.

        Args:
            item: Item de tabela do Docling.

        Returns:
            Lista de listas de strings representando a tabela.
        """
        try:
            df = item.export_to_dataframe(doc=docling_doc)
            if df is not None and not df.empty:
                headers_row = [str(c) for c in df.columns.tolist()]
                data_rows = [
                    [str(v) if v is not None else "" for v in row]
                    for row in df.values.tolist()
                ]
                return [headers_row] + data_rows
        except Exception:
            pass

        return self._cells_to_grid(item)

    def _cells_to_grid(self, item: TableItem) -> list[list[str]]:
        """
        Constrói a grade a partir das células brutas do TableItem.

        Args:
            item: Item de tabela do Docling.

        Returns:
            Lista de listas de strings com conteúdo das células.
        """
        if not hasattr(item, "data") or item.data is None:
            return []

        table_data = item.data
        if not hasattr(table_data, "table_cells") or not table_data.table_cells:
            return []

        num_rows = table_data.num_rows
        num_cols = table_data.num_cols

        if num_rows == 0 or num_cols == 0:
            return []

        grid = [[""] * num_cols for _ in range(num_rows)]

        for cell in table_data.table_cells:
            r = cell.start_row_offset_idx
            c = cell.start_col_offset_idx
            if 0 <= r < num_rows and 0 <= c < num_cols:
                grid[r][c] = (cell.text or "").strip()

        return grid

    def _is_valid_grid(self, grid: list[list[str]]) -> bool:
        """
        Verifica se a grade atende aos critérios mínimos de qualidade.

        Uma tabela é válida se tiver pelo menos _MIN_ROWS linhas de dados
        e _MIN_COLS colunas, e não for composta exclusivamente de células
        vazias.

        Args:
            grid: Grade 2D de strings.

        Returns:
            True se a grade for considerada válida.
        """
        if not grid or len(grid) < self._MIN_ROWS + 1:
            return False
        if not grid[0] or len(grid[0]) < self._MIN_COLS:
            return False
        all_empty = all(
            cell.strip() == ""
            for row in grid
            for cell in row
        )
        return not all_empty

    def _grid_shape(self, grid: list[list[str]]) -> tuple[int, int]:
        """
        Retorna as dimensões (linhas, colunas) da grade.

        Args:
            grid: Grade 2D de strings.

        Returns:
            Tupla (linhas, colunas).
        """
        if not grid:
            return (0, 0)
        return (len(grid), len(grid[0]))

    def _split_headers_rows(
        self, grid: list[list[str]]
    ) -> tuple[list[str], list[list[str]]]:
        """
        Separa a primeira linha como cabeçalho das demais linhas de dados.

        Args:
            grid: Grade 2D com pelo menos uma linha.

        Returns:
            Tupla (cabeçalhos, linhas de dados).
        """
        return grid[0], grid[1:]

    def _grid_to_markdown(
        self, headers: list[str], rows: list[list[str]]
    ) -> str:
        """
        Converte cabeçalhos e linhas de dados para Markdown pipe-table.

        Args:
            headers: Lista de cabeçalhos da tabela.
            rows: Linhas de dados como lista de listas.

        Returns:
            String com a tabela em formato Markdown.
        """
        num_cols = len(headers)

        def _escape(cell: str) -> str:
            return cell.replace("|", "\\|").replace("\n", " ").strip()

        header_line = "| " + " | ".join(_escape(h) for h in headers) + " |"
        separator = "| " + " | ".join("---" for _ in range(num_cols)) + " |"

        data_lines = []
        for row in rows:
            padded = row + [""] * (num_cols - len(row))
            data_lines.append(
                "| " + " | ".join(_escape(str(c)) for c in padded[:num_cols]) + " |"
            )

        return "\n".join([header_line, separator] + data_lines)
