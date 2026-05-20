"""
Script principal para geração de chunks dos documentos processados.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logger import get_timestamped_logfile, setup_logger
from src.core.chunking_config import ChunkingConfig
from src.chunking.chunker import Chunker


def main() -> int:
    """Executa o pipeline de chunking para todos os documentos processados.

    Returns:
        Código de saída 0 em caso de sucesso.
    """
    logger = setup_logger(__name__, log_file=get_timestamped_logfile("chunking"))
    config = ChunkingConfig()

    logger.info("%s", "=" * 60)
    logger.info("Iniciando pipeline de chunking")
    logger.info("%s", "=" * 60)

    logger.info(
        "Configuração | chunk_size=%d | overlap=%d | min_tokens=%d | max_table_tokens=%d",
        config.chunk_size,
        config.overlap,
        config.min_chunk_tokens,
        config.max_table_tokens,
    )

    logger.info("Step 1: Verificando diretórios...")
    config.paths.processed_dir.mkdir(parents=True, exist_ok=True)
    config.paths.chunks_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "✓ Diretórios prontos | entrada=%s | saída=%s",
        config.paths.processed_dir,
        config.paths.chunks_dir,
    )

    logger.info("Step 2: Gerando chunks...")
    chunker = Chunker(config)
    chunks = chunker.chunk_all()

    logger.info("Step 3: Salvando chunks...")
    output_path = chunker.save(chunks)

    total_text = sum(1 for c in chunks if c.type == "text")
    total_table = sum(1 for c in chunks if c.type == "table")
    total_auxiliary = sum(1 for c in chunks if c.is_auxiliary)
    docs = set(c.document for c in chunks)

    logger.info("%s", "-" * 60)
    logger.info("RESUMO DO CHUNKING")
    logger.info("%s", "-" * 60)
    logger.info("Documentos processados: %d", len(docs))
    logger.info("Total de chunks: %d", len(chunks))
    logger.info("  Texto: %d", total_text)
    logger.info("  Tabela: %d", total_table)
    logger.info("  Auxiliares: %d", total_auxiliary)
    logger.info("Arquivo gerado: %s", output_path)
    logger.info("%s", "-" * 60)
    logger.info("✓ CHUNKING CONCLUÍDO")

    return 0


if __name__ == "__main__":
    sys.exit(main())
