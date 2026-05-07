#!/usr/bin/env python3
"""Script principal para pré-processamento de documentos PDF extraídos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logger import setup_logger
from src.core.constants import EXTRACTED_DATA_DIR, PROCESSED_DATA_DIR

logger = setup_logger(__name__)

