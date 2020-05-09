# Smash VOD DL
A utility for downloading Super Smash Bros. Videos-On-Demand (VODs) of professional players.
Sources data from https://vods.co.

## Running Locally
1. Have Python 3 (Python 3.8 was used for developing this project)
1. `pip install -r requirements.txt`
1. `mkdir -p data/videos data/images`
1. `python scrape-vods.py {smash64,melee,meleedoubles,brawl,projectm,smash4,ultimate}` (`python scrape-vods.py -h` for help)
1. `python dl-videos.py {smash64,melee,meleedoubles,brawl,projectm,smash4,ultimate} <CSV_FILENAME_FROM_SCRAPE_VODS_PY>` (`python dl-videos.py -h` for help)
    1. By default, this will only download videos that are <= 15 minutes long. To change that, modify `common.py`'s `YOUTUBE_DL_OPTS`
1. `python split-videos.py {smash64,melee,meleedoubles,brawl,projectm,smash4,ultimate} <CSV_FILENAME_FROM_DL_VIDEOS_PY>` (`python split-videos.py -h` for help)
