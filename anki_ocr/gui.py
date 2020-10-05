# import the main window object (mw) from aqt

from anki.hooks import addHook
from aqt import mw
# import all of the Qt GUI library
from aqt.browser import Browser, QMenu
from aqt.qt import QAction
# import the "show info" tool from utils.py
from aqt.utils import showInfo, askUser

from anki_ocr.ocr import OCR

# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
CONFIG = mw.addonManager.getConfig(__name__)


def on_run_ocr(browser: Browser):
    selected_nids = browser.selectedNotes()
    num_notes = len(selected_nids)
    if num_notes == 0:
        showInfo("No cards selected.")
        return
    elif askUser(f"Are you sure you wish to run OCR processing on {num_notes} notes?") is False:
        return

    progress = mw.progress
    ocr = OCR(col=mw.col, progress=progress, languages=CONFIG["languages"])
    progress.start(immediate=True, min=0, max=num_notes)
    ocr.run_ocr_on_notes(note_ids=selected_nids,
                         overwrite_existing=CONFIG["overwrite_existing"])
    progress.finish()
    browser.model.reset()
    mw.requireReset()
    showInfo(f"Processed OCR for {num_notes} cards")


def on_rm_ocr_fields(browser: Browser):
    selected_nids = browser.selectedNotes()
    num_notes = len(selected_nids)
    if num_notes == 0:
        showInfo("No cards selected.")
        return
    elif askUser(f"Are you sure you wish to remove the OCR field from {num_notes} notes?") is False:
        return

    progress = mw.progress
    progress.start(immediate=True)
    ocr = OCR(col=mw.col, progress=progress, languages=CONFIG["languages"])
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

    act_rm_ocr_fields = QAction(browser, text="Remove OCR field from selected notes")
    act_rm_ocr_fields.triggered.connect(lambda b=browser: on_rm_ocr_fields(browser))
    anki_ocr_menu.addAction(act_rm_ocr_fields)

    browser_cards_menu = browser.form.menu_Cards
    browser_cards_menu.addSeparator()
    browser_cards_menu.addMenu(anki_ocr_menu)


def create_menu():
    addHook("browser.setupMenus", on_menu_setup)
