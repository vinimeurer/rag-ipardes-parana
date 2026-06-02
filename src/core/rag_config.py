"""
Configurações centralizadas para o pipeline RAG.
"""

from dataclasses import dataclass, field
from pathlib import Path


VECTOR_DB_DIR = Path("data/vector_db")
EMBEDDINGS_DATA_DIR = Path("data/embeddings")


@dataclass
class RAGPaths:
    """Caminhos utilizados pelo pipeline RAG."""

    vector_db_dir: Path = VECTOR_DB_DIR
    embeddings_dir: Path = EMBEDDINGS_DATA_DIR


@dataclass
class RetrieverConfig:
    """Parâmetros de configuração do retriever.

    Attributes:
        collection_name: Nome da coleção ChromaDB a consultar.
        top_k: Número de chunks recuperados por query antes do reranking.
            Deve ser maior que reranker_top_k para que o reranker tenha
            candidatos suficientes para reordenar.
        reranker_top_k: Número de chunks selecionados após reranking
            para compor o contexto enviado ao LLM.
        min_similarity: Threshold mínimo de similaridade cosseno aplicado
            após o retriever inicial. Chunks abaixo deste valor são descartados
            antes do reranking. Se nenhum chunk superar o threshold, o sistema
            recusa responder em vez de inventar informação.
    """

    collection_name: str = "chunks"
    top_k: int = 15
    reranker_top_k: int = 5
    min_similarity: float = 0.35


@dataclass
class RerankerConfig:
    """Parâmetros de configuração do reranker.

    Attributes:
        model_name: Nome do modelo cross-encoder para reranking.
            O bge-reranker-v2-m3 é da mesma família do embedder BGE-M3,
            otimizado para trabalhar em conjunto com ele e com suporte a PT-BR.
        cache_folder: Diretório de cache local do modelo de reranking.
        min_score: Score mínimo do reranker para manter um chunk.
            Scores abaixo deste valor são descartados após o reranking.
            O cross-encoder retorna logits sem escala fixa — calibrar
            empiricamente durante os testes.
        enabled: Se False, o reranker é ignorado e o pipeline usa
            apenas os resultados do retriever inicial.
    """

    model_name: str = "BAAI/bge-reranker-v2-m3"
    cache_folder: Path = Path("models/rerankers")
    min_score: float = 0.0
    enabled: bool = True


@dataclass
class LLMConfig:
    """Parâmetros de configuração do modelo de linguagem.

    Attributes:
        model_name: Nome do modelo Ollama a utilizar.
        temperature: Temperatura de geração. Valores baixos produzem
            respostas mais determinísticas e factuais, adequado para RAG.
        max_tokens: Limite de tokens na resposta gerada.
        ollama_host: Endereço do servidor Ollama local.
    """

    model_name: str = "llama3.2:3b"
    temperature: float = 0.1
    max_tokens: int = 1024
    ollama_host: str = "http://localhost:11434"


@dataclass
class RAGConfig:
    """Configuração completa do pipeline RAG.

    Attributes:
        paths: Caminhos de entrada.
        retriever: Configuração do retriever vetorial.
        reranker: Configuração do reranker cross-encoder.
        llm: Configuração do modelo de linguagem.
        embedding_model: Nome do modelo de embedding para codificar queries.
        embedding_model_path: Diretório de cache do modelo de embedding.
    """

    paths: RAGPaths = field(default_factory=RAGPaths)
    retriever: RetrieverConfig = field(default_factory=RetrieverConfig)
    reranker: RerankerConfig = field(default_factory=RerankerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding_model: str = "BAAI/bge-m3"
    embedding_model_path: Path = Path("models/embeddings")
