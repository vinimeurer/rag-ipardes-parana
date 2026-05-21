"""
Pipeline de indexação vetorial usando ChromaDB.

Lê o arquivo chunks_with_embeddings.jsonl e insere todos os chunks
no banco vetorial persistente, recriando a coleção do zero a cada execução.
"""

import json
from pathlib import Path
from typing import Optional

import chromadb

from ..core.logger import setup_logger
from ..core.indexing_config import IndexingConfig


class Indexer:
    """Constrói e persiste o banco vetorial ChromaDB a partir dos embeddings.

    Recria a coleção do zero a cada execução para garantir sincronização
    completa com o arquivo de embeddings. Insere chunks em lotes para
    eficiência de memória.

    Attributes:
        config: Configuração do pipeline de indexação.
        logger: Logger do módulo.
    """

    def __init__(self, config: Optional[IndexingConfig] = None):
        """Inicializa o indexer com a configuração fornecida.

        Args:
            config: Configuração de indexação. Se omitida, usa valores padrão.
        """
        self.config = config or IndexingConfig()
        self.logger = setup_logger(__name__)

    def run(self, embeddings_path: Optional[Path] = None) -> int:
        """Executa o pipeline completo de indexação.

        Lê os embeddings, recria a coleção ChromaDB e insere todos os chunks.

        Args:
            embeddings_path: Caminho do arquivo chunks_with_embeddings.jsonl.
                Se omitido, usa a configuração.

        Returns:
            Número de chunks indexados.
        """
        src = embeddings_path or (
            self.config.paths.embeddings_dir / self.config.embeddings_filename
        )

        chunks = self._load_chunks(src)
        self.logger.info("Chunks carregados: %d", len(chunks))

        collection = self._prepare_collection()
        count = self._insert_batches(chunks, collection)

        self.logger.info(
            "Indexação concluída | chunks=%d | coleção='%s' | db=%s",
            count,
            self.config.collection_name,
            self.config.paths.vector_db_dir,
        )
        return count

    def _load_chunks(self, path: Path) -> list[dict]:
        """Carrega chunks com embeddings do arquivo JSONL.

        Args:
            path: Caminho do arquivo de entrada.

        Returns:
            Lista de dicionários com chunk e embedding.
        """
        chunks = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
        return chunks

    def _prepare_collection(self) -> chromadb.Collection:
        """Cria o cliente ChromaDB e recria a coleção do zero.

        A coleção é sempre deletada e recriada para garantir sincronização
        completa com o arquivo de embeddings atual.

        Returns:
            Coleção ChromaDB pronta para inserção.
        """
        self.config.paths.vector_db_dir.mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(
            path=str(self.config.paths.vector_db_dir)
        )

        try:
            client.delete_collection(self.config.collection_name)
            self.logger.info(
                "Coleção '%s' existente removida.", self.config.collection_name
            )
        except Exception:
            pass

        collection = client.create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": self.config.distance_metric},
        )

        self.logger.info(
            "Coleção '%s' criada com métrica '%s'.",
            self.config.collection_name,
            self.config.distance_metric,
        )
        return collection

    def _insert_batches(
        self, chunks: list[dict], collection: chromadb.Collection
    ) -> int:
        """Insere chunks em lotes na coleção ChromaDB.

        Args:
            chunks: Lista de chunks com embeddings.
            collection: Coleção ChromaDB de destino.

        Returns:
            Total de chunks inseridos com sucesso.
        """
        total = 0
        batch_size = self.config.batch_size

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]

            ids, embeddings, documents, metadatas = [], [], [], []

            for chunk in batch:
                ids.append(chunk["chunk_id"])
                embeddings.append(chunk["embedding"])
                documents.append(chunk["content"])
                metadatas.append(self._build_metadata(chunk))

            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

            total += len(batch)
            self.logger.debug(
                "Lote inserido: %d/%d", total, len(chunks)
            )

        return total

    def _build_metadata(self, chunk: dict) -> dict:
        """Constrói o dicionário de metadados para o ChromaDB.

        ChromaDB não aceita valores None nem listas em metadados.
        Seções são serializadas como string 'A > B > C' para preservar
        a hierarquia de forma consultável. Caption None vira string vazia.

        Args:
            chunk: Dicionário do chunk com todos os campos.

        Returns:
            Dicionário de metadados compatível com ChromaDB.
        """
        return {
            "document": chunk.get("document", ""),
            "page": chunk.get("page", 0),
            "sections": " > ".join(chunk.get("sections", [])),
            "type": chunk.get("type", "text"),
            "token_count": chunk.get("token_count", 0),
            "is_auxiliary": chunk.get("is_auxiliary", False),
            "caption": chunk.get("caption") or "",
        }
