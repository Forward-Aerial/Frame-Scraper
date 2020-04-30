import re
import subprocess
from typing import List, Tuple

from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webelement import FirefoxWebElement
import youtube_dl
import bs4
import pandas as pd

SPRITE_FILENAME_PATTERN = re.compile(r"16px-(?P<charname>.*)$")


def parse_character_from_img(vods_co_img: bs4.Tag) -> str:
    src = vods_co_img.attrs["src"]
    end_of_path = src.split("/")[-1]
    sprite_filename = re.match(SPRITE_FILENAME_PATTERN, end_of_path)
    return sprite_filename.group("charname").split(".png")[0]


def follow_link(driver: webdriver.Firefox, vod_link: str) -> str:
    try:
        driver.get(vod_link)
        iframe: FirefoxWebElement = driver.find_element_by_id("g1-video")
        return iframe.get_attribute("src")
    except NoSuchElementException:
        return None


def get_data_for_page(
    driver: webdriver.Firefox, link: str
) -> List[Tuple[str, str, str]]:
    print(f"Accessing {link}")
    driver.get(link)
    html = driver.page_source
    rows = bs4.BeautifulSoup(html, "lxml").select("tr > td:nth-child(2) > a")
    results: List[Tuple[str, str, str]] = []
    if not rows:
        return None
    for row in rows:
        character_sprites: bs4.ResultSet = row.select("span:nth-child(1) > img")
        if len(character_sprites) == 0:
            continue
        if len(character_sprites) > 2:
            continue
        a_sprite, b_sprite = map(parse_character_from_img, character_sprites)
        youtube_link = follow_link(driver, row.attrs["href"])
        if not youtube_link:
            continue
        results.append((youtube_link, a_sprite, b_sprite))

    return results


def get_all_data():
    driver = webdriver.Firefox()
    try:
        i = 0
        all_results = []
        while page_results := get_data_for_page(
            driver, f"https://vods.co/ultimate?page={i}"
        ):
            i += 1
            all_results += page_results
            df = pd.DataFrame.from_records(
                all_results, columns=["youtube_link", "p1_character", "p2_character"]
            )
            df.to_csv("vods.csv", index=False)
    except Exception as e:
        raise e
    finally:
        driver.close()


get_all_data()
