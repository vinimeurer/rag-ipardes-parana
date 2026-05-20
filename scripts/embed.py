"""
Script principal para geração de embeddings dos chunks processados.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logger import get_timestamped_logfile, setup_logger
from src.core.embedding_config import EmbeddingConfig
from src.embedding.embedder import Embedder


def main() -> int:
    """Executa o pipeline de embedding para todos os chunks.

    Verifica automaticamente se o modelo existe em models/embeddings/.
    Se não existir, baixa do HuggingFace e salva para uso offline futuro.
    Se existir, carrega diretamente sem acesso à internet.

    Returns:
        Código de saída 0 em caso de sucesso.
    """
    logger = setup_logger(__name__, log_file=get_timestamped_logfile("embed"))
    config = EmbeddingConfig()

    logger.info("%s", "=" * 60)
    logger.info("Iniciando pipeline de embedding")
    logger.info("%s", "=" * 60)

    logger.info(
        "Configuração | model=%s | batch_size=%d | device=%s | normalize=%s",
        config.model_name,
        config.batch_size,
        config.device,
        config.normalize,
    )

    model_cached = config.model_local_path.exists()
    logger.info(
        "Modelo em cache local: %s (%s)",
        "SIM" if model_cached else "NÃO — será baixado agora",
        config.model_local_path,
    )

    logger.info("Step 1: Verificando diretórios...")
    config.paths.chunks_dir.mkdir(parents=True, exist_ok=True)
    config.paths.embeddings_dir.mkdir(parents=True, exist_ok=True)
    config.paths.models_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "✓ Diretórios prontos | chunks=%s | saída=%s | modelos=%s",
        config.paths.chunks_dir,
        config.paths.embeddings_dir,
        config.paths.models_dir,
    )

    logger.info("Step 2: Carregando modelo e gerando embeddings...")
    embedder = Embedder(config)
    output_path = embedder.run()

    logger.info("%s", "-" * 60)
    logger.info("RESUMO DO EMBEDDING")
    logger.info("%s", "-" * 60)
    logger.info("Modelo: %s", config.model_name)
    logger.info("Cache local: %s", config.model_local_path)
    logger.info("Dimensão dos vetores: %d", embedder.encoder.embedding_dim)
    logger.info("Arquivo gerado: %s", output_path)
    logger.info("%s", "-" * 60)
    logger.info("✓ EMBEDDING CONCLUÍDO")

    return 0


if __name__ == "__main__":
    sys.exit(main())
