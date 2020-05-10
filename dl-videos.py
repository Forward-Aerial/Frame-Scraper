import argparse
import csv
import glob
import multiprocessing
import os
import random
import subprocess
from multiprocessing import dummy
from typing import List, Optional, Tuple
import logging

import pandas as pd
import youtube_dl

from common import GAMES, MAX_NUM_PLAYERS, YOUTUBE_DL_OPTS


def download_vod(
    link: str, *characters: List[str]
) -> Optional[
    Tuple[
        str,
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
    ]
]:
    """
    Downloads the VOD located at the provided link, and returns the filename. Characters are not modified.
    """
    try:
        with youtube_dl.YoutubeDL(YOUTUBE_DL_OPTS) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info_dict)
            return (filename, *characters)
    except youtube_dl.utils.DownloadError as e:
        logging.fatal(f"Hit an exception downloading {link}:")
        return None


def download_vod_args(args):
    return download_vod(*args)


def download_vods(
    game: str, csv_filename: str, num_processes: int, samples: Optional[int],
):
    if samples is not None:
        logging.info(f"Taking a sample (size {samples}) from {csv_filename}")
        df = pd.read_csv(csv_filename)
        if samples > df.shape[0]:
            logging.warning(
                f"Provided sample was larger than the CSV. Not taking a sample."
            )
        else:
            df = df.sample(samples)
            new_filename = f"{game}-links-sample-{samples}.csv"
            df.to_csv(new_filename, index=False)
            logging.info(f"Wrote samples to CSV named {new_filename}")
            csv_filename = new_filename

    with open(csv_filename, "r") as in_csvfile:
        reader = csv.reader(in_csvfile)
        next(reader)
        with open(csv_filename.replace("links", "vods"), "w+") as out_csvfile:
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
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="The number of samples to take from the downloaded data.",
    )
    args = parser.parse_args()
    download_vods(args.game, args.csv_filename, args.num_processes, args.samples)


if __name__ == "__main__":
    main()
