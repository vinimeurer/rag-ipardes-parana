# Justificativas de Decisões Arquiteturais e Tecnológicas

## Visão Geral

Este documento centraliza todas as justificativas das escolhas feitas no projeto RAG IPARDES Paraná, facilitando a compreensão das decisões técnicas e suas razões.

---

## 1. Extração de PDFs

### Tecnologia: pdfplumber 0.10.3

**Justificativa:**
- **Robustez para português**: pdfplumber é particularmente robusto para processar textos em português, com melhor suporte a caracteres acentuados e layout complexo
- **Manutenção de layout e tabelas**: Preserva a estrutura do documento e pode extrair tabelas de forma estruturada
- **Open-source**: Alternativa confiável sem dependências comerciais
- **Alternativa desconsiderada**: PyMuPDF (fitz) também é bom, mas pdfplumber é mais amigável para uso geral

**Referência no código:** `src/ingestion/pdf_extractor.py`

---

## 2. Centralização de Configuração

### Arquivo: src/core/constants.py

**Justificativa:**
- **Single source of truth**: Centralizar URLs e paths em um único local facilita manutenção
- **Transparência**: Torna fácil entender exatamente quais PDFs serão processados e onde
- **Reutilização**: Evita repetição de constantes em múltiplos módulos
- **Configuração explícita**: Todas as decisões estão documentadas inline

**Benefício:** Mudanças futuras (novos PDFs, novos modelos) exigem apenas alteração neste arquivo

---

## 3. Chunking de Documentos

### Configuração: DEFAULT_CHUNK_SIZE = 512 tokens, DEFAULT_CHUNK_OVERLAP = 0.20

**Justificativa:**
- **512 tokens = compromisso efetivo**: Nem muito pequeno (mantém contexto semântico), nem muito grande (controlável em retrieval)
- **Específico para português**: Português é uma língua mais verbosa que inglês, 512 tokens é apropriado
- **Compatibilidade com LLM**: Trabalha bem com modelos ≤ 9.9B parâmetros (constrição do projeto)
- **20% overlap**: Garante continuidade semântica entre chunks consecutivos, evita cortes no meio de sentimentos

**Cálculo:** 512 tokens ≈ 2000-2500 caracteres em português, tamanho gerenciável para RAG

**Referência:** `src/core/constants.py` - Seção "Chunking Configuration Defaults"

---

## 4. Modelo de Embeddings

### Escolha: intfloat/multilingual-e5-large (1024 dimensões)

**Justificativa:**
- **Multilíngue**: Suporta português nativamente com qualidade comparável ao English
- **Open-source**: Sem custos de API, funciona offline
- **Dimensionalidade**: 1024 dimensões é um bom balance entre:
  - **Expressividade**: Captura nuances semânticas bem
  - **Performance**: Não sobrecarrega FAISS para 3 documentos pequenos
  - **Memória**: Razoável para executar em máquinas com recursos limitados
- **Modelo específico**: Treinado especificamente para semantic search (não um modelo de linguagem genérico)

**Batch size de 32:** Otimização para speed sem sobrecarregar memória

**Referência:** `src/core/constants.py` - Seção "Embedding Configuration"

---

## 5. Vector Store: FAISS vs Alternativas

### Escolha: FAISS (Facebook AI Similarity Search)

**Justificativa:**
- **Dataset pequeno**: 3 PDFs com ~150 páginas totais
- **Eficiência**: FAISS é mais eficiente que HNSW (Hierarchical Navigable Small World) para datasets pequenos
- **Simplicidade**: Implementação simples, sem servidor externo necessário
- **Offline**: Funciona completamente offline, alinhado com restrições do projeto
- **Alternativas desconsideradas**:
  - Qdrant: Overkill para 3 PDFs, complexidade desnecessária
  - Weaviate: Também é overkill, necessita mais infraestrutura
  - Memória pura: Sem persistência, pior para produção

**Nota:** Se escalar para muitos documentos (>10K), considerar Qdrant ou Milvus

**Referência:** `src/core/constants.py` - Seção "Vector Store Configuration"

---

## 6. Recuperação (Retrieval)

### Configuração: top_k=5, similarity_threshold=0.4, use_reranking=True, use_mmr=True

**Justificativa de cada parâmetro:**

- **top_k=5**: Recupera 5 documentos mais similares
  - Suficiente para RAG com 3 PDFs pequenos
  - Evita "noise" de documentos marginalmente relevantes
  - Cabe confortavelmente no context window do LLM

- **similarity_threshold=0.4**: Filtra resultados com similaridade < 0.4
  - Evita recuperar documentos completamente irrelevantes
  - 0.4 é um bom ponto de corte para português (nem muito relaxado, nem muito restritivo)
  - Segurança contra "hallucinations" baseadas em contexto fraco

- **use_reranking=True**: Usa cross-encoder para reordenar resultados
  - Melhora relevância significativamente após retrieval inicial
  - Compensação: custo computacional adicional (aceitável para 5 documentos)

- **use_mmr=True**: Usa Maximal Marginal Relevance
  - Recupera documentos relevantes E diversos
  - Evita que todos os 5 resultados sejam muito similares entre si
  - Melhora cobertura da resposta

**Referência:** `src/core/constants.py` - Seção "Retrieval Configuration"

---

## 7. Modelo de Linguagem (LLM)

### Escolha: Mistral 7B Instruct Q4

**Justificativa:**
- **Tamanho**: 7B parâmetros (< 9.9B, atende restrição do projeto)
- **Qualidade**: Mistral 7B é o melhor modelo 7B disponível (benchmarks)
- **Português**: Suporte decente para português (treinado em dataset multilíngue)
- **Quantização Q4**: Versão 4-bit reduz memória para ~3.5GB (viável em laptops)
- **Open-source**: Apache 2.0, funciona completamente offline
- **Instruct-tuned**: Otimizado para seguir instruções, não precisa de prompt engineering complexo

### Contexto e Temperatura

- **context_window=4096**: Suporta bem os chunks (512 tokens) + prompt + histórico
- **temperature=0.1**: Muito baixa (respostas factuais/determinísticas)
  - Justificativa: RAG deve ser preciso e consistente, não criativo
  - Reduz "hallucinations"

- **max_tokens=500**: Respostas não muito longas (suficiente para resumos)
- **top_p=0.95**: Nucleus sampling conservador (compatível com temperatura baixa)

**Alternativas desconsideradas:**
- Llama 2 7B: Qualidade ligeiramente inferior, sem instruct-tuning
- Orca 7B: Histórico de problemas com português
- Modelos 13B+: Excedem limite de 9.9B parâmetros

**Referência:** `src/core/constants.py` - Seção "LLM Configuration"

---

## 8. Pré-processamento

### Configuração: Stopwords e Lemmatização DESATIVADOS

**Justificativa:**
- **Português é complexo**: Português tem muitos stopwords e variações morfológicas
- **Abordagem conservadora**: Melhor remover stopwords seletivamente após análise do domínio
- **RAG já filtra**: Vector similarity já faz filtragem básica, não precisa de agressividade adicional
- **Preservação de significado**: Remover stopwords indiscriminadamente pode perder contexto importante

**Por que não lemmatizar/stemmar?**
- Pdfplumber já extrai texto bem estruturado
- Lemmatização em português é complexa (não temos morphological analyzer confiável)
- Modelo de embedding já captura similaridade semântica sem precisar normalizar morfologia

**Abordagem futura**: Fazer análise de frequência de termos primeiro, depois decidir

**Referência:** `src/core/constants.py` - Seção "Preprocessing Configuration"

---

## 9. Sistema de Logging

### Arquivo: src/core/logger.py

**Justificativa:**
- **Centralizado**: Todos os módulos usam `setup_logger(__name__)`
- **Consistente**: Mesmo formato em todos os logs (timestamp, módulo, level, mensagem)
- **Dual output**: Console (desenvolvimento) + arquivo com timestamp (produção)
- **Rastreabilidade**: Cada script cria arquivo de log independente: `ingest_YYYYMMDD_HHMMSS.log`

**Benefício:** Debugging facilitado, rastreamento de problemas em produção

**Referência:** `src/core/logger.py`, importado por todos os módulos

---

## 10. Exceções Customizadas

### Arquivo: src/core/exceptions.py

**Justificativa:**
- **Especificidade**: 11 tipos diferentes de exceção para cada etapa do pipeline
- **Tratamento robusto**: Cada módulo pode capturar erros específicos do seu domínio
- **Debugging**: Mensagens de erro claras indicam exatamente onde falhou
- **Separação de concerns**: Exceção diferente para cada tipo de falha

**Exemplo:** `PDFExtractionError` vs `ChunkingError` vs `EmbeddingError` vs `NoRelevantDocumentsError`

**Referência:** `src/core/exceptions.py`

---

## 11. Schemas com Pydantic

### Arquivo: src/schemas/extraction.py

**Justificativa:**
- **Validação automática**: Pydantic valida tipos e restrições
- **Documentação**: Fields têm descriptions automáticas (usado em OpenAPI/FastAPI)
- **JSON Schema**: Facilita integração com frontend e APIs
- **Type safety**: Catch de erros em tempo de desenvolvimento

**Exemplo:**
```python
class PageData(BaseModel):
    page: int = Field(..., ge=1)  # Valida automaticamente >= 1
    text: str                      # Valida que é string
    has_tables: bool               # Valida que é booleano
```

**Referência:** `src/schemas/extraction.py`

---

## 12. Estrutura de Diretórios

### Padrão: Domínio-based (Structure 3)

**Justificativa:**
- **Modularidade**: core/, ingestion/, preprocessing/, vectorization/, retrieval/, prompting/, llm/, api/
- **Escalabilidade**: Novo módulo = novo diretório, sem conflito com existentes
- **Clareza**: Fica óbvio onde cada funcionalidade vive
- **Padrão da indústria**: Usado por MLflow, spaCy, Hugging Face, etc.

**Alternativas desconsideradas:**
- Estrutura 1 (por tipo): core/, models/, pipelines/ - menos modular
- Estrutura 2 (por etapa): extraction/, processing/, embedding/ - menos escalável

**Referência:** PROGRESS.md, Structure and Example

---

## 13. Tecnologias Complementares

### FastAPI + Uvicorn + Pydantic

**Justificativa:**
- **FastAPI**: Framework REST moderno, automático OpenAPI, performance
- **Uvicorn**: ASGI server assíncrono, melhor que flask para múltiplas requisições
- **Pydantic 2.4.2**: Validação automática, documentação, performance otimizada

**Versões locked:** requirements.txt garante reprodutibilidade

---

## 14. Testes Automatizados

### Arquivo: scripts/test_extraction.py

**Justificativa:**
- **6 testes per PDF**: Verifica arquivo, JSON válido, estrutura, sucesso, dados, schema
- **Rápido**: Roda em < 1 segundo
- **Confiável**: Detecta problemas antes de passar para próxima fase
- **Documentado**: Cada teste tem mensagem clara do que verifica

**Antes de executar scripts upstream**, sempre rodar:
```bash
python scripts/test_extraction.py
```

**Referência:** `scripts/test_extraction.py`

---

## 15. CI/CD e Qualidade de Código

### Ferramentas: Black, Flake8, Pytest

**Justificativa:**
- **Black**: Formata código automaticamente (sem discussões sobre estilo)
- **Flake8**: Detecta problemas de qualidade (imports não usados, linhas longas, etc)
- **Pytest**: Framework de testes padrão em Python

**Makefile simplifica:**
```bash
make format   # Black
make lint     # Flake8
make test     # Pytest
```

---

## Resumo de Decisões-chave

| Decisão | Escolha | Razão |
|---------|---------|-------|
| PDF Extraction | pdfplumber | Robusto para português |
| Chunking | 512 tokens, 20% overlap | Bom balance para português |
| Embeddings | multilingual-e5-large | Open-source, multilíngue |
| Vector Store | FAISS | Eficiente para 3 PDFs |
| LLM | Mistral 7B Q4 | Melhor 7B, < 9.9B limit |
| Preprocessing | Desativado | Português complexo, melhor análise depois |
| Logging | Centralizado | Rastreabilidade consistente |
| Exceptions | Customizadas | Debugging específico |
| Estrutura | Domínio-based | Modular e escalável |
| API | FastAPI | Moderno, performance |

---

## Como Usar Este Documento

1. **Para entender uma decisão**: Procure pelo número/título correspondente
2. **Para comparar alternativas**: Veja seção de "Alternativas desconsideradas"
3. **Para referência de código**: Cada seção cita exatamente qual arquivo/função implementa
4. **Para discutir mudanças**: Use este documento como base para argumentação

**Último atualizado:** 29 de abril de 2026
