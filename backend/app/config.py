import os

MODEL_PATH = os.getenv("MODEL_PATH", "/app/model/rps_resnet18.pth")
DEVICE = os.getenv("DEVICE", "cpu")

# bv folders: Paper, Rock, Scissors -> alfabetisch: Paper, Rock, Scissors
CLASS_LABELS = ["paper", "rock", "scissors"]
