import io
import torch
from PIL import Image
from torchvision import transforms
from .model_loader import load_model

model = load_model()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

labels = ["paper", "rock", "scissors"]

def predict_move(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(tensor)
        _, predicted = torch.max(outputs, 1)

    return labels[predicted.item()]
