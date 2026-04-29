"""
Constantes globais do projeto RAG IPARDES Paraná.
Centraliza todos os paths, defaults e configurações.
"""
import os
from pathlib import Path

# ============================================================================
# Paths do Projeto
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIGS_DIR = PROJECT_ROOT / "configs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DOCS_DIR = PROJECT_ROOT / "docs"

# Data subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
EXTRACTED_DATA_DIR = DATA_DIR / "extracted"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CHUNKS_DATA_DIR = DATA_DIR / "chunks"
EMBEDDINGS_DATA_DIR = DATA_DIR / "embeddings"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

# Outputs subdirectories
PROMPTS_OUTPUT_DIR = OUTPUTS_DIR / "prompts"
RETRIEVAL_LOGS_DIR = OUTPUTS_DIR / "retrieval_logs"
RESPONSES_OUTPUT_DIR = OUTPUTS_DIR / "responses"
EVALUATIONS_OUTPUT_DIR = OUTPUTS_DIR / "evaluations"

# ============================================================================
# PDF Sources (os 3 documentos oficiais do IPARDES)
# ============================================================================

PDF_SOURCES = {
    "desenvolvimento_paranaense": {
        "url": "https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2023-09/desenvolvimento_paranaense.pdf",
        "local_path": RAW_DATA_DIR / "desenvolvimento_paranaense.pdf",
        "description": "Desenvolvimento Paranaense - Análise socioeconômica do Estado"
    },
    "analise_conjuntural": {
        "url": "https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2026-02/Analise_Conjuntural_julho_agosto_2025.pdf",
        "local_path": RAW_DATA_DIR / "Analise_Conjuntural_julho_agosto_2025.pdf",
        "description": "Análise Conjuntural - Julho/Agosto 2025"
    },
    "avaliacoes_politicas": {
        "url": "https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2025-12/Avaliacoes%20Politicas%20Publicas%20Brasil_revisao%20escopo.pdf",
        "local_path": RAW_DATA_DIR / "Avaliacoes Politicas Publicas Brasil_revisao escopo.pdf",
        "description": "Avaliações de Políticas Públicas Brasil - Revisão de Escopo"
    }
}

# ============================================================================
# PDF Extraction Configuration
# ============================================================================
PDF_EXTRACTOR_TIMEOUT = 300  # segundos
PDF_EXTRACTOR_MAX_PAGES = None  # None = todos os PDFs

# ============================================================================
# Chunking Configuration Defaults
# ============================================================================
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 0.20  # 20% overlap para continuidade semântica

# ============================================================================
# Embedding Configuration
# ============================================================================
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"

# ============================================================================
# Vector Store Configuration
# ============================================================================
VECTOR_STORE_TYPE = "faiss"
FAISS_INDEX_PATH = VECTOR_DB_DIR / "faiss.index"
FAISS_METADATA_PATH = VECTOR_DB_DIR / "faiss_manifest.json"
# ============================================================================
# Retrieval Configuration
# ============================================================================
RETRIEVAL_TOP_K = 5
SIMILARITY_THRESHOLD = 0.4
USE_RERANKING = True
USE_MMR = True
# ============================================================================
# LLM Configuration
# ============================================================================
LLM_MODEL_NAME = "mistral-7b-instruct-q4"
LLM_CONTEXT_WINDOW = 4096
LLM_TEMPERATURE = 0.1  # Baixa temperatura para respostas factuais
LLM_MAX_TOKENS = 500
LLM_TOP_P = 0.95

# ============================================================================
# Preprocessing Configuration
# ============================================================================
REMOVE_STOPWORDS = False
APPLY_LEMMATIZATION = False
APPLY_STEMMING = False

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# API Configuration
# ============================================================================
API_HOST = "0.0.0.0"
API_PORT = 8000
API_DEBUG = True


def create_directories():
    """
    Cria todos os diretórios necessários se não existirem.
    Chamado no início do projeto.
    """
    dirs = [
        RAW_DATA_DIR,
        EXTRACTED_DATA_DIR,
        PROCESSED_DATA_DIR,
        CHUNKS_DATA_DIR,
        EMBEDDINGS_DATA_DIR,
        VECTOR_DB_DIR,
        PROMPTS_OUTPUT_DIR,
        RETRIEVAL_LOGS_DIR,
        RESPONSES_OUTPUT_DIR,
        EVALUATIONS_OUTPUT_DIR,
        LOGS_DIR,
        CONFIGS_DIR,
        SCRIPTS_DIR,
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    create_directories()
    print(f"✓ Diretórios criados em: {PROJECT_ROOT}")
