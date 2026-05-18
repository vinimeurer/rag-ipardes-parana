"""
Definição da estrutura de dados de um chunk para o pipeline RAG.
"""

from dataclasses import dataclass, field


@dataclass
class Chunk:
    """Representa um chunk de conteúdo pronto para indexação vetorial.

    O chunk_id segue o padrão {pdf_key}_{item_index:03d}_{chunk_index:02d},
    permitindo rastrear de qual item e posição dentro do item cada chunk originou.

    Attributes:
        chunk_id: Identificador único e rastreável do chunk.
        document: Chave do documento de origem.
        page: Número da página de origem.
        sections: Hierarquia de seções ativas no momento do bloco de origem.
        type: Tipo do conteúdo ('text' ou 'table').
        content: Texto do chunk.
        token_count: Número aproximado de tokens do conteúdo.
        is_auxiliary: Indica se o chunk é conteúdo auxiliar (ex: lista de siglas).
        caption: Legenda da tabela, presente apenas quando type='table'.
    """

    chunk_id: str
    document: str
    page: int
    sections: list[str]
    type: str
    content: str
    token_count: int
    is_auxiliary: bool = False
    caption: str | None = None

    def to_dict(self) -> dict:
        """Serializa o chunk para dicionário compatível com JSON.

        Returns:
            Dicionário com todos os campos do chunk.
        """
        return {
            "chunk_id": self.chunk_id,
            "document": self.document,
            "page": self.page,
            "sections": self.sections,
            "type": self.type,
            "content": self.content,
            "token_count": self.token_count,
            "is_auxiliary": self.is_auxiliary,
            "caption": self.caption,
        }
