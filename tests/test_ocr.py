# Some basic tests to make sure major breaking changes dont occur
import shutil
from pathlib import Path

import pytesseract
from anki import Collection

from anki_ocr.api import NotesQuery
from anki_ocr.ocr import OCR
from anki_ocr.utils import format_note_id_query

TESTDATA_DIR = Path(__file__).parent / "testdata"
TEMPLATE_COLLECTION_PTH = TESTDATA_DIR / "test_collection_template" / "collection.anki2"
assert TEMPLATE_COLLECTION_PTH.exists()


# TEMPLATE_COLLECTION = Collection(path=str(TEMPLATE_COLLECTION_PTH))


def gen_test_collection(new_dir) -> Collection:
    """Generates a test collection for us in tests, by copying a template collection"""
    # col_dir = Path(tmp_path_factory, "Collection")
    # col_dir.mkdir()
    print(new_dir)
    shutil.copytree(TEMPLATE_COLLECTION_PTH.parent, new_dir, dirs_exist_ok=True)
    test_col_pth = Path(new_dir, TEMPLATE_COLLECTION_PTH.name)
    assert test_col_pth
    test_col = Collection(path=str(TEMPLATE_COLLECTION_PTH))
    return test_col


class TestOCR:
    test_img_pths = list(Path(TESTDATA_DIR, "annotated_imgs").glob("*"))
    tesseract_cmd = OCR.path_to_tesseract()
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def test_collection_ok(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        assert test_col.basicCheck()

    def test_ocr_img_with_lang(self):
        img_path = self.test_img_pths[0]
        img = str(img_path.absolute())
        ocr_result = OCR._ocr_img(img, num_threads=1, languages=["eng"])
        assert "Superior vena cava" in ocr_result

    def test_ocr_img_without_lang(self):
        img_path = self.test_img_pths[0]
        img = str(img_path.absolute())
        ocr_result = OCR._ocr_img(img, num_threads=1)
        assert "Superior vena cava" in ocr_result

    def test_gen_queryimages(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        ocr = OCR(col=test_col)
        q_images = NotesQuery(col=test_col, query="")
        print(q_images)

    def test_query_noteids(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        ocr = OCR(col=test_col)
        note_ids = [1601851621708, 1601851571572]
        query = format_note_id_query(note_ids)
        q_images = NotesQuery(col=test_col, query=query)
        assert len(q_images.notes) == 2
        for note in q_images.notes:
            assert note.note_id in note_ids

    def test_run_ocr_on_collection(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        ocr = OCR(col=test_col)
        ocr.run_ocr_on_query(query="")


    def test_run_ocr_on_notes_batched_multithreaded(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        ocr = OCR(col=test_col, use_batching=True, num_threads=4)
        ocr.run_ocr_on_notes(note_ids=[1601851571572, 1601851621708])

    def test_run_ocr_on_notes_batched_single_threaded(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        ocr = OCR(col=test_col, use_batching=True, num_threads=1)
        ocr.run_ocr_on_notes(note_ids=[1601851571572, 1601851621708])

    def test_run_ocr_on_notes_unbatched_multithreaded(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        ocr = OCR(col=test_col, use_batching=False, num_threads=4)
        ocr.run_ocr_on_notes(note_ids=[1601851571572, 1601851621708])

    def test_run_ocr_on_notes_unbatched_singlethreaded(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        ocr = OCR(col=test_col, use_batching=False, num_threads=1)
        ocr.run_ocr_on_notes(note_ids=[1601851571572, 1601851621708])

    def test_add_ocr_field_then_remove_text_tooltip(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        ocr = OCR(col=test_col, text_output_location="tooltip")
        note_ids = [1601851571572, 1601851621708]
        ocr.run_ocr_on_notes(note_ids=note_ids)
        ocr.remove_ocr_on_notes(note_ids=note_ids)

    def test_add_ocr_field_then_remove_text_new_field(self, tmpdir):
        col_dir = tmpdir.mkdir("collection")
        test_col = gen_test_collection(col_dir)
        ocr = OCR(col=test_col, text_output_location="new_field")
        note_ids = [1601851571572, 1601851621708]
        ocr.run_ocr_on_notes(note_ids=note_ids)
        ocr.remove_ocr_on_notes(note_ids=note_ids)

    def test_clean_ocr_text(self):
        input_str = "this is some text: with a result\n\n\nThis is some double colon :: with result" \
                     "\n\nwithout spaces::new word\none space:: new word\n\n\n\none space before ::new word\n" \
                     "triple ::: new word\n\n\n\n\nquadruple ::::newword"""
        expected_output = "this is some text: with a result\nThis is some double colon : with result\n" \
                          "without spaces:new word\none space: new word\none space before :new word\n" \
                          "triple : new word\nquadruple :newword"
        output = OCR.clean_ocr_text(input_str)
        assert output == expected_output
