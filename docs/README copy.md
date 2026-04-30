# RAG IPARDES Paraná - Aprendizado de Máquina 2

**Professor:** Mozart Hasse  
**Status:** 🟡 Em andamento - Phase 1-2 concluída (Setup + Ingestão)  
**Última atualização:** 2026-04-29

---

## 📋 Visão Geral

Sistema RAG (Retrieval Augmented Generation) para Q&A sobre documentos do IPARDES (Instituto Paranaense de Desenvolvimento Econômico e Social).

**Objetivo:** Responder perguntas sobre 3 documentos PDF oficiais, citando fontes e evitando alucinações.

**Requisitos:**
- ✅ Code aberto, sem APIs externas
- ✅ Execução 100% local (offline)
- ✅ LLM com max 9.9B parâmetros
- ✅ Logging de prompts, chunks e respostas para avaliação

---

## 🚀 Quick Start

### 1. Setup
```bash
cd /home/vinicius/Área\ de\ trabalho/rag-ipardes-parana
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Baixar PDFs (em `data/raw/`)
```bash
cd data/raw
wget 'https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2023-09/desenvolvimento_paranaense.pdf'
wget 'https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2026-02/Analise_Conjuntural_julho_agosto_2025.pdf'
wget 'https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2025-12/Avaliacoes%20Politicas%20Publicas%20Brasil_revisao%20escopo.pdf' -O 'avaliacoes_politicas.pdf'
```

### 3. Executar
```bash
python scripts/ingest.py           # Extrai PDFs
python scripts/test_extraction.py  # Valida extração
```

---

## 📁 Estrutura do Projeto (Structure 3)

```
rag-ipardes-parana/
├── README.md                           # Este arquivo
├── PROGRESS.md                         # Progresso detalhado com checklist
├── requirements.txt                    # Dependências Python
├── .gitignore
│
├── src/                                # Código-fonte principal
│   ├── __init__.py
│   ├── core/                           # ✅ Configuração centralizada (IMPLEMENTADO)
│   │   ├── __init__.py
│   │   ├── constants.py                # Paths, PDFs, configurações globais
│   │   ├── logger.py                   # Sistema de logging centralizado
│   │   └── exceptions.py               # Exceções customizadas
│   │
│   ├── ingestion/                      # ✅ Extração de PDFs (IMPLEMENTADO)
│   │   ├── __init__.py
│   │   └── pdf_extractor.py            # PDFExtractor com pdfplumber
│   │
│   ├── schemas/                        # ✅ Validação com Pydantic (IMPLEMENTADO)
│   │   ├── __init__.py
│   │   └── extraction.py               # PageData, ExtractionResult
│   │
│   ├── preprocessing/                  # 🔄 Pré-processamento (TODO Phase 3)
│   │   ├── cleaner.py
│   │   ├── normalizer.py
│   │   └── __init__.py
│   │
│   ├── vectorization/                  # 🔄 Chunking + embeddings (TODO Phase 4-5)
│   │   ├── chunker.py
│   │   ├── embedding_model.py
│   │   ├── vector_store.py
│   │   ├── persistence.py
│   │   └── __init__.py
│   │
│   ├── retrieval/                      # 🔄 Busca + reranking (TODO Phase 6)
│   │   ├── retriever.py
│   │   ├── reranker.py
│   │   └── __init__.py
│   │
│   ├── prompting/                      # 🔄 Construção de prompts (TODO Phase 7)
│   │   ├── prompt_builder.py
│   │   ├── citation_handler.py
│   │   └── __init__.py
│   │
│   ├── llm/                            # 🔄 Interface com Ollama (TODO Phase 7)
│   │   ├── client.py
│   │   ├── generation.py
│   │   └── __init__.py
│   │
│   ├── api/                            # 🔄 FastAPI endpoints (TODO Phase 8)
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── chat.py                 # POST /chat
│   │   │   ├── debug.py                # GET /debug-retrieval
│   │   │   └── health.py
│   │   ├── schemas/
│   │   │   ├── request.py
│   │   │   └── response.py
│   │   └── __init__.py
│   │
│   ├── evaluation/                     # 🔄 Métricas e validações (TODO Phase 8)
│   │   ├── retrieval_metrics.py
│   │   ├── grounding_check.py
│   │   ├── hallucination_detector.py
│   │   └── __init__.py
│   │
│   ├── pipeline.py                     # 🔄 Orquestração completa (TODO)
│   └── __init__.py
│
├── data/                               # Dados do projeto
│   ├── raw/                            # ✅ PDFs originais (entrada)
│   ├── extracted/                      # ✅ Texto bruto (JSON) - OUTPUT DE ingest.py
│   ├── processed/                      # 🔄 Texto limpo (TODO Phase 3)
│   ├── chunks/                         # 🔄 Chunks + metadata (TODO Phase 4)
│   ├── embeddings/                     # 🔄 Vetores (TODO Phase 5)
│   └── vector_db/                      # 🔄 Índice FAISS (TODO Phase 5)
│
├── outputs/                            # Outputs para avaliação
│   ├── prompts/                        # Prompt final de cada query
│   ├── retrieval_logs/                 # Chunks recuperados + scores
│   ├── responses/                      # Respostas da LLM
│   └── evaluations/                    # Métricas e relatórios
│
├── logs/                               # Logs estruturados com timestamp
│   ├── ingest_20260429_103045.log      # ✅ OUTPUT DE ingest.py
│   ├── api_YYYYMMDD_HHMMSS.log
│   └── evaluation_YYYYMMDD_HHMMSS.log
│
├── models/                             # Cache de modelos (local, não no git)
│   ├── embeddings/
│   │   └── multilingual-e5-large/
│   └── llm/
│       └── mistral-7b-instruct-q4.gguf
│
├── scripts/                            # Scripts de orquestração
│   ├── ingest.py                       # ✅ Extrai 3 PDFs (IMPLEMENTADO)
│   ├── test_extraction.py              # ✅ Valida extração (IMPLEMENTADO)
│   ├── run_api.py                      # 🔄 Inicializa API (TODO)
│   ├── evaluate.py                     # 🔄 Avaliação (TODO)
│   └── debug_retrieval.py              # 🔄 Debug CLI (TODO)
│
├── configs/                            # Configuração em YAML (com justificativas)
│   ├── chunking_config.yaml
│   ├── retrieval_config.yaml
│   ├── prompting_config.yaml
│   └── preprocessing_config.yaml
│
├── notebooks/                          # Jupyter para análise
│   ├── 01_eda.ipynb
│   ├── 02_chunking_analysis.ipynb
│   └── 03_retrieval_debug.ipynb
│
├── docker/                             # Docker (se necessário)
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── docs/                               # Documentação
    ├── SETUP.md
    ├── ARCHITECTURE.md
    ├── RAG_FLOW.md
    ├── EVALUATION.md
    └── DECISIONS.md
```

---

## ✅ O que foi Implementado (Phase 1-2)

### Phase 1: Setup Inicial
- [x] Estrutura de diretórios
- [x] `src/core/constants.py` - Paths e configurações globais (150 linhas)
- [x] `src/core/logger.py` - Logging centralizado (70 linhas)
- [x] `src/core/exceptions.py` - Exceções customizadas (60 linhas)
- [x] `src/schemas/extraction.py` - Validação Pydantic (60 linhas)

### Phase 2: Pipeline de Ingestão
- [x] `src/ingestion/pdf_extractor.py` - Extrator com pdfplumber (210 linhas)
  - Extrai texto das páginas
  - Extrai e converte tabelas
  - Salva com metadados (página, documento, timestamp)
  
- [x] `scripts/ingest.py` - Orquestrador 5 steps (120 linhas)
  - Cria diretórios
  - Valida PDFs
  - Extrai todos os 3
  - Valida resultados
  - Gera resumo
  
- [x] `scripts/test_extraction.py` - Validação 6 testes (210 linhas)
  - PDFs existem?
  - JSONs válidos?
  - Estrutura esperada?
  - Extração bem-sucedida?
  - Há dados?
  - Estrutura de página correta?

- [x] `requirements.txt` - Todas as dependências (45 linhas)

**Total: ~1000 linhas de código + comentários + docstrings**

---

## 📊 Dados de Saída (Phase 2)

Após executar `python scripts/ingest.py`, são gerados:

**`data/extracted/{pdf_key}.json`** - Um arquivo para cada PDF
```json
{
  "success": true,
  "pdf_key": "desenvolvimento_paranaense",
  "pages_extracted": 45,
  "total_pages": 45,
  "data": [
    {
      "page": 1,
      "text": "...",
      "document": "desenvolvimento_paranaense",
      "has_tables": false,
      "extracted_at": "2026-04-29T10:30:00"
    },
    ...
  ],
  "extraction_time": "2026-04-29T10:35:00"
}
```

**`logs/ingest_YYYYMMDD_HHMMSS.log`** - Log estruturado
```
2026-04-29 10:30:00 - root - INFO - Step 1: Criando estrutura de diretórios...
2026-04-29 10:30:00 - root - INFO - ✓ Diretórios criados com sucesso
2026-04-29 10:30:01 - root - INFO - Step 2: Verificando disponibilidade dos PDFs...
2026-04-29 10:30:01 - root - INFO - ✓ Encontrado: desenvolvimento_paranaense
...
```

---

## 🔄 Próximas Fases (TODO)

### Phase 3: Pré-processamento (próxima)
- Limpeza de texto (headers, footers)
- Normalização linguística (Unicode, case)
- Output: `data/processed/*.json`

### Phase 4: Chunking
- RecursiveCharacterTextSplitter
- Metadata preservation
- Output: `data/chunks/chunks.json`

### Phase 5: Embeddings
- multilingual-e5-large
- Batch processing
- Output: `data/embeddings/embeddings.npy`

### Phase 6: Vector Store
- FAISS indexing
- Persistência
- Output: `data/vector_db/faiss.index`

### Phase 7: Retrieval + Reranking
- Similarity search + MMR
- Cross-encoder ranking

### Phase 8: Prompting + API
- Construção de prompts
- FastAPI endpoints
- Interface web

### Phase 9: Avaliação
- Métricas (precision, recall, NDCG)
- Detecção de alucinações
- Grounding checks

---

## 🎯 Critérios de Avaliação (Professor)

### ✅ Organização e Clareza (20%)
- Código comentado com justificativas ✓
- Boas práticas (Structure 3) ✓
- Funciona offline ✓

### 🔄 Testes Unitários (20%)
- Testes de validação básicos ✓
- Será expandido em Phase 3+

### ✅ Qualidade de Dados (30%)
- Extração estruturada ✓
- Metadados preservados ✓
- Fases seguintes (pré-processamento, chunking)

### 🔄 Qualidade do RAG (30%)
- Pipeline básico ✓
- Logging de prompts/chunks (implementar)
- Validação de alucinações (implementar)

---

## 📖 Documentação

- **`PROGRESS.md`** - Detalhado com checklist
- **`src/core/constants.py`** - Comentários sobre cada config
- **`src/ingestion/pdf_extractor.py`** - Docstrings detalhadas
- **`scripts/ingest.py`** - 5 steps bem documentados
- **`scripts/test_extraction.py`** - 6 testes explicados

---

## 💡 Decisões Técnicas

1. **pdfplumber** para extração
   - Robusto para português, mantém layout, suporta tabelas
   
2. **Pydantic** para validação
   - Type hints, documentação automática, exemplos JSON

3. **Logging centralizado**
   - Uma função setup_logger() para toda aplicação
   
4. **Constants globais**
   - PDF_SOURCES, chunk_size, etc em um único lugar
   
5. **Exceções customizadas**
   - PDFExtractionError, ChunkingError, etc

Cada decisão tem comentário explicativo no código.

---

## 🚦 Como Executar

```bash
# Ambiente
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Dados
# Coloque os 3 PDFs em data/raw/ ou use wget

# Executar
python scripts/ingest.py                # Extrai (5 minutes)
python scripts/test_extraction.py       # Valida (1 minute)

# Outputs
data/extracted/*.json              # Textos extraídos
logs/ingest_*.log                  # Log detalhado
```

---

## 📝 Próximo Passo

**Phase 3 - Pré-processamento:**
- Limpeza: remover headers/footers, normalizar espaços
- Normalização: Unicode, case, opcional stemming
- Output: `data/processed/*.json`
- ETA: 1-2 horas

---

Para detalhes completos, consulte [PROGRESS.md](PROGRESS.md)