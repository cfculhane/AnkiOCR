# Performance testing
from pathlib import Path

import pytest


import os
import tempfile
import time
from typing import List, Tuple

from rich.console import Console

from anki_ocr import pytesseract
from anki_ocr import TESTDATA_DIR
from anki_ocr.ocr import OCR
from anki_ocr.utils import batch

IMGS_DIR = TESTDATA_DIR / "batch_imgs"
assert IMGS_DIR.exists()
# TEMPLATE_COLLECTION = Collection(path=str(TEMPLATE_COLLECTION_PTH))

console = Console(color_system="windows", width=200)


def timeit(func, *args, **kwargs):
    ts = time.time()
    result = func(*args, **kwargs)
    te = time.time()
    return result, te - ts


def gen_batched_txts(img_pths: List[Path], batch_size: int) -> Tuple[List[Path], tempfile.TemporaryDirectory]:
    batched_txts_dir = tempfile.TemporaryDirectory()  # Need to return so we can cleanup later
    batched_txts = []
    for i, batched_img_pths in enumerate(batch(img_pths, batch_size)):
        batch_txt_pth = Path(batched_txts_dir.name, f"batch_imgs_{i}.txt")
        batch_txt_pth.write_text("\n".join([str(i) for i in batched_img_pths]))
        batched_txts.append(batch_txt_pth)

    return batched_txts, batched_txts_dir


@pytest.mark.skip
class TestPerformance:
    test_img_pths = list(Path(TESTDATA_DIR, "annotated_imgs").glob("*"))
    tesseract_cmd = OCR.path_to_tesseract()
    pytesseract.tesseract_cmd = tesseract_cmd
    IMG_PTHS = [img_pth.absolute() for img_pth in IMGS_DIR.glob("*.png")]
    NUM_IMGS = len(IMG_PTHS)
    TXT_PATH = Path(IMGS_DIR, "imgs.txt")
    TXT_PATH.write_text("\n".join([str(i) for i in IMG_PTHS]))
    BATCH_SIZE = 10
    console.log(f"BATCH_SIZE : {BATCH_SIZE}")
    console.log(f"Number of images = {len(IMG_PTHS)}")
    batched_txts, batched_txts_dir = gen_batched_txts(img_pths=IMG_PTHS, batch_size=BATCH_SIZE)
    console.log(f"Generated {len(batched_txts)} batches of max {BATCH_SIZE} images")

    def test_batched_single_threaded(self):
        console.print("Starting batched single threaded")

        ocr = OCR(col=None, progress=None, languages=["eng"], num_threads=1, use_batching=True)
        _, time_taken = timeit(ocr._ocr_batch_process, self.batched_txts)
        try:
            console.print(f"OMP_THREAD_LIMIT = {os.environ['OMP_THREAD_LIMIT']}")
        except KeyError:
            console.print("No thread limit found.")
        return time_taken

    def test_batched_multi_threaded(self):
        console.print("Starting batched multi threaded")

        ocr = OCR(col=None, progress=None, languages=["eng"], num_threads=4, use_batching=True)
        _, time_taken = timeit(ocr._ocr_batch_process, self.batched_txts)
        try:
            console.print(f"OMP_THREAD_LIMIT = {os.environ['OMP_THREAD_LIMIT']}")
        except KeyError:
            console.print("No thread limit found.")
        return time_taken

    def test_unbatched_single_threaded(self):
        console.print("Starting un-batched single threaded")

        ocr = OCR(col=None, progress=None, languages=["eng"], num_threads=1, use_batching=False)
        _, time_taken = timeit(ocr._ocr_unbatched_process, self.IMG_PTHS)
        try:
            console.print(f"OMP_THREAD_LIMIT = {os.environ['OMP_THREAD_LIMIT']}")
        except KeyError:
            console.print("No thread limit found.")
        return time_taken

    def test_unbatched_multi_threaded(self):
        console.print("Starting un-batched multi threaded")

        ocr = OCR(col=None, progress=None, languages=["eng"], num_threads=4, use_batching=False)
        _, time_taken = timeit(ocr._ocr_unbatched_process, self.IMG_PTHS)
        try:
            console.print(f"OMP_THREAD_LIMIT = {os.environ['OMP_THREAD_LIMIT']}")
        except KeyError:
            console.print("No thread limit found.")
        return time_taken


if __name__ == "__main__":
    perf_test = TestPerformance()

    time_batched_single = perf_test.test_batched_single_threaded()
    time_batched_multi = perf_test.test_batched_multi_threaded()
    time_unbatched_single = perf_test.test_unbatched_single_threaded()
    time_unbatched_multi = perf_test.test_unbatched_multi_threaded()
    console.print("\nAll done, timing results: \n")
    console.print(
        f"time_batched_single = {round(time_batched_single, 2)} s | "
        f"{round(time_batched_single / perf_test.NUM_IMGS, 2)} s per image"
    )
    console.print(
        f"time_batched_multi = {round(time_batched_multi, 2)} s | "
        f"{round(time_batched_multi / perf_test.NUM_IMGS, 2)} s per image"
    )
    console.print(
        f"time_unbatched_single = {round(time_unbatched_single, 2)} s | "
        f"{round(time_unbatched_single / perf_test.NUM_IMGS, 2)} s per image"
    )
    console.print(
        f"time_unbatched_multi = {round(time_unbatched_multi, 2)} s | "
        f"{round(time_unbatched_multi / perf_test.NUM_IMGS, 2)} s per image"
    )
