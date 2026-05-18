"""
Módulo responsável por manter o estado das seções ativas durante a travessia das linhas de markdown.
"""

import re


class SectionParser:
    """
    Mantém o estado das seções ativas durante a travessia das linhas de markdown.

    Detecta cabeçalhos markdown e infere hierarquia a partir da numeração das seções(ex: '3.', '3.1', '3.1.2') 
    em vez do nível de cabeçalho markdown (#, ##). Isso é necessário porque o docling frequentemente exporta 
    todos os cabeçalhos no mesmo nível markdown (#), perdendo a hierarquia visual do PDF original. 
    
    O método _infer_level tenta recuperar essa hierarquia numéricapara manter a estrutura de seções mais fiel 
    ao documento original, o que é crucial para o pré-processamento e a organização do conteúdo para o pipeline RAG.
    """

    _HEADER_RE = re.compile(r"^(#+)\s+(.+)$")

    _NUMERIC_RE = re.compile(r"^(\d+(?:\.\d+)*\.?)\s+")
    _PAREN_NUMERIC_SEQUENCE_RE = re.compile(r"^(?:\(\s*[-+]?\d[\d.,]*\s*\)\s*){2,}$")

    def __init__(self):
        self._sections = []

    def _infer_level(self, title: str, markdown_level: int) -> int:
        """
        Infere a profundidade da seção a partir do prefixo numérico, 
        com fallback para o nível markdown.

        Args:
            title: Título do cabeçalho markdown (sem os #)
            markdown_level: Nível do cabeçalho markdown (1 para #, 2 para ##, etc.)

        Returns:
            Profundidade inferida da seção, onde 1 é a seção mais externa.
        """
        match = self._NUMERIC_RE.match(title)
        if not match:
            return markdown_level

        numeric_part = match.group(1).rstrip(".")
        return len(numeric_part.split("."))

    def update(self, line: str) -> bool:
        """
        Atualiza o estado das seções ativas com base em uma linha de markdown.

        Args:
            line: Linha de markdown a ser processada.
            
        Returns:
            True se a linha for um cabeçalho markdown e o estado foi atualizado, False caso contrário.
        """
        match = self._HEADER_RE.match(line.strip())
        if not match:
            return False

        markdown_level = len(match.group(1))
        title = self._normalize_title(match.group(2))

        if self._looks_like_formula(title):
            return False

        level = self._infer_level(title, markdown_level)

        while self._sections and self._sections[-1][0] >= level:
            self._sections.pop()

        self._sections.append((level, title))
        return True

    @property
    def current_sections(self) -> list[str]:
        """
        Retorna a lista de títulos das seções ativas, ordenadas da mais externa para a mais interna.

        Args:
            None

        Returns:
            Lista de títulos das seções ativas.
        """
        return [title for _, title in self._sections]

    def reset(self):
        self._sections = []

    def _normalize_title(self, title: str) -> str:
        """
        Normaliza espaçamento do título antes de decidir se é seção válida.

        Args:
            title: Título a ser normalizado.

        Returns:
            Título normalizado.
        """
        return re.sub(r"\s+", " ", title.replace("\xa0", " ")).strip()

    def _looks_like_formula(self, title: str) -> bool:
        """
        Rejeita títulos que parecem fórmulas ou saídas algébricas.

        Args:
            title: Título a ser verificado.

        Returns:
            True se o título parecer uma fórmula, False caso contrário.
        """
        if not title:
            return True

        if "=" in title:
            return True

        if self._PAREN_NUMERIC_SEQUENCE_RE.match(title):
            return True

        if any(op in title for op in ("+", "-", "*", "/", "×", "÷")):
            if re.search(r"\d", title) and "(" in title and ")" in title:
                return True

        return False