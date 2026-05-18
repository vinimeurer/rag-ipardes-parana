"""
Módulo responsável por mesclar conteúdo de texto e tabelas.
"""


class ContentMerger:
    """
    Responsável por mesclar e ordenar itens de texto e tabelas.
    """
    
    @staticmethod
    def merge_content_and_tables(text_items: list[dict], table_items: list[dict]) -> list[dict]:
        """
        Mescla itens de texto e tabela mantendo a ordem das páginas.
        
        Combina o conteúdo de texto e tabela em um único array ordenado, depois ordena
        por número de página. Dentro de cada página, o texto aparece antes das tabelas.
        Preenche as informações de seção para as tabelas com base nas seções ativas em
        sua página ou na página precedente mais próxima com seções.
        
        Args:
            text_items: Lista de itens de conteúdo de texto.
            table_items: Lista de itens de conteúdo de tabela (com seções vazias).
        
        Returns:
            Lista mesclada e ordenada de itens de conteúdo.
        """
        all_items = text_items + table_items
        all_items.sort(key=lambda x: (x.get("page", 0), x.get("type") == "table"))
        
        section_map = {}
        for item in text_items:
            page = item.get("page")
            if page and item.get("sections"):
                section_map[page] = item.get("sections")
        
        last_sections = None
        for item in all_items:
            page = item.get("page")
            if page in section_map:
                last_sections = section_map[page]
            
            if item.get("type") == "table":
                if page in section_map:
                    item["sections"] = section_map[page]
                elif last_sections:
                    item["sections"] = last_sections
                else:
                    item["sections"] = []
        
        return all_items
