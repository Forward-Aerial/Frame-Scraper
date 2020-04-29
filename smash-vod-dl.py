import re
import subprocess
from typing import List, Tuple

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webelement import FirefoxWebElement
import youtube_dl
import bs4

SPRITE_FILENAME_PATTERN = re.compile(r"16px-(?P<charname>.*)$")


def parse_character_from_img(vods_co_img: bs4.Tag) -> str:
    src = vods_co_img.attrs["src"]
    end_of_path = src.split("/")[-1]
    sprite_filename = re.match(SPRITE_FILENAME_PATTERN, end_of_path)
    return sprite_filename.group("charname").split(".png")[0]


def get_all_data():
    driver = webdriver.Firefox()
    try:

        def follow_link(vod_link: str) -> str:
            driver.get(vod_link)
            iframe: FirefoxWebElement = driver.find_element_by_id("g1-video")
            print(iframe.get_attribute("href"))
            return iframe.get_attribute("href")

        def get_data_for_page(link: str) -> List[Tuple[str, str, str]]:
            driver.get(link)
            html = driver.find_element("html").get_attribute("innerHTML")
            rows = bs4.BeautifulSoup(html, "lxml").select("tr:nth-child(1) > td:nth-child(2) > a")
            results: List[Tuple[str, str, str]] = []
            if not rows:
                print(rows)
                print("rows are empty")
                return None
            for row in rows:
                character_sprites: List[FirefoxWebElement] = row.select(
                    "span:nth-child(1) > img"
                )
                if len(character_sprites) > 2:
                    continue
                a_sprite, b_sprite = map(parse_character_from_img, character_sprites)
                youtube_link = follow_link(row.atrs["href"])
                results.append((youtube_link, a_sprite, b_sprite))

            return results

        i = 0
        while results := get_data_for_page(f"https://vods.co/ultimate?page={i}"):
            i += 1
            print(results)
    except Exception:
        raise e
    finally:
        driver.close()


get_all_data()
