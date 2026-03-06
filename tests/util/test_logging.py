from __future__ import annotations

import logging

from installer_framework.util.logging import configure_logging, get_logger


def test_get_logger_returns_named_logger():
    logger = get_logger("tips.test")
    assert logger.name == "tips.test"


def test_configure_logging_sets_basic_config():
    configure_logging(level=logging.DEBUG)
    root = logging.getLogger()
    assert isinstance(root, logging.Logger)
