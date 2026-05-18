"""
Módulo principal de pré-processamento dos documentos extraídos.
Lê os arquivos markdown gerados pelo extrator, processa o texto 
por página com detecção de seções, integra as tabelas, e salva 
em formato JSON unificado para o pipeline
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.logger import setup_logger
from ..core.preprocessing_config import PreprocessingConfig
from ..core.constants import PDF_SOURCES
from .content_filter import ContentFilter
from .section_parser import SectionParser
from .table_processor import TableProcessor
from .text_cleaner import TextCleaner


@dataclass
class ProcessResult:
    pdf_key: str
    output_path: Path
    total_pages: int
    total_text_items: int
    total_table_items: int
    has_sections: bool
    used_page_fallback: bool = False
    items_filtered: int = 0

    @property
    def total_items(self) -> int:
        """Total content items (text + tables)."""
        return self.total_text_items + self.total_table_items


class Preprocessor:
    """
    Converte os arquivos markdown extraídos para o formato JSON processado c
    compatível com o pipeline de chunking. Lida com limpeza de texto, 
    detecção de seções e integração de tabelas.

    Args:
        config: Configuração de pré-processamento opcional. Se omitida, são usadas as configurações padrão.

    Métodos:
        run_document: Pré-processa um único documento identificado por `pdf_key`.
        run_all: Pré-processa todos os documentos encontrados no diretório de extração.
        _parse_pages_from_markdown: Analisa o conteúdo markdown em páginas usando tags PAGE.
        _process_with_section_detection: Processa páginas com detecção de cabeçalhos markdown, quebrando cada página em múltiplos itens por seção.
        _process_with_page_fallback: Processa páginas usando apenas números de página como seções (para analise_conjuntural).
        _merge_content_and_tables: Mescla itens de texto e tabela mantendo a ordem das páginas.
        _get_timestamp: Retorna o timestamp atual em formato ISO.
        _log_processing_summary: Registra estatísticas resumidas após processar um documento.
    """

    _PAGE_TAG_RE = re.compile(r"<!--\s*PAGE:\s*(\d+)\s*-->")

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.in_dir = Path(self.config.paths.extracted_dir)
        self.out_dir = Path(self.config.paths.processed_dir)
        self.cleaner = TextCleaner(self.config.cleaning)
        self.table_processor = TableProcessor()
        self.content_filter = ContentFilter(self.config.content_filter)
        self.logger = setup_logger(__name__)

    def run_document(self, pdf_key: str) -> ProcessResult:
        """
        Pré-processa um único documento extraído identificado por `pdf_key`.

        Lê a fonte markdown, processa o texto por página com rastreamento 
        de seções, integra tabelas, e salva em formato JSON unificado.

        Args:
            pdf_key: Identificador do documento (corresponde ao nome da pasta no diretório de extração).
        
        Returns:
            Um ProcessResult com estatísticas do processamento.
        """
        src_md = self.in_dir / pdf_key / f"{pdf_key}.md"
        if not src_md.exists():
            raise FileNotFoundError(f"Markdown source not found: {src_md}")

        md_content = src_md.read_text(encoding="utf-8")
        pages_data = self._parse_pages_from_markdown(md_content)

        has_sections = pdf_key != "analise_conjuntural"
        content_items = []

        if has_sections:
            content_items = self._process_with_section_detection(pdf_key, pages_data)
        else:
            content_items = self._process_with_page_fallback(pdf_key, pages_data)

        tables = self.table_processor.load_tables_for_document(pdf_key, self.in_dir)
        content_items = self._merge_content_and_tables(content_items, tables)
        items_before_filter = len(content_items)
        content_items = self.content_filter.filter(content_items, pdf_key)
        items_filtered = items_before_filter - len(content_items)

        metadata = {
            "pdf_key": pdf_key,
            "description": self._get_document_description(pdf_key),
            "total_pages": len(pages_data),
            "processed_at": self._get_timestamp(),
            "has_sections": has_sections,
        }

        output = {
            "metadata": metadata,
            "content": content_items,
        }

        out_path = self.out_dir / f"{pdf_key}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        text_items = sum(1 for i in content_items if i.get("type") == "text")
        table_items = sum(1 for i in content_items if i.get("type") == "table")
        used_fallback = not has_sections

        result = ProcessResult(
            pdf_key=pdf_key,
            output_path=out_path,
            total_pages=len(pages_data),
            total_text_items=text_items,
            total_table_items=table_items,
            has_sections=has_sections,
            used_page_fallback=used_fallback,
            items_filtered=items_filtered,
        )

        self._log_processing_summary(result)
        return result

    def run_all(self, keys: Optional[list[str]] = None) -> list[ProcessResult]:
        """
        Pré-processa todos os documentos encontrados no diretório de extração.

        Args:
            keys: Lista opcional de `pdf_key` explícitos para processar. Se omitida, processa todos os diretórios encontrados.

        Returns:
            Lista de ProcessResult para cada documento processado.
        """
        keys = keys or [p.name for p in self.in_dir.iterdir() if p.is_dir()]
        results = []

        self.logger.info("Starting preprocessing for %d document(s).", len(keys))

        for k in keys:
            try:
                res = self.run_document(k)
                results.append(res)
            except Exception:
                self.logger.exception("Failed to preprocess '%s'", k)
                continue

        self.logger.info("Preprocessing completed: %d document(s).", len(results))
        return results

    def _parse_pages_from_markdown(self, content: str) -> list[dict]:
        """
        Parseia o conteúdo markdown em páginas usando tags PAGE.

        Cada página é extraída entre tags PAGE consecutivas. 
        A primeira página começa do início do documento.

        Args:
            content: Conteúdo markdown completo do arquivo fonte.

        Returns:
            Lista de dicionários com chaves 'page_number' e 'text'.
        """
        pages = []
        tag_positions = [(m.start(), int(m.group(1))) for m in self._PAGE_TAG_RE.finditer(content)]

        if not tag_positions:
            return [{"page_number": 0, "text": content}]

        for idx, (pos, page_num) in enumerate(tag_positions):
            end_pos = tag_positions[idx + 1][0] if idx + 1 < len(tag_positions) else len(content)
            page_content = content[pos:end_pos]
            page_content = self._PAGE_TAG_RE.sub("", page_content, count=1).strip()

            pages.append({"page_number": page_num, "text": page_content})

        return pages

    def _process_with_section_detection(self, pdf_key: str, pages_data: list[dict]) -> list[dict]:
        """
        Processa as páginas com detecção de cabeçalhos markdown, 
        quebrando cada página em múltiplos itens por seção.

        Detecta cabeçalhos markdown (#, ##, ###, etc.) e mantém o estado das 
        seções ativas usando SectionParser. Quando um novo cabeçalho é detectado, 
        o bloco atual é finalizado e um novo bloco começa. Cada bloco herda as seções 
        que estavam ativas ANTES do cabeçalho que o inicia, garantindo que o bloco 
        capture seu contexto circundante.

        Args:
            pdf_key: Identificador do documento.
            pages_data: Lista de dicionários de páginas com page_number e text.

        Returns:
            Lista de itens de conteúdo ordenados por página, com múltiplos itens por página
            quando cabeçalhos são detectados.
        """
        content_items = []
        section_parser = SectionParser()

        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]

            if not text.strip():
                continue

            cleaned_text, _ = self.cleaner.clean_markdown(
                text, source_id=f"{pdf_key}:p{page_num}"
            )

            if not cleaned_text.strip():
                continue

            lines = cleaned_text.split("\n")
            current_block_lines = []
            current_block_sections = section_parser.current_sections.copy()

            for line in lines:
                sections_before_update = section_parser.current_sections.copy()

                is_header = section_parser.update(line)

                if is_header:

                    if current_block_lines:
                        block_text = "\n".join(current_block_lines).strip()
                        if block_text:
                            if not current_block_sections:
                                current_block_sections = [f"pagina_{page_num}"]
                            content_items.append({
                                "document": pdf_key,
                                "page": page_num,
                                "sections": current_block_sections,
                                "type": "text",
                                "content": block_text,
                            })

                    current_block_lines = [line]
                    current_block_sections = section_parser.current_sections.copy() 
                else:
                    current_block_lines.append(line)

            if current_block_lines:
                block_text = "\n".join(current_block_lines).strip()
                if block_text:

                    if not current_block_sections:
                        current_block_sections = [f"pagina_{page_num}"]

                    content_items.append({
                        "document": pdf_key,
                        "page": page_num,
                        "sections": current_block_sections,
                        "type": "text",
                        "content": block_text,
                    })

        return content_items

    def _process_with_page_fallback(self, pdf_key: str, pages_data: list[dict]) -> list[dict]:
        """
        Processa as páginas usando apenas números de página como seções.

        Documentos sem hierarquia de seções verdadeira usam números de página como pseudo-seções, 
        preservando a estrutura do documento para recuperação sem inferir seções.

        Args:
            pdf_key: Identificador do documento.
            pages_data: Lista de dicionários de páginas com page_number e text.

        Returns:
            Lista de itens de conteúdo com seções baseadas em páginas.
        """
        content_items = []

        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]

            if not text.strip():
                continue

            cleaned_text, _ = self.cleaner.clean_markdown(
                text,
                source_id=f"{pdf_key}:p{page_num}",
            )

            if not cleaned_text.strip():
                continue

            content_items.append(
                {
                    "document": pdf_key,
                    "page": page_num,
                    "sections": [f"pagina_{page_num}"],
                    "type": "text",
                    "content": cleaned_text,
                }
            )

        return content_items

    def _merge_content_and_tables(self, text_items: list[dict], table_items: list[dict]) -> list[dict]:
        """
        Mescla itens de texto e tabela mantendo a ordem das páginas.

        Combina o conteúdo de texto e tabela em um único array ordenado, depois ordena 
        por número de página. Dentro de cada página, o texto aparece antes das tabelas. 
        Preenche as informações de seção para as tabelas com base nas seções ativas em sua 
        página ou na página precedente mais próxima com seções.

        Args:
            text_items: Lista de itens de conteúdo de texto.
            table_items: Lista de itens de conteúdo de tabela (com seções vazias).

        Returns:
            Lista mesclada e ordenada de itens de conteúdo.
        """
        all_items = text_items + table_items
        all_items.sort(key=lambda x: (x.get("page", 0), x.get("type") == "table"))

        section_map = {}
        for item in text_items:
            page = item.get("page")
            if page and item.get("sections"):
                section_map[page] = item.get("sections")

        last_sections = None
        for item in all_items:
            page = item.get("page")
            if page in section_map:
                last_sections = section_map[page]
            
            if item.get("type") == "table":
                if page in section_map:
                    item["sections"] = section_map[page]
                elif last_sections:
                    item["sections"] = last_sections
                else:
                    item["sections"] = []

        return all_items

    def _get_document_description(self, pdf_key: str) -> str:
        """
        Pega uma descrição legível para um documento com base em seu `pdf_key`.

        Args:
            pdf_key: Identificador do documento.

        Returns:
            String de descrição.
        """
        return PDF_SOURCES.get(pdf_key, {}).get("description", pdf_key)

    def _get_timestamp(self) -> str:
        """
        Retorna o timestamp atual em formato ISO.
        """
        return datetime.now().isoformat()

    def _log_processing_summary(self, result: ProcessResult) -> None:
        """
        Registra estatísticas resumidas após processar um documento.

        Args:
            result: Objeto de resultado do processamento.
        """
        fallback_note = " (página fallback)" if result.used_page_fallback else ""
        self.logger.info(
            "[%s] páginas=%d | itens_texto=%d | tabelas=%d | total=%d | filtrados=%d%s | saída=%s",
            result.pdf_key,
            result.total_pages,
            result.total_text_items,
            result.total_table_items,
            result.total_items,
            result.items_filtered,
            fallback_note,
            result.output_path.name,
        )

