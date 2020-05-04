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

FORMAT = "134"
OUTTMPL = "test/%(id)s.%(ext)s"
YOUTUBE_DL_OPTS = {
    "format": FORMAT,
    "outtmpl": OUTTMPL,
    "external_downloader": "aria2c",
    "external_downloader_args": ["-c", "-j", "3", "-x", "3", "-s", "3", "-k", "1M"],
    "youtube_include_dash_manifest": False,
}

FRAMES_OUTPUT_PER_SEC = 0.1
MAX_FRAMES = 100
MAX_RETRIES = 10
NUM_PROCESSES = None


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
            f"{FRAMES_OUTPUT_PER_SEC}",
            "-loglevel",
            "quiet",
            "-stats",
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


def download_and_split_video(
    youtube_link: str, p1_character: str, p2_character: str, num_retries=0,
) -> Tuple[str, str, str]:
    try:
        with youtube_dl.YoutubeDL(YOUTUBE_DL_OPTS) as ydl:
            info_dict = ydl.extract_info(youtube_link, download=True)
            filename = ydl.prepare_filename(info_dict)
            ydl.download([youtube_link])
            return split_video(filename, p1_character, p2_character)
    except Exception as e:
        print("Exception for", youtube_link)
        print(e)
        if num_retries < MAX_RETRIES:
            return download_and_split_video(
                youtube_link, p1_character, p2_character, num_retries=num_retries + 1,
            )
        else:
            return None


def download_and_split_video_args(args: Tuple[str, str, str]):
    return download_and_split_video(*args)


def split_video_args(args: Tuple[str, str, str]):
    return split_video(*args)


def retrieve_frames(game: str):
    with open(f"{game}-vods.csv", "r") as read_csvfile:
        reader = csv.reader(read_csvfile)
        header_row = next(reader)  # Skip header row
        with open("records.csv", "w+") as write_csvfile:
            writer = csv.writer(write_csvfile)
            writer.writerow(header_row)
            with dummy.Pool(NUM_PROCESSES) as pool:
                download_and_split_tasks = pool.imap_unordered(
                    download_and_split_video_args, reader
                )
                for result in download_and_split_tasks:
                    if result is None:
                        continue
                    writer.writerows(result)


retrieve_frames(game="melee")
