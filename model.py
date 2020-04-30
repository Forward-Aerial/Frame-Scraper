# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import copy
import os
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from torch.optim import lr_scheduler
from torchvision import datasets, models, transforms

# %%
BATCH_SIZE = 16

# %%

from dataset import SmashVODFrameDataset

frame_df = pd.read_csv("records.csv")
all_characters = sorted(
    pd.concat([frame_df["p1_character"], frame_df["p2_character"]]).unique()
)
character_map = {char: i for i, char in enumerate(all_characters)}

vod_dataset = SmashVODFrameDataset(
    frame_df,
    ".",
    character_map,
    transform=transforms.Compose(
        [transforms.ToPILImage(), transforms.Resize(224), transforms.ToTensor()]
    ),
)

lengths = [round(len(vod_dataset) * 0.8), round(len(vod_dataset) * 0.2)]
print(lengths, sum(lengths), len(vod_dataset))
train_set, val_set = torch.utils.data.random_split(vod_dataset, lengths)

frame_datasets = {"train": train_set, "val": val_set}

dataloaders = {
    x: torch.utils.data.DataLoader(
        frame_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=4
    )
    for x, frame_dataset in frame_datasets.items()
}
dataset_sizes = {x: len(frame_dataset) for x, frame_dataset in frame_datasets.items()}

device = torch.device(
    "cuda:0" if torch.cuda.is_available() else "cpu"
)  # pylint:disable=no-member

# %%
def train_model(model, criterion, optimizer, scheduler, num_epochs=25):
    since = time.time()

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print("Epoch {}/{}".format(epoch, num_epochs - 1))
        print("-" * 10)

        # Each epoch has a training and validation phase
        for phase in ["train", "val"]:
            if phase == "train":
                model.train()  # Set model to training mode
            else:
                model.eval()  # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)

                    preds = outputs.round()
                    preds -= labels
                    num_incorrect = torch.sum(preds.abs(), dim=1)

                    # backward + optimize only if in training phase
                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(torch.Tensor([len(character_map)]).cuda() - num_incorrect)
            if phase == "train":
                scheduler.step()

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print("{} Loss: {:.4f} Acc: {:.4f}".format(phase, epoch_loss, epoch_acc))

            # deep copy the model
            if phase == "val" and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

        print()

    time_elapsed = time.time() - since
    print(
        "Training complete in {:.0f}m {:.0f}s".format(
            time_elapsed // 60, time_elapsed % 60
        )
    )
    print("Best val Acc: {:4f}".format(best_acc))

    # load best model weights
    model.load_state_dict(best_model_wts)
    return model


# %%
model = models.vgg11(pretrained=True)

# Freeze model weights
for param in model.parameters():
    param.requires_grad = False

# Add on classifier
model.classifier[6] = nn.Sequential(
    nn.Linear(4096, 256),
    nn.ReLU(),
    nn.Dropout(0.4),
    nn.Linear(256, len(vod_dataset.character_map.keys())),
    nn.Sigmoid(),
)
model_ft = model.to(device)

criterion = nn.BCELoss()

# Observe that all parameters are being optimized
optimizer_ft = optim.SGD(model_ft.parameters(), lr=0.001, momentum=0.9)

# Decay LR by a factor of 0.1 every 7 epochs
exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=7, gamma=0.1)

# %%
model_ft = train_model(model, criterion, optimizer_ft, exp_lr_scheduler, num_epochs=25)
