from pathlib import Path

VENDOR_DIR = Path(__file__).parent / "_vendor"


class tqdm_null_wrapper:
    def __init__(self, iterable, **kwargs):
        self.iterable = iterable

    def __iter__(self):
        for obj in self.iterable:
            yield obj
