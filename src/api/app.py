"""
API FastAPI para o pipeline RAG IPARDES Paraná.

Expõe endpoints para:
- POST /api/chat: Enviar pergunta e receber resposta com trechos e prompt
- GET /api/health: Verificar saúde da API
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..core.logger import setup_logger
from ..core.rag_config import RAGConfig
from ..rag.rag_pipeline import RAGPipeline, RAGResponse

# ============================================================================
# Modelos de requisição/resposta
# ============================================================================


class ChunkData(BaseModel):
    """Representação de um chunk recuperado para o frontend."""

    chunk_id: str
    document: str
    page: int
    sections: list[str]
    type: str
    content: str
    caption: Optional[str] = None
    similarity: float
    rerank_score: Optional[float] = None


class ChatRequest(BaseModel):
    """Requisição de chat."""

    question: str


class ChatResponse(BaseModel):
    """Resposta completa de uma query ao RAG.
    
    Contém:
    - A pergunta original
    - A resposta gerada
    - Os trechos usados como base
    - O prompt completo (para auditoria)
    - Flag indicando se está fora do escopo
    """

    question: str
    answer: str
    chunks: list[ChunkData]
    prompt: str
    out_of_scope: bool
    chunks_before_rerank: Optional[list[ChunkData]] = None


# ============================================================================
# Inicialização da API
# ============================================================================

logger = setup_logger(__name__)

app = FastAPI(
    title="RAG IPARDES Paraná",
    description="API de Chat Baseada em RAG com Documentos do IPARDES",
    version="1.0.0",
)

# Carrega configuração e inicializa pipeline
try:
    config = RAGConfig()
    pipeline = RAGPipeline(config)
    logger.info("Pipeline RAG inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar pipeline: {e}")
    pipeline = None


# ============================================================================
# Rotas
# ============================================================================


@app.get("/api/health")
async def health() -> dict:
    """Verifica saúde da API e disponibilidade do pipeline."""
    if pipeline is None:
        raise HTTPException(
            status_code=503, detail="Pipeline RAG não disponível"
        )
    return {
        "status": "healthy",
        "pipeline_ready": True,
        "embedding_model": pipeline.config.embedding_model,
        "llm_model": pipeline.config.llm.model_name,
    }


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """Processa uma pergunta e retorna resposta + trechos + prompt.
    
    Args:
        request: Objeto com a pergunta do usuário.
        
    Returns:
        ChatResponse com resposta, chunks utilizados e prompt completo.
        
    Raises:
        HTTPException 503: Se o pipeline não estiver disponível.
        HTTPException 400: Se a pergunta for vazia.
    """
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Pipeline RAG não inicializado. Verifique se o Ollama está rodando e o banco vetorial está disponível.",
        )

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Pergunta não pode ser vazia")

    try:
        logger.info(f"Processando query: {question}")

        # Executa pipeline
        rag_response: RAGResponse = pipeline.query(question)

        # Converte chunks para modelo de resposta
        chunks_data = [
            ChunkData(
                chunk_id=chunk.chunk_id,
                document=chunk.document,
                page=chunk.page,
                sections=chunk.sections,
                type=chunk.type,
                content=chunk.content,
                caption=chunk.caption,
                similarity=chunk.similarity,
                rerank_score=chunk.rerank_score,
            )
            for chunk in rag_response.chunks
        ]

        chunks_before_rerank_data = (
            [
                ChunkData(
                    chunk_id=chunk.chunk_id,
                    document=chunk.document,
                    page=chunk.page,
                    sections=chunk.sections,
                    type=chunk.type,
                    content=chunk.content,
                    caption=chunk.caption,
                    similarity=chunk.similarity,
                    rerank_score=chunk.rerank_score,
                )
                for chunk in rag_response.chunks_before_rerank
            ]
            if rag_response.chunks_before_rerank
            else None
        )

        return ChatResponse(
            question=rag_response.query,
            answer=rag_response.answer,
            chunks=chunks_data,
            prompt=rag_response.prompt,
            out_of_scope=rag_response.out_of_scope,
            chunks_before_rerank=chunks_before_rerank_data,
        )

    except Exception as e:
        logger.exception("Erro ao processar query")
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")


@app.get("/")
async def root() -> FileResponse:
    """Serve a página HTML do frontend."""
    frontend_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if not frontend_path.exists():
        return {"message": "Frontend não encontrado. Acesse /api/health para verificar o status da API."}
    return FileResponse(frontend_path)


# ============================================================================
# Servir arquivos estáticos do frontend
# ============================================================================

frontend_path = Path(__file__).parent.parent.parent / "frontend"
assets_path = frontend_path / "assets"
if assets_path.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(assets_path)),
        name="assets",
    )


# ============================================================================
# Configuração CORS (se necessário)
# ============================================================================

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando servidor FastAPI...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
