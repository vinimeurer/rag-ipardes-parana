"""
Ground truth para testes de qualidade do pipeline RAG.

Cada entrada define uma pergunta, a resposta esperada, o documento de origem
e a página onde a informação se encontra. Usado para calcular métricas de
retrieval precision e validar comportamento fora do escopo.
"""

RETRIEVAL_GROUND_TRUTH = [
    ###############################################
    # DOCUMENTO: Análise Conjuntural
    ###############################################
    {
        "id": "ac_001",
        "query": "Qual foi o rendimento médio mensal dos trabalhadores no Paraná em 2025?",
        "expected_answer": "R$ 3.857,00",
        "document": "analise_conjuntural",
        "expected_page": 12,
        "keywords": ["3.857", "rendimento", "mensal"],
    },
    {
        "id": "ac_002",
        "query": "Qual setor concentra a maior parte dos ocupados no Paraná?",
        "expected_answer": "Serviços (67,8%)",
        "document": "analise_conjuntural",
        "expected_page": 12,
        "keywords": ["serviços", "67,8"],
    },
    {
        "id": "ac_003",
        "query": "Qual foi a taxa de ocupação no Paraná no 2º trimestre de 2025?",
        "expected_answer": "96,2%",
        "document": "analise_conjuntural",
        "expected_page": 12,
        "keywords": ["96,2", "ocupação"],
    },
    ###############################################
    # DOCUMENTO: Avaliações de Políticas Públicas
    ###############################################
    {
        "id": "ap_001",
        "query": "Qual é o principal objetivo de uma revisão de escopo de literatura?",
        "expected_answer": "Mapear uma área do conhecimento, compreender práticas de pesquisa e fornecer panorama geral",
        "document": "avaliacoes_politicas",
        "expected_page": 5,
        "keywords": ["mapear", "área", "conhecimento"],
    },
    {
        "id": "ap_002",
        "query": "Qual o período temporal analisado pelas avaliações de políticas públicas no estudo?",
        "expected_answer": "Entre 2014 e 2024",
        "document": "avaliacoes_politicas",
        "expected_page": 5,
        "keywords": ["2014", "2024"],
    },
    {
        "id": "ap_003",
        "query": "Qual software foi utilizado para análise qualitativa dos documentos de políticas públicas?",
        "expected_answer": "Atlas.ti",
        "document": "avaliacoes_politicas",
        "expected_page": 6,
        "keywords": ["Atlas.ti", "Atlas"],
    },
    {
        "id": "ap_004",
        "query": "Qual protocolo foi utilizado para estruturar o relatório de revisão de políticas públicas?",
        "expected_answer": "PRISMA ScR",
        "document": "avaliacoes_politicas",
        "expected_page": 7,
        "keywords": ["PRISMA", "scoping"],
    },
    {
        "id": "ap_005",
        "query": "Quantos documentos e avaliações compuseram o corpus final da revisão de políticas públicas?",
        "expected_answer": "81 documentos e 83 avaliações",
        "document": "avaliacoes_politicas",
        "expected_page": 20,
        "keywords": ["81", "83", "avaliações"],
    },
]

OUT_OF_SCOPE_QUERIES = [
    {
        "id": "oos_001",
        "query": "Qual é a capital da França?",
        "reason": "Pergunta geográfica sem relação com os documentos IPARDES",
    },
    {
        "id": "oos_002",
        "query": "Quem ganhou a Copa do Mundo de 2022?",
        "reason": "Evento esportivo não coberto pelos documentos",
    },
    {
        "id": "oos_003",
        "query": "Qual é a fórmula química da água?",
        "reason": "Conteúdo científico não presente nos documentos",
    },
    {
        "id": "oos_004",
        "query": "Como funciona a inteligência artificial?",
        "reason": "Tema tecnológico não abordado nos documentos IPARDES",
    },
    {
        "id": "oos_005",
        "query": "Qual é a população do Japão em 2025?",
        "reason": "Dados demográficos internacionais fora do escopo",
    },
]
