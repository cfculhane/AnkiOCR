import itertools
import logging
import time
from pathlib import Path
from typing import Iterable

VENDOR_DIR = Path(__file__).parent / "_vendor"
logger = logging.getLogger(__name__)


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
