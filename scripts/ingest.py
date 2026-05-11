"""
Script principal de ingestão de PDFs.

Ponto de entrada para executar o pipeline completo de extração,
limpeza e serialização dos PDFs do projeto RAG IPARDES.

Uso:
    python -m scripts.ingest
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logger import setup_logger
from src.ingestion import IngestionPipeline


def main() -> int:
    """
    Executa o pipeline completo de ingestão para todos os PDFs configurados.

    Processa sequencialmente todos os documentos definidos em PDF_SOURCES,
    aplicando extração via Docling, limpeza de texto e serialização dos
    artefatos em data/extracted/. PDFs já extraídos são pulados
    automaticamente.

    Returns:
        Código de saída: 0 se todos os documentos foram processados com
        sucesso, 1 se houve falha em ao menos um documento.
    """
    logger = setup_logger("scripts.ingest")

    logger.info("=" * 60)
    logger.info("Iniciando pipeline de ingestão RAG IPARDES")
    logger.info("=" * 60)

    pipeline = IngestionPipeline()
    run_result = pipeline.run()

    logger.info("-" * 60)
    for doc in run_result.documents:
        status = "SKIP" if doc.skipped else ("OK" if doc.success else "FAIL")
        if doc.success and not doc.skipped and doc.cleaning_stats_text:
            st = doc.cleaning_stats_text
            logger.info(
                "[%s] %s | %d→%d chars (%.1f%% redução) | artefatos: %s",
                status,
                doc.pdf_key,
                st.original_chars,
                st.cleaned_chars,
                st.reduction_pct,
                list(doc.saved_artifacts.keys()),
            )
        elif doc.skipped:
            logger.info("[%s] %s", status, doc.pdf_key)
        else:
            logger.error("[%s] %s — %s", status, doc.pdf_key, doc.error)

    logger.info("-" * 60)
    logger.info(run_result.summary())

    return 0 if run_result.failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())