"""
Módulo de ingestão de PDFs para o pipeline RAG IPARDES.

Exporta as classes principais para uso externo.
"""
from .ingestion_pipeline import IngestionPipeline, PipelineDocumentResult, PipelineRunResult
from .pdf_extractor import DoclingPDFExtractor, ExtractedPage, ExtractionResult
from .serializer import ExtractionSerializer
from .table_extractor import ExtractedTable, TableExtractionResult, TableExtractor

__all__ = [
    "IngestionPipeline",
    "PipelineRunResult",
    "PipelineDocumentResult",
    "DoclingPDFExtractor",
    "ExtractionResult",
    "ExtractedPage",
    "ExtractionSerializer",
    "TableExtractor",
    "TableExtractionResult",
    "ExtractedTable",
]
