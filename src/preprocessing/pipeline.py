"""Orquestrador do pipeline de pré-processamento."""

import json
from pathlib import Path
from datetime import datetime

from src.core.preprocessing_config import DEFAULT_PREPROCESSING_CONFIG
from .filters import filter_pages
from .header_footer_remover import identify_repeated_lines, remove_repeated_lines
from .hyphenation_fixer import fix_hyphenation
from .footnote_handler import remove_footnote_superscripts
from .paragraph_reconstructor import reconstruct_paragraphs
from .section_extractor import extract_sections
from .normalizer import normalize_text


class PreprocessingPipeline:
    """Orquestra todas as etapas de pré-processamento."""
    
    def __init__(self, output_dir: str | Path = None, config = None):
        """
        Inicializa o pipeline.
        
        Args:
            output_dir: Diretório para salvar dados processados.
            config: Configuração customizada (usa DEFAULT se não fornecida).
        """
        self.output_dir = Path(output_dir) if output_dir else Path("data/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or DEFAULT_PREPROCESSING_CONFIG
        self.reports = {}
    
    def load_json(self, file_path: str | Path) -> list[dict]:
        """Carrega arquivo JSON com dados extraídos do PDF."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("data", [])
    
    def process(self, input_files: list[str | Path]) -> dict:
        """
        Executa o pipeline completo sobre todos os arquivos.
        
        Args:
            input_files: Lista de caminhos para arquivos JSON extraídos.
        
        Returns:
            Dict com resultados e estatísticas.
        """
        all_pages = []
        
        # Carregar todos os arquivos
        for file_path in input_files:
            pages = self.load_json(file_path)
            all_pages.extend(pages)
        
        print(f"[1/7] Filtrando páginas irrelevantes... ({len(all_pages)} páginas)")
        all_pages, filter_report = filter_pages(all_pages)
        self.reports["filtering"] = filter_report
        print(f"      Removidas: {filter_report['removed_empty']} vazias, "
              f"{filter_report['removed_institutional']} institucionais, "
              f"{filter_report['removed_index']} índices")
        print(f"      Total após filtro: {filter_report['total_output']}")
        
        print(f"\n[2/7] Removendo cabeçalhos e rodapés repetidos...")
        threshold = self.config.header_footer.repetition_threshold
        repeated_lines = identify_repeated_lines(all_pages, threshold=threshold)
        all_pages, header_footer_report = remove_repeated_lines(all_pages, repeated_lines)
        self.reports["header_footer"] = header_footer_report
        for doc, info in header_footer_report["documents"].items():
            print(f"      {doc}: {len(info['lines_removed'])} linhas removidas")
        
        print(f"\n[3/7] Corrigindo hifenização...")
        for page in all_pages:
            page["text"] = fix_hyphenation(page["text"])
        print(f"      Hifenizações corrigidas")
        
        print(f"\n[4/7] Removendo superescritos de notas de rodapé...")
        for page in all_pages:
            page["text"] = remove_footnote_superscripts(page["text"])
        print(f"      Superescritos removidos")
        
        print(f"\n[5/7] Reconstituindo parágrafos...")
        for page in all_pages:
            page["text"] = reconstruct_paragraphs(page["text"])
        print(f"      Parágrafos reconstituídos")
        
        print(f"\n[6/7] Extraindo metadados de seção...")
        all_pages = extract_sections(all_pages)
        print(f"      Seções extraídas")
        
        print(f"\n[7/7] Normalizando texto...")
        for page in all_pages:
            page["text"] = normalize_text(page["text"])
        print(f"      Texto normalizado")
        
        return {
            "pages": all_pages,
            "statistics": self._compute_statistics(all_pages),
            "reports": self.reports,
        }
    
    def save_processed(self, result: dict, base_name: str = "processed"):
        """
        Salva dados processados em JSON.
        
        Args:
            result: Resultado do processamento.
            base_name: Nome base para arquivo de saída.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_file = self.output_dir / f"{base_name}_{timestamp}.json"
        
        output_data = {
            "processed_at": timestamp,
            "total_pages": len(result["pages"]),
            "statistics": result["statistics"],
            "data": result["pages"],
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nDados processados salvos em: {output_file}")
        
        # Salvar relatórios em arquivo separado
        reports_file = self.output_dir / f"reports_{timestamp}.json"
        with open(reports_file, "w", encoding="utf-8") as f:
            json.dump(result["reports"], f, ensure_ascii=False, indent=2)
        
        print(f"Relatórios salvos em: {reports_file}")
        
        return output_file, reports_file
    
    def _compute_statistics(self, pages: list[dict]) -> dict:
        """Computa estatísticas sobre os dados processados."""
        total_chars = sum(len(p.get("text", "")) for p in pages)
        avg_chars_per_page = total_chars / len(pages) if pages else 0
        
        docs = set(p.get("document") for p in pages)
        sections = set(p.get("section") for p in pages if p.get("section"))
        
        return {
            "total_pages": len(pages),
            "total_characters": total_chars,
            "avg_characters_per_page": round(avg_chars_per_page, 2),
            "documents": list(docs),
            "sections_found": list(sections),
            "num_documents": len(docs),
            "num_sections": len(sections),
        }
