import concurrent
import logging
import os
import platform
import re
import sys
import tempfile
from concurrent.futures.thread import ThreadPoolExecutor
from os import PathLike
from pathlib import Path
from typing import Dict, Optional, List, Union, Tuple

from aqt.utils import askUser

try:
    from anki.collection import Collection
except ImportError:  # Older anki versions
    from anki.storage import Collection

from .api import OCRNote, NotesQuery, OCRImage
from .utils import batch

ANKI_ENV = "python" not in Path(sys.executable).stem

SCRIPT_DIR = Path(__file__).parent
DEPS_DIR = SCRIPT_DIR / "deps"
TESSDATA_DIR = DEPS_DIR / "tessdata"

if ANKI_ENV is False:
    sys.path.append(str(SCRIPT_DIR.absolute()))
    import pytesseract
    from tqdm import tqdm

    ProgressManager = None

else:
    from aqt.progress import ProgressManager
    from ._vendor import pytesseract

    tqdm = None

logger = logging.getLogger("anki_ocr")


class OCR:

    def __init__(self, col: Optional[Collection], progress: Optional['ProgressManager'] = None,
                 languages: Optional[List[str]] = None, text_output_location="tooltip",
                 tesseract_exec_pth: Optional[str] = None, num_threads: int = None, batch_size: int = 5,
                 use_batching=True, use_multithreading=True):
        self.col = col
        self.progress = progress
        # ISO 639-2 Code, see https://www.loc.gov/standards/iso639-2/php/code_list.php
        self.languages = languages or ["eng"]

        tesseract_cmd = tesseract_exec_pth or self.path_to_tesseract()
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        assert text_output_location in ["tooltip", "new_field"]
        self.text_output_location = text_output_location
        self.use_batching = use_batching
        self.use_multithreading = use_multithreading
        if use_multithreading is True:
            self.num_threads = num_threads or os.cpu_count()
        else:
            self.num_threads = 1
        self.batch_size = batch_size

    def _ocr_batch_process(self, batched_txts):
        # Split into batches and send each to a different tesseract process
        # Note that the anki.Collection object cannot be accessed by multiple threads at once,
        # So we need to run the OCR then join the results back into the notes afterwards in the main thread
        raw_results = {}
        completed = 0

        # Note that there might be multiple images per note, so num_batches != batch_size * num_notes

        num_batches = len(batched_txts)
        pbar = tqdm(total=num_batches) if ANKI_ENV is False else None

        if self.use_multithreading is True:
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                # noinspection PyProtectedMember
                logger.info(f"Using {executor._max_workers} threads")
                completed = 0
                futures = {
                    executor.submit(self._ocr_img, batched_img_txt, self.num_threads, self.languages): batched_img_txt
                    for
                    batched_img_txt in
                    batched_txts}

                for future in concurrent.futures.as_completed(futures):
                    completed += 1
                    batched_img_txt = futures[future]
                    raw_results[batched_img_txt] = future.result()
                    if self.progress is not None:
                        self.progress.update(value=completed, max=num_batches,
                                             label=f"Running OCR... ({round(100 * completed / num_batches)} %)")
                        want_cancel = self.progress.want_cancel()
                        if want_cancel is True:
                            if askUser(f"Cancel processing?") is True:
                                for future_to_cancel in futures:
                                    future_to_cancel.cancel()
                                raise RuntimeError("Cancelled futures")
                            else:
                                self.progress._win.wantCancel = False
                    elif pbar is not None:
                        pbar.update()
        else:
            for batched_img_txt in batched_txts:
                ocr_text = self._ocr_img(batched_img_txt, num_threads=self.num_threads, languages=self.languages)
                completed += 1
                raw_results[batched_img_txt] = ocr_text
                if self.progress is not None:
                    self.progress.update(value=completed, max=num_batches,
                                         label=f"Running OCR... ({round(100 * completed / num_batches)} %)")
                    want_cancel = self.progress.want_cancel()
                    if want_cancel is True:
                        if askUser(f"Cancel processing?") is True:
                            raise RuntimeError("Cancelled single threaded")
                        else:
                            self.progress._win.wantCancel = False
                elif pbar is not None:
                    pbar.update()

        return raw_results

    def _ocr_unbatched_process(self, image_paths: List[str]):

        raw_results = {}
        completed = 0
        pbar = tqdm(total=len(image_paths)) if ANKI_ENV is False else None

        if self.use_multithreading is True:
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                # noinspection PyProtectedMember
                logger.info(f"Using {executor._max_workers} threads")
                completed = 0
                futures = {
                    executor.submit(self._ocr_img, image_path, self.num_threads, self.languages): image_path
                    for
                    image_path in
                    image_paths}

                for future in concurrent.futures.as_completed(futures):
                    completed += 1
                    image_path = futures[future]
                    raw_results[image_path] = future.result()
                    if self.progress is not None:
                        self.progress.update(value=completed, max=len(image_paths),
                                             label=f"Running OCR... ({round(100 * completed / len(image_paths))} %)")
                        want_cancel = self.progress.want_cancel()
                        if want_cancel is True:
                            if askUser(f"Cancel processing?") is True:
                                for future_to_cancel in futures:
                                    future_to_cancel.cancel()
                                raise RuntimeError("Cancelled futures")
                            else:
                                self.progress._win.wantCancel = False
                    elif pbar is not None:
                        pbar.update()
        else:
            for image_path in image_paths:
                ocr_text = self._ocr_img(image_path, num_threads=self.num_threads, languages=self.languages)
                completed += 1
                raw_results[image_path] = ocr_text

                if self.progress is not None:
                    self.progress.update(value=completed, max=len(image_paths),
                                         label=f"Running OCR... ({round(100 * completed / len(image_paths))} %)")
                    want_cancel = self.progress.want_cancel()
                    if want_cancel is True:
                        if askUser(f"Cancel processing?") is True:
                            raise RuntimeError("Cancelled single threaded")
                        else:
                            self.progress._win.wantCancel = False
                elif pbar is not None:
                    pbar.update()
        return raw_results

    @staticmethod
    def clean_ocr_text(ocr_text: str) -> str:
        """
        :param ocr_text: Text output from tesseract
        :returns: Cleaned text with extraneous newlines and double colon's removed
        """
        cleaned_text = "\n".join([line.strip() for line in ocr_text.splitlines() if line.strip() != ""])
        cleaned_text = re.sub(":+", ":", cleaned_text)
        return cleaned_text

    @staticmethod
    def _process_batched_results(batch_mapping: Dict[str, List[OCRImage]], results: Dict[str, str]) -> List[OCRImage]:
        split_char = u"\u000C"
        ocr_images = []
        for batch_txt, joined_results in results.items():
            image_results = joined_results.split(split_char)
            for ocr_image, ocr_text in zip(batch_mapping[batch_txt], image_results):
                cleaned_text = "\n".join([line.strip() for line in ocr_text.splitlines() if line.strip() != ""])
                ocr_image.text = cleaned_text
                ocr_images.append(ocr_image)
        return ocr_images

    @staticmethod
    def _process_single_results(unbatched_mapped: List[Dict], raw_results: Dict[str, str]) -> List[OCRImage]:
        ocr_images = []
        for mapped_image in unbatched_mapped:
            ocr_image = mapped_image["image"]
            image_path = mapped_image["path"]
            ocr_text = raw_results[image_path]
            cleaned_text = "\n".join([line.strip() for line in ocr_text.splitlines() if line.strip() != ""])
            ocr_image.text = cleaned_text
            ocr_images.append(ocr_image)
        return ocr_images

    @classmethod
    def _gen_batched_txts(cls, notes_to_process: List[OCRNote], batch_size: int) -> \
            Tuple[List[str], tempfile.TemporaryDirectory, Dict[str, List[OCRImage]]]:

        batched_txts_dir = tempfile.TemporaryDirectory()  # Need to return so we can cleanup later
        batched_txts = []
        batch_mapping = {}
        images_to_process = cls._gen_images_to_process(notes_to_process=notes_to_process)

        for batch_id, batched_imgs in enumerate(batch(images_to_process, batch_size)):
            batch_txt_pth = Path(batched_txts_dir.name, f"batch_imgs_{batch_id}.txt")
            batch_txt_pth.write_text("\n".join([str(i.img_pth) for i in batched_imgs]))
            batched_txts.append(str(batch_txt_pth))
            batch_mapping[str(batch_txt_pth)] = batched_imgs

        return batched_txts, batched_txts_dir, batch_mapping

    @staticmethod
    def _gen_images_to_process(notes_to_process: List[OCRNote]) -> List[OCRImage]:
        images_to_process = []
        for note_images in notes_to_process:
            for fields in note_images.field_images:
                for image in fields.images:
                    images_to_process.append(image)
        return images_to_process

    @staticmethod
    def _ocr_img(img_pth: Union[Path, str, PathLike], num_threads: int, languages: List[str] = None) -> str:
        """ Wrapper for pytesseract.image_to_string

        img_pth can be either a pathlink to a single image, or a path to a textfile containing a list of image paths
        """
        if num_threads < 1:
            raise ValueError(
                f"Num of threads must be more than 1! given was: {num_threads} of type {type(num_threads)}")
        # Tesseract uses max of 4 threads: https://github.com/tesseract-ocr/tesseract/issues/1600
        if num_threads < 4:
            os.environ["OMP_THREAD_LIMIT"] = str(num_threads)
        else:
            try:
                del os.environ["OMP_THREAD_LIMIT"]
                os.unsetenv("OMP_THREAD_LIMIT")
            except:
                pass
        tessdata_config = f'--tessdata-dir "{TESSDATA_DIR.absolute()}"'

        return pytesseract.image_to_string(str(img_pth), lang="+".join(languages or ["eng"]),
                                           config=tessdata_config)

    def run_ocr_on_query(self, note_ids: List[int]) -> NotesQuery:
        """ Main method for the ocr class. Runs OCR on a sequence of notes returned from a collection query.

        :param note_ids: Note id's to process
        """
        notes_query = NotesQuery(col=self.col, note_ids=note_ids)
        # self.col.modSchema(check=True)
        if self.use_batching:
            logger.info(f"Processing {len(notes_query)} notes with _ocr_batch_process() ...")
            batched_txts, batched_txts_dir, batch_mapping = self._gen_batched_txts(notes_to_process=notes_query.notes,
                                                                                   batch_size=self.batch_size)
            raw_results = self._ocr_batch_process(batched_txts=batched_txts)
            batched_txts_dir.cleanup()
            ocr_images = self._process_batched_results(batch_mapping, raw_results)

        else:
            logger.info(f"Processing {len(notes_query)} notes with _ocr_unbatched_process() ...")
            images_to_process = self._gen_images_to_process(notes_to_process=notes_query.notes)
            image_paths = [str(i.img_pth) for i in images_to_process]
            unbatched_mapped = [{"image": image, "path": path} for image, path in zip(images_to_process, image_paths)]
            raw_results = self._ocr_unbatched_process(image_paths=image_paths)
            ocr_images = self._process_single_results(unbatched_mapped, raw_results)

        logger.info(f"Processed {len(ocr_images)} images in total")

        # Post processing
        for note in notes_query:
            note.add_imgdata_to_note(method=self.text_output_location)

        if self.col is not None:
            self.col.save()
            self.col.reset()
            logger.info("Databased saved")
        return notes_query

    def run_ocr_on_notes(self, note_ids: List[int]) -> NotesQuery:
        """ Main method for the ocr class. Runs OCR on a sequence of notes returned from a collection query.

        :param note_ids: List of note ids
        """
        # self.col.modSchema(check=True)
        notes_query = self.run_ocr_on_query(note_ids=note_ids)
        return notes_query

    def remove_ocr_on_notes(self, note_ids: List[int]):
        """ Removes the OCR field on a sequence of notes returned from a collection query.

        :param note_ids: List of note ids
        """
        # self.col.modSchema(check=True)
        query_notes = NotesQuery(col=self.col, note_ids=note_ids)
        for note in query_notes:
            note.remove_OCR_text()
        self.col.reset()
        logger.info("Databased saved")

    @staticmethod
    def path_to_tesseract() -> str:
        exec_data = {"Windows": str(Path(DEPS_DIR, "win", "tesseract", "tesseract.exe")),
                     "Darwin": str(Path(DEPS_DIR, "mac", "tesseract", "4.1.1", "bin", "tesseract")),
                     "Linux": "/usr/local/bin/tesseract"}

        platform_name = platform.system()  # E.g. 'Windows'
        return exec_data[platform_name]
