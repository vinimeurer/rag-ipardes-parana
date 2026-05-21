"""
Pipeline de geração de embeddings para os chunks do RAG.

Lê o arquivo chunks.jsonl, gera vetores para cada chunk e salva
o resultado em chunks_with_embeddings.jsonl para indexação posterior.
"""

import json
from pathlib import Path
from typing import Optional

from ..core.logger import setup_logger
from ..core.embedding_config import EmbeddingConfig
from .text_encoder import TextEncoder


class Embedder:
    """Gera e persiste embeddings para todos os chunks do pipeline RAG.

    Produz um arquivo JSONL onde cada linha contém o chunk original
    acrescido do campo 'embedding' com o vetor gerado pelo modelo.
    Este arquivo intermediário permite reindexar sem re-rodar o modelo.

    Attributes:
        config: Configuração do pipeline de embedding.
        encoder: Instância do encoder de texto.
        logger: Logger do módulo.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Inicializa o embedder e carrega o modelo de linguagem.

        Verifica se o modelo já existe em models/embeddings/. Se sim,
        carrega offline. Se não, baixa e salva para uso futuro.

        Args:
            config: Configuração de embedding. Se omitida, usa valores padrão.
        """
        self.config = config or EmbeddingConfig()
        self.logger = setup_logger(__name__)

        local_path = self.config.model_local_path
        if local_path.exists():
            self.logger.info("Modelo encontrado em cache local: %s", local_path)
        else:
            self.logger.info(
                "Modelo não encontrado localmente. Baixando '%s' para '%s'...",
                self.config.model_name,
                self.config.paths.models_dir,
            )

        self.encoder = TextEncoder(
            model_name=self.config.model_name,
            model_local_path=local_path,
            models_dir=self.config.paths.models_dir,
            device=self.config.device,
            normalize=self.config.normalize,
        )

        self.logger.info(
            "Modelo pronto | dim=%d | device=%s",
            self.encoder.embedding_dim,
            self.config.device,
        )

    def run(
        self,
        chunks_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Executa o pipeline completo de embedding.

        Lê todos os chunks, gera embeddings em lotes e salva o resultado.

        Args:
            chunks_path: Caminho do arquivo chunks.jsonl.
                Se omitido, usa a configuração.
            output_path: Caminho do arquivo de saída.
                Se omitido, usa a configuração.

        Returns:
            Caminho do arquivo de saída gerado.
        """
        src = chunks_path or (self.config.paths.chunks_dir / self.config.chunks_filename)
        dst = output_path or (self.config.paths.embeddings_dir / self.config.output_filename)

        chunks = self._load_chunks(src)
        self.logger.info("Chunks carregados: %d", len(chunks))

        texts = [self._build_embedding_text(c) for c in chunks]

        self.logger.info(
            "Gerando embeddings em lotes de %d...", self.config.batch_size
        )
        embeddings = self.encoder.encode(texts, batch_size=self.config.batch_size)

        dst.parent.mkdir(parents=True, exist_ok=True)
        self._save(chunks, embeddings, dst)

        self.logger.info("Embeddings salvos em: %s (%d linhas)", dst, len(chunks))
        return dst

    def _load_chunks(self, path: Path) -> list[dict]:
        """Carrega chunks do arquivo JSONL.

        Args:
            path: Caminho do arquivo chunks.jsonl.

        Returns:
            Lista de dicionários representando os chunks.
        """
        chunks = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
        return chunks

    def _build_embedding_text(self, chunk: dict) -> str:
        """Constrói o texto a ser codificado para um chunk.

        Prefixa o conteúdo com metadados de seção para enriquecer o
        embedding com contexto hierárquico. Isso melhora a recuperação
        de chunks em perguntas temáticas que mencionam seções específicas.

        Para tabelas, inclui a caption quando disponível para dar
        contexto semântico ao embedding, já que o conteúdo markdown
        puro tem baixa semântica isolado.

        Args:
            chunk: Dicionário do chunk com todos os metadados.

        Returns:
            Texto enriquecido pronto para codificação.
        """
        parts = []

        sections = chunk.get("sections", [])
        if sections:
            parts.append(" > ".join(sections))

        if chunk.get("type") == "table" and chunk.get("caption"):
            parts.append(chunk["caption"])

        parts.append(chunk["content"])

        return "\n".join(parts)

    def _save(
        self,
        chunks: list[dict],
        embeddings: list[list[float]],
        path: Path,
    ) -> None:
        """Salva chunks com embeddings em formato JSONL.

        Args:
            chunks: Lista de chunks originais.
            embeddings: Lista de vetores na mesma ordem dos chunks.
            path: Caminho do arquivo de saída.
        """
        with path.open("w", encoding="utf-8") as f:
            for chunk, embedding in zip(chunks, embeddings):
                record = {**chunk, "embedding": embedding}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
