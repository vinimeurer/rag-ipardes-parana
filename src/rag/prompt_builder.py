"""
Construção do prompt final para o pipeline RAG.
"""

from .retriever import RetrievedChunk


SYSTEM_PROMPT = """Você é um assistente especializado nos documentos oficiais do Instituto Paranaense de Desenvolvimento Econômico e Social (IPARDES).

Responda APENAS com base nos trechos fornecidos abaixo. Regras obrigatórias:
- Se a informação não estiver nos trechos, diga explicitamente que não encontrou informação sobre o assunto nos documentos disponíveis.
- Nunca complemente com conhecimento próprio ou informações externas aos trechos.
- Cite sempre o documento, página e seção de onde veio a informação.
- Seja objetivo e preciso."""

SOURCE_LABELS = {
    "desenvolvimento_paranaense": "Desenvolvimento Paranaense: Contexto, Tendências e Desafios (IPARDES, 2022)",
    "analise_conjuntural": "Análise Conjuntural — Julho/Agosto 2025 (IPARDES)",
    "avaliacoes_politicas": "Avaliações de Políticas Públicas no Brasil: Uma Revisão de Escopo (IPARDES, 2025)",
}


class PromptBuilder:
    """Constrói o prompt final enviado ao LLM no pipeline RAG.

    Monta o contexto com os chunks recuperados formatados com suas
    referências de origem, e a instrução do sistema que restringe
    o modelo a responder apenas com base nos trechos fornecidos.
    """

    def build(self, query: str, chunks: list[RetrievedChunk]) -> str:
        """Constrói o prompt completo para o LLM.

        Args:
            query: Pergunta original do usuário.
            chunks: Lista de chunks relevantes recuperados pelo retriever.

        Returns:
            Prompt completo com sistema, contexto e pergunta.
        """
        context = self._format_context(chunks)
        return f"{SYSTEM_PROMPT}\n\n{context}\n\nPergunta: {query}"

    def build_out_of_scope(self, query: str) -> str:
        """Constrói prompt para queries fora do escopo dos documentos.

        Usado quando nenhum chunk supera o threshold de similaridade.
        Instrui o modelo a informar que não há informação disponível
        sem tentar responder com conhecimento próprio.

        Args:
            query: Pergunta original do usuário.

        Returns:
            Prompt que instrui o modelo a recusar a query.
        """
        return (
            f"{SYSTEM_PROMPT}\n\n"
            "CONTEXTO: Nenhum trecho relevante foi encontrado nos documentos disponíveis "
            "para responder à pergunta abaixo.\n\n"
            f"Pergunta: {query}"
        )

    def format_sources(self, chunks: list[RetrievedChunk]) -> str:
        """Formata a lista de fontes utilizadas para exibição ao usuário.

        Args:
            chunks: Lista de chunks utilizados na resposta.

        Returns:
            String formatada com as fontes e trechos utilizados.
        """
        if not chunks:
            return "Nenhum trecho utilizado."

        lines = ["=== TRECHOS UTILIZADOS ===\n"]
        for i, chunk in enumerate(chunks, 1):
            doc_label = SOURCE_LABELS.get(chunk.document, chunk.document)
            sections_str = " > ".join(chunk.sections) if chunk.sections else "—"
            lines.append(
                f"[{i}] {doc_label}\n"
                f"    Página: {chunk.page} | Seções: {sections_str}\n"
                f"    Similaridade: {chunk.similarity:.4f}\n"
                f"    Tipo: {chunk.type}"
            )
            if chunk.type == "table" and chunk.caption:
                lines.append(f"    Legenda: {chunk.caption}")
            lines.append(f"    Trecho: {chunk.content[:300]}{'...' if len(chunk.content) > 300 else ''}")
            lines.append("")

        return "\n".join(lines)

    def _format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Formata os chunks recuperados como contexto do prompt.

        Args:
            chunks: Lista de chunks a incluir no contexto.

        Returns:
            String formatada com os trechos numerados e suas referências.
        """
        lines = ["TRECHOS DOS DOCUMENTOS:"]
        for i, chunk in enumerate(chunks, 1):
            doc_label = SOURCE_LABELS.get(chunk.document, chunk.document)
            sections_str = " > ".join(chunk.sections) if chunk.sections else "sem seção"
            header = f"[Trecho {i} — {doc_label} | Página {chunk.page} | {sections_str}]"
            if chunk.type == "table" and chunk.caption:
                header += f"\n[Tabela: {chunk.caption}]"
            lines.append(f"\n{header}\n{chunk.content}")

        return "\n".join(lines)
