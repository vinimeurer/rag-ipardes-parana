"""
Script de orquestração para ingestão de PDFs.
Extrai todos os 3 PDFs e valida os resultados.
"""

import sys
from pathlib import Path

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logger import setup_logger, get_timestamped_logfile
from src.core.constants import create_directories, PDF_SOURCES
from src.ingestion.pdf_extractor import PDFExtractor, validate_extraction

logger = setup_logger(__name__, log_file=get_timestamped_logfile("ingest"))


def main():
    """
    Função principal: Extrai todos os PDFs e salva como JSON.
    """
    try:
        # Step 1: Criar diretórios necessários
        logger.info("Step 1: Criando estrutura de diretórios...")
        create_directories()
        logger.info("✓ Diretórios criados com sucesso\n")
        
        # Step 2: Verificar que os PDFs existem
        logger.info("Step 2: Verificando disponibilidade dos PDFs...")
        missing_pdfs = []
        for pdf_key, pdf_info in PDF_SOURCES.items():
            pdf_path = pdf_info["local_path"]
            if pdf_path.exists():
                logger.info(f"✓ Encontrado: {pdf_key}")
            else:
                logger.warning(f"✗ Não encontrado: {pdf_key}")
                logger.warning(f"  Caminho esperado: {pdf_path}")
                logger.warning(f"  URL para download: {pdf_info['url']}")
                missing_pdfs.append(pdf_key)
        
        if missing_pdfs:
            logger.warning(f"\n⚠️  {len(missing_pdfs)} PDF(s) não encontrado(s)")
            logger.warning("Por favor, baixe os PDFs e coloque em data/raw/")
            logger.warning("\nDica: Você pode baixar com wget ou curl:")
            for pdf_key in missing_pdfs:
                pdf_info = PDF_SOURCES[pdf_key]
                logger.warning(f"  wget '{pdf_info['url']}' -O {pdf_info['local_path']}")
            return 1
        
        logger.info("✓ Todos os PDFs encontrados\n")
        
        # Step 3: Extrair PDFs
        logger.info("Step 3: Iniciando extração de PDFs...")
        extractor = PDFExtractor()
        results = extractor.extract_all_pdfs()
        logger.info("✓ Extração concluída\n")
        
        # Step 4: Validar resultados
        logger.info("Step 4: Validando resultados...")
        stats = validate_extraction(results)
        logger.info("✓ Validação concluída\n")
        
        # Step 5: Resumo final
        logger.info("=" * 70)
        logger.info("RESUMO DA INGESTÃO")
        logger.info("=" * 70)
        logger.info(f"Total de PDFs: {stats['total_pdfs']}")
        logger.info(f"Sucesso: {stats['successful']}")
        logger.info(f"Falhas: {stats['failed']}")
        logger.info(f"Total de páginas extraídas: {stats['total_pages']}")
        logger.info("=" * 70)
        
        if stats['failed'] == 0:
            logger.info("✓ INGESTÃO BEM-SUCEDIDA!")
            return 0
        else:
            logger.error("✗ INGESTÃO COM ERROS")
            return 1
    
    except Exception as e:
        logger.error(f"Erro fatal: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
