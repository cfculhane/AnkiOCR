# Some basic tests to make sure major breaking changes dont occur
from pathlib import Path

import pytesseract
from anki import Collection

from anki_ocr.ocr import OCR

TESTDATA_DIR = Path(__file__).parent / "testdata"
COLLECTION = Collection(TESTDATA_DIR / "test_collection" / "collection.anki2")


class TestOCR:
    test_img_pths = list(Path(TESTDATA_DIR, "imgs").glob("*"))
    tesseract_cmd = OCR.path_to_tesseract()
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def test_collection_ok(self):
        assert COLLECTION.basicCheck()

    def test_ocr_img_with_lang(self):
        img_path = self.test_img_pths[0]
        img = str(img_path.absolute())
        ocr_result = OCR.ocr_img(img, languages=["eng"])
        assert "Superior vena cava" in ocr_result

    def test_ocr_img_without_lang(self):
        img_path = self.test_img_pths[0]
        img = str(img_path.absolute())
        ocr_result = OCR.ocr_img(img)
        assert "Superior vena cava" in ocr_result

    def test_process_imgs(self):
        ocr = OCR(col=COLLECTION)
        ocr.get_images_from_note(COLLECTION.getNote(0))
