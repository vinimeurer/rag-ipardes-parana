"""
Módulo responsável por processar as tabelas extraídas dos PDFs. 
Lê os arquivos markdown e JSON gerados pelo extrator, extrai metadados, 
e salva as tabelas processadas com conteúdo limpo e metadados em formato JSON.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from ..core.logger import setup_logger
from ..core.preprocessing_config import TableProcessingConfig, CleaningConfig
from .text_cleaner import TextCleaner


@dataclass
class ProcessedTable:
    """
    Representa uma tabela processada com conteúdo e metadados.
    """

    table_index: int
    page_number: int | None
    caption: str | None
    content: str
    document: str


class TableProcessor:
    """
    Processa as tabelas extraídas e prepara para o pipeline RAG.

    Lê os arquivos markdown e JSON do diretório de extração, extrai
    metadados, e salva as tabelas processadas com conteúdo e metadados
    embutidos em formato JSON.

    Args:
        config: Configuração de processamento de tabelas.

    Métodos:
        load_tables_for_document: Carrega tabelas de um documento como itens de conteúdo.
        process_document_tables: Processa todas as tabelas de um documento.
        save_processed_tables: Salva as tabelas processadas em arquivos JSON.
    """

    def __init__(self, config: Optional[TableProcessingConfig] = None):
        self.config = config or TableProcessingConfig()
        self.cleaner = TextCleaner(CleaningConfig())
        self.logger = setup_logger(__name__)

    def load_tables_for_document(self, pdf_key: str, extracted_dir: Path) -> list[dict]:
        """
        Carrega as tabelas de um documento como itens de conteúdo prontos para inserção.

        Retorna uma lista de dicionários no formato esperado pelo array de conteúdo do pré-processador. 
        O campo de seções é deixado vazio e será preenchido pelo pré-processador com base nas seções 
        ativas na página da tabela.

        Args:
            pdf_key: Identificador do documento.
            extracted_dir: Diretório raiz contendo os dados extraídos.

        Returns:
            Lista de itens de conteúdo com type='table'.
        """
        tables_src = extracted_dir / pdf_key / "tables"
        if not tables_src.exists():
            return []

        content_items = []
        tables_index_path = tables_src / "tables_index.json"

        if not tables_index_path.exists():
            return []

        index_payload = tables_index_path.read_text(encoding="utf-8")
        tables_index = json.loads(index_payload)

        for table_info in tables_index.get("tables", []):
            try:
                item = self._table_info_to_content_item(pdf_key, tables_src, table_info)
                if item:
                    content_items.append(item)
            except Exception:
                table_idx = table_info.get("table_index", "?")
                self.logger.warning(
                    "[%s] Failed to load table (index=%s)",
                    pdf_key,
                    table_idx,
                )
                continue

        return content_items

    def _table_info_to_content_item(self, pdf_key: str, tables_dir: Path, table_info: dict) -> dict | None:
        """
        Converte as informações da tabela em um item de conteúdo para o array unificado.

        Args:
            pdf_key: Identificador do documento.
            tables_dir: Diretório contendo os arquivos de tabela.
            table_info: Metadados do tables_index.json.

        Returns:
            Dicionário do item de conteúdo ou None se a conversão falhar.
        """
        table_index = table_info.get("table_index")
        if table_index is None:
            return None

        page_number = table_info.get("page_number")
        caption = table_info.get("caption")

        markdown_file = tables_dir / f"table_{table_index:03d}.md"
        if not markdown_file.exists():
            return None

        content = markdown_file.read_text(encoding="utf-8")
        content = self.cleaner.clean_table_content(content)

        return {
            "document": pdf_key,
            "page": page_number,
            "sections": [],
            "type": "table",
            "caption": caption if caption else None,
            "content": content,
        }

    def process_document_tables(self, pdf_key: str, extracted_dir: Path, processed_dir: Path) -> List[ProcessedTable]:
        """
        Processa todas as tabelas de um documento.

        Args:
            pdf_key: Identificador do documento.
            extracted_dir: Diretório raiz contendo os dados extraídos.
            processed_dir: Diretório raiz para os outputs processados.

        Returns:
            Lista de objetos ProcessedTable.
        """
        tables_src = extracted_dir / pdf_key / "tables"
        if not tables_src.exists():
            return []

        tables_list: List[ProcessedTable] = []
        tables_index_path = tables_src / "tables_index.json"

        if not tables_index_path.exists():
            self.logger.warning(
                "[%s] tables_index.json não encontrado em %s",
                pdf_key,
                tables_src,
            )
            return []

        index_payload = tables_index_path.read_text(encoding="utf-8")
        tables_index = json.loads(index_payload)

        for table_info in tables_index.get("tables", []):
            try:
                processed = self._process_single_table(
                    pdf_key, tables_src, table_info
                )
                if processed:
                    tables_list.append(processed)
            except Exception as e:
                table_idx = table_info.get("table_index", "?")
                self.logger.error(
                    "[%s] Falha ao processar tabela (index=%s): %s",
                    pdf_key,
                    table_idx,
                    str(e),
                )
                continue

        self.save_processed_tables(
            pdf_key, tables_list, extracted_dir, processed_dir
        )

        return tables_list

    def _process_single_table(self, pdf_key: str, tables_dir: Path, table_info: dict) -> ProcessedTable | None:
        """
        Processa uma única tabela a partir dos arquivos extraídos.

        Args:
            pdf_key: Identificador do documento.
            tables_dir: Diretório contendo os arquivos de tabela.
            table_info: Metadados do tables_index.json.

        Returns:
            ProcessedTable ou None se a extração falhar.
        """
        table_index = table_info.get("table_index")
        if table_index is None:
            self.logger.warning(
                "[%s] Tabela sem table_index em tables_index.json",
                pdf_key,
            )
            return None

        page_number = table_info.get("page_number")
        caption = table_info.get("caption") if self.config.include_caption else None

        markdown_file = tables_dir / self.config.markdown_file_pattern.format(
            table_index
        )

        if not markdown_file.exists():
            self.logger.warning(
                "[%s] Arquivo de tabela não encontrado: %s",
                pdf_key,
                markdown_file.name,
            )
            return None

        content = markdown_file.read_text(encoding="utf-8")

        return ProcessedTable(
            table_index=table_index,
            page_number=page_number,
            caption=caption,
            content=content,
            document=pdf_key,
        )

    def save_processed_tables(self, pdf_key: str, tables: List[ProcessedTable], extracted_dir: Path, processed_dir: Path) -> None:
        """
        Salva as tabelas processadas em arquivos JSON no diretório de processados.

        Cria processed/[pdf_key]/tables/ com arquivos JSON 
        individuais contendo o conteúdo da tabela e metadados.

        Args:
            pdf_key: Identificador do documento.
            tables: Lista de objetos ProcessedTable.
            extracted_dir: Diretório raiz contendo os dados extraídos.
            processed_dir: Diretório raiz para os outputs processados.
        """
        if not tables:
            return

        tables_out_dir = processed_dir / pdf_key / "tables"
        tables_out_dir.mkdir(parents=True, exist_ok=True)

        for table in tables:
            output_file = tables_out_dir / self.config.json_output_pattern.format(
                table.table_index
            )

            payload = {
                "table_index": table.table_index,
                "page_number": table.page_number,
                "caption": table.caption,
                "content": table.content,
                "document": table.document,
            }

            if self.config.extract_metadata:
                tables_index_path = (
                    extracted_dir / pdf_key / "tables" / "tables_index.json"
                )
                if tables_index_path.exists():
                    index_data = json.loads(
                        tables_index_path.read_text(encoding="utf-8")
                    )
                    for table_info in index_data.get("tables", []):
                        if table_info.get("table_index") == table.table_index:
                            payload["metadata"] = {
                                "title": table_info.get("caption"),
                                "num_rows": table_info.get("num_rows"),
                                "num_cols": table_info.get("num_cols"),
                            }
                            break

            output_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
