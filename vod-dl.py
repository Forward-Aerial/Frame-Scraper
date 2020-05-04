import argparse
import asyncio
import concurrent
import multiprocessing
import re
import urllib
from typing import Callable, List, NamedTuple, Optional

import aiohttp
import bs4

SSB_N64 = "n64"
SSB_MELEE = "melee"
SSB_PROJECT_M = "projectm"
SSB_ULTIMATE = "ultimate"
GAMES = [SSB_N64, SSB_MELEE, SSB_PROJECT_M, SSB_ULTIMATE]

MAX_NUM_PLAYERS = 8

HOSTNAME = "https://vods.co"
MAX_RETRIES = 10

NUM_WORKERS = 4

SPRITE_FILENAME_PATTERN = re.compile(r"16px-(?P<charname>.*)$")


def parse_character_from_img(vods_co_sprite: bs4.Tag) -> str:
    src = vods_co_sprite.attrs["src"]
    end_of_path = src.split("/")[-1]
    sprite_filename = re.match(SPRITE_FILENAME_PATTERN, end_of_path)
    return sprite_filename.group("charname").split(".png")[0]


class VODEntry(NamedTuple):
    """
    A representation of an https://vods.co entry.
    """

    link: str
    characters_used: List[str]


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    """
    Makes a request to the provided HTML, and returns the HTML.
    """
    async with session.get(url) as response:
        return await response.text()


def extract_noscript_youtube_link(soup: bs4.BeautifulSoup) -> Optional[str]:
    """
    Attempts to extract a YouTube link from a noscript YouTube element.
    """
    yt_anchor = soup.select_one(".submessage > a:nth-child(1)")
    if not yt_anchor:
        return None
    return yt_anchor.attrs["href"]


def extract_youtube_link(soup: bs4.BeautifulSoup) -> Optional[str]:
    """
    Attempts to extract a YouTube link from a specific VOD page. If unable, returns None.
    """
    yt_iframe: bs4.element.Tag = soup.select_one("#g1-video")
    if not yt_iframe:
        return extract_noscript_youtube_link(
            soup
        )  # Might be a <noscript> tag instead, use fallback
    parse_result: urllib.parse.ParseResult = urllib.parse.urlparse(
        yt_iframe.attrs["src"]
    )
    parse_result = parse_result._replace(scheme="https")._replace(query=None)
    return urllib.parse.urlunparse(parse_result)


def extract_twitch_link(soup: bs4.BeautifulSoup) -> Optional[str]:
    """
    Attempts to extract a Twitch link from a specific VOD page. If unable, returns None.
    """
    twitch_iframe: bs4.element.Tag = soup.select_one(".js-video > iframe:nth-child(1)")
    if not twitch_iframe:
        return None
    parse_result: urllib.parse.ParseResult = urllib.parse.urlparse(
        twitch_iframe.attrs["src"]
    )
    return urllib.parse.urlunparse(parse_result)


async def follow_vod_co_link(
    session: aiohttp.ClientSession, url: str, retries=0
) -> Optional[str]:
    """
    Attempts to get a direct link to a VOD. Currently-supported VOD links are: [YouTube, Twitch]. If a link cannot be extracted, returns None.
    """
    html = await fetch(session, url)
    soup = bs4.BeautifulSoup(html, "lxml")

    link_extractors: List[Callable] = [extract_youtube_link, extract_twitch_link]
    for extract in link_extractors:
        link = extract(soup)
        if link:
            return link

    print(f"Found a VOD that was neither YT nor Twitch: {url}")
    print(html)
    return None


async def process_row(
    session: aiohttp.ClientSession, row: bs4.Tag, max_num_players=MAX_NUM_PLAYERS,
) -> Optional[VODEntry]:
    """
    Processes a single row on an https://vods.co table. If a direct link to the VOD cannot be made, returns None.
    """
    character_sprites: bs4.ResultSet = row.select("span:nth-child(1) > img")
    characters = list(map(parse_character_from_img, character_sprites))
    while len(characters) < max_num_players:
        characters.append(None)
    vod_co_link = row.attrs["href"]
    external_link = await follow_vod_co_link(session, vod_co_link)
    if not external_link:
        return None
    return VODEntry(link=external_link, characters_used=characters)


async def fetch_data_for_vod_page(
    session: aiohttp.ClientSession, url: str, retries=0
) -> List[VODEntry]:
    """
    Makes a request to the provided https://vods.co page.
    """
    return [("abcd", ["1", "2", "3"])]
    html = await fetch(session, url)
    rows = bs4.BeautifulSoup(html, "lxml").select("tr > td:nth-child(2) > a")
    vod_entries: List[Optional[VODEntry]] = await asyncio.gather(
        *(process_row(session, row) for row in rows)
    )
    print(f"Finished scraping {url}")
    return [entry for entry in vod_entries if entry is not None]


async def get_page_limit_for(game: str) -> int:
    """
    Makes a single request to figure out how many pages of VODs there are for this game.
    """
    async with aiohttp.ClientSession() as session:
        page_number = 0
        print(f"{HOSTNAME}/{game}?page={page_number}")
        html = await fetch(session, f"{HOSTNAME}/{game}?page={page_number}")
        last_page_link = bs4.BeautifulSoup(html, "lxml").select_one(
            ".pager-last > a:nth-child(1)"
        )
        if not last_page_link:
            raise Exception(
                f"Couldn't get the index of the last page for {game}. The site might be down."
            )
        last_page_href = last_page_link.attrs["href"]
        parse_result: urllib.parse.ParseResult = urllib.parse.urlparse(last_page_href)
        query_dict = urllib.parse.parse_qs(parse_result.query)
        return int(query_dict["page"][0])


async def fetch_data_for(
    game: str, num_workers: int, upper_page_limit=None
) -> List[VODEntry]:
    """
    Retrieves all VOD data for a specific Super Smash Bros. game
    """
    if upper_page_limit is None:
        upper_page_limit = await get_page_limit_for(game)

    urls = [f"{HOSTNAME}/{game}?page={i}" for i in range(upper_page_limit)]
    async with aiohttp.ClientSession() as session:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_url = {
                executor.submit(fetch_data_for_vod_page, session, url): url
                for url in urls
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    vod_entries = future.result()
                except Exception as exc:
                    print(f"{url} generated an exception: {exc}")
                else:
                    for (link, characters_used) in vod_entries:
                        print(link, characters_used)


def main():
    parser = argparse.ArgumentParser(
        description="A utility for aggregating Super Smash Bros. data from https://vods.co"
    )
    parser.add_argument("game", choices=GAMES, help="Which game to retrieve data for")
    parser.add_argument(
        "--num-workers",
        default=NUM_WORKERS,
        help="The number of workers to use while scraping. Too many workers will cause the server to reject requests.",
    )

    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        fetch_data_for(args.game, args.num_workers, upper_page_limit=1)
    )


if __name__ == "__main__":
    main()
