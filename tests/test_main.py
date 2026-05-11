import logging
import sys
from unittest.mock import patch, MagicMock
import pytest

from src.cli import main

def test_main_exits_cleanly_when_no_files(capsys):
    # Простой мок: перенаправляем логи в stdout, чтобы capsys их поймал
    def mock_setup_logging(log_file=None):
        logging.basicConfig(
            level=logging.INFO,
            stream=sys.stdout,
            format="%(message)s",
            force=True,
        )

    mock_config = MagicMock()
    mock_config.telegram_bot_token = ""
    mock_config.telegram_chat_id = ""

    mock_pipeline = MagicMock()
    mock_pipeline.ingestion.get_unprocessed_files.return_value = []
    mock_pipeline.run.return_value = []

    with patch("src.cli.AppConfig", return_value=mock_config), \
         patch("src.cli.AIPipeline", return_value=mock_pipeline), \
         patch("src.cli.setup_logging", mock_setup_logging):

        main()

        captured = capsys.readouterr()
        assert "Нет необработанных файлов" in captured.out
        mock_pipeline.run.assert_not_called()