"""
Recuperação de chunks relevantes a partir do banco vetorial ChromaDB.
"""

from dataclasses import dataclass
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from ..core.logger import setup_logger
from ..core.rag_config import RAGConfig


@dataclass
class RetrievedChunk:
    """Representa um chunk recuperado com sua pontuação de relevância.

    Attributes:
        chunk_id: Identificador único do chunk.
        document: Chave do documento de origem.
        page: Número da página de origem.
        sections: Hierarquia de seções ativas no bloco de origem.
        type: Tipo do conteúdo ('text' ou 'table').
        content: Texto do chunk.
        caption: Legenda da tabela, quando aplicável.
        similarity: Pontuação de similaridade (1 - distância cosseno).
            Valores próximos a 1 indicam alta relevância.
    """

    chunk_id: str
    document: str
    page: int
    sections: list[str]
    type: str
    content: str
    caption: str | None
    similarity: float


class Retriever:
    """Recupera chunks relevantes do banco vetorial para uma query.

    Codifica a query com o mesmo modelo de embedding usado na indexação,
    consulta o ChromaDB por similaridade de cosseno e filtra os resultados
    pelo threshold de similaridade mínima configurado.

    Attributes:
        config: Configuração do pipeline RAG.
        logger: Logger do módulo.
    """

    def __init__(self, config: RAGConfig):
        """Inicializa o retriever carregando modelo e banco vetorial.

        Args:
            config: Configuração completa do pipeline RAG.
        """
        self.config = config
        self.logger = setup_logger(__name__)

        self.logger.info("Carregando modelo de embedding para queries...")
        self._encoder = SentenceTransformer(
            config.embedding_model,
            cache_folder=str(config.embedding_model_path),
        )

        self._collection = self._load_collection()
        self.logger.info("Retriever pronto.")

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        """Recupera os chunks mais relevantes para uma query.

        Codifica a query, consulta o ChromaDB e retorna apenas os chunks
        que superam o threshold mínimo de similaridade. Se nenhum chunk
        superar o threshold, retorna lista vazia — indicando ao pipeline
        RAG que a query está fora do escopo dos documentos.

        Args:
            query: Pergunta em linguagem natural do usuário.

        Returns:
            Lista de chunks relevantes ordenados por similaridade decrescente.
            Lista vazia se nenhum chunk superar o threshold.
        """
        query_vector = self._encoder.encode(
            [query], normalize_embeddings=True
        )[0].tolist()

        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=self.config.retriever.top_k,
            include=["metadatas", "documents", "distances"],
        )

        chunks = []
        ids = results["ids"][0]
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]
        distances = results["distances"][0]

        for chunk_id, meta, content, distance in zip(ids, metadatas, documents, distances):
            similarity = 1.0 - distance
            if similarity >= self.config.retriever.min_similarity:
                chunks.append(RetrievedChunk(
                    chunk_id=chunk_id,
                    document=meta.get("document", ""),
                    page=meta.get("page", 0),
                    sections=meta.get("sections", "").split(" > ") if meta.get("sections") else [],
                    type=meta.get("type", "text"),
                    content=content,
                    caption=meta.get("caption") or None,
                    similarity=round(similarity, 4),
                ))

        self.logger.debug(
            "Query recuperou %d/%d chunks acima do threshold (%.2f)",
            len(chunks),
            self.config.retriever.top_k,
            self.config.retriever.min_similarity,
        )

        return chunks

    def _load_collection(self) -> chromadb.Collection:
        """Carrega a coleção ChromaDB persistida em disco.

        Returns:
            Coleção ChromaDB pronta para consulta.
        """
        client = chromadb.PersistentClient(
            path=str(self.config.paths.vector_db_dir)
        )
        return client.get_collection(self.config.retriever.collection_name)
