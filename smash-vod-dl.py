import csv
import multiprocessing
import re
import subprocess
from multiprocessing import dummy
from typing import List, Tuple

import bs4
import pandas as pd
import requests
import youtube_dl
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webelement import FirefoxWebElement

ULTIMATE = "ultimate"
MELEE = "melee"
PROJECT_M = "projectm"
N64 = "smash64"

SPRITE_FILENAME_PATTERN = re.compile(r"16px-(?P<charname>.*)$")

NUM_PROCESSES = None
MAX_RETRIES = 10


def parse_character_from_img(vods_co_img: bs4.Tag) -> str:
    src = vods_co_img.attrs["src"]
    end_of_path = src.split("/")[-1]
    sprite_filename = re.match(SPRITE_FILENAME_PATTERN, end_of_path)
    return sprite_filename.group("charname").split(".png")[0]


def get_data_for_page(link: str, retries=0) -> List[Tuple[str, str, str]]:
    try:
        print("Requesting", link, f"for the {retries+1} time")
        r = requests.get(link)
        html = r.text
        rows = bs4.BeautifulSoup(html, "lxml").select("tr > td:nth-child(2) > a")
        page_data: List[Tuple[str, str, str]] = []
        for row in rows:
            character_sprites: bs4.ResultSet = row.select("span:nth-child(1) > img")
            if len(character_sprites) != 2:
                continue
            a_sprite, b_sprite = map(parse_character_from_img, character_sprites)
            vod_co_link = row.attrs["href"]
            page_data.append((vod_co_link, a_sprite, b_sprite))
        return page_data
    except requests.exceptions.HTTPError as e:
        if retries < MAX_RETRIES:
            return get_data_for_page(link, retries + 1)
        raise e
    except ValueError as e:
        print(link)
        raise e


def fetch_final_data(
    vod_co_link: str, p1_character: str, p2_character: str, retries=0
) -> Tuple[str, str, str]:
    try:
        r = requests.get(vod_co_link)
        r.raise_for_status()
        html = r.text
        yt_link_anchor = bs4.BeautifulSoup(html, "lxml").select_one("#g1-video")
        if not yt_link_anchor:
            return None
        yt_link = yt_link_anchor.attrs["src"][2:]
        return yt_link, p1_character, p2_character
    except requests.exceptions.HTTPError as e:
        if retries < MAX_RETRIES:
            return fetch_final_data(
                vod_co_link, p1_character, p2_character, retries + 1
            )
        raise e


def fetch_final_data_star(args: Tuple[str, str, str]) -> Tuple[str, str, str]:
    return fetch_final_data(*args)


def get_all_data(game: str):
    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        fetched_data = pool.imap_unordered(
            get_data_for_page, [f"https://vods.co/{game}?page={i}" for i in range(350)]
        )
        all_page_data = []
        for page_data in fetched_data:
            all_page_data += page_data
        print(f"Going to write {len(all_page_data)} rows.")
        with open(f"{game}-vods.csv", "w+") as csvfile:
            writer = csv.writer(csvfile)
            fetched_final_data = pool.imap_unordered(
                fetch_final_data_star, all_page_data
            )
            writer.writerow(["youtube_link", "p1_character", "p2_character"])
            for final_data in fetched_final_data:
                if final_data is None:
                    continue
                writer.writerow(final_data)


get_all_data(game=MELEE)
