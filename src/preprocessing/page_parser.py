"""
Módulo responsável por parsear o conteúdo markdown em páginas.
"""

import re

class PageParser:
    """
    Parser de páginas a partir de conteúdo markdown.
    
    Extrai páginas delimitadas por tags PAGE especiais ou usa o conteúdo
    completo como uma única página.
    """
    
    _PAGE_TAG_RE = re.compile(r"<!--\s*PAGE:\s*(\d+)\s*-->")
    
    @staticmethod
    def parse_pages(content: str) -> list[dict]:
        """
        Parseia o conteúdo markdown em páginas usando tags PAGE.
        
        Cada página é extraída entre tags PAGE consecutivas. A primeira página
        começa do início do documento. Se não houver tags, o conteúdo completo
        é retornado como uma única página.
        
        Args:
            content: Conteúdo markdown completo do arquivo fonte.
        
        Returns:
            Lista de dicionários com chaves 'page_number' e 'text'.
        """
        tag_positions = [
            (m.start(), int(m.group(1)))
            for m in PageParser._PAGE_TAG_RE.finditer(content)
        ]
        
        if not tag_positions:
            return [{"page_number": 0, "text": content}]
        
        pages = []
        for idx, (pos, page_num) in enumerate(tag_positions):
            end_pos = (
                tag_positions[idx + 1][0]
                if idx + 1 < len(tag_positions)
                else len(content)
            )
            page_content = content[pos:end_pos]
            page_content = PageParser._PAGE_TAG_RE.sub("", page_content, count=1).strip()
            pages.append({"page_number": page_num, "text": page_content})
        
        return pages
