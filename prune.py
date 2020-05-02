import glob
import os
import multiprocessing
from multiprocessing import dummy
from typing import Optional
from PIL import Image

dir_path = "test"
i = 0


def img_is_corrupt(filename: str) -> Optional[str]:
    try:
        img = Image.open(filename)
        img.verify()
        img.close()
        return None
    except (IOError, SyntaxError) as e:
        print("Bad file:", filename)
        print(e)
        return filename


PROCESSES = 10

print(len(os.listdir(dir_path)), "files in directory.")
with multiprocessing.Pool(PROCESSES) as pool:
    tasks = pool.imap_unordered(img_is_corrupt, glob.iglob(os.path.join(dir_path, "*.jpg")))
    for i, corrupt_filename in enumerate(tasks):
        if corrupt_filename is not None:
            print(corrupt_filename, "is corrupt.")
        if i % 10000 == 0:
            print(i, "files scanned.")