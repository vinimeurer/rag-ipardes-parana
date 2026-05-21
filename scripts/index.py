"""
Script principal para indexação dos chunks no banco vetorial ChromaDB.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logger import get_timestamped_logfile, setup_logger
from src.core.indexing_config import IndexingConfig
from src.indexing.indexer import Indexer


def main() -> int:
    """Executa o pipeline de indexação vetorial.

    Lê o arquivo chunks_with_embeddings.jsonl, recria a coleção
    ChromaDB do zero e indexa todos os chunks.

    Returns:
        Código de saída 0 em caso de sucesso.
    """
    logger = setup_logger(__name__, log_file=get_timestamped_logfile("index"))
    config = IndexingConfig()

    logger.info("%s", "=" * 60)
    logger.info("Iniciando pipeline de indexação vetorial")
    logger.info("%s", "=" * 60)

    logger.info(
        "Configuração | coleção=%s | métrica=%s | batch_size=%d",
        config.collection_name,
        config.distance_metric,
        config.batch_size,
    )

    logger.info("Step 1: Verificando diretórios...")
    config.paths.embeddings_dir.mkdir(parents=True, exist_ok=True)
    config.paths.vector_db_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "✓ Diretórios prontos | entrada=%s | db=%s",
        config.paths.embeddings_dir,
        config.paths.vector_db_dir,
    )

    logger.info("Step 2: Indexando chunks...")
    indexer = Indexer(config)
    total = indexer.run()

    logger.info("%s", "-" * 60)
    logger.info("RESUMO DA INDEXAÇÃO")
    logger.info("%s", "-" * 60)
    logger.info("Chunks indexados: %d", total)
    logger.info("Coleção: %s", config.collection_name)
    logger.info("Banco vetorial: %s", config.paths.vector_db_dir)
    logger.info("%s", "-" * 60)
    logger.info("✓ INDEXAÇÃO CONCLUÍDA")

    return 0


if __name__ == "__main__":
    sys.exit(main())
