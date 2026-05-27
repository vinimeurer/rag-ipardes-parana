"""
Módulo RAG do pipeline de Retrieval-Augmented Generation.
"""

from .llm_client import LLMClient
from .prompt_builder import PromptBuilder
from .rag_pipeline import RAGPipeline, RAGResponse
from .retriever import RetrievedChunk, Retriever

__all__ = [
    "LLMClient",
    "PromptBuilder",
    "RAGPipeline",
    "RAGResponse",
    "RetrievedChunk",
    "Retriever",
]
