import os

import numpy as np
import pandas as pd
import torch
from skimage import io, transform
from torch.utils.data import Dataset


class SmashVODFrameDataset(Dataset):
    def __init__(
        self,
        frame_df: pd.DataFrame,
        root_dir: str,
        character_map: dict,
        transform=None,
        target_transform=None,
    ):
        self.frame_df = frame_df
        self.root_dir = root_dir
        self.transform = transform
        self.target_transform = target_transform
        self.character_map = character_map

    def __len__(self):
        return self.frame_df.shape[0]

    def __getitem__(self, index):
        if torch.is_tensor(index):
            index = index.tolist()

        img_name = os.path.join(self.root_dir, self.frame_df.iloc[index, 0])
        image = io.imread(img_name)
        target = [0 for _ in range(len(self.character_map))]
        target = torch.Tensor(target)
        characters = self.frame_df.iloc[index, 1:]
        for character in characters:
            target[self.character_map[character]] = 1

        if self.transform is not None:
            image = self.transform(image)
        if self.target_transform is not None:
            target = self.target_transform(target)
        return image, target
