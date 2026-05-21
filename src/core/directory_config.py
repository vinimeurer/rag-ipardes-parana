"""
Configurações centralizadas de diretórios e paths do projeto RAG IPARDES Paraná.

Centraliza todos os paths absolutos do projeto, facilitando a manutenção
e evitando paths hardcoded em diferentes módulos.
"""

from pathlib import Path

# ============================================================================
# Root Directory
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent

# ============================================================================
# Main Directories
# ============================================================================
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
LOGS_DIR = PROJECT_ROOT / "logs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# ============================================================================
# Data Subdirectories
# ============================================================================
RAW_DATA_DIR = DATA_DIR / "raw"
EXTRACTED_DATA_DIR = DATA_DIR / "extracted"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CHUNKS_DATA_DIR = DATA_DIR / "chunks"
EMBEDDINGS_DATA_DIR = DATA_DIR / "embeddings"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

# ============================================================================
# Models Subdirectories
# ============================================================================
EMBEDDINGS_MODELS_DIR = MODELS_DIR / "embeddings"

# ============================================================================
# Outputs Subdirectories
# ============================================================================
PROMPTS_OUTPUT_DIR = OUTPUTS_DIR / "prompts"
RETRIEVAL_LOGS_DIR = OUTPUTS_DIR / "retrieval_logs"
RESPONSES_OUTPUT_DIR = OUTPUTS_DIR / "responses"
EVALUATIONS_OUTPUT_DIR = OUTPUTS_DIR / "evaluations"


def create_directories() -> None:
    """
    Cria todos os diretórios necessários se não existirem.
    Deve ser chamado no início do projeto ou pipeline.
    """
    directories = [
        RAW_DATA_DIR,
        EXTRACTED_DATA_DIR,
        PROCESSED_DATA_DIR,
        CHUNKS_DATA_DIR,
        EMBEDDINGS_DATA_DIR,
        VECTOR_DB_DIR,
        EMBEDDINGS_MODELS_DIR,
        PROMPTS_OUTPUT_DIR,
        RETRIEVAL_LOGS_DIR,
        RESPONSES_OUTPUT_DIR,
        EVALUATIONS_OUTPUT_DIR,
        LOGS_DIR,
        SCRIPTS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    create_directories()
    print(f"✓ Diretórios criados em: {PROJECT_ROOT}")
