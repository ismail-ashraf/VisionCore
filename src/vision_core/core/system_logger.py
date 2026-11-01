import logging
from vision_core.storage.database import Database

class SQLiteLogHandler(logging.Handler):
    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    def emit(self, record: logging.LogRecord):
        try:
            self.database.save_system_log(
                level=record.levelname,
                event=getattr(record, "event", record.name),
                message=self.format(record),
                camera_id=getattr(record, "camera_id", None),
            )
        except Exception:
            self.handleError(record)


def configure_system_logger(database: Database):
    logger = logging.getLogger("vision_core.system_events")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Prevent adding duplicate handlers during development reloads.
    for handler in logger.handlers[:]:
        if isinstance(handler, SQLiteLogHandler):
            logger.removeHandler(handler)
            handler.close()

    handler = SQLiteLogHandler(database)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(handler)

    return logger
