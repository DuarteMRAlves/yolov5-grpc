import torch

_MODEL_REPO = 'ultralytics/yolov5'
_MODEL_VERSION = 'yolov5s'

torch.hub.load(_MODEL_REPO, _MODEL_VERSION, pretrained=True)