import argparse
import csv
import os
import multiprocessing
from multiprocessing import dummy
from typing import List, Tuple, Optional

import youtube_dl

from common import GAMES, MAX_NUM_PLAYERS

FORMAT = "134"
OUTTMPL = "data/videos/%(id)s.%(ext)s"
YOUTUBE_DL_OPTS = {
    "format": FORMAT,
    "outtmpl": OUTTMPL,
    "external_downloader": "aria2c",
    "external_downloader_args": ["-c", "-j", "3", "-x", "3", "-s", "3", "-k", "1M"],
    "youtube_include_dash_manifest": False,
}


def download_vod(link: str, *characters: List[str]) -> Optional[List[str]]:
    """
    Downloads the VOD located at the provided link, and returns the filename. Characters are not modified.
    """
    try:
        with youtube_dl.YoutubeDL(YOUTUBE_DL_OPTS) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info_dict)
            ydl.download([link])
            return [filename, *characters]
    except youtube_dl.utils.DownloadError as e:
        print("Hit an exception:", e)
        return None


def download_vod_args(args: List[str]) -> List[str]:
    return download_vod(*args)


def download_vods(game: str, csv_filename: str, num_processes: int):
    with open(csv_filename, "r") as in_csvfile:
        reader = csv.reader(in_csvfile)
        with open(f"{game}-vods.csv", "w+") as out_csvfile:
            writer = csv.writer(out_csvfile)
            with multiprocessing.Pool(processes=num_processes) as pool:
                download_tasks = pool.imap_unordered(download_vod_args, reader)
                for result in download_tasks:
                    if not result:
                        continue
                    writer.writerow(result)
                    out_csvfile.flush()


def main():
    parser = argparse.ArgumentParser(
        description="Utility for downloading Smash Bros VODs."
    )
    parser.add_argument("game", choices=GAMES, help="Which game to retrieve data for")
    parser.add_argument(
        "csv_filename",
        type=str,
        help="The path to the CSV containing the VODs in the first column, as formatted by scrape-vods.py",
    )
    parser.add_argument(
        "--num_processes",
        type=int,
        default=multiprocessing.cpu_count(),
        help="The number of processes to use while retrieving data.",
    )
    args = parser.parse_args()
    download_vods(args.game, args.csv_filename, args.num_processes)


if __name__ == "__main__":
    main()
