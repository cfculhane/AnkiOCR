import subprocess
import sys
from pathlib import Path

VENDOR_DIR = Path(__file__).parent / "_vendor"
class tqdm_null_wrapper:
    def __init__(self, iterable, **kwargs):
        self.iterable = iterable

    def __iter__(self):
        for obj in self.iterable:
            yield obj



def install(package_name):
    from ._vendor import pip
    print(f"Attempting to install {package_name}")
    pip.main(['install', package_name, f'--install-option="--prefix={VENDOR_DIR.absolute()}"'])

