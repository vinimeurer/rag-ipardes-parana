# RAG IPARDES Paraná

## Sumário

- [Visão Geral](#visão-geral)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
   - [Configuração do Ambiente](#1-configuração-do-ambiente)
   - [Construir o banco de dados (opcional)](#2-construir-o-banco-de-dados-opcional)
   - [Iniciar o servidor RAG](#3-iniciar-o-servidor-rag)
   - [Scripts Individuais em `scripts/`](#scripts-individuais-em-scripts)
- [Testes](#testes)
   - [Testes Unitários e Cobertura de Código](#testes-unitários-e-cobertura-de-código)
   - [Testes de Qualidade do RAG](#testes-de-qualidade-do-rag)
- [Documentação Completa](#documentação-completa)


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
├── tests/                          # Testes unitários e de qualidade
│   └── quality/                    # Testes de qualidade ponta a ponta do RAG
|
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

Este script remove todos os artefatos gerados no diretório `data/`,preservando apenas `data/raw` e reexecuta automaticamente todo o pipeline:
- Extração de PDFs (Docling)
- Pré-processamento (limpeza e estruturação)
- Chunking (divisão section-aware)
- Embedding (geração de vetores)
- Indexação vetorial (ChromaDB)

**Importante:** Para a execução correta da construção do banco de dados, certifique-se de que os arquivos PDF estejam presentes na pasta `data/raw/` com os mesmos nomes utilizados no momento do download das fontes originais. O script processa apenas os arquivos definidos na configuração interna, portanto é necessário manter os nomes esperados e armazená-los corretamente.

### 3. Iniciar o servidor RAG

Para iniciar o servidor web, é necessário que o Ollama esteja rodando. Caso ainda não tenha baixado o modelo, execute uma vez:

```bash
ollama pull llama3.2:3b
```

Em seguida, abra um terminal separado e execute:

```bash
ollama serve
```

Caso retorne uma mensagem semelhante a `address already in use` ou `Error: listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address (protocol/network address/port) is normally permitted.`, significa que o serviço já está ativo e você pode prosseguir. Em outro terminal, execute:

```bash
python run_rag.py
```

Após a inicialização, o terminal exibirá mensagens de log indicando que o servidor está rodando e pronto para receber requisições. Para acessar a interface web, abra o navegador e navegue até: **http://localhost:8000**

Também é possível acessar o endpoint de health check para verificar se a API está ativa: **http://localhost:8000/api/health**

**Requisitos:**
- Modelo `llama3.2:3b` baixado via Ollama (`ollama pull llama3.2:3b`)
- Ollama rodando em localhost:11434 (`ollama serve`)
- ChromaDB indexado (execute `python build_database.py` antes)

**Verificações automáticas:**
- Verifica se Ollama está rodando
- Alerta se ChromaDB ainda não foi criado
- Oferece instruções de próximos passos

### Scripts Individuais em `scripts/`

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

## Testes

### Testes Unitários e Cobertura de Código

Para executar os testes unitários e verificar a cobertura de código, utilize o comando:

```bash
pytest --cov=src --cov-report=term-missing
```

Esses testes validam individualmente os componentes do pipeline, incluindo etapas de processamento, chunking, geração de embeddings e indexação.

### Testes de Qualidade do RAG

Para executar os testes de qualidade do RAG, utilize o comando:

```bash
pytest tests/quality/ -v -s
```

Os testes de qualidade utilizam um conjunto de perguntas de referência (ground truth) construído a partir dos documentos indexados. Para cada pergunta são definidos o documento esperado, a página de origem e palavras-chave associadas à resposta correta.

A avaliação mede métricas de recuperação (retrieval) como:

- **Document Hit@K**: verifica se o documento correto aparece entre os K chunks recuperados.
- **Page Hit@K**: verifica se a página correta foi recuperada.
- **Keyword Hit@K**: verifica se os chunks recuperados contêm termos relevantes da resposta esperada.

Também são executados testes com perguntas fora do escopo dos documentos para validar o mecanismo de recusa do sistema, garantindo que consultas sem relação com o conteúdo indexado não sejam consideradas relevantes pelo retriever.

Ao final da execução, um resumo consolidado das métricas é exibido automaticamente no terminal.

## Documentação Completa

- [**`docs/ARCHITECTURE.md`**](./docs/ARCHITECTURE.md) — Decisões arquiteturais
- [**`docs/ASSIGNMENT.md`**](./docs/ASSIGNMENT.md) — Descrição do trabalho
- [**`docs/DECISIONS.md`**](./docs/DECISIONS.md) — Justificativas de escolhas técnicas
- [**`docs/FRONTEND.md`**](./docs/DECISIONS.md) — Guia completo da interface web
