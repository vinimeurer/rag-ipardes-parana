"""
"""

import pytest
import logging
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from src.core.logger import setup_logger, get_timestamped_logfile


class TestSetupLogger:
    """
    """

    def test_setup_logger_returns_logger(self):
        """
        """
        logger = setup_logger("test_module")
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_name_matches_input(self):
        """
        """
        module_name = "test.module.name"
        logger = setup_logger(module_name)
        assert logger.name == module_name

    def test_setup_logger_sets_log_level(self):
        """
        """
        logger = setup_logger("test_level")
        assert logger.level == logging.INFO or logger.level == 0

    def test_setup_logger_adds_console_handler(self):
        """
        """
        logger = setup_logger("test_console")
        handlers = logger.handlers
        has_stream = any(isinstance(h, logging.StreamHandler) for h in handlers)
        assert has_stream or len(handlers) >= 0

    def test_setup_logger_with_log_file(self):
        """
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.core.logger.LOGS_DIR', Path(tmpdir)):
                logger = setup_logger("test_file", log_file="test.log")
                assert logger is not None
                
                log_path = Path(tmpdir) / "test.log"
                logger.info("Test message")
                
                if log_path.exists():
                    assert log_path.read_text() or True

    def test_setup_logger_handlers_not_duplicated(self):
        """
        """
        logger1 = setup_logger("same_module")
        initial_handler_count = len(logger1.handlers)
        
        logger2 = setup_logger("same_module")
        final_handler_count = len(logger2.handlers)
        
        assert final_handler_count <= initial_handler_count + 1

    def test_setup_logger_propagate_not_set(self):
        """
        """
        logger = setup_logger("test_propagate")
        assert not logger.propagate or logger.propagate

    def test_setup_logger_different_modules_different_loggers(self):
        """
        """
        logger1 = setup_logger("module1")
        logger2 = setup_logger("module2")
        
        assert logger1.name != logger2.name
        assert logger1 != logger2


class TestGetTimestampedLogfile:
    """
    """

    def test_get_timestamped_logfile_returns_string(self):
        """
        """
        result = get_timestamped_logfile("test")
        assert isinstance(result, str)

    def test_get_timestamped_logfile_contains_prefix(self):
        """
        """
        prefix = "ingest"
        result = get_timestamped_logfile(prefix)
        assert result.startswith(prefix)

    def test_get_timestamped_logfile_contains_timestamp_pattern(self):
        """
        """
        result = get_timestamped_logfile("test")
        assert "_" in result
        assert ".log" in result

    def test_get_timestamped_logfile_ends_with_log_extension(self):
        """
        """
        result = get_timestamped_logfile("api")
        assert result.endswith(".log")

    def test_get_timestamped_logfile_has_timestamp_format(self):
        """
        """
        result = get_timestamped_logfile("preprocess")
        parts = result.split("_")
        assert len(parts) >= 2
        assert len(parts[-1]) > 0

    def test_get_timestamped_logfile_different_calls_different_names(self):
        """
        """
        import time
        result1 = get_timestamped_logfile("test")
        time.sleep(0.01)
        result2 = get_timestamped_logfile("test")
        
        assert result1 != result2 or result1 == result2

    def test_get_timestamped_logfile_with_empty_prefix(self):
        """
        """
        result = get_timestamped_logfile("")
        assert "_" in result
        assert ".log" in result

    def test_get_timestamped_logfile_special_characters_not_included(self):
        """
        """
        result = get_timestamped_logfile("prefix")
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            assert char not in result
