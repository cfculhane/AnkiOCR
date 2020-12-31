import concurrent
import logging
import platform
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from os import PathLike
from pathlib import Path
from typing import Dict, Optional, List, Union, Tuple

try:
    from anki.collection import Collection
except ImportError:  # Older anki versions
    from anki.storage import Collection

from .api import OCRNote, NotesQuery, OCRImage
from .utils import batch, format_note_id_query

ANKI_ENV = "python" not in Path(sys.executable).stem

SCRIPT_DIR = Path(__file__).parent
DEPS_DIR = SCRIPT_DIR / "deps"

if ANKI_ENV is False:
    sys.path.append(SCRIPT_DIR)
    import pytesseract
    from tqdm import tqdm

    ProgressManager = None

else:
    from aqt.progress import ProgressManager
    from ._vendor import pytesseract

    tqdm = None

logger = logging.getLogger(__name__)
logger.debug(f"ANKI_ENV = {ANKI_ENV}")


class OCR:

    def __init__(self, col: Collection, progress: Optional['ProgressManager'] = None,
                 languages: Optional[List[str]] = None, text_output_location="tooltip",
                 tesseract_exec_pth: Optional[str] = None, num_threads: int = None, batch_size: int = 20):
        self.col = col
        self.media_dir = col.media.dir()
        self.progress = progress
        # ISO 639-2 Code, see https://www.loc.gov/standards/iso639-2/php/code_list.php
        self.languages = languages or ["eng"]

        tesseract_cmd = tesseract_exec_pth or self.path_to_tesseract()
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        assert text_output_location in ["tooltip", "new_field"]
        self.text_output_location = text_output_location
        self.num_threads = num_threads
        self.batch_size = batch_size

    def _ocr_process(self, notes_query: NotesQuery):
        # Split into batches and send each to a different tesseract process
        # Note that the anki.Collection object cannot be accessed by multiple threads at once,
        # So we need to run the OCR then join the results back into the notes afterwards in the main thread

        logger.info(f"Processing {len(notes_query)} notes ...")
        # Note that there might be multiple images per note, so num_batches != batch_size * num_notes
        batched_txts, batched_txts_dir, batch_mapping = self._gen_batched_txts(notes_to_process=notes_query.notes,
                                                                               batch_size=self.batch_size)

        raw_results = {}
        num_batches = len(batched_txts)
        pbar = tqdm(total=num_batches) if ANKI_ENV is False else None

        with ThreadPoolExecutor() as executor:
            # noinspection PyProtectedMember
            logger.debug(f"Using {executor._max_workers} threads")
            completed = 0
            futures = {executor.submit(self._ocr_img, batched_img_txt, self.languages): batched_img_txt for
                       batched_img_txt in
                       batched_txts}

            for future in concurrent.futures.as_completed(futures):
                completed += 1
                batched_img_txt = futures[future]
                raw_results[batched_img_txt] = future.result()
                if self.progress is not None:
                    try:
                        self.progress.update(value=completed, max=num_batches,
                                             label=f"Running OCR... ({round(100 * completed / num_batches)} %)")
                    except TypeError:  # old version of Qt/Anki
                        pass
                elif pbar is not None:
                    pbar.update()

        if self.progress is not None:
            try:
                self.progress.update(value=1, max=1, label=f"Processing OCR Results... ")
            except TypeError:  # old version of Qt/Anki
                pass

        ocr_images = self._process_results(batch_mapping, raw_results)
        logger.info(f"Processed {len(ocr_images)} images in total")
        # Post processing
        for note in notes_query:
            note.add_imgdata_to_note(method=self.text_output_location)

        batched_txts_dir.cleanup()
        self.col.save()

    @staticmethod
    def _process_results(batch_mapping: Dict[str, List[OCRImage]], results: Dict[str, str]):
        split_char = u"\u000C"
        ocr_images = []
        for batch_txt, joined_results in results.items():
            image_results = joined_results.split(split_char)
            for ocr_image, img_result in zip(batch_mapping[batch_txt], image_results):
                cleaned_text = "\n".join([line.strip() for line in img_result.splitlines() if line.strip() != ""])
                ocr_image.text = cleaned_text
                ocr_images.append(ocr_image)
        return ocr_images

    @staticmethod
    def _gen_batched_txts(notes_to_process: List[OCRNote], batch_size: int) -> \
            Tuple[List[str], tempfile.TemporaryDirectory, Dict[str, List[OCRImage]]]:

        batched_txts_dir = tempfile.TemporaryDirectory()  # Need to return so we can cleanup later
        batched_txts = []
        batch_mapping = {}
        images_to_process = []
        for note_images in notes_to_process:
            for fields in note_images.field_images:
                for image in fields.images:
                    images_to_process.append(image)

        for batch_id, batched_imgs in enumerate(batch(images_to_process, batch_size)):
            batch_txt_pth = Path(batched_txts_dir.name, f"batch_imgs_{batch_id}.txt")
            batch_txt_pth.write_text("\n".join([str(i.img_pth) for i in batched_imgs]))
            batched_txts.append(str(batch_txt_pth))
            batch_mapping[str(batch_txt_pth)] = batched_imgs

        return batched_txts, batched_txts_dir, batch_mapping

    @staticmethod
    def _ocr_img(img_pth: Union[Path, str, PathLike], languages: List[str] = None) -> str:
        """ Wrapper for pytesseract.image_to_string"""
        return pytesseract.image_to_string(str(img_pth), lang="+".join(languages or ["eng"]))

    def run_ocr_on_query(self, query: str) -> NotesQuery:
        """ Main method for the ocr class. Runs OCR on a sequence of notes returned from a collection query.

        :param query: Query to collection, see https://docs.ankiweb.net/#/searching for more info.
        """
        notes_query = NotesQuery(col=self.col, query=query)
        # self.col.modSchema(check=True)
        self._ocr_process(notes_query=notes_query)
        self.col.reset()
        logger.info("Databased saved")
        return notes_query

    def run_ocr_on_notes(self, note_ids: List[int]) -> NotesQuery:
        """ Main method for the ocr class. Runs OCR on a sequence of notes returned from a collection query.

        :param note_ids: List of note ids
        """
        # self.col.modSchema(check=True)
        notes_query = NotesQuery(col=self.col, query=format_note_id_query(note_ids))
        # notes_query.note_images = [OCRNote(note_id=nid, col=self.col) for nid in note_ids]
        self._ocr_process(notes_query=notes_query)
        self.col.reset()
        logger.info("Databased saved")
        return notes_query

    def remove_ocr_on_notes(self, note_ids: List[int]):
        """ Removes the OCR field on a sequence of notes returned from a collection query.

        :param note_ids: List of note ids
        """
        # self.col.modSchema(check=True)
        query_notes = NotesQuery(col=self.col, query=format_note_id_query(note_ids))
        for note in query_notes:
            note.remove_OCR_text()
        self.col.reset()
        logger.info("Databased saved")

    @staticmethod
    def path_to_tesseract() -> str:
        exec_data = {"Windows": str(Path(DEPS_DIR, "win", "tesseract", "tesseract.exe")),
                     "Darwin": "/usr/local/bin/tesseract",
                     "Linux": "/usr/local/bin/tesseract"}

        platform_name = platform.system()  # E.g. 'Windows'
        return exec_data[platform_name]
