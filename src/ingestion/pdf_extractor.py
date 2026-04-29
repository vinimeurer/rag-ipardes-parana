"""
Extrator de PDFs para o projeto RAG.
Responsável por ler os 3 PDFs do IPARDES e extrair texto com metadados.
"""

import json
import pdfplumber
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from src.core.logger import setup_logger
from src.core.exceptions import PDFExtractionError
from src.core.constants import PDF_SOURCES, EXTRACTED_DATA_DIR, PDF_EXTRACTOR_MAX_PAGES

logger = setup_logger(__name__)


class PDFExtractor:
    """
    Extrai texto de PDFs e salva como JSON com metadados.
    
    Cada página de cada PDF é processada e salva com:
    - Texto bruto da página
    - Número da página
    - Nome do documento
    - Timestamp de extração
    
    Example:
        ```python
        extractor = PDFExtractor()
        results = extractor.extract_all_pdfs()
        # Salva automaticamente em data/extracted/
        ```
    """
    
    def __init__(self):
        """Inicializa o extrator."""
        self.extracted_dir = EXTRACTED_DATA_DIR
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_pdf(self, pdf_key: str, pdf_path: Path) -> Dict:
        """
        Extrai texto de um único PDF.
        
        Args:
            pdf_key: Identificador do PDF (ex: "desenvolvimento_paranaense")
            pdf_path: Caminho completo para o PDF
            
        Returns:
            Dicionário com metadados da extração
            
        Raises:
            PDFExtractionError: Se falhar na extração
        """
        logger.info(f"Iniciando extração: {pdf_key}")
        logger.info(f"Caminho: {pdf_path}")
        
        if not pdf_path.exists():
            raise PDFExtractionError(f"PDF não encontrado: {pdf_path}")
        
        try:
            pages_extracted = 0
            extracted_text = []
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                max_pages = PDF_EXTRACTOR_MAX_PAGES or total_pages
                
                logger.info(f"Total de páginas: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages[:max_pages], 1):
                    try:
                        # Extrair texto
                        text = page.extract_text()
                        
                        # Extrair tabelas (se houver)
                        tables = page.extract_tables()
                        
                        # Combinar tabelas em texto
                        if tables:
                            tables_text = self._convert_tables_to_text(tables)
                            text = f"{text}\n\n[TABELAS]\n{tables_text}"
                        
                        page_data = {
                            "page": page_num,
                            "text": text,
                            "document": pdf_key,
                            "has_tables": bool(tables),
                            "extracted_at": datetime.now().isoformat()
                        }
                        
                        extracted_text.append(page_data)
                        pages_extracted += 1
                        
                        if page_num % 5 == 0:
                            logger.debug(f"  Processadas {page_num}/{min(max_pages, total_pages)} páginas")
                    
                    except Exception as e:
                        logger.warning(f"Erro ao extrair página {page_num}: {str(e)}")
                        continue
            
            logger.info(f"✓ Extração concluída: {pages_extracted} páginas extraídas")
            
            return {
                "success": True,
                "pdf_key": pdf_key,
                "pages_extracted": pages_extracted,
                "total_pages": total_pages,
                "data": extracted_text,
                "extraction_time": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"✗ Erro na extração do PDF: {str(e)}")
            raise PDFExtractionError(f"Falha ao extrair {pdf_key}: {str(e)}")
    
    def save_extracted_json(self, extraction_result: Dict, pdf_key: str) -> Path:
        """
        Salva resultado da extração como JSON.
        
        Args:
            extraction_result: Resultado retornado por extract_pdf()
            pdf_key: Identificador do PDF
            
        Returns:
            Caminho para o arquivo salvo
        """
        output_file = self.extracted_dir / f"{pdf_key}.json"
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(extraction_result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Salvo: {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Erro ao salvar JSON: {str(e)}")
            raise PDFExtractionError(f"Falha ao salvar {output_file}: {str(e)}")
    
    def extract_all_pdfs(self) -> Dict[str, Dict]:
        """
        Extrai todos os 3 PDFs do IPARDES.
        
        Returns:
            Dicionário com resultados de cada PDF
        """
        logger.info("=" * 70)
        logger.info("INICIANDO EXTRAÇÃO DE TODOS OS PDFs")
        logger.info("=" * 70)
        
        results = {}
        
        for pdf_key, pdf_info in PDF_SOURCES.items():
            pdf_path = pdf_info["local_path"]
            
            try:
                extraction_result = self.extract_pdf(pdf_key, pdf_path)
                self.save_extracted_json(extraction_result, pdf_key)
                results[pdf_key] = extraction_result
            
            except PDFExtractionError as e:
                logger.error(f"Falha na extração de {pdf_key}: {str(e)}")
                results[pdf_key] = {
                    "success": False,
                    "error": str(e)
                }
        
        logger.info("=" * 70)
        logger.info("EXTRAÇÃO CONCLUÍDA")
        logger.info("=" * 70)
        
        return results
    
    @staticmethod
    def _convert_tables_to_text(tables: List) -> str:
        """
        Converte tabelas extraídas em texto markdown-like.
        
        Args:
            tables: Lista de tabelas do pdfplumber
            
        Returns:
            Texto formatado das tabelas
        """
        result = []
        
        for table_idx, table in enumerate(tables):
            result.append(f"\nTabela {table_idx + 1}:")
            result.append("-" * 40)
            
            # Converter cada linha da tabela
            for row in table:
                row_text = " | ".join(str(cell) if cell else "" for cell in row)
                result.append(row_text)
        
        return "\n".join(result)


def validate_extraction(results: Dict) -> Dict:
    """
    Valida os resultados da extração.
    
    Args:
        results: Dicionário retornado por extract_all_pdfs()
        
    Returns:
        Dicionário com estatísticas de validação
    """
    logger.info("Validando extração...")
    
    stats = {
        "total_pdfs": len(results),
        "successful": 0,
        "failed": 0,
        "total_pages": 0,
        "details": {}
    }
    
    for pdf_key, result in results.items():
        if result.get("success"):
            stats["successful"] += 1
            stats["total_pages"] += result.get("pages_extracted", 0)
            stats["details"][pdf_key] = {
                "pages": result.get("pages_extracted"),
                "status": "✓ OK"
            }
            logger.info(f"✓ {pdf_key}: {result.get('pages_extracted')} páginas")
        else:
            stats["failed"] += 1
            stats["details"][pdf_key] = {
                "error": result.get("error"),
                "status": "✗ ERRO"
            }
            logger.warning(f"✗ {pdf_key}: {result.get('error')}")
    
    logger.info(f"\nResumo:")
    logger.info(f"  Sucesso: {stats['successful']}/{stats['total_pdfs']}")
    logger.info(f"  Total de páginas extraídas: {stats['total_pages']}")
    
    return stats
