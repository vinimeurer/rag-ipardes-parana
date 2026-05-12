#!/usr/bin/env python3
"""Script principal para pré-processamento de documentos PDF extraídos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logger import get_timestamped_logfile, setup_logger
from src.core.preprocessing_config import PreprocessingConfig
from src.preprocessing.preprocessor import Preprocessor


def main() -> int:
	"""Execute the preprocessing pipeline for all extracted documents.

	Returns:
		Exit code 0 on success.
	"""
	logger = setup_logger(__name__, log_file=get_timestamped_logfile("preprocess"))
	config = PreprocessingConfig()

	logger.info("%s", "=" * 60)
	logger.info("Iniciando pipeline de pré-processamento")
	logger.info("%s", "=" * 60)

	logger.info("Step 1: Verificando diretórios de entrada e saída...")
	config.paths.extracted_dir.mkdir(parents=True, exist_ok=True)
	config.paths.processed_dir.mkdir(parents=True, exist_ok=True)
	logger.info(
		"✓ Diretórios prontos | entrada=%s | saída=%s",
		config.paths.extracted_dir,
		config.paths.processed_dir,
	)

	logger.info("Step 2: Iniciando processamento dos documentos...")
	preprocessor = Preprocessor(config)
	results = preprocessor.run_all()

	logger.info("Step 3: Processando tabelas dos documentos...")
	table_results = preprocessor.process_tables_for_all()

	logger.info("Step 4: Consolidando resultados...")
	total_original = sum(r.original_chars for r in results)
	total_cleaned = sum(r.cleaned_chars for r in results)
	total_pages = sum(len(r.pages) for r in results)
	total_reduction = 0.0 if total_original == 0 else round((1 - total_cleaned / total_original) * 100, 2)

	for result in results:
		logger.info(
			"✓ %s | páginas=%d | chars=%d→%d (%.1f%% redução)",
			result.pdf_key,
			len(result.pages),
			result.original_chars,
			result.cleaned_chars,
			result.reduction_pct,
		)

	logger.info("%s", "-" * 60)
	logger.info("RESUMO DO PRÉ-PROCESSAMENTO")
	logger.info("%s", "-" * 60)
	logger.info("Total de documentos processados: %d", len(results))
	logger.info("Total de páginas: %d", total_pages)
	logger.info("Caracteres originais: %d", total_original)
	logger.info("Caracteres finais: %d", total_cleaned)
	logger.info("Redução total: %.2f%%", total_reduction)
	logger.info("Documentos com tabelas: %d", table_results["documents_with_tables"])
	logger.info("Total de tabelas processadas: %d", table_results["total_tables"])
	logger.info("%s", "-" * 60)
	logger.info("✓ PRÉ-PROCESSAMENTO CONCLUÍDO")

	return 0


if __name__ == "__main__":
	sys.exit(main())

