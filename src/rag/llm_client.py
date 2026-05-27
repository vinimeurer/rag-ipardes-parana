"""
Cliente para comunicação com o modelo de linguagem via Ollama.
"""

import ollama

from ..core.logger import setup_logger
from ..core.rag_config import LLMConfig


class LLMClient:
    """Encapsula a comunicação com o modelo Ollama local.

    Envia prompts ao modelo configurado e retorna a resposta gerada.
    O modelo roda inteiramente na máquina local via Ollama, sem
    nenhuma comunicação com serviços externos.

    Attributes:
        config: Configuração do modelo de linguagem.
        logger: Logger do módulo.
    """

    def __init__(self, config: LLMConfig):
        """Inicializa o cliente com a configuração do LLM.

        Args:
            config: Configuração do modelo Ollama.
        """
        self.config = config
        self.logger = setup_logger(__name__)

    def generate(self, prompt: str) -> str:
        """Envia um prompt ao modelo e retorna a resposta gerada.

        Args:
            prompt: Prompt completo a ser enviado ao modelo.

        Returns:
            Texto da resposta gerada pelo modelo.

        Raises:
            RuntimeError: Se o Ollama não estiver disponível ou o modelo
                não estiver instalado.
        """
        try:
            response = ollama.generate(
                model=self.config.model_name,
                prompt=prompt,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            )
            return response["response"].strip()
        except Exception as e:
            raise RuntimeError(
                f"Erro ao comunicar com Ollama ({self.config.model_name}): {e}\n"
                "Verifique se o Ollama está rodando com: ollama serve"
            ) from e

    def is_available(self) -> bool:
        """Verifica se o modelo está disponível no Ollama local.

        Returns:
            True se o modelo estiver instalado e acessível.
        """
        try:
            models = ollama.list()
            names = [m.model for m in models.models]
            return any(self.config.model_name in name for name in names)
        except Exception:
            return False
