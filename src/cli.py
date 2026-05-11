import logging
import sys
from pathlib import Path

from src.config import AppConfig
from src.pipeline import AIPipeline
from src.notifier import TelegramNotifier

def setup_logging(log_file: Path | None = None):
    level = logging.INFO
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        # Создаём директорию, если её нет
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8", mode="a"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,  # Перезаписываем конфигурацию при повторных вызовах
    )
    
def main():
    setup_logging(Path("logs/automation.log"))
    logger = logging.getLogger(__name__)

    try:
        config = AppConfig()
    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        sys.exit(1)

    notifier = TelegramNotifier(
        bot_token=config.telegram_bot_token if hasattr(config, "telegram_bot_token") else "",
        chat_id=config.telegram_chat_id if hasattr(config, "telegram_chat_id") else "",
        enabled=True,
    )

    pipeline = AIPipeline(config)
    unprocessed = list(pipeline.ingestion.get_unprocessed_files())
    notifier.notify_startup(len(unprocessed))

    if not unprocessed:
        logger.info("✨ Нет необработанных файлов. Выход.")
        return

    logger.info(f"🔄 Начало обработки {len(unprocessed)} файлов")

    try:
        results = pipeline.run()  # возвращает список Path
        logger.info(f"✅ Завершено. Обработано: {len(results)}")
        
        # Считаем успехи/ошибки для отчёта
        success_count = len(results)
        
        # Отправляем уведомления по каждому файлу
        for out_path in results:
            # Читаем YAML frontmatter для передачи данных в бот
            import yaml
            meta = {}
            try:
                content = out_path.read_text(encoding="utf-8")
                if content.startswith("---"):
                    frontmatter = content.split("---")[1]
                    meta = yaml.safe_load(frontmatter) or {}
            except Exception:
                pass
                
            notifier.notify_success(out_path.stem + ".txt", meta)
            
    except Exception as e:
        logger.error(f"💥 Pipeline failed: {e}", exc_info=True)
        notifier.notify_error("system", str(e))
        sys.exit(2)
    finally:
        # Ежедневный отчёт (в продакшене можно вынести в cron)
        notifier.notify_daily_summary(success_count if 'success_count' in locals() else 0, 0)