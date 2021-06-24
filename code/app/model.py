from app import db
from app.classes import Candidates
import pandas as pd
import numpy as np
from tqdm import tqdm
import cv2
import torch
from torch.utils.data import DataLoader, Dataset
import torch.nn as nn
import torch.nn.functional as F
import albumentations
import timm
from warnings import filterwarnings
import math
import boto3
import os
filterwarnings("ignore")

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

image_size = 128

transforms_valid = albumentations.Compose([
    albumentations.Resize(image_size, image_size),
    albumentations.Normalize()
])



class DFDataset(Dataset):
    def __init__(self, arr, mode, transform=None):
        
        self.arr = arr
        self.mode = mode
        self.transform = transform
        
    def __len__(self):
        return len(self.arr)
    
    def __getitem__(self, index):
        row = self.arr[index]
        image_name = row[1].split('/')[-1]
        file_obj = s3.get_object(Bucket=img_bucket, Key=image_name)
        file_content = file_obj["Body"].read()

        np_array = np.fromstring(file_content,dtype=np.uint8)
        image_np = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32)
        if self.transform is not None:
            res = self.transform(image=img)
            img = res['image']
                
        img = img.astype(np.float32)
        img = img.transpose(2,0,1)
        
        return torch.tensor(img).float()


class ArcModule(nn.Module):
    def __init__(self, in_features, out_features, s=10, m=0):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.s = s
        self.m = m
        self.weight = nn.Parameter(torch.FloatTensor(out_features, in_features))
        nn.init.xavier_normal_(self.weight)

        self.cos_m = math.cos(m)
        self.sin_m = math.sin(m)
        self.th = torch.tensor(math.cos(math.pi - m))
        self.mm = torch.tensor(math.sin(math.pi - m) * m)

    def forward(self, inputs, labels):
        cos_th = F.linear(inputs, F.normalize(self.weight))
        cos_th = cos_th.clamp(-1, 1)
        sin_th = torch.sqrt(1.0 - torch.pow(cos_th, 2))
        cos_th_m = cos_th * self.cos_m - sin_th * self.sin_m
        cos_th_m = torch.where(cos_th > self.th, cos_th_m, cos_th - self.mm)

        cond_v = cos_th - self.th
        cond = cond_v <= 0
        cos_th_m[cond] = (cos_th - self.mm)[cond]

        if labels.dim() == 1:
            labels = labels.unsqueeze(-1)
        onehot = torch.zeros(cos_th.size()).cuda()
        labels = labels.type(torch.LongTensor).cuda()
        onehot.scatter_(1, labels, 1.0)
        outputs = onehot * cos_th_m + (1.0 - onehot) * cos_th
        outputs = outputs * self.s
        return outputs




class MetricLearningModel(nn.Module):

    def __init__(self, channel_size, out_feature, dropout=0.5, backbone='densenet121', pretrained=True):
        super(MetricLearningModel, self).__init__()
        self.backbone = timm.create_model(backbone, pretrained=pretrained)
        self.channel_size = channel_size
        self.out_feature = out_feature
        self.in_features = self.backbone.classifier.in_features
        self.margin = ArcModule(in_features=self.channel_size, out_features = self.out_feature)
        self.bn1 = nn.BatchNorm2d(self.in_features)
        self.dropout = nn.Dropout2d(dropout, inplace=True)
        self.fc1 = nn.Linear(16384 , self.channel_size)
        self.bn2 = nn.BatchNorm1d(self.channel_size)
        
    def forward(self, x, labels=None):
        features = self.backbone.features(x)
        features = self.bn1(features)
        features = self.dropout(features)
        features = features.view(features.size(0), -1)
        features = self.fc1(features)
        features = self.bn2(features)
        features = F.normalize(features)

        return features




def generate_test_features(test_loader):
    model.eval()
    bar = tqdm(test_loader)
    
    FEAS = []
    TARGETS = []

    with torch.no_grad():
        for batch_idx, (images) in enumerate(bar):

            images = images.to(device)

            features = model(images)

            FEAS += [features.detach().to(device)]

    FEAS = torch.cat(FEAS).to('cpu').numpy()
    
    return FEAS

model = MetricLearningModel(128, 5555)
model.to(device)
model.load_state_dict(torch.load('dense121_feature_extractor3.pth',map_location=torch.device('cpu')))
if os.path.exists('features.npy'):
	features = np.load('features.npy')
	print('loaded precomputed embeddings')

























