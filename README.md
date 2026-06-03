# RAG IPARDES Paraná

## Sumário

- [Visão Geral](#visão-geral)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
   - [Configuração do Ambiente](#1-configuração-do-ambiente)
   - [Construir o banco de dados (opcional)](#2-construir-o-banco-de-dados-opcional)
   - [Iniciar o servidor RAG](#3-iniciar-o-servidor-rag)


## Visão Geral

Pipeline completo de Retrieval-Augmented Generation (RAG) sobre documentos oficiais publicados pelo governo do Estado do Paraná. O sistema responde perguntas em linguagem natural citando trechos e fontes dos documentos indexados, ou informa quando o assunto não está coberto pelo material disponível.

Todo o pipeline foi projetado para execução **100% offline**, sem dependência de APIs externas ou serviços de LLM na internet, utilizando exclusivamente ferramentas de código aberto.

## Estrutura do projeto

```
rag-ipardes-parana/
├── data/
│   ├── raw/                        # PDFs originais
│   ├── extracted/                  # Artefatos de extração (markdown, tabelas)
│   ├── processed/                  # JSON processado e estruturado por documento
│   ├── chunks/                     # Chunks section-aware prontos para indexação
│   ├── embeddings/                 # Chunks com vetores de embedding
│   └── vector_db/                  # Índice vetorial persistido (ChromaDB)
│
├── docs/                           # Artefatos de documentação técnica
│
├── frontend/                       # Código da interface web (HTML/CSS/JS)
│
├── logs/                           # (Não Versionado) Logs estruturados por execução
│
├── models/                         # (Não Versionado) Cache local dos modelos de embedding e reranking
│
├── scripts/                        # Scripts de execução de cada etapa
│
├── src/
│   ├── core/                       # Módulos de configurações e utilitários do projeto
│   ├── ingestion/                  # Módulos de Extração de PDFs com Docling
│   ├── preprocessing/              # Módulos de Limpeza, estruturação e filtragem
│   ├── chunking/                   # Módulos de Divisão section-aware em chunks
│   ├── embedding/                  # Módulos de Geração de vetores com sentence-transformers
│   └── indexing/                   # Módulos de Construção do índice ChromaDB
│
├── README.md                       # Documentação principal do projeto
├── build_database.py               # Script orquestrador para construção do banco de dados
├── run_rag.py                      # Script para iniciar o servidor RAG
└── requirements.txt                # Dependências do projeto
```





## Como Executar

### 1. Configuração do Ambiente

1. **Clone o repositório:**
   ```sh
   git clone <url-do-repositorio>
   ```

2. **Entre no diretório:**
   ```sh
   cd rag-ipardes-parana
   ```

3. **Criação do ambiente virtual:**
   ```sh
   python3 -m venv .venv
   ```

4. **Ative o ambiente virtual:**
   - Linux/macOS:
     ```sh
     source .venv/bin/activate
     ```
   - Windows:
     ```sh
     .venv\Scripts\activate
     ```

5. **Instalação das dependências:**
   ```sh
   pip install -r requirements.txt
   ```

### 2. Construir o banco de dados (opcional)

Os dados já estão pré-processados e indexados no repositório, mas se quiser reconstruir o banco de dados do zero (por exemplo, para atualizar os documentos ou testar o pipeline), execute:

```bash
python build_database.py
```

Este script executa automaticamente todo o pipeline:
- Extração de PDFs (Docling)
- Pré-processamento (limpeza e estruturação)
- Chunking (divisão section-aware)
- Embedding (geração de vetores)
- Indexação vetorial (ChromaDB)


### 3. Iniciar o servidor RAG

Para iniciar o servidor web, é necessário que o Ollama esteja rodando. Para certificar-se disso, abra um terminal separado e execute:

```bash
ollama serve
```

Caso retorne uma mensagem semelhante a `address already in use`, significa que o serviço já está ativo e você pode prosseguir para iniciar o servidor RAG. Em outro terminal, execute:

```bash
python run_rag.py
```

Após a inicialização, o terminal exibirá mensagens de log indicando que o servidor está rodando e pronto para receber requisições. Para acessar a interface web, abra o navegador e navegue até: **http://localhost:8000**

Também é possível acessar o endpoint de health check para verificar se a API está ativa: **http://localhost:8000/api/health**

**Requisitos:**
- Ollama rodando em localhost:11434 (`ollama serve`)
- ChromaDB indexado (execute `python build_database.py` antes)

**Verificações automáticas:**
- Verifica se Ollama está rodando
- Alerta se ChromaDB ainda não foi criado
- Oferece instruções de próximos passos


## Scripts Individuais em `scripts/`

Para mais controle granular, Também  é possível executar cada etapa separadamente:

```bash
# Etapa 1: Extração
python scripts/ingest.py

# Etapa 2: Pré-processamento
python scripts/preprocess.py

# Etapa 3: Chunking
python scripts/chunk.py

# Etapa 4: Embedding
python scripts/embed.py

# Etapa 5: Indexação
python scripts/index.py

# Interface CLI
python scripts/chat.py

# Servidor (alternativa a run_rag.py)
python scripts/server.py
```

Cada script gera um log com timestamp em `logs/`.

---

## 📖 Documentação Completa

- **`docs/technical_documentation.md`** — Documentação técnica detalhada (7 etapas + frontend)
- **`docs/FRONTEND_README.md`** — Guia completo da interface web
- **`docs/QUICKSTART_FRONTEND.md`** — Quick start rápido (3 passos)
- **`docs/ARCHITECTURE.md`** — Decisões arquiteturais
- **`docs/DECISIONS.md`** — Justificativas de escolhas técnicas


## limpar cache

find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; echo "Cache limpo"