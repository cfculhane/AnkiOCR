import itertools
import logging
import time
from logging.handlers import MemoryHandler
from pathlib import Path
from typing import Iterable, List

VENDOR_DIR = Path(__file__).parent / "_vendor"

logger = logging.getLogger("anki_ocr")


class AnkiOCRLogger(MemoryHandler):

    def flush(self) -> str:
        log_message = ""
        if len(self.buffer) > 0:
            messages = "\n\n".join([msg.getMessage() for msg in self.buffer])
            log_message = f"\n{'-'*50}\nLog messages encountered during OCR processing: \n\n{messages}"
            self.buffer = []
        try:
            self.release()
        except RuntimeError:
            pass
        return log_message


def create_ocr_logger():
    ocr_logger = logging.getLogger("anki_ocr")
    ocr_logger.addHandler(AnkiOCRLogger(capacity=2000, flushLevel=logging.CRITICAL))
    ocr_logger.setLevel(logging.WARNING)
    return ocr_logger


def batch(it: Iterable, batch_size: int):
    """Batches an Iterable into batches of at most batch_size in length"""
    it = iter(it)
    while True:
        p = tuple(itertools.islice(it, batch_size))
        if not p:
            break
        yield p


def timeit(func):
    """ Decorater to time a function and print to console"""

    def wrapped_f(*args, **kwargs):
        ts = time.time()
        result = func(*args, **kwargs)
        te = time.time()
        print(f"'{func.__name__}' completed in {round(te - ts, 4)} s")
        return result

    return wrapped_f
