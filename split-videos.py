import argparse
import csv
import glob
import multiprocessing
import os
import subprocess
from multiprocessing import dummy
from typing import List, Tuple
import random

from common import GAMES

FRAMES_OUTPUT_PER_SEC = 0.1
MAX_FRAMES_PER_VOD = 200


def split_vod_into_frames(
    filename: str, fps: float, characters_used: List[str],
) -> List[Tuple[str, List[str]]]:
    subprocess.check_call(
        [
            "ffmpeg",
            "-nostdin",
            "-i",
            filename,
            "-r",
            str(fps),
            "-loglevel",
            "quiet",
            "-stats",
            f"data/images/{filename.split('/')[-1].split('.')[0]}.%03d.jpg",
        ]
    )
    created_frames = glob.glob(
        f"data/images/{filename.split('/')[-1].split('.')[0]}*.jpg"
    )
    if len(created_frames) >= MAX_FRAMES_PER_VOD:
        sampled_frames = random.sample(created_frames, MAX_FRAMES_PER_VOD)
        for frame in created_frames:
            if frame not in sampled_frames:
                os.remove(frame)
        created_frames = sampled_frames
    return [(frame_filename, *characters_used) for frame_filename in created_frames]


def split_vod_into_frames_args(args) -> List[Tuple[str, List[str]]]:
    return split_vod_into_frames(*args)


def main(game: str, in_filename: str, num_processes: int, fps: float):
    with open(in_filename, "r") as in_csvfile:
        reader = csv.reader(in_csvfile)
        with open(f"{game}-vod-frames.csv", "w+") as out_csvfile:
            writer = csv.writer(out_csvfile)
            with dummy.Pool(processes=num_processes) as pool:
                args = [
                    (filename, fps, characters_used)
                    for (filename, *characters_used) in reader
                ]
                print(len(args))
                split_tasks = pool.imap_unordered(split_vod_into_frames_args, args,)

                for result in split_tasks:
                    writer.writerows(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Utility for splitting VODs into their component frames"
    )
    parser.add_argument("game", choices=GAMES, help="Which game to retrieve data for")
    parser.add_argument(
        "in_filename",
        type=str,
        help="The path to the CSV containing the VODs in the first column, as formatted by scrape-vods.py",
    )
    parser.add_argument(
        "--num_processes",
        type=int,
        default=multiprocessing.cpu_count(),
        help="The number of processes to use while retrieving data.",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=FRAMES_OUTPUT_PER_SEC,
        help="The number of frames to capture per second.",
    )
    args = parser.parse_args()
    main(args.game, args.in_filename, args.num_processes, args.fps)
