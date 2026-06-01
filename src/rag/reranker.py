"""
Reranking de chunks recuperados usando cross-encoder.

Reordena os candidatos do retriever inicial com base em scores
de relevância calculados pelo cross-encoder, que compara query
e chunk diretamente em vez de usar embeddings separados.
"""

from sentence_transformers import CrossEncoder

from ..core.logger import setup_logger
from ..core.rag_config import RerankerConfig
from .retriever import RetrievedChunk


class Reranker:
    """Reordena chunks recuperados usando um modelo cross-encoder.

    O retriever inicial usa similaridade de cosseno entre embeddings
    gerados separadamente (bi-encoder), o que é rápido mas impreciso.
    O reranker usa um cross-encoder que recebe query e chunk juntos,
    calculando um score de relevância mais preciso ao custo de maior
    latência — por isso é aplicado apenas nos top-K candidatos do retriever.

    O modelo bge-reranker-v2-m3 foi escolhido por ser da mesma família
    do embedder BGE-M3, otimizado para trabalhar em conjunto com ele
    e com suporte nativo a português.

    Attributes:
        config: Configuração do reranker.
        logger: Logger do módulo.
    """

    def __init__(self, config: RerankerConfig):
        """Carrega o modelo cross-encoder do cache local ou HuggingFace.

        Args:
            config: Configuração do reranker com nome do modelo e cache.
        """
        self.config = config
        self.logger = setup_logger(__name__)

        self.logger.info("Carregando reranker '%s'...", config.model_name)
        self._model = CrossEncoder(
            config.model_name,
            cache_folder=str(config.cache_folder),
        )
        self.logger.info("Reranker pronto.")

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Reordena os chunks por relevância usando o cross-encoder.

        Calcula scores de relevância para cada par (query, chunk),
        reordena por score decrescente e descarta chunks abaixo do
        threshold mínimo configurado.

        Args:
            query: Pergunta original do usuário.
            chunks: Chunks candidatos do retriever inicial.

        Returns:
            Lista de chunks reordenados por relevância do cross-encoder,
            filtrados pelo threshold min_score.
        """
        if not chunks:
            return []

        pairs = [(query, chunk.content) for chunk in chunks]
        scores = self._model.predict(pairs)

        scored = sorted(
            zip(scores, chunks),
            key=lambda x: x[0],
            reverse=True,
        )

        reranked = []
        for score, chunk in scored:
            if float(score) >= self.config.min_score:
                chunk.rerank_score = round(float(score), 4)
                reranked.append(chunk)

        self.logger.debug(
            "Reranking: %d → %d chunks (min_score=%.2f)",
            len(chunks),
            len(reranked),
            self.config.min_score,
        )

        return reranked