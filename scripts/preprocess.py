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

	logger.info("Step 3: Consolidando resultados...")
	total_pages = sum(r.total_pages for r in results)
	total_text_items = sum(r.total_text_items for r in results)
	total_table_items = sum(r.total_table_items for r in results)
	total_items = sum(r.total_items for r in results)

	for result in results:
		logger.info(
			"✓ %s | páginas=%d | itens_texto=%d | tabelas=%d | total=%d",
			result.pdf_key,
			result.total_pages,
			result.total_text_items,
			result.total_table_items,
			result.total_items,
		)

	logger.info("%s", "-" * 60)
	logger.info("RESUMO DO PRÉ-PROCESSAMENTO")
	logger.info("%s", "-" * 60)
	logger.info("Total de documentos: %d", len(results))
	logger.info("Total de páginas: %d", total_pages)
	logger.info("Total de itens texto: %d", total_text_items)
	logger.info("Total de tabelas: %d", total_table_items)
	logger.info("Total de itens: %d", total_items)
	logger.info("%s", "-" * 60)
	logger.info("✓ PRÉ-PROCESSAMENTO CONCLUÍDO")

	return 0


if __name__ == "__main__":
	sys.exit(main())

