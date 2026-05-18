# Estrutura do Projeto

```
rag-ipardes-parana/
│
├── data/
│   ├── raw/                            # PDFs originais (descartáveis)
│   │   ├── desenvolvimento_paranaense.pdf
│   │   ├── analise_conjuntural.pdf
│   │   └── avaliacoes_politicas.pdf
│   │
│   ├── extracted/                                   # Artefatos de extração por documento (texto, markdown, tabelas)
│   │   ├── desenvolvimento_paranaense/
│   │   │   ├── desenvolvimento_paranaense.txt       # Texto plano limpo sem tabelas
│   │   │   ├── desenvolvimento_paranaense.md        # Markdown com estrutura hierárquica
│   │   │   ├── desenvolvimento_paranaense.json      # Metadados + páginas
│   │   │   └── tables/                              # Tabelas extraídas com semântica matricial
│   │   │       ├── tables_index.json                # Índice de todas as tabelas
│   │   │       ├── table_000.md                     # Cada tabela em Markdown para embedding
│   │   │       ├── table_000.json                   # Cada tabela em JSON estruturado
│   │   │       └── ... (table_001, table_002, etc)
│   │   ├── analise_conjuntural/
│   │   │   ├── analise_conjuntural.txt
│   │   │   ├── analise_conjuntural.md
│   │   │   ├── analise_conjuntural.json
│   │   │   └── tables/
│   │   └── avaliacoes_politicas/
│   │       ├── avaliacoes_politicas.txt
│   │       ├── avaliacoes_politicas.md
│   │       ├── avaliacoes_politicas.json
│   │       └── tables/
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
├── src/
│   ├── core/
│   │   ├── constants.py                 # Paths, PDF sources, configurações globais do projeto
│   │   ├── ingestion_config.py          # Configuração centralizada do pipeline de ingestão
│   │   ├── preprocessing_config.py      # Configuração centralizada do pipeline de preprocessamento
│   │   ├── logger.py                    # Sistema de logging centralizado com suporte a arquivo
│   │   └── __init__.py
│   │
│   ├── ingestion/                       # Pipeline de extração de PDFs com Docling + tratamento de tabelas
│   │   ├── ingestion_pipeline.py        # Orquestrador: executa extração + serialização para cada PDF
│   │   ├── pdf_extractor.py             # Extrator CPU-only usando Docling (sem GPU, sem APIs externas)
│   │   ├── table_extractor.py           # Extração dedicada de tabelas em formato matricial e Markdown
│   │   ├── serializer.py                # Persiste artefatos em múltiplos formatos (txt, md, json + tables/)
│   │   └── __init__.py
│   │
│   ├── preprocessing/                   # Limpeza, normalização e processamento de conteúdo extraído
│   │   ├── preprocessor.py              # Orquestrador: converte markdown extraído → JSON processado
│   │   ├── text_cleaner.py              # Limpeza Unicode, remoção de artefatos, normalização de espaços
│   │   ├── section_parser.py            # Detector de hierarquia de seções via prefixo numérico (ex: 3.1.2)
│   │   ├── page_parser.py               # Parser de páginas delimitadas por tags <!-- PAGE: X -->
│   │   ├── content_processor.py         # Estratégias de processamento: detecção de seções vs fallback por página
│   │   ├── content_filter.py            # Filtros progressivos: headers-only, institucionais, sumários, refs
│   │   ├── content_merger.py            # Mescla e ordenação de itens de texto e tabelas por página
│   │   ├── table_processor.py           # Processamento de tabelas: carregamento, limpeza, serialização
│   │   ├── preprocessor_utils.py        # Utilitários: build_metadata, logging de resumos, ProcessResult
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
│
├── scripts/
│   ├── ingest.py                       # Pipeline de ingestão: PDF → Docling → extração + serialização em data/extracted
│   └── preprocess.py                   # Pipeline de pré-processamento: markdown → JSON processado em data/processed
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
├── README.md                           # Visão geral + execução rápida
├── requirements.txt                    # Dependências Python
├── pyproject.toml                      # Configuração do projeto
├── .env.example                        # Variáveis de ambiente
├── Makefile                            # Comandos utilitários
├── .gitignore
└── .gitkeep                            # Placeholder para pastas vazias
```

## limpar cache

find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; echo "Cache limpo"