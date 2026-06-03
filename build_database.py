"""
Script centralizado para construir todo o banco de dados RAG.

Executa a pipeline completa de construção do banco de dados:
  1. Extração de PDFs (Docling)
  2. Pré-processamento (limpeza e estruturação)
  3. Chunking (divisão section-aware)
  4. Embedding (geração de vetores)
  5. Indexação vetorial (ChromaDB)

Uso:
    python build_database.py

Este script é uma orquestração de todos os scripts individuais em scripts/,
permitindo construir o banco de dados com um único comando.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.logger import get_timestamped_logfile, setup_logger
from src.core.directory_config import create_directories
from scripts.ingest import main as ingest_main
from scripts.preprocess import main as preprocess_main
from scripts.chunk import main as chunk_main
from scripts.embed import main as embed_main
from scripts.index import main as index_main



def run_step(step_name: str, step_number: int, total_steps: int, step_func) -> bool:
    """
    Executa uma etapa do pipeline com logging estruturado.

    Args:
        step_name: Nome da etapa para logging
        step_number: Número da etapa (1, 2, 3, ...)
        total_steps: Total de etapas
        step_func: Função que executa a etapa (deve retornar int, 0=sucesso)

    Returns:
        True se sucesso, False se falha
    """
    logger = setup_logger(__name__)
    start_time = time.time()

    logger.info("")
    logger.info("=" * 70)
    logger.info("ETAPA %d/%d — %s", step_number, total_steps, step_name)
    logger.info("=" * 70)

    try:
        result = step_func()
        elapsed = time.time() - start_time

        if result == 0:
            logger.info("✓ %s concluída com sucesso em %.2fs", step_name, elapsed)
            return True
        else:
            logger.error("✗ %s falhou (código %d)", step_name, result)
            return False

    except Exception as e:
        elapsed = time.time() - start_time
        logger.exception("✗ %s falhou com exceção após %.2fs", step_name, elapsed)
        return False


def main() -> int:
    """
    Executa o pipeline completo de construção do banco de dados.

    Returns:
        0 se todas as etapas foram executadas com sucesso, 1 se falha em alguma
    """

    logger = setup_logger(__name__, log_file=get_timestamped_logfile("build_database"))

    create_directories()

    logger.info("")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "  RAG IPARDES PARANÁ — CONSTRUÇÃO DO BANCO DE DADOS".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "=" * 68 + "╝")

    steps = [
        ("Extração de PDFs (Docling)", ingest_main),
        ("Pré-processamento", preprocess_main),
        ("Chunking", chunk_main),
        ("Embedding", embed_main),
        ("Indexação Vetorial", index_main),
    ]

    results = []
    for step_number, (step_name, step_func) in enumerate(steps, 1):
        success = run_step(step_name, step_number, len(steps), step_func)
        results.append((step_name, success))

        if not success:
            logger.error("")
            logger.error("!" * 70)
            logger.error(
                "PIPELINE INTERROMPIDA: Falha em '%s' (Etapa %d)",
                step_name,
                step_number,
            )
            logger.error("!" * 70)
            return 1

    logger.info("")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "  ✓ BANCO DE DADOS CONSTRUÍDO COM SUCESSO".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "=" * 68 + "╝")

    logger.info("")
    logger.info("Resumo das etapas:")
    logger.info("-" * 70)
    for step_name, success in results:
        status = "✓ OK" if success else "✗ FALHA"
        logger.info("  [%s] %s", status, step_name)
    logger.info("-" * 70)

    logger.info("")
    logger.info("Próximos passos:")
    logger.info("  1. Inicie o Ollama em outro terminal:")
    logger.info("     $ ollama serve")
    logger.info("")
    logger.info("  2. Em outro terminal, inicie o servidor:")
    logger.info("     $ python run_rag.py")
    logger.info("")
    logger.info("  3. Abra no navegador:")
    logger.info("     http://localhost:8000")
    logger.info("")

    return 0

if __name__ == "__main__":
    sys.exit(main())
