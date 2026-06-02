"""
Script para iniciar o servidor web FastAPI com o frontend RAG.

Execução:
    python scripts/server.py

O servidor estará disponível em: http://localhost:8000
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importações
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from src.core.logger import setup_logger

logger = setup_logger(__name__)


def main() -> int:
    """Inicia o servidor FastAPI."""
    logger.info("Iniciando servidor RAG...")
    logger.info("")
    logger.info("=" * 60)
    logger.info("RAG IPARDES Paraná — Servidor Web")
    logger.info("=" * 60)
    logger.info("🚀 Servidor disponível em: http://localhost:8000")
    logger.info("📡 API disponível em:      http://localhost:8000/api/health")
    logger.info("")
    logger.info("Pressione Ctrl+C para parar o servidor.")
    logger.info("=" * 60)
    logger.info("")

    try:
        uvicorn.run(
            "src.api.app:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
        )
    except KeyboardInterrupt:
        logger.info("Servidor encerrado.")
        return 0
    except Exception as e:
        logger.exception("Erro ao iniciar servidor:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
