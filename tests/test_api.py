from pathlib import Path

from anki_ocr.api import OCRField

TESTDATA_DIR = Path(__file__).parent / "testdata"
COLLECTION_MEDIA_DIR = TESTDATA_DIR / "test_collection_template/collection.media"

assert TESTDATA_DIR.exists()
assert COLLECTION_MEDIA_DIR.exists()


class TestOCRField:
    def test_field_img_is_link(self):
        invalid_field = OCRField(
            field_name="Front",
            field_text="""<img src="https://upload.wikimedia.org/wikipedia/commons/f/f0/Tesseractv411_light.png">""",
            note_id=0,
            media_dir=str(COLLECTION_MEDIA_DIR.absolute()),
        )
        print(invalid_field.images)
