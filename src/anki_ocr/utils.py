import itertools
import logging
import os
import subprocess
import time
from logging.handlers import MemoryHandler
from pathlib import Path
from typing import Iterable, Optional, Union, Dict, List, Tuple

from anki_ocr import colorlog

VENDOR_DIR = Path(__file__).parent / "_vendor"

logger = logging.getLogger("anki_ocr")


class AnkiOCRLogger(MemoryHandler):
    def flush(self) -> str:  # type: ignore[override]
        log_message = ""
        if len(self.buffer) > 0:
            messages = "\n\n".join([msg.getMessage() for msg in self.buffer])
            log_message = f"\n{'-' * 50}\nLog messages encountered during OCR processing: \n\n{messages}"
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
    """Decorater to time a function and print to console"""

    def wrapped_f(*args, **kwargs):
        ts = time.time()
        result = func(*args, **kwargs)
        te = time.time()
        print(f"'{func.__name__}' completed in {round(te - ts, 4)} s")
        return result

    return wrapped_f


class CalledCommandError(Exception):
    def __init__(self, returncode, cmd, stdout, stderr):
        self.returncode = returncode
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr
        self.message = f"Called cmd {cmd} failed with returncode {returncode}"
        logger.error(
            f"{self.message} \n"
            f"stdout:\n{stdout} \n"
            f"stderr:{stderr} \n"
            f"cmd_str: {' '.join(cmd) if isinstance(cmd, List) else cmd}"
        )
        super().__init__(self.message)


def run_cmd(
    cmd: Union[str, List[str]],
    cwd: Optional[Union[Path, str]] = None,
    extra_env: Optional[Dict] = None,
    capture_output=False,
    text=True,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Runs a cmd and returns its output, allowing the capturing of output and specifying a new environment vars for the
    command to run in.
    :param cmd: Either a string cmd for shell, or a list of args to be run outside of a shell
    :param cwd: Working directory of the process, else will be run in the CLIENT_LIBS_ROOT
    :param extra_env: Dict of extra env to add to the subprocess
    :param capture_output:  If true, will capture output and store it at p.stdout / p.stderr
    :param text: If true, stdout/stderr will be returned as strings rather than bytes
    :returns Tuple of (stdout, stderr) if capture_output is True, else (None, None)
    """
    shell = True if isinstance(cmd, str) else False

    if isinstance(cwd, Path):
        cwd = str(cwd.absolute())

    cwd = cwd or Path(__file__).parent.parent.absolute()
    logger.debug(f"Running cmd: \n{cmd}")
    if extra_env:
        updated_env = os.environ.copy()
        updated_env.update(extra_env)

    p = subprocess.run(cmd, shell=shell, cwd=cwd, env=extra_env, check=False, capture_output=capture_output, text=text)
    if p.returncode != 0:
        raise CalledCommandError(returncode=p.returncode, cmd=cmd, stdout=p.stdout, stderr=p.stderr)
    if capture_output:
        return p.stdout.rstrip(), p.stderr.rstrip()
    else:
        return None, None


def create_logger(name: str) -> logging.Logger:
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    _logger = colorlog.getLogger(name)
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = True
    return _logger
