import os

import numpy as np
import pandas as pd
import torch
from skimage import io, transform
from torch.utils.data import Dataset


class SmashVODFrameDataset(Dataset):
    def __init__(self, csv_file: str, root_dir: str, transform=None):
        self.frame_df = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform

        # Build character map
        all_characters = sorted(
            pd.concat(
                [self.frame_df["p1_character"], self.frame_df["p2_character"]]
            ).unique()
        )
        self.character_map = {char: i for i, char in enumerate(all_characters)}

    def __len__(self):
        return self.frame_df.shape[0]

    def __getitem__(self, index):
        if torch.is_tensor(index):
            index = index.tolist()

        img_name = os.path.join(self.root_dir, self.frame_df.iloc[index, 0])
        image = io.imread(img_name)
        labels = [0 for _ in range(len(self.character_map))]
        characters = self.frame_df.iloc[index, 1:]
        for character in characters:
            labels[self.character_map[character]] = 1
        labels = np.array(labels)

        sample = {"image": image, "labels": labels}
        if self.transform:
            sample = self.transform(sample)

        return sample
