import logging
from pathlib import Path

from anki import Collection

from anki_ocr.ocr import SCRIPT_DIR, OCR

if __name__ == '__main__':
    logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=logging_format, level=logging.INFO)
    # Not to be run inside Anki
    PROFILE_HOME = Path(SCRIPT_DIR.parent, "tests/User 1")
    cpath = PROFILE_HOME / "collection.anki2"

    collection = Collection(str(cpath), log=True)  # Collection is locked from here on

    ocr = OCR(col=collection, text_output_location="new_field")
    all_note_ids = ocr.col.db.list("select * from notes")
    ocr.run_ocr_on_query(note_ids=all_note_ids)
    # collection.close(save=True)
    # ocr.remove_ocr_on_notes(note_ids_c)
