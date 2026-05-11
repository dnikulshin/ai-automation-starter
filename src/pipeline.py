import logging
from pathlib import Path
from typing import List

from src.config import AppConfig
from src.ingestion import FileIngestion
from src.processor import LLMProcessor
from src.exporter import MarkdownExporter

logger = logging.getLogger(__name__)

class AIPipeline:
    def __init__(self, config: AppConfig, prompt_path: Path | None = None):
        base = Path("data")
        self.ingestion = FileIngestion(base / "input", base / "processed")
        self.exporter = MarkdownExporter(base / "output")
        self.processor = LLMProcessor(config, prompt_path)

    def run(self) -> List[Path]:
        processed = []
        for file_path in self.ingestion.get_unprocessed_files():
            try:
                raw = self.ingestion.read_text(file_path)
                if not raw.strip():
                    logger.warning(f"⚠️ Skipping empty: {file_path.name}")
                    self.ingestion.mark_processed(file_path)
                    continue

                logger.info(f"🔄 Processing: {file_path.name}")
                structured = self.processor.process(raw)
                out = self.exporter.export(file_path.name, structured)
                self.ingestion.mark_processed(file_path)
                processed.append(out)
            except Exception as e:
                logger.error(f"❌ Failed {file_path.name}: {e}")
                # Не перемещаем в processed, чтобы повторить при следующем запуске
        return processed