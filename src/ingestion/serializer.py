"""
Serialização dos resultados de extração para disco.

Salva o conteúdo extraído e limpo em múltiplos formatos por documento:
- <key>.txt    — texto corrido limpo (sem tabelas)
- <key>.md     — markdown limpo (sem tabelas)
- <key>.json   — estrutura completa com páginas e metadados
- tables/      — subdiretório com artefatos dedicados de tabelas:
    - tables_index.json       — índice de todas as tabelas
    - table_<N>.md            — cada tabela em Markdown
    - table_<N>.json          — cada tabela em JSON estruturado

A separação física de tabelas e texto facilita chunking diferenciado
na etapa seguinte do pipeline RAG.
"""
import json
from pathlib import Path

from .pdf_extractor import ExtractionResult
from .table_extractor import ExtractedTable
from ..core.ingestion_config import IngestionPipelineConfig
from ..core.logger import setup_logger


logger = setup_logger(__name__)

_TABLES_SUBDIR = "tables"


class ExtractionSerializer:
    """
    Serializador de resultados de extração de PDFs.

    Organiza a saída em extracted/<pdf_key>/ com separação explícita
    entre conteúdo textual e tabelas para permitir chunking diferenciado.
    """

    def __init__(self, config: IngestionPipelineConfig):
        """
        Inicializa o serializador com a configuração do pipeline.

        Args:
            config: Configuração completa do pipeline de ingestão.
        """
        self.config = config

    def save(
        self,
        result: ExtractionResult,
        cleaned_text: str,
        cleaned_markdown: str,
    ) -> dict[str, Path]:
        """
        Persiste todos os artefatos de extração de um PDF no disco.

        Args:
            result: Resultado bruto da extração pelo Docling.
            cleaned_text: Texto corrido limpo (sem tabelas).
            cleaned_markdown: Markdown limpo (sem tabelas).

        Returns:
            Dicionário mapeando tipo de artefato para seu Path.
        """
        output_dir = self.config.pdf_output_dir(result.pdf_key)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved: dict[str, Path] = {}

        if self.config.output.save_raw_text:
            saved["text"] = self._save_text(output_dir, result.pdf_key, cleaned_text)

        if self.config.output.save_markdown:
            saved["markdown"] = self._save_markdown(
                output_dir, result.pdf_key, cleaned_markdown
            )

        if self.config.output.save_json:
            saved["json"] = self._save_json(
                output_dir, result, cleaned_text, cleaned_markdown
            )

        if result.has_tables:
            table_paths = self._save_tables(output_dir, result)
            saved["tables_index"] = table_paths["index"]
            saved["tables_dir"] = output_dir / _TABLES_SUBDIR

        logger.info(
            "Artefatos de '%s' salvos em: %s (%d tabelas)",
            result.pdf_key,
            output_dir,
            len(result.tables),
        )
        return saved

    def _save_text(self, output_dir: Path, pdf_key: str, text: str) -> Path:
        """
        Salva o texto corrido limpo em arquivo .txt.

        Args:
            output_dir: Diretório de destino.
            pdf_key: Chave do PDF.
            text: Texto limpo sem tabelas.

        Returns:
            Path do arquivo salvo.
        """
        path = output_dir / f"{pdf_key}.txt"
        path.write_text(text, encoding="utf-8")
        logger.debug("Texto salvo: %s (%d chars)", path, len(text))
        return path

    def _save_markdown(self, output_dir: Path, pdf_key: str, markdown: str) -> Path:
        """
        Salva o conteúdo em Markdown limpo em arquivo .md.

        Args:
            output_dir: Diretório de destino.
            pdf_key: Chave do PDF.
            markdown: Markdown limpo sem tabelas.

        Returns:
            Path do arquivo salvo.
        """
        path = output_dir / f"{pdf_key}.md"
        path.write_text(markdown, encoding="utf-8")
        logger.debug("Markdown salvo: %s (%d chars)", path, len(markdown))
        return path

    def _save_json(
        self,
        output_dir: Path,
        result: ExtractionResult,
        cleaned_text: str,
        cleaned_markdown: str,
    ) -> Path:
        """
        Salva o resultado estruturado completo em arquivo .json.

        O JSON inclui metadados e conteúdo por página. Tabelas são 
        referenciadas pelo índice mas salvas em separado no subdiretório 
        tables/. Texto e Markdown completos são salvos em arquivos 
        separados (.txt e .md).

        Args:
            output_dir: Diretório de destino.
            result: Resultado bruto da extração.
            cleaned_text: Texto limpo.
            cleaned_markdown: Markdown limpo.

        Returns:
            Path do arquivo salvo.
        """
        payload = {
            "metadata": result.metadata,
            "pages": [
                {
                    "page_number": p.page_number,
                    "text": p.text,
                }
                for p in result.pages
            ],
            "tables_count": len(result.tables),
            "tables_ref": f"{_TABLES_SUBDIR}/tables_index.json" if result.has_tables else None,
        }

        path = output_dir / f"{result.pdf_key}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.debug("JSON principal salvo: %s", path)
        return path

    def _save_tables(
        self, output_dir: Path, result: ExtractionResult
    ) -> dict[str, Path]:
        """
        Salva todos os artefatos de tabelas no subdiretório tables/.

        Para cada tabela gera:
        - table_<N>.md   — representação Markdown para embedding
        - table_<N>.json — estrutura completa para recuperação precisa

        Ao final gera tables_index.json com o sumário de todas as
        tabelas e seus arquivos correspondentes.

        Args:
            output_dir: Diretório base do documento.
            result: Resultado da extração com lista de tabelas.

        Returns:
            Dicionário com path do arquivo de índice.
        """
        tables_dir = output_dir / _TABLES_SUBDIR
        tables_dir.mkdir(parents=True, exist_ok=True)

        index_entries = []

        for table in result.tables:
            md_path = self._save_table_markdown(tables_dir, table)
            json_path = self._save_table_json(tables_dir, table)

            index_entries.append(
                {
                    "table_index": table.table_index,
                    "page_number": table.page_number,
                    "caption": table.caption,
                    "num_rows": table.num_rows,
                    "num_cols": table.num_cols,
                    "markdown_file": md_path.name,
                    "json_file": json_path.name,
                }
            )

        index_path = tables_dir / "tables_index.json"
        index_path.write_text(
            json.dumps(
                {
                    "pdf_key": result.pdf_key,
                    "total_tables": len(result.tables),
                    "tables": index_entries,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        logger.debug(
            "%d tabelas salvas em: %s", len(result.tables), tables_dir
        )
        return {"index": index_path}

    def _save_table_markdown(self, tables_dir: Path, table: ExtractedTable) -> Path:
        """
        Salva a representação Markdown de uma tabela.

        O arquivo inclui a legenda (se existir) seguida da pipe-table,
        no formato adequado para ser tratada como chunk independente.

        Args:
            tables_dir: Diretório de destino das tabelas.
            table: Tabela extraída.

        Returns:
            Path do arquivo .md salvo.
        """
        path = tables_dir / f"table_{table.table_index:03d}.md"
        path.write_text(table.to_text_block(), encoding="utf-8")
        return path

    def _save_table_json(self, tables_dir: Path, table: ExtractedTable) -> Path:
        """
        Salva a representação JSON estruturada de uma tabela.

        Args:
            tables_dir: Diretório de destino das tabelas.
            table: Tabela extraída.

        Returns:
            Path do arquivo .json salvo.
        """
        path = tables_dir / f"table_{table.table_index:03d}.json"
        path.write_text(
            json.dumps(table.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def already_extracted(self, pdf_key: str) -> bool:
        """
        Verifica se os artefatos de extração já existem no disco.

        Args:
            pdf_key: Chave do PDF.

        Returns:
            True se o JSON principal já existe e overwrite está desabilitado.
        """
        if self.config.output.overwrite_existing:
            return False
        json_path = self.config.pdf_output_dir(pdf_key) / f"{pdf_key}.json"
        return json_path.exists()
