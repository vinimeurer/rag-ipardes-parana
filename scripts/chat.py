"""
Interface de linha de comando interativa para o pipeline RAG.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logger import setup_logger
from src.core.rag_config import RAGConfig
from src.rag.rag_pipeline import RAGPipeline


SEPARATOR = "=" * 60
THIN_SEPARATOR = "-" * 60


def print_response(response) -> None:
    """Exibe as duas saídas obrigatórias do pipeline RAG.

    Saída 1: prompt montado e trechos utilizados (auditoria).
    Saída 2: resposta final gerada pelo LLM.

    Args:
        response: RAGResponse com todos os dados da query.
    """
    from src.rag.prompt_builder import PromptBuilder
    builder = PromptBuilder()

    print(f"\n{SEPARATOR}")
    print("SAÍDA 1 — PROMPT E TRECHOS UTILIZADOS")
    print(SEPARATOR)

    if response.out_of_scope:
        print("[Nenhum trecho relevante encontrado — query fora do escopo]")
    else:
        print(builder.format_sources(response.chunks))

    print(THIN_SEPARATOR)
    print("PROMPT ENVIADO AO LLM:")
    print(THIN_SEPARATOR)
    print(response.prompt)

    print(f"\n{SEPARATOR}")
    print("SAÍDA 2 — RESPOSTA FINAL")
    print(SEPARATOR)
    print(response.answer)
    print(SEPARATOR)


def main() -> int:
    """Executa o loop interativo de perguntas e respostas.

    Returns:
        Código de saída 0 em caso de encerramento normal.
    """
    logger = setup_logger(__name__)
    config = RAGConfig()

    print(SEPARATOR)
    print("RAG IPARDES Paraná — Interface Interativa")
    print(SEPARATOR)
    print(f"Modelo LLM  : {config.llm.model_name}")
    print(f"Top-K       : {config.retriever.top_k}")
    print(f"Similaridade: {config.retriever.min_similarity}")
    print(f"Documentos  : desenvolvimento_paranaense | analise_conjuntural | avaliacoes_politicas")
    print(SEPARATOR)
    print("Digite sua pergunta e pressione Enter.")
    print("Para sair, digite 'sair' ou pressione Ctrl+C.")
    print(SEPARATOR)

    try:
        pipeline = RAGPipeline(config)
    except Exception as e:
        logger.exception("Falha ao inicializar o pipeline RAG.")
        print(f"\nErro ao inicializar: {e}")
        return 1

    while True:
        try:
            print()
            question = input("Pergunta: ").strip()

            if not question:
                continue

            if question.lower() in {"sair", "exit", "quit"}:
                print("Encerrando.")
                break

            response = pipeline.query(question)
            print_response(response)

        except KeyboardInterrupt:
            print("\nEncerrando.")
            break
        except Exception as e:
            logger.exception("Erro ao processar query.")
            print(f"\nErro ao processar: {e}")
            continue

    return 0


if __name__ == "__main__":
    sys.exit(main())
