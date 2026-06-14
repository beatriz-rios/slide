from ultralytics import YOLO
import sys

try:
    model = YOLO(r'C:\xampp\htdocs\epi-apresentacao\bestnovoMelhor.pt')
    print(f"Classes: {model.names}")
except Exception as e:
    print(f"Erro: {e}")
