"""
Script para executar o servidor web RAG IPARDES com suporte a CLI opcional.

Executa o servidor FastAPI com o frontend e aceita um argumento
opcional para ativar a interface CLI (chat interativo).

Uso:
    python run_rag.py              # Apenas servidor web
    python run_rag.py --cli        # Servidor + interface CLI
    python run_rag.py --help       # Mostrar ajuda

O servidor estará disponível em: http://localhost:8000

Requisitos:
    - Ollama deve estar rodando em http://localhost:11434
    - ChromaDB deve estar indexado (execute build_database.py antes)
"""

import sys
import time
import argparse
import threading
import uvicorn
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.directory_config import VECTOR_DB_DIR
from src.core.logger import setup_logger
from scripts.chat import main as chat_main
from src.api.app import app

logger = setup_logger(__name__)

def check_dependencies() -> bool:
    """
    Verifica se as dependências estão disponíveis.

    Returns:
        True se todas as dependências estão OK, False caso contrário
    """

    logger.info("Verificando dependências...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 11434))
        sock.close()

        if result == 0:
            logger.info("✓ Ollama está rodando em localhost:11434")
        else:
            logger.error("✗ Ollama NÃO está rodando em localhost:11434")
            logger.error("  Execute em outro terminal: ollama serve")
            return False

    except Exception as e:
        logger.error("✗ Erro ao verificar Ollama: %s", e)
        return False

    db_path = VECTOR_DB_DIR / "chroma.sqlite3"
    if db_path.exists():
        logger.info("✓ Banco de dados ChromaDB encontrado")
    else:
        logger.warning("⚠ ChromaDB ainda não foi criado")
        logger.warning("  Execute antes: python build_database.py")
        logger.warning("  Continuando mesmo assim...")

    return True


def start_server() -> None:
    """Inicia o servidor FastAPI."""

    logger.info("")
    logger.info("=" * 60)
    logger.info("RAG IPARDES Paraná — Servidor Web")
    logger.info("=" * 60)
    logger.info("🚀 Servidor disponível em: http://localhost:8000")
    logger.info("📡 API Health Check:       http://localhost:8000/api/health")
    logger.info("")
    logger.info("Pressione Ctrl+C para parar o servidor.")
    logger.info("=" * 60)
    logger.info("")

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
        )
    except KeyboardInterrupt:
        logger.info("Servidor encerrado.")
    except Exception as e:
        logger.exception("Erro ao iniciar servidor: %s", e)
        sys.exit(1)


def start_cli_interactive() -> None:
    """Inicia a interface CLI interativa (chat)."""

    time.sleep(2)

    try:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Interface CLI RAG (rodando em paralelo)")
        logger.info("=" * 60)
        logger.info("")

        chat_main()

    except Exception as e:
        logger.exception("Erro ao iniciar CLI: %s", e)


def main() -> int:
    """
    Ponto de entrada principal.

    Returns:
        Código de saída (0 = sucesso)
    """
    parser = argparse.ArgumentParser(
        description="Inicia o servidor web RAG IPARDES com opção de CLI"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Ativa a interface CLI interativa (chat) em paralelo",
    )

    args = parser.parse_args()

    if not check_dependencies():
        return 1

    logger.info("")

    if args.cli:
        cli_thread = threading.Thread(target=start_cli_interactive, daemon=False)
        cli_thread.start()

    start_server()

    return 0

if __name__ == "__main__":
    sys.exit(main())
