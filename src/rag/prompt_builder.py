"""
Construção do prompt final para o pipeline RAG.
"""

from .retriever import RetrievedChunk


SYSTEM_PROMPT = """Você é um assistente especializado nos documentos oficiais do Instituto Paranaense de Desenvolvimento Econômico e Social (IPARDES).

Responda APENAS com base nos trechos fornecidos abaixo. Regras obrigatórias:
- Se a informação não estiver nos trechos, diga explicitamente que não encontrou informação sobre o assunto nos documentos disponíveis.
- Nunca complemente com conhecimento próprio ou informações externas aos trechos.
- Ao final de cada informação relevante, indique a fonte no formato: (Documento, p. N, Seção X).
- Seja objetivo e preciso."""

SOURCE_LABELS = {
    "desenvolvimento_paranaense": "Desenvolvimento Paranaense: Contexto, Tendências e Desafios (IPARDES, 2022)",
    "analise_conjuntural": "Análise Conjuntural — Julho/Agosto 2025 (IPARDES)",
    "avaliacoes_politicas": "Avaliações de Políticas Públicas no Brasil: Uma Revisão de Escopo (IPARDES, 2025)",
}

SOURCE_SHORT_LABELS = {
    "desenvolvimento_paranaense": "Desenvolvimento Paranaense",
    "analise_conjuntural": "Análise Conjuntural",
    "avaliacoes_politicas": "Avaliações de Políticas Públicas",
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

        Gera uma representação legível e amigável de cada chunk utilizado,
        incluindo localização precisa (documento, página, seção) e
        scores de relevância para auditoria do pipeline.

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
            location = self._format_location(chunk)
            lines.append(f"[{i}] {doc_label}")
            lines.append(f"    Localização: {location}")
            lines.append(f"    Tipo: {'Tabela' if chunk.type == 'table' else 'Texto'}")

            scores = f"Similaridade: {chunk.similarity:.4f}"
            if chunk.rerank_score is not None:
                scores += f" | Score reranker: {chunk.rerank_score:.4f}"
            lines.append(f"    {scores}")

            if chunk.type == "table" and chunk.caption:
                lines.append(f"    Legenda: {chunk.caption}")

            preview = chunk.content[:300]
            if len(chunk.content) > 300:
                preview += "..."
            lines.append(f"    Trecho: {preview}")
            lines.append("")

        return "\n".join(lines)

    def _format_location(self, chunk: RetrievedChunk) -> str:
        """Formata a localização de um chunk de forma amigável.

        Gera uma string legível indicando página e seção do chunk,
        usada tanto na exibição ao usuário quanto como referência
        nas instruções do LLM para formatar as citações na resposta.

        Args:
            chunk: Chunk com metadados de localização.

        Returns:
            String formatada como 'página N, seção X > Y' ou 'página N'.
        """
        doc_short = SOURCE_SHORT_LABELS.get(chunk.document, chunk.document)
        page_str = f"página {chunk.page}"

        if chunk.sections:
            section_str = " > ".join(chunk.sections)
            return f"{doc_short}, {page_str}, seção: {section_str}"

        return f"{doc_short}, {page_str}"
    
    def _format_citation(self, chunk: RetrievedChunk) -> str:
        """
        Formata a citação exata que o LLM deve usar na resposta.

        Gera uma string concisa para a citação, usada nas instruções do
        LLM para garantir que as fontes sejam citadas de forma consistente
        e legível, seguindo o formato: (Documento, p. N, Seção X).

        Args:
            chunk: Chunk com metadados de localização.

        Returns:
            String formatada para citação, como '(Documento, p. N, Seção X)'.
        """
        doc_short = SOURCE_SHORT_LABELS.get(chunk.document, chunk.document)
        section_str = " > ".join(chunk.sections) if chunk.sections else "—"
        return f"({doc_short}, p. {chunk.page}, Seção: {section_str})"

    def _format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Formata os chunks recuperados como contexto do prompt.

        Cada trecho inclui sua localização precisa no formato que o LLM
        deve usar ao citar a fonte na resposta final.

        Args:
            chunks: Lista de chunks a incluir no contexto.

        Returns:
            String formatada com os trechos numerados e suas referências.
        """
        lines = ["TRECHOS DOS DOCUMENTOS:"]
        for i, chunk in enumerate(chunks, 1):
            location = self._format_location(chunk)
            citation = self._format_citation(chunk)
            header = f"[Trecho {i} — {location}]\n[Citar como: {citation}]"
            if chunk.type == "table" and chunk.caption:
                header += f"\n[Tabela: {chunk.caption}]"
            lines.append(f"\n{header}\n{chunk.content}")

        return "\n".join(lines)
