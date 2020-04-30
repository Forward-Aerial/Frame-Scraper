from torchvision import models
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
import os
from skimage import io, transform
from torchvision import transforms
import numpy as np


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

class ToTensor(object):
    """Convert ndarrays in sample to Tensors."""

    def __call__(self, sample):
        image, labels = sample['image'], sample['labels']

        # swap color axis because
        # numpy image: H x W x C
        # torch image: C X H X W
        image = image.transpose((2, 0, 1))
        return {'image': torch.from_numpy(image),
                'labels': torch.from_numpy(labels)}


# Test Dataset
vod_frame_dataset = SmashVODFrameDataset("records.csv", ".", transform=transforms.Compose([ToTensor()]))
for i in range(len(vod_frame_dataset)):
    sample = vod_frame_dataset[i]

    print(i, sample['image'].shape, sample['labels'].shape)
    
    if i == 5:
        break


model = models.vgg16(pretrained=True)

# Freeze model weights
for param in model.parameters():
    param.requires_grad = False

import torch.nn as nn

# Add on classifier
model.classifier[6] = nn.Sequential(
    nn.Linear(n_inputs, 256),
    nn.ReLU(),
    nn.Dropout(0.4),
    nn.Linear(256, n_classes),
    nn.LogSoftmax(dim=1),
)
