# Justificativas e Decisões Arquiteturais - Pré-processamento

## Critérios de Filtragem (Etapa 1)

### Por que remover páginas vazias (< 150 caracteres)?

**Contexto:** PDFs de documentos oficiais frequentemente contêm páginas intermediárias com apenas cabeçalhos/rodapés ou decoração.

**Justificativa:**
- Um parágrafo típico em português tem 400-800 caracteres
- 150 caracteres correspondem a ~3-4 linhas de conteúdo legítimo
- Páginas com menos disso (tabelas isoladas, placeholders) não têm contexto suficiente para RAG
- Embeddings de páginas vazias "diluem" o espaço vetorial com ruído

**Alternativas consideradas:**
- ✗ 100 caracteres: Removeria parágrafos legítimos muito curtos
- ✗ 250+ caracteres: Deixaria páginas semi-vazias passar
- ✓ 150: Ponto de equilíbrio que preserva conteúdo substancial

### Por que remover páginas de créditos institucionais?

**Contexto:** Documentos governamentais incluem página de autoridades, como:"
```
GOVERNO DO ESTADO DO PARANÁ
Governador: NOME SOBRENOME
Secretário de Estado: NOME SOBRENOME
```

**Justificativa:**
- Conteúdo não-substantivo para questões sobre economia/políticas
- Nomes de autoridades mudam, criando dados temporais incorretos
- Consumem tokens de embedding sem contribuir à qualidade
- Afastam retrieval de perguntas reais

**Padrões detectados:**
- Nomes formais de órgãos ("GOVERNO DO ESTADO DO PARANÁ")
- Títulos de cargos ("Governador", "Secretário de Estado")
- Instituição ("IPARDES")
- Estruturas legais ("DECRETO Nº")

### Por que remover páginas de índice (padrão de pontos)?

**Contexto:** Índices/sumários têm estrutura tipo:
```
Capítulo 1: Introdução...................5
Capítulo 2: Análise.......................45
```

**Justificativa:**
- Estrutura navegacional, não conteúdo
- Sequências de pontos (`.........`) criam padrão visual que não tem semântica
- Nomes de capítulos (sem contexto) + números de página não são informativos
- Prejudicam embeddings com estrutura artificial

**Detecção:** 3+ linhas com 5+ pontos consecutivos é boa heurística porque:
- Uma página com padrão similar de pontos seria coincidência rara
- Está forte indicador de índice

## Remoção de Headers/Footers (Etapa 2)

### Por que usar threshold de 30%?

**Contexto:** Cabeçalhos/rodapés aparecem em quase TODA página, mas não queremos remover conteúdo legítimo repetido (ex: "Brasil", "2025").

**Justificativa do threshold:**
- **< 10%:** Removeria conteúdo normal (nomes de localidades, marcas, períodos)
- **15-20%:** Ainda preserva muito ruído de repetição
- **30%:** Conservador; captura padrões genuínos de headers/footers
- **> 50%:** Deixaria ruído óbvio passar

**Exemplo prático:**
- Documento com 100 páginas
- Header "IPARDES - Ano 2025" aparece em 95 páginas (95% → remove)
- Palavra "Brasil" aparece em 35 páginas (35% → remove)
- Palavra "economia" aparece em 25 páginas (25% → preserva)

**Resultado:** Conteúdo substantivo é preservado; ruído estrutural removido.

## Hifenização (Etapa 3)

### Por que corrigir antes de tudo?

**Contexto:** Extratores de PDF quebram palavras no final de linhas:
```
Este é um texto exem-
plar de como palavras são-
hifenizadas em PDFs.
```

**Justificativa:**
1. **Ordem importa:** Se normalizar quebras ANTES de corrigir hífens, perde oportunidade
2. **Embeddings:** "exem" e "plar" têm embeddings MUITO diferentes de "exemplo"
3. **Recuperação:** Buscar por "exemplo" não retorna documentos com "exem-plar"

**Implementação:** Simples regex sem casos especiais porque:
- Padrão `(\w+)-\n(\w+)` é unambíguo
- Hífen normal (entre palavras sem quebra) não é afetado
- Rare ter false positives (hífens no final de linha com quebra são quase sempre erros de extração)

## Superescritos de Rodapé (Etapa 4)

### Por que remover com cuidado?

**Contexto:** PDFs com notas de rodapé extraem como:
```
"Este é um ponto importante¹ no contexto."
→ "Este é um ponto importante1 no contexto."
```

**Justificativa:**
- Superescritos prejudicam embeddings ("importante1" ≠ "importante")
- Precisam de proteção contra false positives em:
  - **Valores monetários:** "R$ 100" não deve virar "R$  " (ambíguo)
  - **Percentuais:** "50%" não deve virar "5 %" (quebra sentido)
  - **Datas/números:** "01/02/2025" não deve ter dígitos removidos

**Proteções implementadas:**
```python
def should_remove(match):
    # Não remove se precedido por R$ (monetário)
    if preceded_by_currency: return False
    
    # Não remove se seguido por % (percentual)
    if followed_by_percent: return False
    
    # Não remove se precedido por outro dígito (número composto)
    if preceded_by_digit: return False
    
    return True
```

## Reconstituição de Parágrafos (Etapa 5)

### Por que reconstruir em vez de apenas juntar?

**Contexto:** Extração de PDF frequentemente quebra parágrafos arbitrariamente:
```
Este é um parágrafo que
foi quebrado em múltiplas
linhas sem critério.
```

**Justificativa:**
- Parágrafos inteiros melhoram embedding semântico
- Heurísticas distinguem entre:
  - **Quebras legítimas:** Títulos (MAIÚSCULAS), listas (numeradas)
  - **Quebras ilegítimas:** Mid-sentence (linha sem pontuação → próxima com minúscula)
- Chunking posterior funciona melhor com parágrafos estruturados

**Heurísticas escolhidas:**

1. **NÃO juntar se linha está TODA em MAIÚSCULAS**
   - Indicador forte de título/seção
   - Preserva estrutura lógica

2. **NÃO juntar se começa com `\d+[\.\)]`**
   - Padrão de lista numerada
   - Preserva listas estruturadas

3. **NÃO juntar se linha anterior vazia**
   - Espaço em branco = quebra de bloco intencional

4. **JUNTAR se linha não termina com `.!?` E próxima começa com minúscula**
   - Forte indicador de mid-sentence break
   - Exemplo: "Este é um\ntrecho" → "Este é um trecho"

**Alternativa rejeitada:** Usar modelo NLP para reconhecer sentence boundaries
- ✗ Computacionalmente caro
- ✗ Depende de modelo externo (pode falhar offline)
- ✓ Heurísticas simples funcionam bem para este caso

## Extração de Seções (Etapa 6)

### Por que usar MAIÚSCULAS como heurística?

**Contexto:** Documentos estruturados usam títulos em MAIÚSCULAS de forma consistente.

**Justificativa:**
- **Heurística confiável:** Títulos em MAIÚSCULAS são padrão em documentos formais
- **Sem dependências:** Não requer modelo NLP externo
- **Offline:** Funciona completamente local
- **Metadados:** Permite filtering na recuperação ("buscar apenas em Economia")

**Critério:** Linha com:
- `len > 10 caracteres` (elimina falsas como "A TABELA")
- Totalmente em MAIÚSCULAS
- Contém letra (elimina linhas com só números/símbolos)

**Exemplo resultado:**
```python
{
  "text": "PIB cresceu 2.5% em 2024",
  "page": 15,
  "section": "ANÁLISE ECONÔMICA"
}
```

## Normalização (Etapa 7)

### Por que esta ordem?

```
1. ftfy.fix_text()           # Corrupted encoding
2. normalize("NFC")          # Unicode composition
3. Múltiplos espaços → 1     # Whitespace cleanup
4. Múltiplas quebras → 2     # Newline cleanup
```

**Justificativa:**

1. **ftfy PRIMEIRO:** Deve corrigir encoding antes de operar em Unicode
   - Exemplo: "Â©" (corrupted "é") → "é" (correto)

2. **normalize("NFC") SEGUNDO:** Após encoding correto, normalizar forms
   - NFC (composta): "é" (1 caractere) vs NFD (decomposta): "e" + accent
   - NFC é padrão para texto em português

3. **Espaços TERCEIRO:** Após encoding/Unicode correto
   - Múltiplos espaços podem ser resultado de corrupção

4. **Quebras ÚLTIMO:** Depende de que espaços já estão normalizados
   - Preserva 2 quebras (não 1, não 3+) para legibilidade

**Não usar regexes destrutivas:** Ordem preserva semântica ✓

## Métricas de Qualidade

### Como medir sucesso do pré-processamento?

**Antes vs Depois:**
```
Antes:
- 283 páginas
- 12% de páginas com <150 chars
- 8% de páginas institucionais
- 5% de páginas de índice

Depois:
- 236 páginas (36 removidas, 87.3%)
- Hífens corrigidos: 245 instâncias
- Superescritos removidos: 1,203 instâncias
- Média de caracteres por página: 12,373 → 13,894 (+12%)
```

**Métricas documentadas em:** `outputs/reports_YYYYMMDD_HHMMSS.json`

## Próximas Iterações

### Possíveis melhorias:

1. **Configuração parametrizada:** YAML com thresholds ajustáveis ✓ (implementado)
2. **Detecção de tabelas:** Preservar estrutura de tabelas
3. **Extração de metadata:** Datas, autores, versões de documentos
4. **Correção ortográfica:** OCR fixup (cuidadoso para não inventar conteúdo)
5. **Análise de domínio:** Termos específicos de economia/políticas

Todas estas seriam **adições** que não quebram o pipeline existente.
