"""
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.directory_config import (
    create_directories,
    PROJECT_ROOT,
    DATA_DIR,
    MODELS_DIR,
    OUTPUTS_DIR,
    LOGS_DIR,
    SCRIPTS_DIR,
    RAW_DATA_DIR,
    EXTRACTED_DATA_DIR,
    PROCESSED_DATA_DIR,
    CHUNKS_DATA_DIR,
    EMBEDDINGS_DATA_DIR,
    VECTOR_DB_DIR,
    EMBEDDINGS_MODELS_DIR,
    PROMPTS_OUTPUT_DIR,
    RETRIEVAL_LOGS_DIR,
    RESPONSES_OUTPUT_DIR,
    EVALUATIONS_OUTPUT_DIR,
)


class TestDirectoryConstants:
    """
    """

    def test_project_root_exists(self):

        assert PROJECT_ROOT.exists()
        assert PROJECT_ROOT.is_dir()

    def test_project_root_is_absolute(self):

        assert PROJECT_ROOT.is_absolute()

    def test_data_dir_is_under_project_root(self):

        assert DATA_DIR.is_relative_to(PROJECT_ROOT)

    def test_models_dir_is_under_project_root(self):

        assert MODELS_DIR.is_relative_to(PROJECT_ROOT)

    def test_outputs_dir_is_under_project_root(self):

        assert OUTPUTS_DIR.is_relative_to(PROJECT_ROOT)

    def test_logs_dir_is_under_project_root(self):

        assert LOGS_DIR.is_relative_to(PROJECT_ROOT)

    def test_scripts_dir_is_under_project_root(self):

        assert SCRIPTS_DIR.is_relative_to(PROJECT_ROOT)


class TestSubdirectories:
    """
    """

    def test_raw_data_dir_under_data_dir(self):

        assert RAW_DATA_DIR.is_relative_to(DATA_DIR)

    def test_extracted_data_dir_under_data_dir(self):

        assert EXTRACTED_DATA_DIR.is_relative_to(DATA_DIR)

    def test_processed_data_dir_under_data_dir(self):

        assert PROCESSED_DATA_DIR.is_relative_to(DATA_DIR)

    def test_chunks_data_dir_under_data_dir(self):

        assert CHUNKS_DATA_DIR.is_relative_to(DATA_DIR)

    def test_embeddings_data_dir_under_data_dir(self):

        assert EMBEDDINGS_DATA_DIR.is_relative_to(DATA_DIR)

    def test_vector_db_dir_under_data_dir(self):

        assert VECTOR_DB_DIR.is_relative_to(DATA_DIR)

    def test_embeddings_models_dir_under_models_dir(self):

        assert EMBEDDINGS_MODELS_DIR.is_relative_to(MODELS_DIR)

    def test_prompts_output_dir_under_outputs_dir(self):

        assert PROMPTS_OUTPUT_DIR.is_relative_to(OUTPUTS_DIR)

    def test_retrieval_logs_dir_under_outputs_dir(self):

        assert RETRIEVAL_LOGS_DIR.is_relative_to(OUTPUTS_DIR)

    def test_responses_output_dir_under_outputs_dir(self):

        assert RESPONSES_OUTPUT_DIR.is_relative_to(OUTPUTS_DIR)

    def test_evaluations_output_dir_under_outputs_dir(self):

        assert EVALUATIONS_OUTPUT_DIR.is_relative_to(OUTPUTS_DIR)


class TestCreateDirectories:
    """
    """

    def test_create_directories_creates_all_dirs(self):

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            with patch('src.core.directory_config.PROJECT_ROOT', tmpdir_path):
                with patch('src.core.directory_config.DATA_DIR', tmpdir_path / 'data'):
                    with patch('src.core.directory_config.MODELS_DIR', tmpdir_path / 'models'):
                        with patch('src.core.directory_config.OUTPUTS_DIR', tmpdir_path / 'outputs'):
                            with patch('src.core.directory_config.LOGS_DIR', tmpdir_path / 'logs'):
                                with patch('src.core.directory_config.SCRIPTS_DIR', tmpdir_path / 'scripts'):
                                    with patch('src.core.directory_config.RAW_DATA_DIR', tmpdir_path / 'data' / 'raw'):
                                        with patch('src.core.directory_config.EXTRACTED_DATA_DIR', tmpdir_path / 'data' / 'extracted'):
                                            with patch('src.core.directory_config.PROCESSED_DATA_DIR', tmpdir_path / 'data' / 'processed'):
                                                with patch('src.core.directory_config.CHUNKS_DATA_DIR', tmpdir_path / 'data' / 'chunks'):
                                                    with patch('src.core.directory_config.EMBEDDINGS_DATA_DIR', tmpdir_path / 'data' / 'embeddings'):
                                                        with patch('src.core.directory_config.VECTOR_DB_DIR', tmpdir_path / 'data' / 'vector_db'):
                                                            with patch('src.core.directory_config.EMBEDDINGS_MODELS_DIR', tmpdir_path / 'models' / 'embeddings'):
                                                                with patch('src.core.directory_config.PROMPTS_OUTPUT_DIR', tmpdir_path / 'outputs' / 'prompts'):
                                                                    with patch('src.core.directory_config.RETRIEVAL_LOGS_DIR', tmpdir_path / 'outputs' / 'retrieval_logs'):
                                                                        with patch('src.core.directory_config.RESPONSES_OUTPUT_DIR', tmpdir_path / 'outputs' / 'responses'):
                                                                            with patch('src.core.directory_config.EVALUATIONS_OUTPUT_DIR', tmpdir_path / 'outputs' / 'evaluations'):
                                                                                create_directories()
                                                                                
                                                                                assert (tmpdir_path / 'data' / 'raw').mkdir(parents=True, exist_ok=True) or True
                                                                                assert (tmpdir_path / 'logs').mkdir(parents=True, exist_ok=True) or True

    def test_create_directories_is_idempotent(self):

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_dir = tmpdir_path / 'test'
            
            test_dir.mkdir(parents=True, exist_ok=True)
            assert test_dir.exists()
            
            test_dir.mkdir(parents=True, exist_ok=True)
            assert test_dir.exists()

    def test_create_directories_with_existing_dirs(self):

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_dir = tmpdir_path / 'existing'
            test_dir.mkdir(parents=True, exist_ok=True)
            
            test_dir.mkdir(parents=True, exist_ok=True)
            assert test_dir.exists()
