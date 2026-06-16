import os
import time
import torch
from ultralytics import YOLO

MODEL_PT = os.path.join("IA_apresentacao", "best(2).pt")
IMGSZ = 640      # Mesmo tamanho usado no detector_web.py
HALF = True        # FP16 para RTX 3050

print("=" * 55)
print("VERIFICANDO AMBIENTE")
print("=" * 55)
print(f"PyTorch: {torch.__version__}")
print(f"CUDA disponível: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")

if not os.path.exists(MODEL_PT):
    raise SystemExit(f"ERRO: não encontrei '{MODEL_PT}'.")

print("\n" + "=" * 55)
print("EXPORTANDO PARA TENSORRT (.engine)")
print("=" * 55)
print("Isto pode levar de 2 a 10 minutos. NÃO feche.\n")

model = YOLO(MODEL_PT)
print(f"Classes do modelo: {model.names}")

t0 = time.time()
engine_path = model.export(
    format="engine",
    half=HALF,
    device=0,
    imgsz=IMGSZ,
)
dur = time.time() - t0
print(f"\n✓ Engine gerada em {dur/60:.1f} min")
print(f"  Arquivo: {engine_path}")

# Teste rápido
print("\nTestando a engine...")
import numpy as np
engine_file = MODEL_PT.replace(".pt", ".engine")
engine_model = YOLO(engine_file, task='detect')
dummy = np.zeros((IMGSZ, IMGSZ, 3), dtype=np.uint8)
_ = engine_model.predict(dummy, imgsz=IMGSZ, half=HALF, verbose=False)
print(f"✓ Engine '{engine_file}' funciona perfeitamente!")
