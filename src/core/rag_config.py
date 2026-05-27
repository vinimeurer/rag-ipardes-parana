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
        top_k: Número de chunks recuperados por query.
        min_similarity: Threshold mínimo de similaridade (distância cosseno).
            Chunks com distância acima deste valor são considerados irrelevantes.
            Se todos os chunks recuperados forem irrelevantes, o sistema recusa
            responder em vez de inventar informação.
    """

    collection_name: str = "chunks"
    top_k: int = 5
    min_similarity: float = 0.35


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
        llm: Configuração do modelo de linguagem.
        embedding_model: Nome do modelo de embedding para codificar queries.
        embedding_model_path: Caminho local do modelo de embedding em cache.
    """

    paths: RAGPaths = field(default_factory=RAGPaths)
    retriever: RetrieverConfig = field(default_factory=RetrieverConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding_model: str = "BAAI/bge-m3"
    embedding_model_path: Path = Path("models/embeddings")
