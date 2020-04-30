import os
import subprocess
import csv
import pandas as pd
import youtube_dl
import glob
import random
FORMAT = "243"
OUTTMPL = "test/%(id)s.%(ext)s"
FRAMES_TO_GRAB_PER_SEC = 0.1
MAX_FRAMES = 100
MAX_VODS_PER_CHARACTER = 20
pd.set_option("max_rows", None)



def split_youtube_video_into_frames(
    ydl: youtube_dl.YoutubeDL, youtube_link: str, p1_character: str, p2_character: str
):
    info_dict = ydl.extract_info(youtube_link, download=True)
    filename = ydl.prepare_filename(info_dict)
    subprocess.run(
        [
            "ffmpeg",
            "-i",
            filename,
            "-r",
            f"{FRAMES_TO_GRAB_PER_SEC}",
            f"test/{filename.split('/')[-1].split('.')[0]}.%03d.jpg",
        ]
    )
    os.remove(filename)
    created_frames = glob.glob(f"test/{filename.split('/')[-1].split('.')[0]}*")
    if len(created_frames) > MAX_FRAMES:
        selected_frames = random.sample(created_frames, MAX_FRAMES)
        excess_frames = filter(lambda x: x not in selected_frames, created_frames)
        for frame in excess_frames:
            os.remove(frame)
        created_frames = selected_frames
    return [(frame, p1_character, p2_character) for frame in created_frames]
    



df = pd.read_csv("vods.csv")

records = []
with youtube_dl.YoutubeDL({"format": FORMAT, "outtmpl": OUTTMPL}) as ydl:
    for _, row in df.iterrows():
        youtube_link = row["youtube_link"]
        p1_character = row["p1_character"]
        p2_character = row["p2_character"]
        records += split_youtube_video_into_frames(ydl, youtube_link, p1_character, p2_character)
        record_df = pd.DataFrame.from_records(records, columns=["filename", "p1_character", "p2_character"])
        record_df.to_csv("records.csv", index=False)