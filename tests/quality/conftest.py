"""
Configuração compartilhada para os testes de qualidade do RAG.

Define fixtures e configurações globais usadas pelos módulos de teste.
O conftest é descoberto automaticamente pelo pytest sem necessidade
de importação explícita.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="session", autouse=True)
def print_quality_summary(request):
    """
    Exibe um resumo consolidado das métricas de retrieval ao final
    da execução dos testes.
    """
    yield

    results = getattr(
        request.config,
        "_retrieval_results",
        None,
    )

    if results is None:
        return

    from tests.quality.retrieval_metrics import evaluate_retrieval

    top_k = getattr(
        request.config,
        "_retrieval_top_k",
        5,
    )

    metrics = evaluate_retrieval(
        results,
        top_k,
    )

    print("\n")
    print("=" * 70)
    print("RAG QUALITY SUMMARY")
    print("=" * 70)
    print(f"Document Hit@{top_k}: {metrics.document_precision:.1%}")
    print(f"Keyword Hit@{top_k}:  {metrics.keyword_precision:.1%}")
    print(f"Page Hit@{top_k}:     {metrics.page_precision:.1%}")
    print("=" * 70)