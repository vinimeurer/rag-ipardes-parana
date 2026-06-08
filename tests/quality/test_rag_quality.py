"""
Testes de qualidade do pipeline RAG.

Avalia retrieval precision e comportamento fora do escopo sem depender
do Ollama ou de geração de texto — testa apenas o retriever e reranker.

Requer:
- Banco vetorial já indexado em data/vector_db/
- Modelos de embedding e reranking em cache local em models/

Executar com:
    pytest tests/quality/ -v
    pytest tests/quality/ -v --tb=short -s   # para ver métricas impressas
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.quality.ground_truth import OUT_OF_SCOPE_QUERIES, RETRIEVAL_GROUND_TRUTH
from tests.quality.retrieval_metrics import (
    RetrievalResult,
    check_keywords_in_chunks,
    evaluate_retrieval,
)
from src.core.rag_config import RAGConfig, RetrieverConfig
from src.rag.retriever import Retriever


TOP_K_EVAL = 5
MIN_DOCUMENT_PRECISION = 0.75
MIN_KEYWORD_PRECISION = 0.75
MIN_PAGE_PRECISION = 0.50
MAX_SIMILARITY_OUT_OF_SCOPE = 0.35


@pytest.fixture(scope="module")
def retriever():
    """Inicializa o retriever uma única vez para todos os testes do módulo.

    Usa top_k maior que o padrão para garantir que os chunks relevantes
    apareçam nos candidatos antes do threshold de similaridade ser aplicado.
    Isso permite avaliar o retriever de forma mais abrangente.
    """
    config = RAGConfig()
    config.retriever = RetrieverConfig(
        top_k=TOP_K_EVAL,
        reranker_top_k=TOP_K_EVAL,
        min_similarity=0.0,
    )
    return Retriever(config)

@pytest.fixture(scope="module")
def oos_retriever():
    """
    Retriever utilizado para avaliação de similaridade bruta.

    O threshold é zerado para permitir inspeção dos scores
    retornados pelo embedding sem filtragem.
    """
    config = RAGConfig()
    config.retriever = RetrieverConfig(
        top_k=5,
        reranker_top_k=5,
        min_similarity=0.0,
    )
    return Retriever(config)

@pytest.fixture(scope="module")
def retrieval_results(retriever, request):
    """
    Executa todas as queries do ground truth e coleta resultados.
    """
    results = []

    for gt in RETRIEVAL_GROUND_TRUTH:
        chunks = retriever.retrieve(gt["query"])

        retrieved_documents = [c.document for c in chunks]
        retrieved_pages = [c.page for c in chunks]
        retrieved_contents = [c.content for c in chunks]

        hit_doc = gt["document"] in retrieved_documents
        hit_page = gt["expected_page"] in retrieved_pages
        hit_kw = check_keywords_in_chunks(
            gt["keywords"],
            retrieved_contents,
        )

        results.append(
            RetrievalResult(
                query_id=gt["id"],
                query=gt["query"],
                expected_document=gt["document"],
                expected_page=gt["expected_page"],
                keywords=gt["keywords"],
                retrieved_documents=retrieved_documents,
                retrieved_pages=retrieved_pages,
                retrieved_contents=retrieved_contents,
                hit_document=hit_doc,
                hit_page=hit_page,
                hit_keywords=hit_kw,
                top_k=TOP_K_EVAL,
            )
        )

    request.config._retrieval_results = results
    request.config._retrieval_top_k = TOP_K_EVAL

    return results


class TestRetrievalPrecision:
    """Testes de precisão do retrieval para queries com resposta conhecida."""

    def test_document_precision_above_threshold(self, retrieval_results):
        """Document Hit@K deve ser maior ou igual ao threshold mínimo configurado.

        Mede se o retriever consegue identificar o documento correto entre
        os top-K resultados. Um valor baixo indica que o embedder ou o
        banco vetorial não estão funcionando adequadamente.
        """
        metrics = evaluate_retrieval(retrieval_results, TOP_K_EVAL)
        print(f"\n{metrics}")
        assert metrics.document_precision >= MIN_DOCUMENT_PRECISION, (
            f"Document precision ({metrics.document_precision:.1%}) abaixo do mínimo "
            f"({MIN_DOCUMENT_PRECISION:.1%}). Verifique o modelo de embedding e o índice."
        )

    def test_keyword_precision_above_threshold(self, retrieval_results):
        """Keyword Hit@K deve ser maior ou igual ao threshold mínimo configurado.

        Mede se o conteúdo relevante com as palavras-chave da resposta
        aparece nos chunks recuperados. É a métrica mais diretamente
        relacionada à qualidade da resposta final do RAG.
        """
        metrics = evaluate_retrieval(retrieval_results, TOP_K_EVAL)
        assert metrics.keyword_precision >= MIN_KEYWORD_PRECISION, (
            f"Keyword precision ({metrics.keyword_precision:.1%}) abaixo do mínimo "
            f"({MIN_KEYWORD_PRECISION:.1%}). Os chunks com a resposta correta não estão "
            "sendo recuperados — verifique o chunking e o enriquecimento do embedding."
        )

    def test_page_precision_above_threshold(self, retrieval_results):
        """Page Hit@K deve ser maior ou igual ao threshold mínimo configurado.

        Mede se a página correta aparece nos resultados, validando a
        rastreabilidade das citações. Threshold menor que document precision
        pois a mesma informação pode aparecer em páginas adjacentes.
        """
        metrics = evaluate_retrieval(retrieval_results, TOP_K_EVAL)
        assert metrics.page_precision >= MIN_PAGE_PRECISION, (
            f"Page precision ({metrics.page_precision:.1%}) abaixo do mínimo "
            f"({MIN_PAGE_PRECISION:.1%})."
        )

    @pytest.mark.parametrize("gt", RETRIEVAL_GROUND_TRUTH, ids=[g["id"] for g in RETRIEVAL_GROUND_TRUTH])
    def test_individual_keyword_hit(self, retriever, gt):
        """Cada query individualmente deve recuperar chunks com as keywords esperadas.

        Testa cada par (query, resposta esperada) do ground truth
        isoladamente para identificar quais queries específicas estão
        falhando, facilitando diagnóstico de problemas pontuais.
        """
        chunks = retriever.retrieve(gt["query"])
        contents = [c.content for c in chunks]
        hit = check_keywords_in_chunks(gt["keywords"], contents)

        assert hit, (
            f"[{gt['id']}] Keywords {gt['keywords']} não encontradas nos chunks "
            f"recuperados para: '{gt['query']}'\n"
            f"Chunks recuperados: {[c[:80] for c in contents]}"
        )

    @pytest.mark.parametrize("gt", RETRIEVAL_GROUND_TRUTH, ids=[g["id"] for g in RETRIEVAL_GROUND_TRUTH])
    def test_individual_document_hit(self, retriever, gt):
        """Cada query individualmente deve recuperar chunks do documento esperado.

        Valida que o documento de origem correto aparece entre os resultados,
        garantindo que o sistema não está confundindo informações entre documentos.
        """
        chunks = retriever.retrieve(gt["query"])
        retrieved_docs = [c.document for c in chunks]

        assert gt["document"] in retrieved_docs, (
            f"[{gt['id']}] Documento '{gt['document']}' não encontrado nos resultados "
            f"para: '{gt['query']}'\n"
            f"Documentos recuperados: {retrieved_docs}"
        )


class TestOutOfScope:
    """Testes de comportamento para queries fora do escopo dos documentos."""

    @pytest.mark.parametrize(
        "oos", OUT_OF_SCOPE_QUERIES, ids=[q["id"] for q in OUT_OF_SCOPE_QUERIES]
    )
    def test_out_of_scope_below_similarity_threshold(self, oos_retriever, oos):
        """Queries fora do escopo devem ter similaridade abaixo do threshold.

        Usa um retriever com threshold zero para verificar a similaridade
        bruta dos resultados. Se todos os chunks estão abaixo de
        MAX_SIMILARITY_OUT_OF_SCOPE, o pipeline vai recusar responder
        corretamente em produção com o threshold padrão de 0.35.

        Este teste é a garantia técnica do comportamento de recusa do RAG:
        não depende do LLM ignorar a instrução, mas sim de os embeddings
        genuinamente não encontrarem similaridade com o conteúdo dos PDFs.
        """
        config = RAGConfig()
        config.retriever = RetrieverConfig(
            top_k=5,
            reranker_top_k=5,
            min_similarity=0.0,
        )

        chunks = oos_retriever.retrieve(oos["query"])

        if not chunks:
            return

        max_similarity = max(c.similarity for c in chunks)
        assert max_similarity < MAX_SIMILARITY_OUT_OF_SCOPE, (
            f"[{oos['id']}] Query fora do escopo retornou similaridade alta "
            f"({max_similarity:.4f} >= {MAX_SIMILARITY_OUT_OF_SCOPE}): "
            f"'{oos['query']}'\n"
            f"Razão: {oos['reason']}\n"
            f"Chunk mais similar: {chunks[0].content[:100]}"
        )

    def test_all_out_of_scope_below_threshold(self, retriever):
        """Todas as queries fora do escopo devem ser recusadas pelo threshold padrão.

        Verifica que o retriever com threshold padrão (0.35) retorna lista
        vazia para todas as queries out-of-scope, garantindo que o pipeline
        vai acionar o comportamento de recusa em produção.
        """
        config = RAGConfig()
        config.retriever = RetrieverConfig(
            top_k=5,
            reranker_top_k=5,
            min_similarity=MAX_SIMILARITY_OUT_OF_SCOPE,
        )
        threshold_retriever = Retriever(config)

        failures = []
        for oos in OUT_OF_SCOPE_QUERIES:
            chunks = threshold_retriever.retrieve(oos["query"])
            if chunks:
                max_sim = max(c.similarity for c in chunks)
                failures.append(f"  [{oos['id']}] sim={max_sim:.4f}: {oos['query']}")

        assert not failures, (
            f"As seguintes queries out-of-scope passaram pelo threshold {MAX_SIMILARITY_OUT_OF_SCOPE}:\n"
            + "\n".join(failures)
        )


class TestRetrievalConsistency:
    """Testes de consistência e estabilidade do retrieval."""

    def test_retriever_returns_nonempty_for_in_scope_queries(self, retriever):
        """O retriever deve retornar chunks para todas as queries dentro do escopo.

        Verifica que nenhuma query com resposta conhecida nos documentos
        retorna lista vazia, o que indicaria problema no índice ou no modelo.
        """
        empty_results = []
        for gt in RETRIEVAL_GROUND_TRUTH:
            chunks = retriever.retrieve(gt["query"])
            if not chunks:
                empty_results.append(gt["id"])

        assert not empty_results, (
            f"Retriever retornou lista vazia para queries in-scope: {empty_results}. "
            "Verifique se o banco vetorial está indexado corretamente."
        )

    def test_retrieved_chunks_have_required_metadata(self, retriever):
        """Todos os chunks recuperados devem conter os campos de metadados obrigatórios.

        Garante que document, page e sections estão sempre presentes,
        pois são necessários para montar a citação de fonte na resposta.
        """
        gt = RETRIEVAL_GROUND_TRUTH[0]
        chunks = retriever.retrieve(gt["query"])

        for chunk in chunks:
            assert chunk.document, f"chunk_id={chunk.chunk_id} sem campo 'document'"
            assert chunk.page > 0, f"chunk_id={chunk.chunk_id} com page inválida: {chunk.page}"
            assert isinstance(chunk.sections, list), (
                f"chunk_id={chunk.chunk_id} com sections inválido: {chunk.sections}"
            )

    def test_retrieval_is_deterministic(self, retriever):
        """Duas chamadas com a mesma query devem retornar os mesmos chunk_ids.

        Verifica estabilidade do retriever — resultados não devem variar
        entre execuções com a mesma entrada, o que indicaria problema
        no índice vetorial ou na serialização dos embeddings.
        """
        gt = RETRIEVAL_GROUND_TRUTH[0]
        chunks_first = retriever.retrieve(gt["query"])
        chunks_second = retriever.retrieve(gt["query"])

        ids_first = [c.chunk_id for c in chunks_first]
        ids_second = [c.chunk_id for c in chunks_second]

        assert ids_first == ids_second, (
            f"Retrieval não é determinístico para '{gt['query']}': "
            f"\n  1ª chamada: {ids_first}"
            f"\n  2ª chamada: {ids_second}"
        )

    def test_analise_conjuntural_retrievable(self, retriever):
        """Deve ser possível recuperar chunks do documento analise_conjuntural.

        Testa especificamente o documento sem hierarquia de seções, que usa
        fallback de página. Garante que o tratamento especial deste documento
        não degradou a qualidade do embedding ou da indexação.
        """
        ac_queries = [gt for gt in RETRIEVAL_GROUND_TRUTH if gt["document"] == "analise_conjuntural"]
        hits = 0
        for gt in ac_queries:
            chunks = retriever.retrieve(gt["query"])
            docs = [c.document for c in chunks]
            if "analise_conjuntural" in docs:
                hits += 1

        precision = hits / len(ac_queries) if ac_queries else 0
        assert precision >= 0.66, (
            f"Document precision para analise_conjuntural ({precision:.1%}) abaixo de 66%. "
            "O documento sem hierarquia de seções pode estar sendo prejudicado na indexação."
        )
