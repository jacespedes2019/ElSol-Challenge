import time
import logging
from contextlib import contextmanager

logger = logging.getLogger("elsol")
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@contextmanager
def span(name: str):
    t0 = time.time()
    logger.info(f"▶️  {name} START")
    try:
        yield
    finally:
        dt = time.time() - t0
        logger.info(f"✅ {name} END — {dt:.2f}s")