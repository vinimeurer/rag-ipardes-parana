"""
Implementação de recursive character text splitting para o pipeline de chunking.

Divide textos longos em blocos menores respeitando separadores naturais,
sem dependência de bibliotecas externas.
"""


def count_tokens(text: str) -> int:
    """Conta tokens aproximados de um texto por contagem de palavras.

    A contagem por split() é uma aproximação offline adequada para chunking.
    Tokenizadores específicos de modelo podem divergir em até 20%, mas a
    margem de erro é aceitável dado que os limites são configuráveis.

    Args:
        text: Texto a ser contado.

    Returns:
        Número aproximado de tokens.
    """
    return len(text.split())


class RecursiveTextSplitter:
    """Divide texto em chunks respeitando separadores naturais recursivamente.

    A estratégia tenta dividir pelo separador de maior granularidade primeiro
    (parágrafos), regredindo para separadores menores (linhas, espaços) quando
    os pedaços ainda excedem o tamanho máximo. O overlap garante continuidade
    de contexto entre chunks consecutivos.

    Attributes:
        chunk_size: Número máximo de tokens por chunk.
        overlap: Número de tokens de sobreposição entre chunks consecutivos.
        separators: Lista de separadores em ordem decrescente de preferência.
    """

    def __init__(self, chunk_size: int, overlap: int, separators: list[str]):
        """Inicializa o splitter com os parâmetros de chunking.

        Args:
            chunk_size: Número máximo de tokens por chunk.
            overlap: Número de tokens de sobreposição entre chunks.
            separators: Separadores em ordem decrescente de granularidade.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = separators

    def split(self, text: str) -> list[str]:
        """Divide o texto em chunks respeitando o tamanho máximo.

        Args:
            text: Texto a ser dividido.

        Returns:
            Lista de chunks de texto.
        """
        if count_tokens(text) <= self.chunk_size:
            return [text]

        chunks = self._split_recursive(text, self.separators)
        return self._apply_overlap(chunks)

    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        """Divide texto recursivamente usando o melhor separador disponível.

        Args:
            text: Texto a ser dividido.
            separators: Separadores restantes a tentar.

        Returns:
            Lista de pedaços de texto.
        """
        if not separators:
            return self._force_split(text)

        separator = separators[0]
        remaining = separators[1:]

        parts = text.split(separator)
        parts = [p for p in parts if p.strip()]

        merged = self._merge_parts(parts, separator)

        result = []
        for piece in merged:
            if count_tokens(piece) <= self.chunk_size:
                result.append(piece)
            else:
                result.extend(self._split_recursive(piece, remaining))

        return result

    def _merge_parts(self, parts: list[str], separator: str) -> list[str]:
        """Agrupa partes pequenas para evitar chunks desnecessariamente curtos.

        Args:
            parts: Partes resultantes da divisão por separador.
            separator: Separador usado para reunir partes ao mesclar.

        Returns:
            Lista de grupos de partes.
        """
        merged = []
        current: list[str] = []
        current_tokens = 0

        for part in parts:
            part_tokens = count_tokens(part)

            if current_tokens + part_tokens <= self.chunk_size:
                current.append(part)
                current_tokens += part_tokens
            else:
                if current:
                    merged.append(separator.join(current))
                current = [part]
                current_tokens = part_tokens

        if current:
            merged.append(separator.join(current))

        return merged

    def _force_split(self, text: str) -> list[str]:
        """Divide texto por palavras quando nenhum separador funciona.

        Usado como fallback quando o texto não possui separadores naturais
        e ainda excede o tamanho máximo do chunk.

        Args:
            text: Texto a ser dividido forçadamente.

        Returns:
            Lista de chunks divididos por palavras.
        """
        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            start = end

        return chunks

    def _apply_overlap(self, chunks: list[str]) -> list[str]:
        """Aplica sobreposição entre chunks consecutivos.

        Adiciona o final do chunk anterior ao início do próximo para
        preservar continuidade de contexto nas fronteiras dos chunks.

        Args:
            chunks: Lista de chunks sem sobreposição.

        Returns:
            Lista de chunks com sobreposição aplicada.
        """
        if len(chunks) <= 1 or self.overlap == 0:
            return chunks

        result = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_words = chunks[i - 1].split()
            overlap_words = prev_words[-self.overlap:] if len(prev_words) >= self.overlap else prev_words
            overlap_text = " ".join(overlap_words)
            result.append(overlap_text + " " + chunks[i])

        return result
