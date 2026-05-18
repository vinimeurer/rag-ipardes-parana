"""
Módulo principal de chunking do pipeline RAG.

Lê os JSONs processados, divide o conteúdo em chunks section-aware
e salva o resultado em formato JSONL pronto para indexação vetorial.
"""

import json
from pathlib import Path
from typing import Optional

from .chunk_dataclass import Chunk
from .text_splitter import RecursiveTextSplitter, count_tokens
from ..core.logger import setup_logger
from ..core.chunking_config import ChunkingConfig

class Chunker:
    """Gera chunks section-aware a partir dos documentos processados.

    O chunking é section-aware por design: cada item recebido do preprocessador
    já representa um bloco de texto dentro de uma seção específica. O chunker
    apenas resolve granularidade de tamanho, preservando os metadados de seção
    em todos os chunks filhos gerados.

    Attributes:
        config: Configuração de chunking.
        splitter: Instância do splitter de texto recursivo.
        logger: Logger do módulo.
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        """Inicializa o chunker com a configuração fornecida.

        Args:
            config: Configuração de chunking. Se omitida, usa valores padrão.
        """
        self.config = config or ChunkingConfig()
        self.splitter = RecursiveTextSplitter(
            chunk_size=self.config.chunk_size,
            overlap=self.config.overlap,
            separators=self.config.separators,
        )
        self.logger = setup_logger(__name__)

    def chunk_document(self, processed_path: Path) -> list[Chunk]:
        """Gera chunks a partir de um único arquivo JSON processado.

        Args:
            processed_path: Caminho para o arquivo JSON processado.

        Returns:
            Lista de chunks gerados do documento.
        """
        data = json.loads(processed_path.read_text(encoding="utf-8"))
        pdf_key = data["metadata"]["pdf_key"]
        content_items = data.get("content", [])

        chunks: list[Chunk] = []
        discarded = 0

        for item_index, item in enumerate(content_items):
            item_type = item.get("type")

            if item_type == "table":
                chunk = self._chunk_table_item(item, pdf_key, item_index)
                if chunk:
                    chunks.append(chunk)
                else:
                    discarded += 1

            elif item_type == "text":
                item_chunks = self._chunk_text_item(item, pdf_key, item_index)
                valid = [c for c in item_chunks if c.token_count >= self.config.min_chunk_tokens]
                discarded += len(item_chunks) - len(valid)
                chunks.extend(valid)

        self.logger.info(
            "[%s] chunks=%d | descartados=%d",
            pdf_key,
            len(chunks),
            discarded,
        )

        return chunks

    def chunk_all(self, processed_dir: Optional[Path] = None) -> list[Chunk]:
        """Gera chunks para todos os documentos no diretório processado.

        Args:
            processed_dir: Diretório contendo os JSONs processados.
                Se omitido, usa o valor da configuração.

        Returns:
            Lista de todos os chunks gerados.
        """
        directory = processed_dir or self.config.paths.processed_dir
        json_files = list(directory.glob("*.json"))

        self.logger.info("Iniciando chunking para %d documento(s).", len(json_files))

        all_chunks: list[Chunk] = []

        for path in json_files:
            try:
                doc_chunks = self.chunk_document(path)
                all_chunks.extend(doc_chunks)
            except Exception:
                self.logger.exception("Falha ao processar '%s'", path.name)
                continue

        self.logger.info("Chunking concluído: %d chunks gerados.", len(all_chunks))
        return all_chunks

    def save(self, chunks: list[Chunk], output_path: Optional[Path] = None) -> Path:
        """Salva os chunks em formato JSONL.

        Cada linha do arquivo de saída contém um chunk serializado em JSON.
        O formato JSONL permite leitura linha a linha sem carregar tudo na memória.

        Args:
            chunks: Lista de chunks a salvar.
            output_path: Caminho do arquivo de saída. Se omitido, usa a configuração.

        Returns:
            Caminho do arquivo salvo.
        """
        path = output_path or (self.config.paths.chunks_dir / "chunks.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")

        self.logger.info("Chunks salvos em: %s (%d linhas)", path, len(chunks))
        return path

    def _chunk_text_item(self, item: dict, pdf_key: str, item_index: int) -> list[Chunk]:
        """Divide um item de texto em um ou mais chunks.

        Cada chunk filho herda os metadados de seção, página e documento
        do item pai. O chunk_index identifica a posição dentro do item.

        Args:
            item: Item de conteúdo do tipo 'text'.
            pdf_key: Chave do documento de origem.
            item_index: Índice do item no array de conteúdo.

        Returns:
            Lista de chunks gerados a partir do item.
        """
        content = item.get("content", "").strip()
        if not content:
            return []

        parts = self.splitter.split(content)
        chunks = []

        for chunk_index, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            chunk_id = f"{pdf_key}_{item_index:03d}_{chunk_index:02d}"

            chunks.append(Chunk(
                chunk_id=chunk_id,
                document=pdf_key,
                page=item.get("page", 0),
                sections=item.get("sections", []),
                type="text",
                content=part,
                token_count=count_tokens(part),
                is_auxiliary=item.get("is_auxiliary", False),
                caption=None,
            ))

        return chunks

    def _chunk_table_item(self, item: dict, pdf_key: str, item_index: int) -> Optional[Chunk]:
        """Converte um item de tabela em um único chunk.

        Tabelas não são divididas para preservar sua estrutura. Se excederem
        o limite máximo de tokens, são truncadas com aviso no log.

        Args:
            item: Item de conteúdo do tipo 'table'.
            pdf_key: Chave do documento de origem.
            item_index: Índice do item no array de conteúdo.

        Returns:
            Chunk da tabela ou None se o conteúdo estiver vazio.
        """
        content = item.get("content", "").strip()
        if not content:
            return None

        token_count = count_tokens(content)

        if token_count > self.config.max_table_tokens:
            self.logger.warning(
                "[%s] Tabela item=%d excede %d tokens (%d). Será truncada.",
                pdf_key,
                item_index,
                self.config.max_table_tokens,
                token_count,
            )
            words = content.split()
            content = " ".join(words[:self.config.max_table_tokens])
            token_count = self.config.max_table_tokens

        chunk_id = f"{pdf_key}_{item_index:03d}_00"

        return Chunk(
            chunk_id=chunk_id,
            document=pdf_key,
            page=item.get("page", 0),
            sections=item.get("sections", []),
            type="table",
            content=content,
            token_count=token_count,
            is_auxiliary=item.get("is_auxiliary", False),
            caption=item.get("caption"),
        )
