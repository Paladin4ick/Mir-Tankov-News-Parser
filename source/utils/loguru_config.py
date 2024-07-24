from loguru import logger


def setup_logger():
    logger.add(
        "logs/error_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="10 days",
        compression="zip",
        level="ERROR",
    )

    logger.add(
        "logs/success_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="10 days",
        compression="zip",
        level="SUCCESS",
    )

    return logger
