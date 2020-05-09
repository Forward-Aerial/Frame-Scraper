import youtube_dl

SSB_N64 = "smash64"
SSB_MELEE = "melee"
SSB_MELEE_DOUBLES = "meleedoubles"
SSB_BRAWL = "brawl"
SSB_PROJECT_M = "projectm"
SSB_4 = "smash4"
SSB_ULTIMATE = "ultimate"
GAMES = [
    SSB_N64,
    SSB_MELEE,
    SSB_MELEE_DOUBLES,
    SSB_BRAWL,
    SSB_PROJECT_M,
    SSB_4,
    SSB_ULTIMATE,
]

MAX_NUM_PLAYERS = 8

FORMAT = "134"
YOUTUBEDL_OUT_TEMPLATE = "data/videos/%(id)s.%(ext)s"
MAX_DURATION = 15 * 60
YOUTUBE_DL_OPTS = {
    "format": FORMAT,
    "outtmpl": YOUTUBEDL_OUT_TEMPLATE,
    "external_downloader": "aria2c",
    "external_downloader_args": ["-c", "-j", "3", "-x", "3", "-s", "3", "-k", "1M"],
    "youtube_include_dash_manifest": False,
    "match_filter": youtube_dl.utils.match_filter_func(f"duration <= {MAX_DURATION}"),
}
