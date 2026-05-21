"""
Divisão de PDFs em batches para processamento memory-efficient.

Implementa estratégia de split-process-merge para evitar sobrecarga
de memória ao converter PDFs grandes com Docling.
"""
import tempfile
from pathlib import Path
from typing import List, Tuple

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    raise ImportError(
        "PyPDF2 é necessário para o splitting de PDFs. "
        "Instale com: pip install PyPDF2"
    )

from ..core.logger import setup_logger

logger = setup_logger(__name__)


def split_pdf(input_path: Path, batch_size: int) -> List[Tuple[Path, int]]:
    """
    Divide um PDF em arquivos temporários com páginas em batches.

    Args:
        input_path: Caminho do PDF de entrada.
        batch_size: Quantidade de páginas por batch.

    Returns:
        Lista de tuplas (temp_path, page_offset) onde cada tupla representa
        um batch. page_offset é o número da primeira página do batch no PDF original.

    Raises:
        FileNotFoundError: Se o PDF não existir.
        ValueError: Se batch_size <= 0.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {input_path}")

    if batch_size <= 0:
        raise ValueError(f"batch_size deve ser > 0, recebido: {batch_size}")

    reader = PdfReader(str(input_path))
    total_pages = len(reader.pages)

    if total_pages == 0:
        raise ValueError(f"PDF vazio: {input_path}")

    splits: List[Tuple[Path, int]] = []

    for batch_idx in range(0, total_pages, batch_size):
        start_page = batch_idx
        end_page = min(batch_idx + batch_size, total_pages)
        offset = start_page

        writer = PdfWriter()

        for page_idx in range(start_page, end_page):
            writer.add_page(reader.pages[page_idx])

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False, prefix=f"batch_{batch_idx}_"
        )
        temp_path = Path(temp_file.name)
        temp_file.close()

        with open(temp_path, "wb") as f:
            writer.write(f)

        logger.debug(
            "Split criado: %s (páginas %d-%d, offset=%d)",
            temp_path.name,
            start_page + 1,
            end_page,
            offset,
        )

        splits.append((temp_path, offset))

    logger.info(
        "PDF dividido em %d batches (%d páginas, batch_size=%d)",
        len(splits),
        total_pages,
        batch_size,
    )

    return splits


def cleanup_splits(splits: List[Tuple[Path, int]]) -> None:
    """
    Remove arquivos temporários de splits.

    Args:
        splits: Lista de tuplas (temp_path, page_offset) retornadas por split_pdf.
    """
    for temp_path, _ in splits:
        try:
            temp_path.unlink()
            logger.debug("Arquivo temporário removido: %s", temp_path.name)
        except Exception as e:
            logger.warning("Erro ao remover arquivo temporário %s: %s", temp_path.name, e)
