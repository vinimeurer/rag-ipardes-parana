# Documentação Técnica — RAG IPARDES Paraná

Pipeline completo de Retrieval-Augmented Generation (RAG) sobre documentos oficiais publicados pelo governo do Estado do Paraná. O sistema responde perguntas em linguagem natural citando trechos e fontes dos documentos indexados, ou informa quando o assunto não está coberto pelo material disponível.

Todo o pipeline foi projetado para execução **100% offline**, sem dependência de APIs externas ou serviços de LLM na internet, utilizando exclusivamente ferramentas de código aberto.

---

## Documentos indexados

| Chave | Documento | Fonte |
|---|---|---|
| `desenvolvimento_paranaense` | Desenvolvimento Paranaense: Contexto, Tendências e Desafios | IPARDES, 2022 |
| `analise_conjuntural` | Análise Conjuntural — Julho/Agosto 2025 | IPARDES, 2025 |
| `avaliacoes_politicas` | Avaliações de Políticas Públicas no Brasil: Uma Revisão de Escopo | IPARDES, 2025 |

---

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
├── models/
│   └── embeddings/                 # Cache local do modelo de embedding
│
├── src/
│   ├── core/                       # Configurações e utilitários globais
│   ├── ingestion/                  # Extração de PDFs com Docling
│   ├── preprocessing/              # Limpeza, estruturação e filtragem
│   ├── chunking/                   # Divisão section-aware em chunks
│   ├── embedding/                  # Geração de vetores com sentence-transformers
│   └── indexing/                   # Construção do índice ChromaDB
│
├── scripts/                        # Scripts de execução de cada etapa
└── logs/                           # Logs estruturados por execução
```

---

## Visão geral do pipeline

```
PDFs originais
    └─► scripts/ingest.py
          └─► data/extracted/           (markdown + tabelas por documento)
                └─► scripts/preprocess.py
                      └─► data/processed/       (JSON estruturado por seções)
                            └─► scripts/chunk.py
                                  └─► data/chunks/chunks.jsonl
                                        └─► scripts/embed.py
                                              └─► data/embeddings/chunks_with_embeddings.jsonl
                                                    └─► scripts/index.py
                                                          └─► data/vector_db/
```

Cada etapa gera um artefato intermediário persistido em disco. Isso permite reprocessar qualquer etapa isoladamente sem precisar rerodar as anteriores — decisão importante para iteração e para atender ao requisito de entrega dos artefatos intermediários prontos para uso.

---

## Etapa 1 — Extração

### Objetivo

Converter os PDFs originais em representações estruturadas em texto, preservando a hierarquia do documento e extraindo tabelas de forma separada.

### Tecnologia utilizada

**Docling** foi escolhido como biblioteca de extração por ser a única ferramenta de código aberto que combina extração de texto com detecção de layout, reconhecimento de tabelas e exportação para Markdown estruturado em um único pipeline. Alternativas como `pdfplumber` e `pypdf` não oferecem detecção de hierarquia nem exportação de tabelas em formato matricial.

O extrator roda exclusivamente na CPU (`AcceleratorOptions(num_threads=4, device=AcceleratorDevice.CPU)`), sem dependência de GPU, garantindo reprodutibilidade em qualquer máquina.

### Processamento em batches para PDFs grandes

Para evitar erro `std::bad_alloc` (estouro de memória) ao processar PDFs grandes, a extração implementa estratégia de **split-process-merge**:

**Divisão em batches** — o `pdf_splitter.py` divide o PDF em chunks temporários contendo `batch_size` páginas cada (padrão: 10 páginas). Usa PyPDF2 para manipulação de páginas sem carregar o documento inteiro em memória.

**Processamento independente** — cada batch é convertido isoladamente pelo Docling, liberando memória após cada conversão.

**Agregação com rastreabilidade** — os resultados são mesclados preservando offset de página global. Cada página e tabela recebe ajuste de numeração (`page.page_number += offset`) para manter correspondência com o PDF original. Índices de tabelas são reajustados globalmente com incremento sequencial (`table.table_index = len(all_tables) + idx`) para garantir que cada tabela receba um índice único e evitar overwrite no serializer.

**Cleanup automático** — arquivos temporários são removidos imediatamente após processamento.

Impacto: elimina `std::bad_alloc`, reduz consumo de memória para O(batch_size) em vez de O(total_pages), com custo negligenciável de tempo.

### O que é gerado

Para cada documento, a etapa produz:

```
data/extracted/{pdf_key}/
    ├── {pdf_key}.md           # Texto completo com tags <!-- PAGE: N --> e headers markdown
    ├── {pdf_key}.txt          # Texto plano sem formatação
    ├── {pdf_key}.json         # Metadados e páginas estruturadas
    └── tables/
        ├── tables_index.json  # Índice de todas as tabelas com metadados
        ├── table_000.md       # Cada tabela em Markdown formatado
        ├── table_000.json     # Cada tabela em JSON estruturado
        └── ...
```

As tags `<!-- PAGE: N -->` inseridas no Markdown são o mecanismo de rastreamento de páginas usado pelas etapas seguintes. Cada tabela recebe um arquivo próprio com seus metadados (`page_number`, `caption`, `num_rows`, `num_cols`), mantendo o conteúdo tabular separado do texto corrido para tratamento diferenciado no chunking.

### Como executar

```bash
python3 scripts/ingest.py
```

---

## Etapa 2 — Preprocessamento

### Objetivo

Transformar o Markdown extraído em um JSON estruturado, limpo e organizado hierarquicamente por seções, pronto para o chunker. Esta é a etapa com maior impacto direto na qualidade do RAG.

### Abordagem

O preprocessamento segue um pipeline em camadas com responsabilidades separadas:

**Parsing de páginas** — o arquivo Markdown é dividido pelas tags `<!-- PAGE: N -->` em blocos por página, preservando a numeração original para rastreabilidade na citação de fontes.

**Detecção de hierarquia de seções** — o `SectionParser` percorre as linhas do Markdown detectando headers. Uma decisão técnica crítica aqui: o Docling exporta todos os headers com o mesmo nível `#`, perdendo a hierarquia visual do PDF original. Para recuperá-la, o parser infere o nível pelo padrão numérico do título (`3.` = nível 1, `3.1` = nível 2, `3.1.2` = nível 3), em vez de contar os caracteres `#`. Isso garante que `["3. METODOLOGIA", "3.1 PROTOCOLO"]` seja preservado como hierarquia pai-filho corretamente.

**Estado de seção persistente entre páginas** — quando uma seção começa na página 4 e o texto continua na página 5 sem novo header, a página 5 herda as seções ativas da página 4. Isso evita que páginas do meio de uma seção longa fiquem sem contexto hierárquico.

**Quebra por bloco de seção** — em vez de um item por página, cada mudança de header gera um novo item no array de conteúdo. Assim, uma página com três seções vira três itens distintos, cada um com suas seções corretas. Isso é o que torna o chunking genuinamente section-aware.

**Tratamento especial para `analise_conjuntural`** — este documento não possui hierarquia de seções no Markdown extraído (ausência de headers numerados). Para ele, o número de página é usado como pseudo-seção (`"pagina_N"`), preservando localização sem inferir estrutura inexistente.

**Integração de tabelas** — as tabelas extraídas na etapa anterior são carregadas e inseridas no array de conteúdo na posição correspondente à sua página, após o texto. Cada tabela herda as seções ativas da página onde aparece. O conteúdo de tabelas passa apenas por normalização Unicode e remoção de caracteres de controle — filtros de parágrafos curtos não são aplicados, pois células de tabela são naturalmente curtas e seriam incorretamente descartadas.

**Filtros progressivos** — após a montagem do conteúdo, um `ContentFilter` remove itens de baixo valor semântico para o RAG:

| Filtro | Critério | Justificativa |
|---|---|---|
| Headers-only | Conteúdo vazio após remover linhas `#` | Zero valor semântico para embedding |
| Páginas institucionais | Páginas iniciais de capa e ficha técnica | Nomes de governadores e equipe editorial não respondem perguntas |
| Sumários | Seções com nome "SUMÁRIO" | Tabela de navegação, não conteúdo informativo |
| Referências bibliográficas | Seções com nome "REFERÊNCIAS" | Citações sem conteúdo respondível |
| Fórmulas matemáticas como seção | Linhas com `=` e padrão numérico detectadas como header | Artefato de extração, não título real |

Itens de lista de siglas são mantidos mas marcados com `"is_auxiliary": true`, permitindo que o retriever aplique peso diferenciado sem descartar informação potencialmente útil.

### Schema do JSON processado

```json
{
  "metadata": {
    "pdf_key": "avaliacoes_politicas",
    "description": "Avaliações de Políticas Públicas Brasil",
    "total_pages": 40,
    "processed_at": "2026-05-14T00:10:49",
    "has_sections": true
  },
  "content": [
    {
      "document": "avaliacoes_politicas",
      "page": 7,
      "sections": ["3. METODOLOGIA", "3.1 PROTOCOLO E REGISTRO"],
      "type": "text",
      "content": "# 3.1 PROTOCOLO E REGISTRO\n\nO presente relatório..."
    },
    {
      "document": "avaliacoes_politicas",
      "page": 15,
      "sections": ["4. SELEÇÃO DE EVIDÊNCIAS"],
      "type": "table",
      "caption": "Tabela de distribuição de documentos",
      "content": "| Tema | Quantidade |\n|---|---|\n| Saúde | 42 |"
    }
  ]
}
```

### Limpezas aplicadas ao texto

- Normalização Unicode NFC
- Remoção de caracteres de controle (`\x00`–`\x1f`, exceto `\t` e `\n`)
- Conversão de `\xa0` (non-breaking space) para espaço comum
- Remoção de hifenização artificial de quebra de linha
- Colapso de múltiplos espaços e linhas em branco consecutivas
- Remoção de linhas isoladas contendo apenas números de página

### Como executar

```bash
python3 scripts/preprocess.py
```

---

## Etapa 3 — Chunking

### Objetivo

Dividir os itens do JSON processado em chunks de tamanho controlado, preservando todos os metadados de rastreabilidade para citação de fonte.

### Abordagem section-aware

O chunking é section-aware **por design herdado do preprocessamento**: cada item recebido já representa um bloco dentro de uma seção específica. O chunker não precisa detectar seções — apenas resolve granularidade de tamanho. Cada chunk filho herda `document`, `page` e `sections` do item pai.

**Texto** — aplica recursive character splitting com overlap. A estratégia tenta dividir pelo separador de maior granularidade primeiro (`\n\n`), regredindo para `\n` e depois espaço quando os pedaços ainda excedem o limite. O overlap de 32 tokens garante continuidade de contexto nas fronteiras entre chunks.

**Tabelas** — sempre um chunk único, sem divisão. Tabelas não podem ser partidas no meio de uma linha Markdown sem destruir sua estrutura. Se uma tabela exceder o limite máximo configurado (`max_table_tokens=512`), é truncada com aviso no log — decisão documentada e auditável.

**Contagem de tokens** — usa contagem por `split()` (palavras), uma aproximação offline sem dependência de tokenizador específico. A margem de erro em relação a tokenizadores de modelos reais é de aproximadamente 15-20%, aceitável dado que os limites são configuráveis.

### Parâmetros de configuração

| Parâmetro | Valor padrão | Descrição |
|---|---|---|
| `chunk_size` | 256 | Máximo de tokens por chunk de texto |
| `overlap` | 32 | Tokens de sobreposição entre chunks consecutivos |
| `min_chunk_tokens` | 10 | Chunks abaixo deste valor são descartados |
| `max_table_tokens` | 512 | Tabelas acima deste valor são truncadas |

Esses valores foram escolhidos considerando a janela de contexto de modelos com até 9,9B parâmetros. Com 5 chunks recuperados por query (K=5) e overhead do prompt, o contexto total enviado ao LLM fica em torno de 1.500 tokens — dentro da janela de modelos como Llama 3.2 e Qwen 2.5.

### Schema do chunk

```json
{
  "chunk_id": "avaliacoes_politicas_007_00",
  "document": "avaliacoes_politicas",
  "page": 7,
  "sections": ["3. METODOLOGIA", "3.1 PROTOCOLO E REGISTRO"],
  "type": "text",
  "content": "O presente relatório seguiu as diretrizes...",
  "token_count": 187,
  "is_auxiliary": false,
  "caption": null
}
```

O `chunk_id` segue o padrão `{pdf_key}_{item_index:03d}_{chunk_index:02d}`, permitindo rastrear exatamente de qual item e de qual posição dentro do item cada chunk originou.

### Resultado

A etapa gera 556 chunks distribuídos da seguinte forma:

| Documento | Chunks de texto | Chunks de tabela | Total |
|---|---|---|---|
| `desenvolvimento_paranaense` | 337 | 77 | 414 |
| `analise_conjuntural` | 38 | 25 | 63 |
| `avaliacoes_politicas` | 68 | 11 | 79 |
| **Total** | **443** | **113** | **556** |

### Como executar

```bash
python3 scripts/chunk.py
```

---

## Etapa 4 — Embedding

### Objetivo

Gerar representações vetoriais para cada chunk, permitindo busca por similaridade semântica no banco vetorial.

### Modelo escolhido

**`paraphrase-multilingual-mpnet-base-v2`** via `sentence-transformers`.

A escolha priorizou quatro critérios:

**Suporte a português técnico** — o modelo foi treinado em dados multilíngues com cobertura sólida de PT-BR, adequado para textos técnicos governamentais e econômicos como os do corpus IPARDES.

**Operação offline com `sentence-transformers`** — o modelo é baixado automaticamente na primeira execução e armazenado em cache local em `models/embeddings/`. Execuções posteriores carregam do cache sem qualquer acesso à internet. Modelos alternativos de maior qualidade como `Qwen3-Embedding` exigem Ollama como servidor separado, adicionando complexidade de configuração e dependência de infraestrutura externa.

**Dimensão vetorial** — 768 dimensões, equilibrio entre expressividade semântica e custo de armazenamento e busca.

**Execução na CPU** — roda sem GPU, garantindo reprodutibilidade em qualquer máquina do laboratório.

### Enriquecimento do texto para embedding

Antes de codificar, cada chunk tem seu texto enriquecido com metadados contextuais:

```
3. METODOLOGIA > 3.1 PROTOCOLO E REGISTRO
# 3.1 PROTOCOLO E REGISTRO

O presente relatório seguiu as diretrizes...
```

Para tabelas, a caption é incluída antes do conteúdo Markdown, pois o conteúdo tabular puro (`| col1 | col2 |`) tem baixa semântica isolado. Esse enriquecimento melhora a recuperação de chunks em perguntas que mencionam temas de seções específicas sem usar as palavras exatas do texto.

### Cache local do modelo

```
models/
└── embeddings/
    └── paraphrase-multilingual-mpnet-base-v2/   # baixado automaticamente
```

O script detecta automaticamente se o modelo está em cache:

```
[INFO] Modelo encontrado em cache local: models/embeddings/paraphrase-...
# ou
[INFO] Modelo não encontrado localmente. Baixando para models/embeddings/...
```

### Artefato gerado

`data/embeddings/chunks_with_embeddings.jsonl` — cada linha contém o chunk completo acrescido do campo `"embedding"` com o vetor de 768 floats. Este arquivo é o artefato intermediário que permite reindexar no banco vetorial sem re-rodar o modelo de embedding.

### Como executar

```bash
# Primeira execução (requer internet para baixar o modelo)
python3 scripts/embed.py

# Execuções seguintes (totalmente offline)
python3 scripts/embed.py
```

---

## Etapa 5 — Indexação vetorial

### Objetivo

Inserir os chunks e seus embeddings em um banco vetorial persistente para busca por similaridade em tempo de resposta.

### Tecnologia escolhida

**ChromaDB** foi escolhido sobre FAISS pelos seguintes motivos:

**Recuperação de metadados nativa** — o ChromaDB retorna `document`, `page`, `sections`, `type` e `caption` junto com cada resultado de busca, sem cruzamento manual de índices. O pipeline RAG precisa desses metadados para montar a citação de fonte exigida pelo professor.

**Persistência automática em disco** — o `PersistentClient` persiste o índice em `data/vector_db/` automaticamente, sem configuração adicional.

**Sem infraestrutura adicional** — roda em processo Python puro via `pip install chromadb`, sem Docker, sem servidor separado.

Com FAISS, seria necessário implementar manualmente o armazenamento e cruzamento dos metadados pelo índice numérico — complexidade desnecessária dado que o ChromaDB resolve nativamente.

### Recriação do zero

A coleção é sempre deletada e recriada a cada execução para garantir sincronização completa com o arquivo de embeddings. Isso é intencional — com um corpus fixo de três documentos, a recriação completa leva menos de 1 segundo e elimina qualquer risco de inconsistência entre o JSONL e o índice.

### Tratamento de metadados

O ChromaDB não aceita `None` nem listas como valores de metadados. Dois tratamentos foram necessários:

- **Seções** — lista `["3. METODOLOGIA", "3.1 PROTOCOLO"]` é serializada como string `"3. METODOLOGIA > 3.1 PROTOCOLO"`. O pipeline RAG desserializa com `.split(" > ")` ao recuperar.
- **Caption** — `None` é convertido para string vazia `""`.

### Métrica de distância

`cosine` — adequada para vetores normalizados (a etapa de embedding já normaliza com `normalize_embeddings=True`). A similaridade de cosseno mede o ângulo entre vetores independentemente da magnitude, o que é o comportamento correto para busca semântica.

### Como executar

```bash
python3 scripts/index.py
```

---

## Executando o pipeline completo do zero

Para recriar todos os artefatos desde os PDFs originais:

```bash
# 1. Extrair PDFs (requer internet apenas para baixar bibliotecas)
python3 scripts/ingest.py

# 2. Preprocessar e estruturar
python3 scripts/preprocess.py

# 3. Gerar chunks section-aware
python3 scripts/chunk.py

# 4. Gerar embeddings (baixa modelo na primeira vez se não estiver em cache)
python3 scripts/embed.py

# 5. Indexar no banco vetorial
python3 scripts/index.py
```

Para usar os artefatos intermediários já gerados (sem reprocessar desde o início):

```bash
# Usar chunks já gerados, apenas reindexar
python3 scripts/index.py

# Usar embeddings já gerados, apenas reindexar
python3 scripts/index.py

# Reparar apenas o preprocessamento mantendo extração
python3 scripts/preprocess.py
python3 scripts/chunk.py
python3 scripts/embed.py
python3 scripts/index.py
```

---

## Dependências

```bash
pip install docling sentence-transformers chromadb PyPDF2
```

Todas as bibliotecas são de código aberto e disponíveis via PyPI. Nenhuma API externa ou serviço de nuvem é necessário após o download inicial das bibliotecas e do modelo de embedding.

| Biblioteca | Versão mínima | Uso |
|---|---|---|
| `docling` | 2.x | Extração de PDFs com detecção de layout |
| `sentence-transformers` | 3.x | Geração de embeddings vetoriais |
| `chromadb` | 0.5.x | Banco vetorial persistente |
| `PyPDF2` | 4.x | Divisão de PDFs em batches para memory-efficiency |

---

## Decisões de arquitetura

**Artefatos intermediários persistidos em disco** — cada etapa lê da etapa anterior e escreve em disco antes de passar para a próxima. Isso permite auditoria de cada transformação, reprocessamento parcial sem rerodar tudo, e entrega dos artefatos intermediários conforme exigido.

**Separação entre embedding e indexação** — o modelo de embedding é computacionalmente caro. Separar a geração de vetores (`embed.py`) da inserção no banco (`index.py`) permite reindexar com parâmetros diferentes sem re-rodar o modelo.

**Configuração centralizada por etapa** — cada etapa tem seu próprio `*_config.py` em `src/core/`, evitando parâmetros hardcoded espalhados pelo código. Todos os valores relevantes (tamanho de chunk, overlap, modelo, batch size) são ajustáveis em um único lugar.

**Logging estruturado** — todas as etapas usam o sistema de logging centralizado com timestamps, permitindo auditoria completa de cada execução em `logs/`.
