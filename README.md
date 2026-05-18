# Estrutura do Projeto

```
rag-ipardes-parana/
│
├── README.md                           # Visão geral + execução rápida
├── requirements.txt                    # Dependências Python
├── pyproject.toml                      # Configuração do projeto
├── .env.example                        # Variáveis de ambiente
├── Makefile                            # Comandos utilitários
├── .gitignore
│
├── src/
│   ├── core/
│   │   ├── config.py                   # Configurações globais
│   │   ├── logger.py                   # Sistema de logging centralizado
│   │   └── utils.py                    # Helpers genéricos
│   │
│   ├── ingestion/
│   │   ├── pdf_extractor.py            # Extração de PDFs
│   │   └── __init__.py
│   │
│   ├── preprocessing/
│   │   ├── cleaner.py                  # Limpeza de texto
│   │   ├── normalizer.py               # Normalização linguística
│   │   └── __init__.py
│   │
│   ├── vectorization/
│   │   ├── chunker.py                  # Estratégias de chunking
│   │   ├── embedding_model.py          # Carregamento e cache de embeddings
│   │   ├── vector_store.py             # FAISS/Qdrant persistência
│   │   └── __init__.py
│   │
│   ├── retrieval/
│   │   ├── retriever.py                # Similarity search + MMR
│   │   ├── reranker.py                 # Cross-encoder ranking
│   │   └── __init__.py
│   │
│   ├── prompting/
│   │   ├── prompt_builder.py           # Construção do prompt final
│   │   ├── citation_handler.py         # Formatação de citações
│   │   └── __init__.py
│   │
│   ├── llm/
│   │   ├── client.py                   # Interface com ollama/llama.cpp
│   │   ├── generation.py               # Geração com controle de parâmetros
│   │   └── __init__.py
│   │
│   ├── api/
│   │   ├── main.py                     # FastAPI init + middleware
│   │   ├── routes/
│   │   │   ├── chat.py                 # POST /chat
│   │   │   ├── debug.py                # GET /debug-retrieval
│   │   │   └── health.py               # GET /health
│   │   ├── schemas/
│   │   │   ├── request.py              # Pydantic models de entrada
│   │   │   └── response.py             # Pydantic models de saída
│   │   └── __init__.py
│   │
│   ├── evaluation/
│   │   ├── retrieval_metrics.py        # Precision, recall, NDCG
│   │   ├── grounding_check.py          # Validação de correspondência
│   │   ├── hallucination_detector.py   # Detecção de alucinações
│   │   └── __init__.py
│   │
│   ├── pipeline.py                     # Orquestração completa (RAG)
│   └── __init__.py
│
├── data/
│   ├── raw/                            # PDFs originais (descartáveis)
│   │   ├── desenvolvimento_paranaense.pdf
│   │   ├── analise_conjuntural.pdf
│   │   └── avaliacoes_politicas.pdf
│   │
│   ├── extracted/                      # Texto BRUTO do PDF (JSON)
│   │   ├── desenvolvimento_paranaense.json
│   │   ├── analise_conjuntural.json
│   │   └── avaliacoes_politicas.json
│   │
│   ├── processed/                      # Texto após limpeza/normalização (JSON)
│   │   ├── desenvolvimento_paranaense.json
│   │   ├── analise_conjuntural.json
│   │   └── avaliacoes_politicas.json
│   │
│   ├── chunks/                         # Chunks finais com metadados
│   │   ├── chunks.json
│   │   └── chunks_manifest.json        # Qual chunker? qual chunk_size? quando?
│   │
│   ├── embeddings/                     # Vetores + metadata
│   │   ├── embeddings.npy
│   │   └── embeddings_manifest.json    # Qual modelo? qual tamanho? quando?
│   │
│   └── vector_db/                      # Índice persistido
│       ├── faiss.index
│       └── faiss_manifest.json         # Versão FAISS, timestamp, dim
│
├── outputs/
│   ├── prompts/                        # Prompt final de cada query
│   │   └── query_YYYYMMDD_HHMMSS.json
│   │
│   ├── retrieval_logs/                 # Chunks recuperados + scores
│   │   └── query_YYYYMMDD_HHMMSS.json
│   │
│   ├── responses/                      # Resposta final da LLM
│   │   └── query_YYYYMMDD_HHMMSS.json
│   │
│   └── evaluations/                    # Resultados de métricas
│       ├── session_YYYYMMDD_HHMMSS.json
│       └── benchmark_report.md
│
├── models/
│   ├── embeddings/
│   │   └── multilingual-e5-large/      # Cache local do modelo
│   │
│   └── llm/
│       └── mistral-7b-instruct-q4.gguf  # Quantizado para rodar local
│
├── logs/                               # Logs de execução estruturados
│   ├── ingest_YYYYMMDD_HHMMSS.log
│   ├── api_YYYYMMDD_HHMMSS.log
│   └── evaluation_YYYYMMDD_HHMMSS.log
│
├── scripts/
│   ├── setup.py                        # Download/preparação inicial
│   ├── ingest.py                       # Orquestração: PDF → chunks → index
│   ├── run_api.py                      # Inicialização da API
│   ├── evaluate.py                     # Runner de avaliação com métricas
│   └── debug_retrieval.py              # CLI para debugar retrieval
│
├── notebooks/
│   ├── 01_eda.ipynb                    # Exploração dos PDFs
│   ├── 02_chunking_analysis.ipynb      # Análise de chunks
│   └── 03_retrieval_debug.ipynb        # Debugging de retrieval
│
├── configs/
│   ├── config.yaml                     # Parâmetros do RAG (chunk_size, top_k, etc)
│   └── prompts.yaml                    # Templates de prompt
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/
│   ├── SETUP.md                        # Instalação e execução offline
│   ├── ARCHITECTURE.md                 # Decisões arquiteturais
│   ├── RAG_FLOW.md                     # Pipeline completo com diagramas
│   ├── EVALUATION.md                   # Estratégia de métricas
│   └── DECISIONS.md                    # Justificativas de cada escolha
│
└── .gitkeep                            # Placeholder para pastas vazias
```


## limpar cache

find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; echo "Cache limpo"