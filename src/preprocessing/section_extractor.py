"""Etapa 6: Extração de metadados de seção."""

import re
from src.core.preprocessing_config import DEFAULT_PREPROCESSING_CONFIG


def _is_fake_section(line: str) -> bool:
    """
    Verifica se uma linha é um falso título (header/footer, caption, etc).
    
    Filtra: headers/footers, linhas de tabela, referências, metadados.
    Permite: tabelas, gráficos, figuras, quadros como seções válidas.

    Args:
        line: Linha de texto para avaliar.

    Returns:
        True se for um falso título, False se for potencial seção legítima.
    """
    stripped = line.strip()
    
    if not stripped:
        return True
    
    # 1. Excluir header/footer do rodapé
    if "DESENVOLVIMENTO PARANAENSE" in stripped and "CONTEXTO" in stripped:
        return True
    
    # 2. Excluir linhas que contêm pipes (linhas de tabelas quebradas)
    if "|" in stripped:
        return True
    
    # 2b. Excluir linhas com "/" (padrão de cabeçalho de tabela como "CONDIÇÃO/TIPO/ESPÉCIE")
    if "/" in stripped and not stripped.startswith("DESENVOLVIMENTO"):
        return True
    
    # 3. Excluir referências em parênteses (ex: "(CASTRO, 2007).", "(EAESP-FGV)")
    if re.match(r"^\([\w\s,\-\.;:]+\)\.?$", stripped):
        return True
    
    # 4. Excluir índices de página pura (ex: "23" sozinho ou "23    TÍTULO")
    if re.match(r"^\d+\s+", stripped) and not re.match(r"^\d+[\.\)]\s+[A-Z]", stripped):
        return True
    
    # 5. Excluir linhas que parecem dados numéricos (ex: "PR / BR (%) 2005 101,7 102,4...")
    if re.search(r"\d+[,\.]\d+\s+\d+[,\.]\d+", stripped):
        return True
    
    # 6. Excluir referências bibliográficas (padrão: NOME, SOBRENOME; NOME2, SOBRENOME2)
    if re.search(r"^[A-Z][A-Z\s,\.;]+,\s+[A-Z]\.?\s+[A-Z]", stripped):
        return True
    
    # 6b. Excluir padrão "N = 34 N = 44" (contagens de tabela)
    if re.search(r"N\s*=\s*\d+", stripped):
        return True
    
    # 7. Excluir cabeçalhos de tabela: múltiplas colunas com % ou parênteses
    # Ex: "FAIXA ETÁRIA (%) ANO", "IDH SAÚDE EDUCAÇÃO RENDA"
    parenthesis_count = stripped.count("(") + stripped.count(")")
    if parenthesis_count >= 2 or (parenthesis_count >= 1 and "%" in stripped):
        return True
    
    # 7b. Excluir headers de tabela com muitos termos de coluna
    # Padrão: palavras muito curtas (1-3 palavras) em maiúsculas separadas por espaço
    # Ex: "IDH SAÚDE EDUCAÇÃO RENDA", "PERÍODO ANO GRUPOS"
    # MAS: permitir TABELA/GRÁFICO/FIGURA/QUADRO legítimos
    if not any(keyword in stripped for keyword in ["TABELA", "GRÁFICO", "FIGURA", "QUADRO", "IMAGEM"]):
        words = stripped.split()
        if len(words) >= 3:
            uppercase_words = [w for w in words if w.isupper() and len(w) <= 20 and not w.startswith("(")]
            if len(uppercase_words) >= len(words) - 1:  # Quase todas as palavras são maiúsculas e curtas
                # Se tem palavras que parecem colunas de tabela
                column_keywords = ["PERÍODO", "ANO", "RENDA", "EDUCAÇÃO", "SAÚDE", "GRUPO", 
                                  "REGIÃO", "PAÍS", "INCREMENTO", "VARIAÇÃO", "MODALIDADE",
                                  "CARTEIRA", "ATIVO", "REAIS", "IDH", "ESPERADOS", "OBSERVAÇÃO"]
                if any(keyword in stripped for keyword in column_keywords):
                    return True
    
    # 8. Excluir metadados puros
    metadata = ["FONTE:", "NOTA:", "REFERÊNCIA", "PÁGINA", "ÍNDICE", "SUMÁRIO",
                "OCUPAÇÃO", "MODALIDADE", "PERCENTUAL", "PERIODO", "PORTE",
                "CONSUMO (%)", "RETIRADA (%)", "INCREMENTO", "COMPONENTE",
                "SEGMENTO", "TIPO E FONTE", "LOCAL |", "DEMANDANTE",
                "NOME DO PERIÓDICO", "RENDA NACIONAL PERÍODO", "RENDA NACIONAL BRUTA",
                "ÓRGÃOS DE FORMULAÇÃO", "RECORTE GEOGRÁFICO"]
    if any(m in stripped for m in metadata):
        return True
    
    # 9. Excluir listas de commodities curtas
    products = ["ARROZ", "BATATA", "CAFÉ", "MILHO", "TABACO", "MANDIOCA", "CANA"]
    if any(p in stripped for p in products) and len(stripped.split()) <= 5:
        return True
    
    # 10. Excluir muito curtas (menos de 10 caracteres)
    if len(stripped) < 10:
        return True
    
    # 11. Rejeitar seções que terminam com hífen isolado (incompletas)
    if stripped.endswith(" -"):
        return True
    
    return False


def extract_sections(pages: list[dict]) -> list[dict]:
    """
    Extrai metadados de seção de cada página.
    
    Varre páginas em ordem. Quando encontra linha toda em maiúsculas
    com mais de 10 caracteres (título de seção), registra como secao_atual.
    Propaga para todos os blocos seguintes até novo título.
    
    Trata títulos multi-linha: se linha termina sem ponto/vírgula/hífen 
    e próxima também está em maiúsculas, junta ambas.
    
    Filtra headers/footers, captions de tabelas/gráficos e linhas falsas.
    
    Args:
        pages: Lista de dicts com 'text', 'page', 'document'.
    
    Returns:
        Lista de páginas com campo 'section' adicionado.
    """
    processed = []
    current_section = "Unknown"
    config = DEFAULT_PREPROCESSING_CONFIG.sections
    
    for page in pages:
        text = page.get("text", "")
        lines = text.split("\n")
        
        # Procurar por títulos de seção em maiúsculas
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            
            # Critério: linha toda em maiúsculas com mais de min_title_length caracteres
            if (
                len(stripped) > config.min_title_length
                and stripped.isupper()
                and any(c.isalpha() for c in stripped)
                and not _is_fake_section(stripped)
            ):
                # Começar com esta linha
                section_lines = [stripped]
                
                # Verificar se próximas linhas continuam o título (multi-linha)
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    
                    # Se próxima linha está vazia, parar
                    if not next_line:
                        break
                    
                    # Parar se próxima linha é metadado (FONTE:, NOTA:, etc)
                    if next_line.startswith(("FONTE:", "NOTA:", "REFERÊNCIA:", "ÍNDICE:", "SUMÁRIO:")):
                        break
                    
                    # Se próxima linha é totalmente maiúscula e linha atual não termina com pontuação
                    # forte, é continuação
                    current_ends = stripped[-1] if stripped else ""
                    if (
                        next_line.isupper()
                        and any(c.isalpha() for c in next_line)
                        and current_ends not in ".!?;"
                    ):
                        section_lines.append(next_line)
                        stripped = next_line  # Atualizar para próxima iteração
                        j += 1
                    else:
                        break
                
                # Juntar linhas do título
                joined_section = " ".join(section_lines)
                
                # Validar a seção juntada também
                if not _is_fake_section(joined_section):
                    current_section = joined_section
                
                i = j
                break
            
            i += 1
        
        # Adicionar seção ao page data
        page_copy = page.copy()
        page_copy["section"] = current_section
        processed.append(page_copy)
    
    return processed
