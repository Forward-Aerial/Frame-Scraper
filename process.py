import csv
import glob
import multiprocessing
import os
import random
import subprocess
from multiprocessing import dummy
from typing import Tuple, List

import pandas as pd
import youtube_dl

FORMAT = "243"
OUTTMPL = "test/%(id)s.%(ext)s"
YOUTUBE_DL_OPTS = {"format": FORMAT, "outtmpl": OUTTMPL}

FRAMES_TO_GRAB_PER_SEC = 0.1
MAX_FRAMES = 100
MAX_RETRIES = 10
NUM_PROCESSES = 10


def download_video(
    youtube_link: str, p1_character: str, p2_character: str, num_retries=0,
) -> Tuple[str, str, str]:
    try:
        with youtube_dl.YoutubeDL(YOUTUBE_DL_OPTS) as ydl:
            info_dict = ydl.extract_info(youtube_link, download=True)
            filename = ydl.prepare_filename(info_dict)
            subprocess.check_call(
                ["echo", "youtube-dl", "-F", FORMAT, "-o", OUTTMPL, youtube_link]
            )
            return filename, p1_character, p2_character
    except Exception as e:
        print("Exception for", youtube_link)
        if num_retries < MAX_RETRIES:
            return download_video(
                youtube_link, p1_character, p2_character, num_retries=num_retries + 1,
            )
        else:
            raise e


def split_video(
    filename: str, p1_character: str, p2_character: str
) -> List[Tuple[str, str, str]]:
    subprocess.check_call(
        [
            "ffmpeg",
            "-nostdin",
            "-i",
            filename,
            "-r",
            f"{FRAMES_TO_GRAB_PER_SEC}",
            f"test/{filename.split('/')[-1].split('.')[0]}.%03d.jpg",
        ]
    )
    os.remove(filename)
    created_frames = glob.glob(f"test/{filename.split('/')[-1].split('.')[0]}*.jpg")
    if len(created_frames) > MAX_FRAMES:
        selected_frames = random.sample(created_frames, MAX_FRAMES)
        excess_frames = filter(lambda x: x not in selected_frames, created_frames)
        for frame in excess_frames:
            os.remove(frame)
        created_frames = selected_frames
    return [(frame, p1_character, p2_character) for frame in created_frames]


def download_video_args(args: Tuple[str, str, str]):
    return download_video(*args)


def split_video_args(args: Tuple[str, str, str]):
    return split_video(*args)


with open("vods.csv", "r") as read_csvfile:
    reader = csv.reader(read_csvfile)
    next(reader)  # Skip header row
    i = 0
    with open("records.csv", "w+") as write_csvfile:
        writer = csv.writer(write_csvfile)
        download_results: List[Tuple[str, str, str]] = []
        with dummy.Pool(NUM_PROCESSES) as pool:
            download_tasks = pool.imap_unordered(download_video_args, reader)
            for download_result in download_tasks:
                download_results.append(download_result)

            split_tasks = pool.imap_unordered(split_video_args, download_results)
            for result in split_tasks:
                writer.writerows(result)
