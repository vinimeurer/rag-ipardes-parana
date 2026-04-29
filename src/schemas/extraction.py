"""
Schemas para os dados extraídos dos PDFs.
Usando Pydantic para validação e documentação automática.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PageData(BaseModel):
    """Dados de uma página extraída de um PDF."""
    page: int = Field(..., ge=1, description="Número da página (1-indexed)")
    text: str = Field(..., description="Texto bruto da página")
    document: str = Field(..., description="Identificador do documento")
    has_tables: bool = Field(default=False, description="Se a página contém tabelas")
    extracted_at: str = Field(..., description="Timestamp ISO da extração")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 5,
                "text": "O PIB do Paraná cresceu 2.3% em 2024...",
                "document": "desenvolvimento_paranaense",
                "has_tables": False,
                "extracted_at": "2026-04-29T10:30:00"
            }
        }


class ExtractionResult(BaseModel):
    """Resultado completo da extração de um PDF."""
    success: bool = Field(..., description="Se a extração foi bem-sucedida")
    pdf_key: str = Field(..., description="Identificador do PDF")
    pages_extracted: int = Field(..., ge=0, description="Número de páginas extraídas")
    total_pages: Optional[int] = Field(None, description="Total de páginas do PDF")
    data: List[PageData] = Field(default_factory=list, description="Dados das páginas")
    extraction_time: str = Field(..., description="Timestamp ISO da conclusão")
    error: Optional[str] = Field(None, description="Mensagem de erro (se houver)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "pdf_key": "desenvolvimento_paranaense",
                "pages_extracted": 45,
                "total_pages": 45,
                "data": [],
                "extraction_time": "2026-04-29T10:35:00",
                "error": None
            }
        }
