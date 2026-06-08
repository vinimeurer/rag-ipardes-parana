"""
Métricas de qualidade para avaliação do pipeline de retrieval RAG.

Implementa Precision@K, Hit@K e métricas de cobertura de documento,
calculadas sobre o ground truth definido em ground_truth.py.
"""

from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """Resultado de avaliação para uma única query.

    Attributes:
        query_id: Identificador da query no ground truth.
        query: Texto da pergunta.
        expected_document: Documento esperado pelo ground truth.
        expected_page: Página esperada pelo ground truth.
        keywords: Palavras-chave que devem aparecer nos chunks recuperados.
        retrieved_documents: Lista de documentos dos chunks recuperados.
        retrieved_pages: Lista de páginas dos chunks recuperados.
        retrieved_contents: Lista de conteúdos dos chunks recuperados.
        hit_document: True se o documento esperado apareceu nos resultados.
        hit_page: True se a página esperada apareceu nos resultados.
        hit_keywords: True se alguma keyword apareceu em algum chunk.
        top_k: Número de chunks avaliados.
    """

    query_id: str
    query: str
    expected_document: str
    expected_page: int
    keywords: list[str]
    retrieved_documents: list[str]
    retrieved_pages: list[int]
    retrieved_contents: list[str]
    hit_document: bool
    hit_page: bool
    hit_keywords: bool
    top_k: int


@dataclass
class RetrievalMetrics:
    """Métricas agregadas de qualidade do retrieval.

    Attributes:
        total_queries: Total de queries avaliadas.
        document_precision: Proporção de queries onde o documento correto foi recuperado.
        page_precision: Proporção de queries onde a página correta foi recuperada.
        keyword_precision: Proporção de queries onde keywords foram encontradas nos chunks.
        top_k: Valor de K usado na avaliação.
    """

    total_queries: int
    document_precision: float
    page_precision: float
    keyword_precision: float
    top_k: int

    def __str__(self) -> str:
        """Formata as métricas para exibição legível."""
        return (
            f"Retrieval Quality Metrics (top-{self.top_k})\n"
            f"  Total queries    : {self.total_queries}\n"
            f"  Document Hit@{self.top_k}  : {self.document_precision:.1%}\n"
            f"  Page Hit@{self.top_k}      : {self.page_precision:.1%}\n"
            f"  Keyword Hit@{self.top_k}   : {self.keyword_precision:.1%}"
        )


def evaluate_retrieval(
    results: list[RetrievalResult],
    top_k: int,
) -> RetrievalMetrics:
    """Calcula métricas agregadas a partir de uma lista de resultados.

    Args:
        results: Lista de RetrievalResult, um por query avaliada.
        top_k: Valor de K usado na recuperação.

    Returns:
        RetrievalMetrics com as métricas agregadas.
    """
    if not results:
        return RetrievalMetrics(
            total_queries=0,
            document_precision=0.0,
            page_precision=0.0,
            keyword_precision=0.0,
            top_k=top_k,
        )

    n = len(results)
    doc_hits = sum(1 for r in results if r.hit_document)
    page_hits = sum(1 for r in results if r.hit_page)
    kw_hits = sum(1 for r in results if r.hit_keywords)

    return RetrievalMetrics(
        total_queries=n,
        document_precision=doc_hits / n,
        page_precision=page_hits / n,
        keyword_precision=kw_hits / n,
        top_k=top_k,
    )


def check_keywords_in_chunks(
    keywords: list[str],
    contents: list[str],
) -> bool:
    """Verifica se alguma keyword aparece em algum chunk recuperado.

    A verificação é case-insensitive e busca por substring, permitindo
    que variações de formatação numérica (ex: '3.857' e '3857') sejam
    detectadas mesmo com pequenas diferenças tipográficas.

    Args:
        keywords: Lista de palavras-chave esperadas.
        contents: Lista de conteúdos dos chunks recuperados.

    Returns:
        True se ao menos uma keyword foi encontrada em ao menos um chunk.
    """
    combined = " ".join(contents).lower()
    return any(kw.lower() in combined for kw in keywords)
