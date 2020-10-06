import logging

from anki.hooks import addHook
from aqt import mw
from aqt.browser import Browser, QMenu
from aqt.qt import QAction
from aqt.utils import showInfo, askUser, showCritical

from ._vendor import pytesseract
from .ocr import OCR

logger = logging.getLogger(__name__)


def on_run_ocr(browser: Browser):
    selected_nids = browser.selectedNotes()
    num_notes = len(selected_nids)
    config = mw.addonManager.getConfig(__name__)
    if num_notes == 0:
        showInfo("No cards selected.")
        return
    elif askUser(f"Are you sure you wish to run OCR processing on {num_notes} notes?") is False:
        return

    if config.get("tesseract_install_valid") is not True and config.get("text_output_location") == "new_field":
        showInfo(
            f"Note that because this addon changes the note template, you will see a warning about changing the database and uploading to AnkiWeb. \n"
            f"This is normal, and will be shown each time you modify a note template.\n"
            f"This message will be only be shown once.")
        mw.addonManager.writeConfig(__name__, config)

    config["tesseract_install_valid"] = True  # Stop the above msg appearing multiple times

    progress = mw.progress
    ocr = OCR(col=mw.col, progress=progress, languages=config["languages"])
    progress.start(immediate=True, min=0, max=num_notes)
    try:
        ocr.run_ocr_on_notes(note_ids=selected_nids,
                             overwrite_existing=config["overwrite_existing"])
        progress.finish()
        showInfo(f"Processed OCR for {num_notes} cards")

    except pytesseract.TesseractNotFoundError:
        progress.finish()
        showCritical(text=f"Could not find a valid Tesseract-OCR installation! \n"
                          f"Please visit the addon page in at https://ankiweb.net/shared/info/450181164 for"
                          f" install instructions")
    except Exception as errmsg:
        progress.finish()
        showCritical(f"Error encountered during processing, attempting to stop AnkiOCR gracefully. Error below:\n"
                     f"{errmsg}")
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
    showInfo(f"Removed the OCR field from {num_notes} cards")


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
    addHook("browser.setupMenus", on_menu_setup)
