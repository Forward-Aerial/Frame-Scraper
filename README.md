# Frame Scraper
A utility for downloading Super Smash Bros. Videos-On-Demand of professional games, and splitting those games into frames.
Sources data from https://vods.co.

## External Dependencies
1. [FFmpeg](https://www.ffmpeg.org/download.html) (used for splitting videos into frames)
2. [Aria2](https://aria2.github.io/) (used for faster video downloads)

## Running Locally
1. Have Python 3 (Python 3.8 was used for developing this project)
1. `pip install -r requirements.txt`
1. `mkdir -p data/videos data/images`
1. `python scrape-vods.py {smash64,melee,meleedoubles,brawl,projectm,smash4,ultimate}` (`python scrape-vods.py -h` for help)
1. `python dl-videos.py {smash64,melee,meleedoubles,brawl,projectm,smash4,ultimate} <CSV_FILENAME_FROM_SCRAPE_VODS_PY>` (`python dl-videos.py -h` for help)
    1. By default, this will only download videos that are <= 15 minutes long. To change that, modify `common.py`'s `MAX_DURATION`
1. `python split-videos.py {smash64,melee,meleedoubles,brawl,projectm,smash4,ultimate} <CSV_FILENAME_FROM_DL_VIDEOS_PY>` (`python split-videos.py -h` for help)
