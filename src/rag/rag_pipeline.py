"""
Pipeline RAG principal — orquestra retrieval, reranking, construção de prompt e geração.
"""

from dataclasses import dataclass

from ..core.logger import setup_logger
from ..core.rag_config import RAGConfig
from .llm_client import LLMClient
from .prompt_builder import PromptBuilder
from .reranker import Reranker
from .retriever import RetrievedChunk, Retriever


@dataclass
class RAGResponse:
    """Resultado completo de uma query ao pipeline RAG.

    Attributes:
        query: Pergunta original do usuário.
        answer: Resposta gerada pelo LLM.
        chunks: Chunks utilizados como contexto após reranking.
        chunks_before_rerank: Chunks recuperados antes do reranking.
        prompt: Prompt completo enviado ao LLM.
        out_of_scope: True se a query estava fora do escopo dos documentos.
    """

    query: str
    answer: str
    chunks: list[RetrievedChunk]
    chunks_before_rerank: list[RetrievedChunk]
    prompt: str
    out_of_scope: bool


class RAGPipeline:
    """Orquestra o pipeline completo de Retrieval-Augmented Generation.

    Para cada query:
    1. Recupera os top_k chunks mais similares do banco vetorial (retriever)
    2. Reordena os candidatos com o cross-encoder (reranker)
    3. Seleciona os reranker_top_k melhores chunks
    4. Verifica se algum chunk supera os thresholds de relevância
    5. Se sim, monta o prompt com contexto e gera a resposta
    6. Se não, informa que o assunto não está coberto pelos documentos

    O pipeline produz duas saídas por query: o prompt com os trechos
    utilizados e a resposta final, atendendo ao requisito de auditabilidade.

    Attributes:
        config: Configuração completa do pipeline.
        retriever: Componente de recuperação vetorial inicial.
        reranker: Componente de reordenação por cross-encoder.
        prompt_builder: Componente de construção de prompts.
        llm: Cliente do modelo de linguagem.
        logger: Logger do módulo.
    """

    def __init__(self, config: RAGConfig | None = None):
        """Inicializa o pipeline carregando todos os componentes.

        Args:
            config: Configuração do pipeline. Se omitida, usa valores padrão.
        """
        self.config = config or RAGConfig()
        self.logger = setup_logger(__name__)

        self.logger.info("Inicializando pipeline RAG...")
        self.retriever = Retriever(self.config)

        self.reranker = None
        if self.config.reranker.enabled:
            self.reranker = Reranker(self.config.reranker)

        self.prompt_builder = PromptBuilder()
        self.llm = LLMClient(self.config.llm)

        if not self.llm.is_available():
            self.logger.warning(
                "Modelo '%s' não encontrado no Ollama. "
                "Execute: ollama pull %s",
                self.config.llm.model_name,
                self.config.llm.model_name,
            )

        self.logger.info(
            "Pipeline pronto | modelo=%s | top_k=%d | reranker_top_k=%d | reranker=%s",
            self.config.llm.model_name,
            self.config.retriever.top_k,
            self.config.retriever.reranker_top_k,
            "ativo" if self.reranker else "desativado",
        )

    def query(self, question: str) -> RAGResponse:
        """Processa uma pergunta e retorna a resposta com auditoria completa.

        Args:
            question: Pergunta em linguagem natural do usuário.

        Returns:
            RAGResponse com resposta, chunks utilizados e prompt completo.
        """
        self.logger.info("Query: %s", question)

        retrieved = self.retriever.retrieve(question)
        chunks_before_rerank = list(retrieved)

        if retrieved and self.reranker:
            reranked = self.reranker.rerank(question, retrieved)
            chunks = reranked[: self.config.retriever.reranker_top_k]
            self.logger.info(
                "Reranking: %d → %d chunks selecionados",
                len(retrieved),
                len(chunks),
            )
        else:
            chunks = retrieved[: self.config.retriever.reranker_top_k]

        out_of_scope = len(chunks) == 0

        if out_of_scope:
            self.logger.info("Query fora do escopo — nenhum chunk acima do threshold.")
            prompt = self.prompt_builder.build_out_of_scope(question)
        else:
            self.logger.info("Chunks enviados ao LLM: %d", len(chunks))
            prompt = self.prompt_builder.build(question, chunks)

        answer = self.llm.generate(prompt)

        return RAGResponse(
            query=question,
            answer=answer,
            chunks=chunks,
            chunks_before_rerank=chunks_before_rerank,
            prompt=prompt,
            out_of_scope=out_of_scope,
        )
