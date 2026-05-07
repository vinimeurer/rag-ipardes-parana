"""
Script de orquestração para ingestão estrutural de PDFs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.constants import PDF_SOURCES, create_directories
from src.core.logger import get_timestamped_logfile, setup_logger
from src.ingestion.pdf_extractor import (
    PDFLayoutExtractor,
    validate_extraction,
)

logger = setup_logger(
    __name__,
    log_file=get_timestamped_logfile("ingest"),
)


def validate_structural_output(results: dict) -> dict:
    """
    Valida estrutura extraída dos PDFs.

    Args:
        results: Resultados da extração.

    Returns:
        Estatísticas estruturais.
    """
    stats = {
        "documents": {},
        "total_blocks": 0,
        "total_tables": 0,
    }

    for pdf_key, result in results.items():
        if not result.get("success"):
            continue

        pages = result.get("data", [])

        total_blocks = sum(
            len(page.get("blocks", []))
            for page in pages
        )

        total_tables = sum(
            len(page.get("tables", []))
            for page in pages
        )

        stats["documents"][pdf_key] = {
            "blocks": total_blocks,
            "tables": total_tables,
            "pages": len(pages),
        }

        stats["total_blocks"] += total_blocks
        stats["total_tables"] += total_tables

        logger.info(
            "✓ %s | páginas=%s | blocos=%s | tabelas=%s",
            pdf_key,
            len(pages),
            total_blocks,
            total_tables,
        )

    return stats


def check_pdf_availability() -> list[str]:
    """
    Verifica disponibilidade dos PDFs.

    Returns:
        Lista de PDFs ausentes.
    """
    logger.info("Step 2: Verificando disponibilidade dos PDFs...")

    missing_pdfs = []

    for pdf_key, pdf_info in PDF_SOURCES.items():
        pdf_path = pdf_info["local_path"]

        if pdf_path.exists():
            logger.info("✓ Encontrado: %s", pdf_key)
        else:
            logger.warning("✗ Não encontrado: %s", pdf_key)
            logger.warning("  Caminho esperado: %s", pdf_path)
            logger.warning("  URL para download: %s", pdf_info["url"])

            missing_pdfs.append(pdf_key)

    return missing_pdfs


def log_missing_pdfs(missing_pdfs: list[str]) -> None:
    """
    Exibe instruções para PDFs ausentes.

    Args:
        missing_pdfs: Lista de PDFs não encontrados.
    """
    logger.warning(
        "\n⚠️ %s PDF(s) não encontrado(s)",
        len(missing_pdfs),
    )

    logger.warning(
        "Por favor, baixe os PDFs e coloque em data/raw/"
    )

    logger.warning("\nDica: Você pode baixar com wget:")

    for pdf_key in missing_pdfs:
        pdf_info = PDF_SOURCES[pdf_key]

        logger.warning(
            "wget '%s' -O %s",
            pdf_info["url"],
            pdf_info["local_path"],
        )


def run_extraction() -> dict:
    """
    Executa extração estrutural dos PDFs.

    Returns:
        Resultados da extração.
    """
    logger.info("Step 3: Iniciando extração estrutural...")

    extractor = PDFLayoutExtractor()

    results = extractor.extract_all_pdfs()

    logger.info("✓ Extração concluída\n")

    return results


def log_final_summary(
    extraction_stats: dict,
    structural_stats: dict,
) -> None:
    """
    Exibe resumo final da ingestão.

    Args:
        extraction_stats: Estatísticas da extração.
        structural_stats: Estatísticas estruturais.
    """
    logger.info("=" * 70)
    logger.info("RESUMO DA INGESTÃO")
    logger.info("=" * 70)

    logger.info(
        "Total de PDFs: %s",
        extraction_stats["total_pdfs"],
    )

    logger.info(
        "Sucesso: %s",
        extraction_stats["successful"],
    )

    logger.info(
        "Falhas: %s",
        extraction_stats["failed"],
    )

    logger.info(
        "Total de páginas: %s",
        extraction_stats["total_pages"],
    )

    logger.info(
        "Total de blocos: %s",
        structural_stats["total_blocks"],
    )

    logger.info(
        "Total de tabelas: %s",
        structural_stats["total_tables"],
    )

    logger.info("=" * 70)


def main() -> int:
    """
    Executa pipeline completo de ingestão.

    Returns:
        Código de saída.
    """
    try:
        logger.info("Step 1: Criando estrutura de diretórios...")

        create_directories()

        logger.info("✓ Diretórios criados com sucesso\n")

        missing_pdfs = check_pdf_availability()

        if missing_pdfs:
            log_missing_pdfs(missing_pdfs)
            return 1

        logger.info("✓ Todos os PDFs encontrados\n")

        results = run_extraction()

        logger.info("Step 4: Validando resultados...")

        extraction_stats = validate_extraction(results)

        structural_stats = validate_structural_output(results)

        logger.info("✓ Validação concluída\n")

        log_final_summary(
            extraction_stats=extraction_stats,
            structural_stats=structural_stats,
        )

        if extraction_stats["failed"] == 0:
            logger.info("✓ INGESTÃO BEM-SUCEDIDA!")
            return 0

        logger.error("✗ INGESTÃO COM ERROS")

        return 1

    except Exception as exc:
        logger.error(
            "Erro fatal: %s",
            str(exc),
            exc_info=True,
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())