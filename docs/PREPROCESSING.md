# Pré-processamento de Documentos para RAG

## Visão Geral

Este módulo implementa um pipeline completo de pré-processamento de documentos PDF extraídos, preparando os dados para vetorização e recuperação em um sistema RAG offline e open source.

## Arquitetura

O pipeline segue uma arquitetura modular com 7 etapas sequenciais:

```
JSON Extraído → [1] Filtro → [2] Headers/Footers → [3] Hifenização 
  → [4] Rodapés → [5] Parágrafos → [6] Seções → [7] Normalização
  → JSON Processado
```

Cada etapa é implementada em um módulo separado (`src/preprocessing/`), facilitando testes e manutenção.

## Etapas do Pipeline

### Etapa 1: Filtragem de Páginas Irrelevantes

**Arquivo:** `filters.py`

Função: `filter_pages(pages: list[dict]) -> tuple[list[dict], dict]`

Remove páginas que não contribuem para a qualidade do RAG segundo três critérios:

#### Critério A: Páginas Vazias
- **Justificativa:** Páginas com muito pouco conteúdo útil não agregam informação e apenas diluem os embeddings do vetor de recuperação.
- **Implementação:** Remove páginas com menos de 150 caracteres úteis (após `strip()`).

#### Critério B: Páginas de Créditos Institucionais
- **Justificativa:** Nomes de autoridades, secretários e estrutura governamental não são relevantes para as perguntas que o RAG precisa responder sobre economia e políticas públicas.
- **Implementação:** Detecta padrões como "GOVERNO DO ESTADO DO PARANÁ", "Governador", "Secretário de Estado", "Vice-Governador", "IPARDES".

#### Critério C: Páginas de Sumário/Índice
- **Justificativa:** Índices e sumários são estruturas de navegação, não conteúdo substantivo. Seu padrão visual (muitos pontos) não é adequado para embeddings.
- **Implementação:** Detecta 3+ linhas contendo 5+ pontos consecutivos (padrão `\.{5,}`).

**Retorno:** Relatório com contagem de páginas removidas por cada critério.

### Etapa 2: Remoção de Cabeçalhos e Rodapés Repetidos

**Arquivo:** `header_footer_remover.py`

Funções:
- `identify_repeated_lines(pages, threshold=0.3) -> dict`
- `remove_repeated_lines(pages, repeated_lines_per_doc) -> tuple`

**Justificativa:** Cabeçalhos e rodapés repetem conteúdo não-informativo em muitas páginas, criando ruído para embeddings. O threshold de 30% é conservador (exige que a linha apareça em >30% das páginas do documento) para evitar remover conteúdo legítimo repetido.

**Processo:**
1. Para cada documento, conta ocorrências de cada linha em páginas distintas
2. Identifica linhas que aparecem em >30% das páginas
3. Remove essas linhas de todas as ocorrências
4. Gera relatório de linhas removidas por documento

### Etapa 3: Correção de Hifenização

**Arquivo:** `hyphenation_fixer.py`

Função: `fix_hyphenation(text: str) -> str`

**Justificativa:** Hifenização no final de linha é comum em PDFs extraídos. Palavras quebradas prejudicam tanto a qualidade semântica do embedding quanto a legibilidade e precisão de termos-chave.

**Implementação:** Detecta padrão regex `(\w+)-\n(\w+)` e substitui por `\1\2` (une as partes).

**Ordem importante:** Esta etapa é executada ANTES de qualquer outra manipulação de `\n`, pois afeta a estrutura de quebras de linha.

### Etapa 4: Remoção de Superescritos de Notas de Rodapé

**Arquivo:** `footnote_handler.py`

Função: `remove_footnote_superscripts(text: str) -> str`

**Justificativa:** Números superescritos (notas de rodapé) no texto extraído prejudicam a semântica. Exemplos: "palavra1 seguinte" (1 é superscrito, não dígito).

**Padrão regex:** `(?<=\w)(\d{1,2})(?=[\s,\.;])`

**Proteções (não remove se):**
- Precedido por espaço e "R" (parte de "R$" para valores monetários)
- Seguido por "%" (percentuais)
- Precedido por outro dígito (datas ou números compostos)

### Etapa 5: Reconstituição de Parágrafos

**Arquivo:** `paragraph_reconstructor.py`

Função: `reconstruct_paragraphs(text: str) -> str`

**Justificativa:** PDFs com extração problemática quebram parágrafos em múltiplas linhas sem padrão claro. Reconstruir parágrafos melhora a coesão semântica para chunking posterior.

**Heurísticas de Junção:**
- NÃO juntar se:
  - Linha em branco separa blocos
  - Linha está toda em MAIÚSCULAS (título/subtítulo)
  - Linha começa com `\d+[\.\)]` (item de lista numerada)
- JUNTAR se:
  - Linha atual não termina com `.`, `!` ou `?`
  - Próxima linha começa com letra minúscula

**Substituição:** Quebra de linha `\n` é substituída por espaço simples ` `.

### Etapa 6: Extração de Metadados de Seção

**Arquivo:** `section_extractor.py`

Função: `extract_sections(pages: list[dict]) -> list[dict]`

**Justificativa:** Contexto de qual seção/capítulo o parágrafo pertence é crucial para RAG. Permite filtros de metadados ("buscar apenas em Economia") e melhora relevância de chunks.

**Lógica:**
1. Varre páginas em ordem sequencial
2. Quando encontra linha com:
   - Comprimento > 10 caracteres
   - Totalmente em MAIÚSCULAS
   - Contém pelo menos uma letra
3. Registra como `secao_atual` e propaga para todas as páginas seguintes até novo título
4. Adiciona campo `"section"` em cada página

### Etapa 7: Normalização de Texto

**Arquivo:** `normalizer.py`

Função: `normalize_text(text: str) -> str`

**Ordem de aplicação (crítica):**

1. **ftfy.fix_text()**: Corrige encoding corrupto (HTML entities, caracteres misalinhados)
2. **unicodedata.normalize("NFC", text)**: Normalização Unicode para forma NFC (composta)
3. **Múltiplos espaços → um espaço**: `\s{2,}` → ` ` (evita espaços em branco soltos)
4. **Múltiplas quebras → duas quebras**: `\n{3,}` → `\n\n` (preserva separação sem excesso)

## Estrutura de Dados

### Entrada
```json
{
  "success": true,
  "pdf_key": "desenvolvimento_paranaense",
  "pages_extracted": 211,
  "total_pages": 211,
  "data": [
    {
      "page": 1,
      "text": "...",
      "document": "desenvolvimento_paranaense",
      "has_tables": false,
      "extracted_at": "2026-05-05T10:30:00"
    },
    ...
  ],
  "extraction_time": 45.2
}
```

### Saída
```json
{
  "processed_at": "20260505_103045",
  "total_pages": 198,
  "statistics": {
    "total_pages": 198,
    "total_characters": 2450000,
    "avg_characters_per_page": 12373.74,
    "documents": ["analise_conjuntural", "avaliacoes_politicas", "desenvolvimento_paranaense"],
    "sections_found": ["INTRODUÇÃO", "CONTEXTO ECONÔMICO", ...],
    "num_documents": 3,
    "num_sections": 24
  },
  "data": [
    {
      "page": 1,
      "text": "...",
      "document": "desenvolvimento_paranaense",
      "has_tables": false,
      "extracted_at": "2026-05-05T10:30:00",
      "section": "INTRODUÇÃO"
    },
    ...
  ]
}
```

## Uso

### Como Script Standalone

```bash
python scripts/preprocess.py
```

Processa os três JSONs em `data/extracted/` e salva em `data/processed/`.

### Como Módulo Python

```python
from src.preprocessing.pipeline import PreprocessingPipeline

pipeline = PreprocessingPipeline(output_dir="data/processed")
result = pipeline.process([
    "data/extracted/analise_conjuntural.json",
    "data/extracted/avaliacoes_politicas.json",
    "data/extracted/desenvolvimento_paranaense.json",
])

output_file, reports_file = pipeline.save_processed(result)
```

## Testes

Executar testes unitários:

```bash
python -m pytest tests/test_preprocessing.py -v
```

Cobertura de testes:
- Filtros (vazias, institucionais, índices)
- Hifenização (simples, múltiplas, preservação)
- Superescritos de rodapé (remoção, proteções)
- Reconstituição de parágrafos (junção, separadores)
- Normalização (espaços, quebras, Unicode)

## Decisões de Design

### Por que modularização?
Facilita testes isolados, reutilização e debugging de etapas específicas.

### Por que 7 etapas separadas?
Cada etapa endereça um problema específico do PDF extraído. Ordem importa (ex: hifenização antes de normalizando quebras).

### Por que 30% threshold para headers/footers?
- <20%: Removeria conteúdo legítimo repetido
- 30%: Conservador mas eficaz para remover cabeçalhos/rodapés
- >50%: Deixaria ruído passar

### Por que 150 caracteres para páginas vazias?
- <100: Removeria parágrafos legítimos
- 150: Corresponde a ~3-4 linhas de conteúdo mínimo útil
- >200: Deixaria páginas muito vazias passar

## Próximas Etapas

Dados processados alimentam:
1. **Chunking** (`src/vectorization/chunker.py`): Divide texto em chunks semânticos
2. **Embeddings** (`src/vectorization/embedding_model.py`): Vetoriza chunks
3. **Vector Store** (`src/vectorization/vector_store.py`): Indexa para recuperação
