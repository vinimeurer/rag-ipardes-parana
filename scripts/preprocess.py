#!/usr/bin/env python3
"""Script principal para pré-processamento de documentos PDF extraídos."""

import sys
from pathlib import Path

# Adicionar src ao path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing.pipeline import PreprocessingPipeline
from src.core.logger import setup_logger
from src.core.constants import EXTRACTED_DATA_DIR, PROCESSED_DATA_DIR

logger = setup_logger(__name__)


def main():
    """Executa o pipeline de pré-processamento."""
    
    # Definir caminhos
    extracted_dir = EXTRACTED_DATA_DIR
    processed_dir = PROCESSED_DATA_DIR
    
    # Arquivos de entrada esperados
    input_files = [
        extracted_dir / "analise_conjuntural.json",
        extracted_dir / "avaliacoes_politicas.json",
        extracted_dir / "desenvolvimento_paranaense.json",
    ]
    
    # Verificar que arquivos existem
    missing = [f for f in input_files if not f.exists()]
    if missing:
        logger.error(f"Arquivos não encontrados: {missing}")
        return 1
    
    logger.info(f"Iniciando pré-processamento...")
    logger.info(f"Arquivos de entrada: {[f.name for f in input_files]}")
    
    # Inicializar pipeline
    pipeline = PreprocessingPipeline(output_dir=processed_dir)
    
    # Executar processamento
    result = pipeline.process(input_files)
    
    # Salvar resultados
    output_file, reports_file = pipeline.save_processed(result, base_name="all_documents")
    
    # Imprimir sumário
    stats = result["statistics"]
    print("\n" + "="*60)
    print("RESUMO DO PROCESSAMENTO")
    print("="*60)
    print(f"Total de páginas: {stats['total_pages']}")
    print(f"Total de caracteres: {stats['total_characters']:,}")
    print(f"Média de caracteres por página: {stats['avg_characters_per_page']}")
    print(f"Documentos processados: {stats['num_documents']}")
    print(f"Seções identificadas: {stats['num_sections']}")
    print("="*60)
    
    logger.info("Pré-processamento concluído com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
