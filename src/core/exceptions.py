"""
Exceções customizadas para o projeto RAG IPARDES.
Facilita tratamento robusto de erros em cada etapa do pipeline.
"""


class RAGException(Exception):
    """Exceção base para todas as exceções do RAG."""
    pass


class PDFExtractionError(RAGException):
    """Erro ao extrair conteúdo de PDF."""
    pass


class PreprocessingError(RAGException):
    """Erro ao pré-processar texto."""
    pass


class ChunkingError(RAGException):
    """Erro ao fazer chunking dos documentos."""
    pass


class EmbeddingError(RAGException):
    """Erro ao gerar embeddings."""
    pass


class VectorStoreError(RAGException):
    """Erro ao acessar/persistir vector store."""
    pass


class RetrievalError(RAGException):
    """Erro durante retrieval."""
    pass


class RerankingError(RAGException):
    """Erro durante reranking."""
    pass


class NoRelevantDocumentsError(RAGException):
    """Nenhum documento relevante encontrado."""
    pass


class ContextWindowExceededError(RAGException):
    """Contexto excede janela da LLM."""
    pass


class LLMGenerationError(RAGException):
    """Erro ao gerar resposta com LLM."""
    pass


class PromptBuildingError(RAGException):
    """Erro ao construir prompt final."""
    pass
