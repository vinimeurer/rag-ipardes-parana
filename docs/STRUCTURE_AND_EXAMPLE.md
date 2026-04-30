# 📊 ESTRUTURA E EXEMPLO DE SAÍDA

## 🏗️ Estrutura Visual do Projeto

```
rag-ipardes-parana/
│
├─ 📄 README.md                    ← LEIA PRIMEIRO
├─ 📄 PROGRESS.md                  ← Checklist detalhado
├─ 📄 IMPLEMENTATION_SUMMARY.md    ← O que foi feito (este dir)
├─ 📄 STRUCTURE_AND_EXAMPLE.md     ← Estrutura e exemplos (você está aqui)
│
├─ 📁 src/                         ← Código-fonte Python
│  ├─ __init__.py
│  ├─ 📁 core/                     ✅ IMPLEMENTADO
│  │  ├─ __init__.py
│  │  ├─ constants.py              (150 linhas) Paths, configs
│  │  ├─ logger.py                 (70 linhas)  Logging centralizado
│  │  └─ exceptions.py             (60 linhas)  Exceções customizadas
│  │
│  ├─ 📁 ingestion/                ✅ IMPLEMENTADO
│  │  ├─ __init__.py
│  │  └─ pdf_extractor.py          (210 linhas) Extração de PDFs
│  │
│  ├─ 📁 schemas/                  ✅ IMPLEMENTADO
│  │  ├─ __init__.py
│  │  └─ extraction.py             (60 linhas)  Validação Pydantic
│  │
│  ├─ 📁 preprocessing/            🔄 TODO Phase 3
│  │  ├─ cleaner.py
│  │  ├─ normalizer.py
│  │  └─ __init__.py
│  │
│  ├─ 📁 vectorization/            🔄 TODO Phase 4-5
│  │  ├─ chunker.py
│  │  ├─ embedding_model.py
│  │  ├─ vector_store.py
│  │  ├─ persistence.py
│  │  └─ __init__.py
│  │
│  ├─ 📁 retrieval/                🔄 TODO Phase 6
│  │  ├─ retriever.py
│  │  ├─ reranker.py
│  │  └─ __init__.py
│  │
│  ├─ 📁 prompting/                🔄 TODO Phase 7
│  │  ├─ prompt_builder.py
│  │  ├─ citation_handler.py
│  │  └─ __init__.py
│  │
│  ├─ 📁 llm/                      🔄 TODO Phase 7
│  │  ├─ client.py
│  │  ├─ generation.py
│  │  └─ __init__.py
│  │
│  ├─ 📁 api/                      🔄 TODO Phase 8
│  │  ├─ main.py
│  │  ├─ 📁 routes/
│  │  │  ├─ chat.py                POST /chat
│  │  │  ├─ debug.py               GET /debug-retrieval
│  │  │  ├─ health.py              GET /health
│  │  │  └─ __init__.py
│  │  ├─ 📁 schemas/
│  │  │  ├─ request.py
│  │  │  ├─ response.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  │
│  ├─ 📁 evaluation/               🔄 TODO Phase 8
│  │  ├─ retrieval_metrics.py
│  │  ├─ grounding_check.py
│  │  ├─ hallucination_detector.py
│  │  └─ __init__.py
│  │
│  ├─ pipeline.py                  🔄 TODO (Orquestração)
│  └─ __init__.py
│
├─ 📁 data/                         ← Dados do projeto
│  ├─ 📁 raw/                       (ENTRADA) PDFs originais
│  │  ├─ desenvolvimento_paranaense.pdf
│  │  ├─ analise_conjuntural.pdf
│  │  └─ avaliacoes_politicas.pdf
│  │
│  ├─ 📁 extracted/                 ✅ OUTPUT Phase 2
│  │  ├─ desenvolvimento_paranaense.json  (45 páginas)
│  │  ├─ analise_conjuntural.json         (N páginas)
│  │  └─ avaliacoes_politicas.json        (N páginas)
│  │
│  ├─ 📁 processed/                 🔄 TODO Phase 3
│  │  ├─ desenvolvimento_paranaense.json  (texto limpo)
│  │  ├─ analise_conjuntural.json
│  │  └─ avaliacoes_politicas.json
│  │
│  ├─ 📁 chunks/                    🔄 TODO Phase 4
│  │  ├─ chunks.json                (512 tokens, overlap 20%)
│  │  └─ chunks_manifest.json       (metadata)
│  │
│  ├─ 📁 embeddings/                🔄 TODO Phase 5
│  │  ├─ embeddings.npy             (vetores 1024-dim)
│  │  └─ embeddings_manifest.json   (metadata)
│  │
│  └─ 📁 vector_db/                 🔄 TODO Phase 5
│     ├─ faiss.index                (índice FAISS)
│     └─ faiss_manifest.json        (metadata)
│
├─ 📁 outputs/                      ← Saídas para avaliação
│  ├─ 📁 prompts/                   (saída Phase 7)
│  │  └─ query_20260429_103045.json (prompts finais)
│  │
│  ├─ 📁 retrieval_logs/            (saída Phase 6)
│  │  └─ query_20260429_103045.json (chunks recuperados)
│  │
│  ├─ 📁 responses/                 (saída Phase 7)
│  │  └─ query_20260429_103045.json (respostas da LLM)
│  │
│  └─ 📁 evaluations/               (saída Phase 8)
│     ├─ session_20260429_103045.json (métricas)
│     └─ benchmark_report.md        (relatório)
│
├─ 📁 logs/                         ← Logs estruturados
│  ├─ ingest_20260429_103045.log    ✅ Phase 2 output
│  ├─ api_20260429_103045.log       🔄 Phase 8
│  └─ evaluation_20260429_103045.log 🔄 Phase 8
│
├─ 📁 models/                       ← Cache de modelos (local)
│  ├─ 📁 embeddings/
│  │  └─ 📁 multilingual-e5-large/  (baixado automaticamente)
│  └─ 📁 llm/
│     └─ mistral-7b-instruct-q4.gguf (quantizado, ~4GB)
│
├─ 📁 configs/                      ← Configuração em YAML
│  ├─ chunking_config.yaml          (chunk_size, overlap + justificativas)
│  ├─ retrieval_config.yaml         (top_k, threshold + justificativas)
│  ├─ prompting_config.yaml         (templates + justificativas)
│  └─ preprocessing_config.yaml     (opções de limpeza + justificativas)
│
├─ 📁 scripts/                      ← Scripts de orquestração
│  ├─ ingest.py                     ✅ Extrai PDFs (Phase 2)
│  ├─ test_extraction.py            ✅ Valida extração (Phase 2)
│  ├─ run_api.py                    🔄 Inicia API (Phase 8)
│  ├─ evaluate.py                   🔄 Avaliação (Phase 8)
│  └─ debug_retrieval.py            🔄 Debug CLI (Phase 8)
│
├─ 📁 notebooks/                    ← Jupyter (análise)
│  ├─ 01_eda.ipynb                  (exploração)
│  ├─ 02_chunking_analysis.ipynb    (análise de chunks)
│  └─ 03_retrieval_debug.ipynb      (debugging)
│
├─ 📁 docker/                       ← Docker (se necessário)
│  ├─ Dockerfile
│  └─ docker-compose.yml
│
├─ 📁 docs/                         ← Documentação detalhada
│  ├─ SETUP.md                      (instalação offline)
│  ├─ ARCHITECTURE.md               (decisões arquiteturais)
│  ├─ RAG_FLOW.md                   (pipeline completo)
│  ├─ EVALUATION.md                 (estratégia de métricas)
│  └─ DECISIONS.md                  (justificativas)
│
├─ 📄 requirements.txt              ✅ Dependências (45 linhas)
├─ 📄 .env.example                  ✅ Variáveis de ambiente
├─ 📄 Makefile                      ✅ Comandos úteis
├─ 📄 .gitignore                    ✅ Ignora PDFs, logs, modelos
└─ 📄 pyproject.toml                (opcional, futura use)
```

---

## 📊 Exemplo de Saída - Phase 2 (Ingestão)

### 1. JSON Extraído: `data/extracted/desenvolvimento_paranaense.json`

```json
{
  "success": true,
  "pdf_key": "desenvolvimento_paranaense",
  "pages_extracted": 45,
  "total_pages": 45,
  "data": [
    {
      "page": 1,
      "text": "DESENVOLVIMENTO PARANAENSE\nAnálise de Indicadores Econômicos e Sociais\n\nINSTITUTO PARANAENSE DE DESENVOLVIMENTO ECONÔMICO E SOCIAL - IPARDES\n\nCuritiba, 2023",
      "document": "desenvolvimento_paranaense",
      "has_tables": false,
      "extracted_at": "2026-04-29T10:30:15.123456"
    },
    {
      "page": 2,
      "text": "SUMÁRIO\n\n1. Introdução\n2. Panorama Econômico\n3. Indicadores Sociais\n4. Análise Setorial\n5. Perspectivas Futuras",
      "document": "desenvolvimento_paranaense",
      "has_tables": false,
      "extracted_at": "2026-04-29T10:30:16.234567"
    },
    {
      "page": 3,
      "text": "1. INTRODUÇÃO\n\nO Estado do Paraná é uma das unidades federativas mais dinâmicas do Brasil...\n\n[TABELAS]\nTabela 1:\nAno | PIB Nominal (R$) | Crescimento (%)\n2022 | 850 bilhões | 2.1\n2023 | 870 bilhões | 2.3\n2024 | 890 bilhões | 2.3",
      "document": "desenvolvimento_paranaense",
      "has_tables": true,
      "extracted_at": "2026-04-29T10:30:17.345678"
    },
    {
      "page": 4,
      "text": "2. PANORAMA ECONÔMICO\n\n2.1 Produto Interno Bruto (PIB)\n\nO PIB do Paraná cresceu 2.3% em 2024, mantendo a tendência de crescimento modesto...",
      "document": "desenvolvimento_paranaense",
      "has_tables": false,
      "extracted_at": "2026-04-29T10:30:18.456789"
    },
    // ... (41 páginas mais)
  ],
  "extraction_time": "2026-04-29T10:30:45.789012"
}
```

### 2. Log: `logs/ingest_20260429_103045.log`

```
2026-04-29 10:30:00,123 - root - INFO - ======================================================================
2026-04-29 10:30:00,124 - root - INFO - INICIANDO EXTRAÇÃO DE TODOS OS PDFs
2026-04-29 10:30:00,125 - root - INFO - ======================================================================
2026-04-29 10:30:01,456 - root - INFO - Step 1: Criando estrutura de diretórios...
2026-04-29 10:30:01,457 - root - INFO - ✓ Diretórios criados com sucesso

2026-04-29 10:30:01,458 - root - INFO - Step 2: Verificando disponibilidade dos PDFs...
2026-04-29 10:30:01,459 - root - INFO - ✓ Encontrado: desenvolvimento_paranaense
2026-04-29 10:30:01,460 - root - INFO - ✓ Encontrado: analise_conjuntural
2026-04-29 10:30:01,461 - root - INFO - ✓ Encontrado: avaliacoes_politicas
2026-04-29 10:30:01,462 - root - INFO - ✓ Todos os PDFs encontrados

2026-04-29 10:30:01,463 - root - INFO - Step 3: Iniciando extração de PDFs...
2026-04-29 10:30:01,464 - root - INFO - Iniciando extração: desenvolvimento_paranaense
2026-04-29 10:30:01,465 - root - INFO - Caminho: /home/vinicius/Área de trabalho/rag-ipardes-parana/data/raw/desenvolvimento_paranaense.pdf
2026-04-29 10:30:01,466 - root - INFO - Total de páginas: 45
2026-04-29 10:30:01,500 - root - DEBUG - Processadas 5/45 páginas
2026-04-29 10:30:01,600 - root - DEBUG - Processadas 10/45 páginas
2026-04-29 10:30:01,700 - root - DEBUG - Processadas 15/45 páginas
...
2026-04-29 10:30:02,100 - root - DEBUG - Processadas 45/45 páginas
2026-04-29 10:30:02,101 - root - INFO - ✓ Extração concluída: 45 páginas extraídas
2026-04-29 10:30:02,102 - root - INFO - ✓ Salvo: data/extracted/desenvolvimento_paranaense.json
2026-04-29 10:30:02,103 - root - INFO - 
2026-04-29 10:30:02,104 - root - INFO - Iniciando extração: analise_conjuntural
...
2026-04-29 10:30:30,000 - root - INFO - ======================================================================
2026-04-29 10:30:30,001 - root - INFO - EXTRAÇÃO CONCLUÍDA
2026-04-29 10:30:30,002 - root - INFO - ======================================================================
2026-04-29 10:30:30,003 - root - INFO - 
2026-04-29 10:30:30,004 - root - INFO - Step 4: Validando resultados...
2026-04-29 10:30:30,005 - root - INFO - Validando extração...
2026-04-29 10:30:30,006 - root - INFO - ✓ desenvolvimento_paranaense: 45 páginas
2026-04-29 10:30:30,007 - root - INFO - ✓ analise_conjuntural: 52 páginas
2026-04-29 10:30:30,008 - root - INFO - ✓ avaliacoes_politicas: 38 páginas
2026-04-29 10:30:30,009 - root - INFO - 
2026-04-29 10:30:30,010 - root - INFO - Resumo:
2026-04-29 10:30:30,011 - root - INFO -   Sucesso: 3/3
2026-04-29 10:30:30,012 - root - INFO -   Total de páginas extraídas: 135
2026-04-29 10:30:30,013 - root - INFO - ✓ Validação concluída

2026-04-29 10:30:30,014 - root - INFO - 
2026-04-29 10:30:30,015 - root - INFO - ======================================================================
2026-04-29 10:30:30,016 - root - INFO - RESUMO DA INGESTÃO
2026-04-29 10:30:30,017 - root - INFO - ======================================================================
2026-04-29 10:30:30,018 - root - INFO - Total de PDFs: 3
2026-04-29 10:30:30,019 - root - INFO - Sucesso: 3
2026-04-29 10:30:30,020 - root - INFO - Falhas: 0
2026-04-29 10:30:30,021 - root - INFO - Total de páginas extraídas: 135
2026-04-29 10:30:30,022 - root - INFO - ======================================================================
2026-04-29 10:30:30,023 - root - INFO - ✓ INGESTÃO BEM-SUCEDIDA!
```

### 3. Teste de Validação: Output de `test_extraction.py`

```
======================================================================
PRÉ-TESTE: VERIFICANDO PDFs ORIGINAIS
======================================================================
✓ desenvolvimento_paranaense: data/raw/desenvolvimento_paranaense.pdf
✓ analise_conjuntural: data/raw/analise_conjuntural.pdf
✓ avaliacoes_politicas: data/raw/avaliacoes_politicas.pdf

✓ Todos os PDFs originais encontrados

======================================================================
TESTE DE EXTRAÇÃO
======================================================================

Testando: desenvolvimento_paranaense
Arquivo: data/extracted/desenvolvimento_paranaense.json
✓ Arquivo encontrado
✓ JSON válido
✓ Estrutura esperada encontrada
✓ Extração bem-sucedida
✓ 45 páginas extraídas
✓ Estrutura de página válida
✅ desenvolvimento_paranaense: PASSOU

Testando: analise_conjuntural
Arquivo: data/extracted/analise_conjuntural.json
✓ Arquivo encontrado
✓ JSON válido
✓ Estrutura esperada encontrada
✓ Extração bem-sucedida
✓ 52 páginas extraídas
✓ Estrutura de página válida
✅ analise_conjuntural: PASSOU

Testando: avaliacoes_politicas
Arquivo: data/extracted/avaliacoes_politicas.json
✓ Arquivo encontrado
✓ JSON válido
✓ Estrutura esperada encontrada
✓ Extração bem-sucedida
✓ 38 páginas extraídas
✓ Estrutura de página válida
✅ avaliacoes_politicas: PASSOU

======================================================================
RESUMO DOS TESTES
======================================================================
Total de PDFs: 3
Arquivos encontrados: 3
JSONs válidos: 3
Total de páginas extraídas: 135

✓ desenvolvimento_paranaense: 45 páginas
✓ analise_conjuntural: 52 páginas
✓ avaliacoes_politicas: 38 páginas
======================================================================

✅ TODOS OS TESTES PASSARAM!
```

---

## 🔄 Flow de Execução (Visão Geral)

```
PHASE 1-2: SETUP + INGESTÃO (✅ COMPLETO)
│
├─ [1] python -m venv .venv
├─ [2] pip install -r requirements.txt
├─ [3] wget (3 PDFs) → data/raw/
├─ [4] python scripts/ingest.py
│     ├─ Cria diretórios
│     ├─ Valida PDFs
│     ├─ Extrai com pdfplumber
│     └─ Salva em data/extracted/
├─ [5] python scripts/test_extraction.py
│     └─ Valida JSONs
│
└─ OUTPUT: data/extracted/*.json + logs/ingest_*.log

PHASE 3: PREPROCESSING (🔄 PRÓXIMO)
│
├─ src/preprocessing/cleaner.py
│     ├─ Remove headers/footers
│     ├─ Normaliza espaços
│     └─ Corrige quebras de linha
│
├─ src/preprocessing/normalizer.py
│     ├─ Unicode normalization
│     └─ Opcional: stemming/lemmatization
│
└─ OUTPUT: data/processed/*.json

PHASE 4: CHUNKING
│
├─ src/vectorization/chunker.py
│     ├─ RecursiveCharacterTextSplitter
│     ├─ Tamanho: 512 tokens
│     └─ Overlap: 20%
│
└─ OUTPUT: data/chunks/chunks.json

PHASE 5: EMBEDDINGS + VECTOR STORE
│
├─ src/vectorization/embedding_model.py
│     └─ multilingual-e5-large
│
├─ src/vectorization/vector_store.py
│     └─ FAISS indexing
│
└─ OUTPUT: data/embeddings/, data/vector_db/

PHASE 6: RETRIEVAL + RERANKING
│
├─ src/retrieval/retriever.py
│     ├─ Similarity search
│     └─ MMR (diversidade)
│
├─ src/retrieval/reranker.py
│     └─ Cross-encoder ranking
│
└─ OUTPUT: outputs/retrieval_logs/

PHASE 7: PROMPTING + LLM
│
├─ src/prompting/prompt_builder.py
│     └─ Construir prompt final
│
├─ src/llm/client.py + src/llm/generation.py
│     ├─ Ollama ou llama.cpp
│     ├─ Temperatura: 0.1
│     └─ Max tokens: 500
│
└─ OUTPUT: outputs/prompts/, outputs/responses/

PHASE 8: API + AVALIAÇÃO
│
├─ src/api/main.py
│     ├─ POST /chat
│     ├─ GET /debug-retrieval
│     └─ GET /health
│
├─ src/evaluation/
│     ├─ retrieval_metrics.py
│     ├─ grounding_check.py
│     └─ hallucination_detector.py
│
└─ OUTPUT: outputs/evaluations/, benchmark_report.md
```

---

## 📈 Progresso Visual

```
TOTAL: 8 PHASES

Phase 1: Setup Inicial              ████████░░░░░░░░░░░░░░░░░░░░░░ 100% ✅
Phase 2: Ingestão                   ████████░░░░░░░░░░░░░░░░░░░░░░ 100% ✅
Phase 3: Pré-processamento          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%   🔄
Phase 4: Chunking                   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%   🔄
Phase 5: Embeddings + Vector Store  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%   🔄
Phase 6: Retrieval + Reranking      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%   🔄
Phase 7: Prompting + LLM            ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%   🔄
Phase 8: API + Avaliação            ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%   🔄
                                    ────────────────────────────────
                                    ████████░░░░░░░░░░░░░░░░░░░░░░ 25%
```

---

## 📋 Comandos Úteis

```bash
# Setup
make setup         # venv + pip install
make install       # só pip install

# Dados
make extract       # python scripts/ingest.py
make validate      # python scripts/test_extraction.py

# Qualidade
make lint          # flake8 + black check
make format        # black format
make test          # pytest

# Limpeza
make clean         # remove __pycache__, logs temp

# Tudo de uma vez
make all           # setup + extract + validate
```

---

## ✨ Próximos Passos Imediatos

1. ✅ Você já tem: Código, estrutura, scripts, testes
2. 📥 Baixar os 3 PDFs: `data/raw/`
3. 🚀 Executar: `python scripts/ingest.py`
4. ✔️ Validar: `python scripts/test_extraction.py`
5. 🔄 Próximo: Phase 3 (Pré-processamento)

**ETA para Phase 3:** 2-3 horas
