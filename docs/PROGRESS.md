# PROGRESSO DO PROJETO

## Status Geral: 🟡 Em Andamento

**Data de início:** 2026-04-29  
**Última atualização:** 2026-04-29

---

## ✅ Implementado - Phase 1: Setup Inicial

### 1.1 Estrutura de Diretórios
- [x] Criar estrutura base do projeto
- [x] Diretórios de dados (`data/raw/`, `data/extracted/`, etc)
- [x] Diretórios de outputs (`outputs/prompts/`, `outputs/responses/`, etc)
- [x] Diretórios de logging e configs

### 1.2 Core - Sistema Centralizado
- [x] **`src/core/constants.py`** - Paths e configurações globais
  - PDF_SOURCES com os 3 documentos do IPARDES
  - Defaults para chunking, embeddings, retrieval, LLM
  - Função `create_directories()` para inicializar estrutura
  - ✨ JUSTIFICATIVAS comentadas para cada parâmetro

- [x] **`src/core/logger.py`** - Sistema de logging centralizado
  - Logs em console e arquivo
  - Timestamps em nomes de arquivo (`ingest_YYYYMMDD_HHMMSS.log`)
  - Função `setup_logger(name, log_file)` para uso em módulos

- [x] **`src/core/exceptions.py`** - Exceções customizadas
  - RAGException (base)
  - PDFExtractionError, PreprocessingError, ChunkingError
  - EmbeddingError, VectorStoreError, RetrievalError
  - NoRelevantDocumentsError, ContextWindowExceededError, etc.

### 1.3 Schemas de Dados (Pydantic)
- [x] **`src/schemas/extraction.py`**
  - `PageData` - Dados de uma página extraída
  - `ExtractionResult` - Resultado completo da extração
  - ✨ Validação automática com Pydantic + exemplos JSON

### 1.4 Dependências
- [x] **`requirements.txt`** - Todas as dependências do projeto
  - PDF: pdfplumber 0.10.3 (robusto para português)
  - Embeddings: sentence-transformers + faiss-cpu
  - LLM: ollama, llama-cpp-python (local)
  - API: FastAPI + Uvicorn + Pydantic
  - NLP: nltk, spacy (com modelo pt_core_news_lg)
  - Utilities: python-dotenv, pyyaml, tqdm
  - Dev: pytest, black, flake8

---

## ✅ Implementado - Phase 2: Pipeline de Ingestão

### 2.1 Extrator de PDFs
- [x] **`src/ingestion/pdf_extractor.py`** - Classe PDFExtractor
  - Método `extract_pdf(pdf_key, pdf_path)` - Extrai um PDF
    - Lê página por página
    - Extrai tabelas com pdfplumber
    - Combina tabelas em texto markdown-like
    - Salva metadados (página, documento, timestamp)
  
  - Método `save_extracted_json(extraction_result, pdf_key)` - Salva como JSON
    - Salva em `data/extracted/{pdf_key}.json`
    - UTF-8 com indentação legível
  
  - Método `extract_all_pdfs()` - Extrai todos os 3 PDFs
    - Itera sobre PDF_SOURCES
    - Trata erros individualmente
    - Retorna dicionário de resultados
  
  - Função `validate_extraction(results)` - Valida resultados
    - Conta sucessos/falhas
    - Retorna estatísticas

### 2.2 Scripts de Orquestração
- [x] **`scripts/ingest.py`** - Orquestrador principal
  - Step 1: Criar diretórios
  - Step 2: Verificar disponibilidade dos PDFs (com URLs para download)
  - Step 3: Extrair todos os PDFs
  - Step 4: Validar resultados
  - Step 5: Resumo final
  - ✨ Logging estruturado em arquivo + console
  - ✨ Mensagens claras sobre como baixar PDFs faltantes

- [x] **`scripts/test_extraction.py`** - Validação de extração
  - Pré-teste: Verifica se PDFs originais existem
  - Teste 1: Arquivo JSON existe?
  - Teste 2: JSON é válido?
  - Teste 3: Estrutura esperada?
  - Teste 4: Extração bem-sucedida?
  - Teste 5: Há dados?
  - Teste 6: Estrutura de PageData está correta?
  - ✨ Resumo com ✓ e ✗ para cada PDF

---

## 📝 Uso Prático

### Passo 1: Instalar dependências
```bash
cd /home/vinicius/Área\ de\ trabalho/rag-ipardes-parana
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou: .venv\Scripts\activate (Windows)
pip install -r requirements.txt
```

### Passo 2: Baixar os 3 PDFs
Coloque os PDFs em `data/raw/`:
- `desenvolvimento_paranaense.pdf`
- `analise_conjuntural.pdf`
- `avaliacoes_politicas.pdf`

Ou execute:
```bash
wget 'https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2023-09/desenvolvimento_paranaense.pdf' -O data/raw/desenvolvimento_paranaense.pdf
wget 'https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2026-02/Analise_Conjuntural_julho_agosto_2025.pdf' -O data/raw/analise_conjuntural.pdf
wget 'https://www.ipardes.pr.gov.br/sites/ipardes/arquivos_restritos/files/documento/2025-12/Avaliacoes%20Politicas%20Publicas%20Brasil_revisao%20escopo.pdf' -O data/raw/avaliacoes_politicas.pdf
```

### Passo 3: Extrair PDFs
```bash
python scripts/ingest.py
```

Output esperado:
```
======================================================================
INICIANDO EXTRAÇÃO DE TODOS OS PDFs
======================================================================
Iniciando extração: desenvolvimento_paranaense
Total de páginas: 45
✓ Extração concluída: 45 páginas extraídas
✓ Salvo: data/extracted/desenvolvimento_paranaense.json
...
======================================================================
EXTRAÇÃO CONCLUÍDA
======================================================================
```

### Passo 4: Validar extração
```bash
python scripts/test_extraction.py
```

Output esperado:
```
======================================================================
PRÉ-TESTE: VERIFICANDO PDFs ORIGINAIS
======================================================================
✓ desenvolvimento_paranaense: data/raw/desenvolvimento_paranaense.pdf
✓ analise_conjuntural: data/raw/analise_conjuntural.pdf
✓ avaliacoes_politicas: data/raw/avaliacoes_politicas.pdf

======================================================================
TESTE DE EXTRAÇÃO
======================================================================
Testando: desenvolvimento_paranaense
✓ Arquivo encontrado
✓ JSON válido
✓ Estrutura esperada encontrada
✓ Extração bem-sucedida
✓ 45 páginas extraídas
✓ Estrutura de página válida
✅ desenvolvimento_paranaense: PASSOU
...
======================================================================
✅ TODOS OS TESTES PASSARAM!
```

---

## 🔄 Próximos Passos - Phase 3 (TODO)

### 3.1 Pré-processamento
- [ ] `src/preprocessing/cleaner.py` - Limpeza de texto
  - Remover headers/footers
  - Normalizar espaços e quebras de linha
  - Correção de OCR artifacts
  
- [ ] `src/preprocessing/normalizer.py` - Normalização linguística
  - Unicode normalization
  - Case handling
  - Opcional: stemming/lemmatization

### 3.2 Chunking
- [ ] `src/vectorization/chunker.py` - Estratégias de chunking
  - RecursiveCharacterTextSplitter
  - Tamanho configurável (512 tokens)
  - Overlap (20%)
  - Preservação de metadata

### 3.3 Embeddings
- [ ] `src/vectorization/embedding_model.py` - Geração de embeddings
  - Carregar modelo multilíngue
  - Cache local
  - Batch processing

### 3.4 Vector Store
- [ ] `src/vectorization/vector_store.py` - FAISS indexing
  - Criar índice
  - Persistir
  - Carregar

### 3.5 Retrieval
- [ ] `src/retrieval/retriever.py` - Busca similaridade + MMR
- [ ] `src/retrieval/reranker.py` - Cross-encoder reranking

### 3.6 Prompting e Geração
- [ ] `src/prompting/prompt_builder.py` - Construção do prompt final
- [ ] `src/prompting/citation_handler.py` - Formatação de citações
- [ ] `src/llm/client.py` - Interface com ollama/llama.cpp
- [ ] `src/llm/generation.py` - Geração com LLM

### 3.7 API e Interface
- [ ] `src/api/main.py` - FastAPI app
- [ ] `src/api/routes/chat.py` - POST /chat (query + response + sources)
- [ ] `src/api/routes/debug.py` - GET /debug-retrieval
- [ ] Interface Streamlit/Gradio

### 3.8 Avaliação
- [ ] `src/evaluation/retrieval_metrics.py` - Precision, recall, NDCG
- [ ] `src/evaluation/grounding_check.py` - Validação de correspondência
- [ ] `src/evaluation/hallucination_detector.py` - Detecção de alucinações

---

## 📊 Arquivos Criados até Agora

```
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── constants.py          ✅ 150 linhas
│   ├── logger.py             ✅ 70 linhas
│   └── exceptions.py         ✅ 60 linhas
├── ingestion/
│   ├── __init__.py
│   └── pdf_extractor.py      ✅ 210 linhas
└── schemas/
    ├── __init__.py
    └── extraction.py         ✅ 60 linhas

scripts/
├── ingest.py                 ✅ 120 linhas
└── test_extraction.py        ✅ 210 linhas

requirements.txt              ✅ 45 linhas
```

**Total: ~1000 linhas de código + comentários + docstrings**

---

## 🎯 Decisões Arquiteturais Documentadas

1. **PDF Extraction: pdfplumber**
   - ✓ Robusto para português
   - ✓ Mantém layout/tabelas
   - ✓ Open-source
   - Alternativa: PyMuPDF (fitz) também seria bom

2. **Logging Centralizado**
   - Função `setup_logger()` em todos os módulos
   - Logs em arquivo com timestamp
   - Console sempre visível

3. **Schemas com Pydantic**
   - Validação automática
   - Documentação auto-gerada
   - Exemplos JSON nos schemas

4. **Constants em um lugar**
   - Fácil encontrar configurações
   - Documentação inline
   - Sem magic numbers/strings espalhados

5. **Exceções customizadas**
   - Tratamento específico em cada etapa
   - Mensagens claras
   - Facilita debugging

---

## 📋 Checklist para o Professor

- [x] Código comentado com justificativas de escolhas
- [x] Organização seguindo boas práticas (structure.3 escolhida)
- [x] Logging estruturado
- [x] Tratamento robusto de erros
- [x] Validação de dados com Pydantic
- [x] Documentação inline no código
- [x] Testes para validar cada etapa
- [ ] Testes unitários (será implementado depois, conforme requisito)

---

## 🚀 Como Executar (Resumido)

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Baixar PDFs (3 comandos wget ou download manual)

# Executar
python scripts/ingest.py      # Extrai PDFs
python scripts/test_extraction.py  # Valida

# Saídas
data/extracted/desenvolvimento_paranaense.json
data/extracted/analise_conjuntural.json
data/extracted/avaliacoes_politicas.json
logs/ingest_YYYYMMDD_HHMMSS.log
```
