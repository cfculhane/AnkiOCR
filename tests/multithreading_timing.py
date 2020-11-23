# Some basic tests to make sure major breaking changes dont occur
import itertools
import tempfile
import time
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from multiprocessing import Pool
from pathlib import Path
from typing import Iterable, List, Tuple

import pytesseract
from tqdm import tqdm

IMGS_DIR = Path(__file__).parent / "testdata" / "batch_imgs"
assert IMGS_DIR.exists()

tesseract_cmd = str(Path(r"C:\GitHub\AnkiOCR\anki_ocr\deps\win\tesseract\tesseract.exe"))
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
NUM_PROCESSES = 4
BATCH_SIZE = 5


def timeit(func):
    def wrapped_f(*args, **kwargs):
        ts = time.time()
        result = func(*args, **kwargs)
        te = time.time()
        print(f"'{func.__name__}' completed in {round(te - ts, 4)} s")
        return result

    return wrapped_f


@timeit
def big_batch():
    out = pytesseract.image_to_string(str(TXT_PATH), lang="eng")


@timeit
def seq_iter():
    out_iter = []
    for img_pth in TXT_PATH.parent.glob("*.png"):
        out_iter.append(pytesseract.image_to_string(str(img_pth), lang="eng"))


def batch(it: Iterable, batch_size):
    it = iter(it)
    while True:
        p = tuple(itertools.islice(it, batch_size))
        if not p:
            break
        yield p


@timeit
def gen_batched_txts(img_pths: List[Path], batch_size: int) -> Tuple[List[Path], tempfile.TemporaryDirectory]:
    batched_txts_dir = tempfile.TemporaryDirectory()  # Need to return so we can cleanup later
    batched_txts = []
    for i, batched_img_pths in enumerate(batch(img_pths, batch_size)):
        batch_txt_pth = Path(batched_txts_dir.name, f"batch_imgs_{i}.txt")
        batch_txt_pth.write_text("\n".join([str(i) for i in batched_img_pths]))
        batched_txts.append(batch_txt_pth)

    return batched_txts, batched_txts_dir


def tesseract(img_pth):
    return pytesseract.image_to_string(str(img_pth), lang="eng")


@timeit
def mp_pool(thread_f, thread_iter):
    with Pool(processes=NUM_PROCESSES) as pool:
        pooled_output = pool.map(thread_f, thread_iter)


@timeit
def mp_pool_batched(thread_f, thread_iter):
    with Pool(processes=NUM_PROCESSES) as pool:
        pooled_output = pool.map(thread_f, thread_iter)


@timeit
def time_pool_progress(thread_f, thread_iter):
    with Pool(processes=NUM_PROCESSES) as pool:
        # print "[0, 1, 4,..., 81]"
        # pooled__batch_output = pool.map(f, batched_txts_)
        max_ = len(thread_iter)
        with tqdm(total=max_) as pbar:
            for i, _ in enumerate(pool.imap_unordered(thread_f, thread_iter)):
                pbar.update()


@timeit
def thread_pool_exec(thread_f, thread_iter):
    with ThreadPoolExecutor() as executor:
        executor.map(thread_f, thread_iter)


@timeit
def thread_pool_exec_batched(thread_f, thread_iter):
    results = []
    with ThreadPoolExecutor() as executor:
        print(f"Using {executor._max_workers} threads")
        max_ = len(thread_iter)
        with tqdm(total=max_, unit="batch") as pbar:
            for i, output in enumerate(executor.map(thread_f, thread_iter)):
                results.append(output)
                pbar.update()
    return results


def process_result(future):
    print(future.result())


def run_proc(thread_f, thread_iter):
    pbar = tqdm(total=len(thread_iter), unit="batch")
    executor = ThreadPoolExecutor()
    futures = [executor.submit(thread_f, i) for i in thread_iter]
    for future in futures:
        future.add_done_callback(process_result)
    executor.shutdown()
    print("done")
    return futures


@timeit
def process_pool_exec(thread_f, thread_iter):
    with ProcessPoolExecutor() as executor:
        executor.map(thread_f, thread_iter)


@timeit
def process_pool_exec_batched(thread_f, thread_iter):
    results = []
    with ProcessPoolExecutor() as executor:
        max_ = len(thread_iter)
        with tqdm(total=max_, unit="batch") as pbar:
            for i, output in enumerate(executor.map(thread_f, thread_iter)):
                results.append(output)
                pbar.update()
    return results


if __name__ == '__main__':
    IMG_PTHS = [img_pth.absolute() for img_pth in IMGS_DIR.glob("*.png")]
    TXT_PATH = Path(IMGS_DIR, "imgs.txt")
    TXT_PATH.write_text("\n".join([str(i) for i in IMG_PTHS]))

    print(f"NUM PROCESSES/THREADS : {NUM_PROCESSES}")
    print(f"BATCH_SIZE : {BATCH_SIZE}")
    print(f"Number of images = {len(IMG_PTHS)}")
    batched_txts, batched_txts_dir = gen_batched_txts(IMG_PTHS, BATCH_SIZE)
    print(f"Generated {len(batched_txts)} batches of max {BATCH_SIZE} images")

    seq_iter()
    big_batch()
    mp_pool(tesseract, IMG_PTHS)
    mp_pool_batched(tesseract, batched_txts)
    thread_pool_exec(tesseract, IMG_PTHS)
    thread_pool_exec_batched(tesseract, batched_txts)
    process_pool_exec(tesseract, batched_txts)
    results = thread_pool_exec_batched(tesseract, batched_txts)

    batched_txts_dir.cleanup()
