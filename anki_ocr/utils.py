import platform
from pathlib import Path

DEPS_DIR = Path(__file__).parent / "deps"
VENDOR_DIR = Path(__file__).parent / "_vendor"


class tqdm_null_wrapper:
    def __init__(self, iterable, **kwargs):
        self.iterable = iterable

    def __iter__(self):
        for obj in self.iterable:
            yield obj


def path_to_tesseract():
    exec_data = {"Windows": str(Path(DEPS_DIR, "win", "tesseract", "tesseract.exe")),
                 "Darwin": "/usr/local/bin/tesseract",
                 "Linux": "/usr/local/bin/tesseract"}

    platform_name = platform.system()  # E.g. 'Windows'
    return exec_data[platform_name], platform_name
