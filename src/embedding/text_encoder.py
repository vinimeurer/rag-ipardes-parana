"""
Responsável por carregar o modelo de embedding e gerar vetores de texto.
"""

from pathlib import Path

from sentence_transformers import SentenceTransformer


class TextEncoder:
    """Encapsula o modelo sentence-transformers para geração de embeddings.

    Carrega o modelo do cache local em models/embeddings/ se disponível.
    Caso contrário, baixa do HuggingFace e salva no cache local para
    execuções futuras offline.

    Attributes:
        model_name: Nome do modelo carregado.
        normalize: Se os vetores são normalizados para norma unitária.
        embedding_dim: Dimensão dos vetores gerados pelo modelo.
    """

    def __init__(
        self,
        model_name: str,
        model_local_path: Path,
        models_dir: Path,
        device: str = "cpu",
        normalize: bool = True,
    ):
        """Carrega o modelo de embedding, priorizando cache local.

        Se model_local_path existir, carrega diretamente sem internet.
        Caso contrário, baixa do HuggingFace e salva em models_dir
        para uso offline nas próximas execuções.

        Args:
            model_name: Nome do modelo sentence-transformers.
            model_local_path: Caminho local esperado para o modelo.
            models_dir: Diretório raiz onde o modelo será salvo após download.
            device: Dispositivo de inferência ('cpu' ou 'cuda').
            normalize: Se True, normaliza vetores para norma unitária.
                Necessário para uso de similaridade de cosseno.
        """
        self.model_name = model_name
        self.normalize = normalize

        if model_local_path.exists():
            self._model = SentenceTransformer(str(model_local_path), device=device)
        else:
            models_dir.mkdir(parents=True, exist_ok=True)
            self._model = SentenceTransformer(
                model_name,
                device=device,
                cache_folder=str(models_dir),
            )

        self.embedding_dim = self._model.get_sentence_embedding_dimension()

    def encode(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        """Gera embeddings para uma lista de textos.

        Args:
            texts: Lista de textos a codificar.
            batch_size: Número de textos processados por lote.

        Returns:
            Lista de vetores de embedding como listas de float.
        """
        vectors = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def encode_single(self, text: str) -> list[float]:
        """Gera embedding para um único texto.

        Usado para codificar queries em tempo de busca.

        Args:
            text: Texto a codificar.

        Returns:
            Vetor de embedding como lista de float.
        """
        return self.encode([text])[0]
