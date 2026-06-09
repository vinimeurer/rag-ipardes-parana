# Justificativas de Escolhas Técnicas

Este documento registra o **porquê** de cada escolha técnica relevante do pipeline RAG IPARDES Paraná. Para a descrição do *que* foi construído e *como* executar, ver `ARCHITECTURE.md`.

## Princípios transversais

### Artefatos intermediários persistidos em disco

Cada etapa lê da etapa anterior e escreve em disco. Isso permite:

- **Auditoria** de cada transformação individualmente
- **Reprocessamento parcial** — mudar o chunker não exige re-extrair os PDFs
- **Entrega dos artefatos** conforme exigido pelo enunciado do trabalho

### Separação entre embedding e indexação

O modelo de embedding é computacionalmente caro. Separar `embed.py` de `index.py` permite reindexar o ChromaDB com parâmetros diferentes (ex: tamanho de coleção, métrica de distância) sem re-rodar o modelo de embedding.

### Configuração centralizada por etapa

Cada etapa tem seu próprio `*_config.py` em `src/core/`. Todos os parâmetros relevantes são ajustáveis em um único lugar sem tocar no código de produção.

### Logging estruturado

Todas as etapas usam o sistema de logging centralizado com timestamps, permitindo auditoria completa de cada execução em `logs/`.

### Offline-first

Modelos de embedding e reranking são baixados uma vez e servidos do cache local em `models/`. O pipeline completo roda sem internet após o setup inicial, atendendo à restrição do trabalho.

## Etapa 1 — Extração

### Por que Docling?

**Docling** foi escolhido como biblioteca de extração por ser a única ferramenta de código aberto que combina, em um único pipeline:

- Extração de texto com detecção de layout
- Reconhecimento de tabelas em formato matricial
- Exportação para Markdown estruturado com hierarquia de headers

Alternativas como `pdfplumber` e `pypdf` não oferecem detecção de hierarquia nem exportação de tabelas em formato matricial. Isso tornaria a recuperação de estrutura de seções e de conteúdo tabular significativamente mais difícil nas etapas seguintes.

### Por que CPU-only no extrator?

O extrator é configurado com `AcceleratorOptions(num_threads=4, device=AcceleratorDevice.CPU)`, sem dependência de GPU. Isso garante **reprodutibilidade em qualquer máquina** — incluindo a do professor no momento da avaliação.

### Por que processar em batches?

PDFs grandes carregados inteiramente na memória pelo Docling causam erro `std::bad_alloc`. A estratégia de **split-process-merge** via `pdf_splitter.py` (batches de 10 páginas) processa cada batch isoladamente e libera memória após cada conversão, tornando a ingestão viável em máquinas com RAM limitada.

### Por que separar tabelas em arquivos próprios?

Conteúdo tabular puro (`| col1 | col2 |`) tem baixa semântica quando misturado ao texto corrido. Separar cada tabela em `table_NNN.md` e `table_NNN.json` permite:

- Tratamento diferenciado no chunking (tabelas nunca são divididas)
- Enriquecimento com caption antes do embedding
- Filtros de parágrafos curtos não se aplicarem a células de tabela

## Etapa 2 — Preprocessamento

### Por que inferir hierarquia pelo prefixo numérico?

O Docling exporta todos os headers com o mesmo nível `#`, perdendo a hierarquia visual do PDF original. Para recuperá-la, o `SectionParser` infere o nível pelo padrão numérico do título:

- `3.` → nível 1
- `3.1` → nível 2
- `3.1.2` → nível 3

Isso garante que `["3. METODOLOGIA", "3.1 PROTOCOLO"]` seja preservado como hierarquia pai-filho corretamente, sem depender da formatação do PDF.

### Por que manter estado de seção entre páginas?

Quando uma seção começa na página 4 e o texto continua na página 5 sem novo header, a página 5 herda as seções ativas da página 4. Sem esse mecanismo, páginas do meio de seções longas ficariam sem contexto hierárquico — o que prejudicaria tanto o chunking quanto a citação de fontes.

### Por que quebrar por bloco de seção (em vez de por página)?

Em vez de um item por página, cada mudança de header gera um item distinto no array de conteúdo. Assim, uma página com três seções vira três itens com seções corretas. Isso é o que torna o chunking genuinamente section-aware: o chunker não precisa detectar seções — elas já estão resolvidas antes de chegar a ele.

### Por que o `analise_conjuntural` usa páginas como pseudo-seção?

Este documento não possui hierarquia de seções no Markdown extraído pelo Docling. Forçar detecção de seções inexistentes geraria contexto falso. O fallback para `"pagina_N"` como pseudo-seção preserva localização sem inventar estrutura — documentado no campo `has_sections: false` nos metadados para transparência.

### Por que aplicar filtros progressivos?

Chunks com zero valor semântico (headers sem conteúdo, capas, sumários, referências bibliográficas) poluem o índice vetorial e aumentam o risco de resultados irrelevantes no retrieval. Os filtros são progressivos e documentados para facilitar auditoria e ajuste.

### Por que não filtrar células de tabela como parágrafos curtos?

Células de tabela são naturalmente curtas e seriam incorretamente descartadas pelo filtro de `min_length`. Tabelas passam apenas por normalização Unicode e remoção de caracteres de controle.

## Etapa 3 — Chunking

### Por que recursive character splitting?

A estratégia tenta dividir pelo separador de maior granularidade primeiro (`\n\n`), regredindo para `\n` e depois espaço quando os pedaços ainda excedem o limite. Isso preserva parágrafos inteiros quando possível, quebrando apenas quando necessário — produzindo chunks semanticamente mais coesos do que divisão por contagem fixa de caracteres.

### Por que overlap de 32 tokens?

O overlap preserva contexto entre chunks consecutivos. Sem overlap, a última sentença de um chunk e a primeira do seguinte ficam sem o contexto uma da outra, prejudicando perguntas cujas respostas cruzam fronteiras de chunk.

### Por que tabelas nunca são divididas?

Uma tabela dividida ao meio perde o relacionamento entre cabeçalho e dados. O significado de uma célula depende de sua coluna. Por isso tabelas são sempre um chunk único — se excederem `max_table_tokens=512`, são truncadas com aviso no log (preferível a uma divisão que destrua a semântica).

### Por que contagem de tokens por `split()` (palavras)?

Contagem por tokenizador específico (ex: tiktoken, sentencepiece) exige download do tokenizador do modelo e introduz dependência extra. A contagem por palavras é uma aproximação com erro de ~15-20% em relação a tokenizadores reais — aceitável dado que os limites são configuráveis e a margem pode ser compensada com valores conservadores no `chunk_size`.

## Etapa 4 — Embedding

### Por que BGE-M3?

A escolha priorizou quatro critérios:

**Qualidade de recuperação** — o BGE-M3 foi treinado com multi-granularity retrieval, gerando embeddings densos com representações semânticas superiores para textos técnicos em português em comparação com alternativas como `paraphrase-multilingual-mpnet-base-v2`.

**Suporte a português técnico** — cobertura sólida de PT-BR adequada para textos técnicos governamentais e econômicos como os do corpus IPARDES.

**Operação offline** — o modelo é baixado automaticamente na primeira execução e armazenado em cache local. Execuções posteriores carregam do cache sem qualquer acesso à internet.

**Dimensão vetorial** — 1024 dimensões, oferecendo alta expressividade semântica para o domínio de recuperação de informação.

### Por que enriquecer o texto antes de codificar?

Prefixar o chunk com o breadcrumb de seções (`3. METODOLOGIA > 3.1 PROTOCOLO E REGISTRO`) melhora a recuperação de chunks em perguntas que mencionam temas de seções específicas sem usar as palavras exatas do texto do chunk. Para tabelas, incluir a caption antes do conteúdo Markdown resolve a baixa semântica do conteúdo tabular puro.

### Por que normalizar os embeddings?

`normalize_embeddings=True` garante que todos os vetores tenham norma unitária, tornando a métrica de distância `cosine` equivalente ao produto interno — computacionalmente mais eficiente e matematicamente adequada para busca por similaridade semântica.

## Etapa 5 — Indexação vetorial

### Por que ChromaDB e não FAISS?

**Recuperação de metadados nativa** — o ChromaDB retorna `document`, `page`, `sections`, `type` e `caption` junto com cada resultado de busca, sem cruzamento manual de índices. O pipeline RAG precisa desses metadados para montar a citação de fonte.

**Persistência automática em disco** — o `PersistentClient` persiste o índice em `data/vector_db/` sem configuração adicional.

**Sem infraestrutura adicional** — roda em processo Python puro via `pip install chromadb`, sem Docker, sem servidor separado.

Com FAISS, seria necessário manter um índice separado de metadados (ex: SQLite) e cruzar resultados manualmente — adicionando complexidade sem benefício para um corpus fixo de três documentos.

### Por que recriar a coleção a cada indexação?

Com um corpus fixo de três documentos, a recriação completa leva menos de 1 segundo. Recriar garante sincronização completa com o arquivo de embeddings sem lógica de diff ou upsert, eliminando uma classe inteira de bugs de inconsistência.

### Por que serializar seções como string com separador `>`?

O ChromaDB não aceita listas como valores de metadados. A serialização `["3. METODOLOGIA", "3.1 PROTOCOLO"] → "3. METODOLOGIA > 3.1 PROTOCOLO"` preserva a hierarquia de forma reversível com `.split(" > ")` — sem perda de informação e sem dependência de formato binário.

## Etapa 6 — Pipeline RAG

### Por que o reranker é da mesma família do embedder?

**`BAAI/bge-reranker-v2-m3`** (reranker) e **`BAAI/bge-m3`** (embedder) são treinados em conjunto pela BAAI, garantindo compatibilidade semântica entre as representações usadas nas duas etapas de recuperação. Um cross-encoder genérico poderia introduzir incompatibilidade entre o espaço semântico do retriever e o do reranker.

### Por que usar dois estágios (retriever + reranker)?

O bi-encoder (retriever) gera embeddings de query e chunk **separadamente** — rápido, mas menos preciso. O cross-encoder (reranker) recebe query e chunk **juntos** — mais preciso, porém mais lento, pois requer uma passagem do modelo para cada par. A solução de dois estágios usa o retriever para filtrar rapidamente 15 candidatos do corpus inteiro, e o reranker para reordenar apenas esses 15 com alta precisão.

### Por que `top_k=15` no retriever?

Recuperar mais candidatos do que o necessário (`reranker_top_k=5`) dá ao reranker candidatos suficientes para reordenar com precisão. Um `top_k` muito baixo arrisca descartar o chunk correto antes do reranking; muito alto aumenta a latência do reranker.

### Por que threshold de similaridade `0.35`?

Perguntas fora do escopo dos documentos ainda retornam chunks — os mais similares ao que existe no índice. O threshold garante que apenas chunks com similaridade mínima real sejam considerados. Abaixo de `0.35`, o sistema considera a query fora do escopo e instrui o LLM a recusar sem inventar.

### Por que llama3.2:3b?

- Modelo leve e eficiente, viável em hardware com recursos limitados sem GPU dedicada
- Suporte nativo a instruções via Ollama, sem configuração adicional
- Dentro do limite de 9,9B parâmetros exigido pelo enunciado

Para uso em hardware mais robusto, `qwen2.5:7b` também é suportado via configuração e tende a seguir instruções com maior consistência em português técnico.

### Por que fornecer o formato de citação pronto no prompt?

Em vez de instruir o modelo a deduzir como citar, o `PromptBuilder` injeta o formato exato diretamente no contexto:

```
[Citar como: (Análise Conjuntural, p. 12, Seção: pagina_12)]
```

Fornecer o formato pronto reduz significativamente casos de citações ausentes ou mal formatadas em modelos pequenos, que tendem a ignorar instruções de formatação complexas quando o contexto é longo.

### Por que temperatura `0.1`?

Temperatura baixa produz respostas mais determinísticas e factuais, reduzindo variação aleatória que poderia introduzir informações não presentes nos chunks recuperados. Para um sistema RAG onde fidelidade ao documento é o critério central de avaliação, criatividade é indesejável.

### Por que duas saídas obrigatórias por query?

O enunciado do trabalho exige explicitamente que o prompt enriquecido e os trechos utilizados sejam exibidos separadamente da resposta final, para fins de avaliação. A separação em **Saída 1 (auditoria)** e **Saída 2 (resposta final)** atende a esse requisito e é igualmente útil para diagnóstico de falhas de retrieval em produção.

## Etapa 7 — Testes de qualidade do RAG

### Por que usar retrieval precision como métrica principal?

A qualidade de um sistema RAG depende fundamentalmente de duas coisas: recuperar os chunks certos e gerar uma resposta fiel a eles. O segundo depende inteiramente do primeiro — um LLM não pode responder corretamente com base em chunks errados, por melhor que seja o prompt. Por isso, **retrieval precision é a métrica de maior impacto** para o sistema como um todo.

Medir qualidade pelo texto gerado seria instável: o mesmo conjunto de chunks pode produzir respostas diferentes entre execuções, entre modelos e até entre temperaturas diferentes. Medir pelo retrieval é determinístico — dado o mesmo índice e o mesmo modelo de embedding, a mesma query sempre retorna os mesmos chunks.

### Por que não usar o LLM nos testes de qualidade?

Três razões práticas e uma técnica:

**Praticidade** — os testes de qualidade precisam rodar sem infraestrutura extra. Exigir Ollama rodando em segundo plano tornaria os testes frágeis em ambientes de CI ou em máquinas sem o modelo instalado.

**Velocidade** — uma chamada ao LLM leva entre 30 e 120 segundos dependendo do hardware. Com 8 queries no ground truth e múltiplas execuções durante o desenvolvimento, o custo se torna proibitivo.

**Determinismo** — mesmo com `temperature=0.1`, o LLM pode variar a formulação da resposta entre execuções. Um teste que verifica se "3.857" aparece na resposta pode falhar se o modelo escrever "R$ 3 mil e 857 reais" numa execução específica. O retrieval não tem esse problema.

**Separação de responsabilidades** — se um teste de qualidade que envolve o LLM falha, não é possível saber imediatamente se o problema está no retrieval, no prompt ou na geração. Testar o retriever isoladamente localiza o problema com precisão.

### Por que Document Hit@K, Keyword Hit@K e Page Hit@K?

Cada métrica avalia uma dimensão diferente da qualidade:

**Document Hit@K** — mede se o documento correto aparece entre os top-K resultados. Falha aqui indica que o embedder não está separando bem os três documentos semanticamente, ou que o índice está corrompido.

**Keyword Hit@K** — mede se o conteúdo com a resposta correta aparece nos chunks recuperados. É a métrica mais diretamente ligada à qualidade da resposta final: se as keywords não estão nos chunks, o LLM não tem como responder corretamente, independente de quão bom seja o prompt.

**Page Hit@K** — mede se a página correta aparece nos resultados, validando a rastreabilidade das citações. Tem threshold menor que as outras duas porque a mesma informação pode aparecer em chunks de páginas adjacentes — a informação está presente mesmo que a página exata não coincida.

### Por que testar out-of-scope pelo threshold de similaridade e não pela resposta do LLM?

O comportamento de recusa do sistema em produção depende do threshold: se nenhum chunk supera `min_similarity=0.35`, o pipeline marca a query como fora do escopo e o LLM recebe um prompt de recusa. O teste valida **exatamente esse mecanismo** — verifica que as queries fora do escopo têm similaridade bruta abaixo do threshold, garantindo que a recusa acontece na camada de retrieval e não depende do LLM interpretar corretamente uma instrução de prompt.

Isso é importante porque instruções de prompt podem ser ignoradas por modelos pequenos. A garantia técnica de recusa deve estar no retrieval, não no prompt.