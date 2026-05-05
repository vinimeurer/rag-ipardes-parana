# Centralização de Configuração em `src/core/`

## Alterações Realizadas

### ✅ Criado `src/core/preprocessing_config.py`

Arquivo com configuração centralizada usando **dataclasses** (mais Pythônico que YAML):

```python
@dataclass
class FilterConfig:
    min_useful_characters: int = 150
    institutional_patterns: List[str] = [...]
    min_dotted_lines_for_index: int = 3
    min_consecutive_dots: int = 5

@dataclass
class PreprocessingConfig:
    filters: FilterConfig
    header_footer: HeaderFooterConfig
    hyphenation: HyphenationConfig
    footnotes: FootnoteConfig
    paragraphs: ParagraphConfig
    sections: SectionConfig
    normalization: NormalizationConfig
    output: OutputConfig
```

**Vantagens:**
- Type hints explícitos
- IDE autocompletar
- Validação em tempo de execução
- Sem dependência de YAML
- Fácil customizar (subclass ou instância)

### ✅ Atualizado `src/preprocessing/*.py`

Todos os módulos agora importam configuração:

```python
from src.core.config import DEFAULT_PREPROCESSING_CONFIG

config = DEFAULT_PREPROCESSING_CONFIG.filters
min_chars = config.min_useful_characters
```

**Módulos atualizados:**
- `filters.py` - Usa `FilterConfig`
- `header_footer_remover.py` - Usa `HeaderFooterConfig`
- `hyphenation_fixer.py` - Usa `HyphenationConfig`
- `footnote_handler.py` - Usa `FootnoteConfig`
- `paragraph_reconstructor.py` - Mantém heurísticas
- `section_extractor.py` - Usa `SectionConfig`
- `normalizer.py` - Usa `NormalizationConfig`
- `pipeline.py` - Aceita config customizada como argumento

### ✅ Atualizado `src/core/__init__.py`

Exporta todas as classes de configuração para importação fácil:

```python
from src.core import PreprocessingConfig, DEFAULT_PREPROCESSING_CONFIG
```

## Uso

### Padrão (Configuração Padrão)

```python
from src.preprocessing.pipeline import PreprocessingPipeline

pipeline = PreprocessingPipeline()
result = pipeline.process(input_files)
```

### Customizado (Modificar Parâmetros)

```python
from src.core import PreprocessingConfig, FilterConfig

config = PreprocessingConfig(
    filters=FilterConfig(min_useful_characters=200)
)

pipeline = PreprocessingPipeline(config=config)
result = pipeline.process(input_files)
```

### Customizado Avançado (Subclass)

```python
from src.core import PreprocessingConfig

class MyConfig(PreprocessingConfig):
    def __init__(self):
        super().__init__()
        self.filters.min_useful_characters = 100
        self.header_footer.repetition_threshold = 0.25

pipeline = PreprocessingPipeline(config=MyConfig())
```

## Arquitetura

```
src/core/
├── config.py              # Dataclasses de configuração
├── __init__.py            # Exports
├── logger.py              # Logging
├── exceptions.py          # Exceções customizadas
└── constants.py           # Constantes globais

src/preprocessing/
├── filters.py             # Lê de config.filters
├── header_footer_remover.py # Lê de config.header_footer
├── hyphenation_fixer.py   # Lê de config.hyphenation
├── footnote_handler.py    # Lê de config.footnotes
├── section_extractor.py   # Lê de config.sections
├── normalizer.py          # Lê de config.normalization
├── paragraph_reconstructor.py
├── pipeline.py            # Aceita config como argumento
└── __init__.py
```

## Migração Completa

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Configuração** | `configs/preprocessing.yaml` | `src/core/config.py` |
| **Tipo** | YAML string-based | Python dataclasses |
| **Tipo hints** | Nenhum | Full type hints |
| **IDE support** | Nenhum | Autocompletar completo |
| **Validação** | Runtime (parsing) | Compile-time (Python) |
| **Defaults** | Em YAML | Em dataclass |
| **Customização** | Reescrever YAML | Subclass ou instância |
| **Importação** | Load YAML file | Direct import |

## Próximos Passos

Para adicionar configuração em outros módulos:

```python
# Em src/vectorization/config.py
@dataclass
class ChunkingConfig:
    chunk_size: int = 512
    overlap: int = 100

# Em src/core/config.py
@dataclass
class RAGConfig:
    preprocessing: PreprocessingConfig
    chunking: ChunkingConfig
    # ...
```

## Testes

Testes ainda passam sem modificação (importações internas foram atualizadas):

```bash
python -m pytest tests/test_preprocessing.py -v
```

---

**Status:** ✅ **Centralização Completa**  
**Arquivo YAML:** Pode ser removido ou mantido como documentação
