import time
import traceback
from math import ceil
from typing import List

from PyQt5.QtWidgets import QMenu
from aqt import mw
from aqt.browser import Browser
from aqt.qt import QAction
from aqt.utils import showInfo, askUser, showCritical

from ._vendor import pytesseract
from .ocr import OCR
from .utils import create_ocr_logger

logger = create_ocr_logger()


def on_run_ocr(browser: Browser):
    time_start = time.time()

    selected_nids = browser.selectedNotes()
    config = mw.addonManager.getConfig(__name__)
    num_notes = len(selected_nids)
    num_batches = ceil(num_notes / config["batch_size"])

    if num_notes == 0:
        showInfo("No cards selected.")
        return
    elif askUser(f"Are you sure you wish to run OCR processing on {num_notes} notes?") is False:
        return

    if config.get("tesseract_install_valid") is not True and config.get("text_output_location") == "new_field":
        showInfo(
            f"Note that because this addon changes the note template, you will see a warning about changing the "
            f"database and uploading to AnkiWeb. \n "
            f"This is normal, and will be shown each time you modify a note template.\n"
            f"This message will be only be shown once.")

    config["tesseract_install_valid"] = True  # Stop the above msg appearing multiple times
    mw.addonManager.writeConfig(__name__, config)

    try:
        progress = mw.progress
        progress.start(immediate=True, min=0, max=num_batches)
        progress.update(value=0, max=num_batches, label="Starting OCR processing...")
    except TypeError:  # old version of Qt/Anki
        progress = None

    ocr = OCR(col=mw.col,
              progress=progress,
              languages=config["languages"],
              text_output_location=config["text_output_location"],
              tesseract_exec_pth=config["tesseract_exec_path"] if config["override_tesseract_exec"] else None,
              batch_size=config["batch_size"], num_threads=config["num_threads"], use_batching=config["use_batching"],
              use_multithreading=config["use_multithreading"])
    try:
        ocr.run_ocr_on_notes(note_ids=selected_nids)
        if progress:
            progress.finish()
        time_taken = time.time() - time_start
        log_messages = logger.handlers[0].flush()
        showInfo(
            f"Processed OCR for {num_notes} notes in {round(time_taken, 1)}s ({round(time_taken / num_notes, 1)}s per note)\n"
            f"{log_messages}")

    except pytesseract.TesseractNotFoundError:
        if progress:
            progress.finish()
        showCritical(text=f"Could not find a valid Tesseract-OCR installation! \n"
                          f"Please visit the addon page in at https://ankiweb.net/shared/info/450181164 for"
                          f" install instructions")

    except (RuntimeError, Exception) as exc:
        from anki_ocr import __version__ as anki_ocr_version
        from anki.buildinfo import version as anki_version
        import sys
        import platform

        if progress:
            progress.finish()
        msg = f"Error encountered during processing. Debug info: \n" \
              f"Anki Version: {anki_version} , AnkiOCR Version: {anki_ocr_version}\n" \
              f"Platform: {platform.system()} , Python Version: {sys.version}"
        log_messages = logger.handlers[0].flush()
        if len(log_messages) > 0:
            msg += f"Logging message generated during processing:\n{log_messages}"
        exception_str: List[str] = traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
        msg += "".join(exception_str)
        showInfo(msg)

    finally:

        browser.model.reset()
        mw.requireReset()


def on_rm_ocr_fields(browser: Browser):
    config = mw.addonManager.getConfig(__name__)
    selected_nids = browser.selectedNotes()
    num_notes = len(selected_nids)
    if num_notes == 0:
        showInfo("No cards selected.")
        return
    elif askUser(f"Are you sure you wish to remove the OCR field from {num_notes} notes?") is False:
        return

    progress = mw.progress
    progress.start(immediate=True)
    ocr = OCR(col=mw.col, progress=progress, languages=config["languages"])
    ocr.remove_ocr_on_notes(note_ids=selected_nids)
    mw.progress.finish()
    browser.model.reset()
    mw.requireReset()
    log_messages = logger.handlers[0].flush()
    showInfo(f"Removed the OCR field from {num_notes} cards\n"
             f"{log_messages}")


def on_menu_setup(browser: Browser):
    anki_ocr_menu = QMenu(("AnkiOCR"), browser)

    act_run_ocr = QAction(browser, text="Run AnkiOCR on selected notes")
    act_run_ocr.triggered.connect(lambda b=browser: on_run_ocr(browser))
    anki_ocr_menu.addAction(act_run_ocr)

    act_rm_ocr_fields = QAction(browser, text="Remove OCR data from selected notes")
    act_rm_ocr_fields.triggered.connect(lambda b=browser: on_rm_ocr_fields(browser))
    anki_ocr_menu.addAction(act_rm_ocr_fields)

    browser_cards_menu = browser.form.menu_Cards
    browser_cards_menu.addSeparator()
    browser_cards_menu.addMenu(anki_ocr_menu)


def create_menu():
    from anki.hooks import addHook
    addHook("browser.setupMenus", on_menu_setup)
