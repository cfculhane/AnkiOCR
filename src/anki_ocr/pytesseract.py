# Modified pytesseract to work with Anki, see original https://github.com/madmaze/pytesseract
import re
import shlex
import string
import subprocess
import sys
from contextlib import contextmanager
from distutils.version import LooseVersion
from enum import Enum
from errno import ENOENT
from functools import wraps
from glob import iglob
from os import environ
from os import extsep
from os import linesep
from os import remove
from os.path import normcase
from os.path import normpath
from os.path import realpath
from tempfile import NamedTemporaryFile
from time import sleep
from typing import Optional

# Anki does not come with Pillow, numpy or pandas installed, and I'm not going to attempt to vendorise it!
tesseract_cmd = "tesseract"

DEFAULT_ENCODING = "utf-8"
LANG_PATTERN = re.compile("^[a-z_]+$")
RGB_MODE = "RGB"
SUPPORTED_FORMATS = {
    "JPEG",
    "PNG",
    "PBM",
    "PGM",
    "PPM",
    "TIFF",
    "BMP",
    "GIF",
    "WEBP",
}


class Output(Enum):
    BYTES = 0
    STRING = 1


class PandasNotSupported(EnvironmentError):
    def __init__(self):
        super().__init__("Missing pandas package")


class TesseractError(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        self.args = (status, message)


class TesseractNotFoundError(EnvironmentError):
    def __init__(self):
        super().__init__(
            f"{tesseract_cmd} is not installed or it's not in your PATH." + " See README file for more information.",
        )


class TSVNotSupported(EnvironmentError):
    def __init__(self):
        super().__init__(
            "TSV output not supported. Tesseract >= 3.05 required",
        )


class ALTONotSupported(EnvironmentError):
    def __init__(self):
        super().__init__(
            "ALTO output not supported. Tesseract >= 4.1.0 required",
        )


def kill(process, code):
    process.terminate()
    try:
        process.wait(1)
    except TypeError:  # python2 Popen.wait(1) fallback
        sleep(1)
    except Exception:  # python3 subprocess.TimeoutExpired
        pass
    finally:
        process.kill()
        process.returncode = code


@contextmanager
def timeout_manager(proc, seconds=None):
    try:
        if not seconds:
            yield proc.communicate()[1]
            return

        try:
            _, error_string = proc.communicate(timeout=seconds)
            yield error_string
        except subprocess.TimeoutExpired:
            kill(proc, -1)
            raise RuntimeError("Tesseract process timeout")
    finally:
        proc.stdin.close()
        proc.stdout.close()
        proc.stderr.close()


def run_once(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if wrapper._result is wrapper:
            wrapper._result = func(*args, **kwargs)
        return wrapper._result

    wrapper._result = wrapper
    return wrapper


def get_errors(error_string):
    return " ".join(line for line in error_string.decode(DEFAULT_ENCODING).splitlines()).strip()


def cleanup(temp_name):
    """Tries to remove temp files by filename wildcard path."""
    for filename in iglob(temp_name + "*" if temp_name else temp_name):
        try:
            remove(filename)
        except OSError as e:
            if e.errno != ENOENT:
                raise e


@contextmanager
def save(image):
    try:
        with NamedTemporaryFile(prefix="tess_", delete=False) as f:
            if isinstance(image, str):
                yield f.name, realpath(normpath(normcase(image)))
                return
            else:
                raise TypeError("Only file paths are supported as Pillow and Numpy are not installed in Anki!")
    finally:
        cleanup(f.name)


def subprocess_args(include_stdout=True):
    # See https://github.com/pyinstaller/pyinstaller/wiki/Recipe-subprocess
    # for reference and comments.

    kwargs = {
        "stdin": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "startupinfo": None,
        "env": environ,
    }

    if hasattr(subprocess, "STARTUPINFO"):
        kwargs["startupinfo"] = subprocess.STARTUPINFO()
        kwargs["startupinfo"].dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs["startupinfo"].wShowWindow = subprocess.SW_HIDE

    if include_stdout:
        kwargs["stdout"] = subprocess.PIPE
    else:
        kwargs["stdout"] = subprocess.DEVNULL

    return kwargs


def run_tesseract(
    input_filename,
    output_filename_base,
    extension,
    lang,
    config="",
    nice=0,
    timeout=0,
):
    cmd_args = []

    if not sys.platform.startswith("win32") and nice != 0:
        cmd_args += ("nice", "-n", str(nice))

    cmd_args += (tesseract_cmd, input_filename, output_filename_base)

    if lang is not None:
        cmd_args += ("-l", lang)

    if config:
        cmd_args += shlex.split(config)

    if extension and extension not in {"box", "osd", "tsv", "xml"}:
        cmd_args.append(extension)

    try:
        proc = subprocess.Popen(cmd_args, **subprocess_args())
    except OSError as e:
        if e.errno != ENOENT:
            raise e
        raise TesseractNotFoundError()

    with timeout_manager(proc, timeout) as error_string:
        if proc.returncode:
            raise TesseractError(proc.returncode, get_errors(error_string))


def run_and_get_output(
    image,
    extension="",
    lang=None,
    config="",
    nice=0,
    timeout=0,
    return_bytes=False,
):
    with save(image) as (temp_name, input_filename):
        kwargs = {
            "input_filename": input_filename,
            "output_filename_base": temp_name,
            "extension": extension,
            "lang": lang,
            "config": config,
            "nice": nice,
            "timeout": timeout,
        }

    run_tesseract(**kwargs)
    filename = kwargs["output_filename_base"] + extsep + extension
    with open(filename, "rb") as output_file:
        if return_bytes:
            return output_file.read()
        return output_file.read().decode(DEFAULT_ENCODING)


def file_to_dict(tsv, cell_delimiter, str_col_idx):
    result = {}
    rows = [row.split(cell_delimiter) for row in tsv.strip().split("\n")]
    if len(rows) < 2:
        return result

    header = rows.pop(0)
    length = len(header)
    if len(rows[-1]) < length:
        # Fixes bug that occurs when last text string in TSV is null, and
        # last row is missing a final cell in TSV file
        rows[-1].append("")

    if str_col_idx < 0:
        str_col_idx += length

    for i, head in enumerate(header):
        result[head] = list()
        for row in rows:
            if len(row) <= i:
                continue

            val = row[i]
            if row[i].isdigit() and i != str_col_idx:
                val = int(row[i])
            result[head].append(val)

    return result


def is_valid(val, _type):
    if _type is int:
        return val.isdigit()

    if _type is float:
        try:
            float(val)
            return True
        except ValueError:
            return False

    return True


@run_once
def get_languages(config=""):
    cmd_args = [tesseract_cmd, "--list-langs"]
    if config:
        cmd_args += shlex.split(config)

    try:
        result = subprocess.run(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except OSError:
        raise TesseractNotFoundError()

    # tesseract 3.x
    if result.returncode not in (0, 1):
        raise TesseractNotFoundError()

    languages = []
    if result.stdout:
        for line in result.stdout.decode(DEFAULT_ENCODING).split(linesep):
            lang = line.strip()
            if LANG_PATTERN.match(lang):
                languages.append(lang)

    return languages


@run_once
def get_tesseract_version():
    """
    Returns LooseVersion object of the Tesseract version
    """
    try:
        output = subprocess.check_output(
            [tesseract_cmd, "--version"],
            stderr=subprocess.STDOUT,
            env=environ,
            stdin=subprocess.DEVNULL,
        )
    except OSError:
        raise TesseractNotFoundError()

    raw_version = output.decode(DEFAULT_ENCODING)
    version = raw_version.lstrip(string.printable[10:])

    try:
        loose_version = LooseVersion(version)
        assert loose_version > "0"
    except AttributeError:
        raise SystemExit(f'Invalid tesseract version: "{raw_version}"')

    return loose_version


def image_to_string(
    image: str,
    lang: Optional[str] = None,
    config: str = "",
    nice: int = 0,
    timeout=0,
):
    """
    Returns the result of a Tesseract OCR run on the provided image to string
    """
    args = [image, "txt", lang, config, nice, timeout]

    return run_and_get_output(*args)
