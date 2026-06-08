"""
Testes para table_extractor.py
"""

from unittest.mock import MagicMock, patch

from src.ingestion.table_extractor import (
    ExtractedTable,
    TableExtractionResult,
    TableExtractor,
)


class TestExtractedTable:

    def test_to_dict(self):

        table = ExtractedTable(
            table_index=0,
            page_number=1,
            caption="Tabela teste",
            headers=["A", "B"],
            rows=[["1", "2"]],
            markdown="| A | B |",
            num_rows=1,
            num_cols=2,
        )

        result = table.to_dict()

        assert result["table_index"] == 0
        assert result["page_number"] == 1
        assert result["caption"] == "Tabela teste"
        assert result["num_rows"] == 1
        assert result["num_cols"] == 2

    def test_to_text_block_with_caption(self):

        table = ExtractedTable(
            table_index=0,
            page_number=1,
            caption="Minha tabela",
            headers=[],
            rows=[],
            markdown="| A |",
            num_rows=0,
            num_cols=1,
        )

        result = table.to_text_block()

        assert "Minha tabela" in result
        assert "| A |" in result

    def test_to_text_block_without_caption(self):

        table = ExtractedTable(
            table_index=0,
            page_number=1,
            caption="",
            headers=[],
            rows=[],
            markdown="| A |",
            num_rows=0,
            num_cols=1,
        )

        result = table.to_text_block()

        assert result == "| A |"


class TestTableExtractionResult:

    def test_has_tables_true(self):

        result = TableExtractionResult(
            pdf_key="doc",
            tables=[
                MagicMock()
            ]
        )

        assert result.has_tables is True

    def test_has_tables_false(self):

        result = TableExtractionResult(
            pdf_key="doc",
            tables=[]
        )

        assert result.has_tables is False


class TestTableExtractor:

    def test_is_valid_grid_true(self):

        extractor = TableExtractor()

        grid = [
            ["A", "B"],
            ["1", "2"],
        ]

        assert extractor._is_valid_grid(grid) is True

    def test_is_valid_grid_empty(self):

        extractor = TableExtractor()

        assert extractor._is_valid_grid([]) is False

    def test_is_valid_grid_one_column(self):

        extractor = TableExtractor()

        grid = [
            ["A"],
            ["1"],
        ]

        assert extractor._is_valid_grid(grid) is False

    def test_is_valid_grid_all_empty(self):

        extractor = TableExtractor()

        grid = [
            ["", ""],
            ["", ""],
        ]

        assert extractor._is_valid_grid(grid) is False

    def test_grid_shape(self):

        extractor = TableExtractor()

        grid = [
            ["A", "B"],
            ["1", "2"],
            ["3", "4"],
        ]

        assert extractor._grid_shape(grid) == (3, 2)

    def test_grid_shape_empty(self):

        extractor = TableExtractor()

        assert extractor._grid_shape([]) == (0, 0)

    def test_split_headers_rows(self):

        extractor = TableExtractor()

        grid = [
            ["A", "B"],
            ["1", "2"],
            ["3", "4"],
        ]

        headers, rows = extractor._split_headers_rows(grid)

        assert headers == ["A", "B"]
        assert len(rows) == 2

    def test_grid_to_markdown(self):

        extractor = TableExtractor()

        markdown = extractor._grid_to_markdown(
            headers=["Nome", "Idade"],
            rows=[
                ["João", "20"],
                ["Maria", "30"],
            ],
        )

        assert "| Nome | Idade |" in markdown
        assert "João" in markdown
        assert "Maria" in markdown

    def test_grid_to_markdown_escapes_pipe(self):

        extractor = TableExtractor()

        markdown = extractor._grid_to_markdown(
            headers=["A"],
            rows=[
                ["x|y"]
            ],
        )

        assert "\\|" in markdown

    def test_get_page_number_with_prov(self):

        extractor = TableExtractor()

        item = MagicMock()

        prov = MagicMock()
        prov.page_no = 7

        item.prov = [prov]

        assert extractor._get_page_number(item) == 7

    def test_get_page_number_without_prov(self):

        extractor = TableExtractor()

        item = MagicMock()
        item.prov = []

        assert extractor._get_page_number(item) == 0

    def test_get_caption_from_caption_text(self):

        extractor = TableExtractor()

        item = MagicMock()
        item.caption_text.return_value = "Legenda"

        doc = MagicMock()

        result = extractor._get_caption(item, doc)

        assert result == "Legenda"

    def test_get_caption_returns_empty(self):

        extractor = TableExtractor()

        item = MagicMock()
        item.caption_text.side_effect = Exception()

        item.captions = []

        doc = MagicMock()

        result = extractor._get_caption(item, doc)

        assert result == ""

    def test_cells_to_grid_empty(self):

        extractor = TableExtractor()

        item = MagicMock()
        item.data = None

        result = extractor._cells_to_grid(item)

        assert result == []

    def test_cells_to_grid_valid(self):

        extractor = TableExtractor()

        cell = MagicMock()
        cell.start_row_offset_idx = 0
        cell.start_col_offset_idx = 0
        cell.text = "A"

        data = MagicMock()
        data.num_rows = 1
        data.num_cols = 1
        data.table_cells = [cell]

        item = MagicMock()
        item.data = data

        result = extractor._cells_to_grid(item)

        assert result == [["A"]]

    def test_item_to_grid_dataframe(self):

        extractor = TableExtractor()

        item = MagicMock()

        df = MagicMock()
        df.empty = False
        df.columns.tolist.return_value = ["A", "B"]
        df.values.tolist.return_value = [["1", "2"]]

        item.export_to_dataframe.return_value = df

        result = extractor._item_to_grid(item, MagicMock())

        assert len(result) == 2
        assert result[0] == ["A", "B"]

    def test_item_to_grid_fallback(self):

        extractor = TableExtractor()

        item = MagicMock()
        item.export_to_dataframe.side_effect = Exception()

        with patch.object(
            extractor,
            "_cells_to_grid",
            return_value=[["A", "B"]]
        ) as mock_cells:

            result = extractor._item_to_grid(
                item,
                MagicMock()
            )

            mock_cells.assert_called_once()
            assert result == [["A", "B"]]