# 🚀 Quick Start — Frontend Web RAG IPARDES

## Início Rápido em 3 Passos

### 1️⃣ Instale dependências

```bash
pip install -r requirements.txt
```

### 2️⃣ Inicie o Ollama

Em outro terminal:
```bash
ollama serve
```

### 3️⃣ Inicie o servidor web

```bash
python scripts/server.py
```

**Pronto!** Abra http://localhost:8000 no navegador.

---

## 📋 Pré-requisitos

- **Python 3.10+**
- **Ollama** instalado (https://ollama.ai)
- **Modelos Ollama** já baixados (configurados no `src/core/rag_config.py`)

## 🌐 Interface

| Painel | Conteúdo |
|--------|----------|
| **Esquerda** | System message e prompt final (debug/auditoria) |
| **Centro** | Chat com perguntas e respostas |
| **Direita** | Detalhes do trecho selecionado (documento, página, seção, score) |

## ⌨️ Controles

- **Enter**: Enviar pergunta
- **Shift+Enter**: Nova linha no textarea
- **Clique em chip de referência**: Ver detalhes no painel direito
- **Anterior/Próxima**: Navegar entre trechos utilizados

## 🔍 Pontos-chave

✅ **Auditoria completa**: Veja o system message e o prompt final na barra esquerda  
✅ **Referências rastreáveis**: Cada trecho mostra documento, página, seção e score  
✅ **Fidelidade**: Sistema avisa quando a pergunta está fora do escopo  
✅ **Responsivo**: Funciona em desktop, tablet e mobile  

## 📚 Documentação Completa

Veja [docs/FRONTEND_README.md](docs/FRONTEND_README.md) para guia detalhado com:
- Arquitetura completa
- Endpoints da API
- Tratamento de erros
- Troubleshooting
- Configuração avançada

## ⚠️ Requisitos de Execução

- Ollama **DEVE estar rodando** na porta 11434
- Banco vetorial ChromaDB **deve estar indexado** (execute os scripts de ingestão primeiro)
- Modelos LLM e embedding **devem estar disponíveis localmente**

### Verificar saúde da API

```bash
curl http://localhost:8000/api/health
```

## 📝 Exemplo de Query

```
Pergunta: "Qual foi o crescimento do PIB do Paraná?"

Resposta esperada:
- Texto com citação dos documentos
- Chips com referências abaixo
- Clique em um chip para ver o trecho completo
- Painel esquerdo mostra o prompt enviado ao LLM
```

## 🆘 Problemas Comuns

### "Pipeline não disponível"
```bash
# Verifique se Ollama está rodando
ollama list
```

### "Erro ao processar: connection refused"
```bash
# Reinicie o Ollama
ollama serve
```

### Frontend não carrega
```bash
# Verificar se servidor está rodando
curl http://localhost:8000/api/health
```

---

**Mais dúvidas?** Veja [docs/FRONTEND_README.md](docs/FRONTEND_README.md) ou [docs/technical_documentation.md](docs/technical_documentation.md).
