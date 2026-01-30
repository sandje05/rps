import torch
import torch.nn as nn
from torchvision.models import resnet18

DEVICE = torch.device("cpu")
MODEL_PATH = "/app/model/rps_resnet18.pth"

def load_model():
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 3)

    state = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True)
    model.load_state_dict(state)

    model.to(DEVICE)
    model.eval()
    return model
