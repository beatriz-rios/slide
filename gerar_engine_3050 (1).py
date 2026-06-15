# ==============================================================
# GERAR .engine (TensorRT) A PARTIR DO best.pt
# Rodar NA MÁQUINA DE PRODUÇÃO (a que tem a RTX 3050)
# A engine gerada serve SÓ para esta GPU/ambiente.
# ==============================================================

# --------------------------------------------------------------
# 0. INSTALAÇÃO (rode uma vez, no terminal ou descomente abaixo)
# --------------------------------------------------------------
# pip install ultralytics
# pip install tensorrt        # necessário para exportar .engine
#
# Pré-requisitos no sistema (fora do Python):
#   - Driver NVIDIA atualizado
#   - CUDA instalado
# Para conferir o driver, rode no terminal:  nvidia-smi

import os
import time

# --------------------------------------------------------------
# 1. CONFIGURAÇÃO
# --------------------------------------------------------------
MODEL_PT = "best.pt"      # caminho do seu best.pt (ajuste se estiver em outra pasta)
IMGSZ    = 640            # tamanho de inferência. 640 = bom equilíbrio p/ portaria.
                          # NÃO troque depois sem reexportar: a engine fica fixa neste valor.
HALF     = True           # FP16 — mais rápido na GPU. Mantenha True na 3050.

# --------------------------------------------------------------
# 2. VERIFICAÇÃO DE AMBIENTE
# --------------------------------------------------------------
print("=" * 55)
print("VERIFICANDO AMBIENTE")
print("=" * 55)

import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA disponível: {torch.cuda.is_available()}")

if not torch.cuda.is_available():
    print("\n⚠ ERRO: CUDA não está disponível.")
    print("  A 3050 não está sendo detectada. Verifique:")
    print("  - Driver NVIDIA instalado (rode 'nvidia-smi' no terminal)")
    print("  - PyTorch com suporte CUDA (não a versão CPU-only)")
    raise SystemExit("Sem GPU CUDA — não é possível gerar a engine.")

print(f"GPU detectada: {torch.cuda.get_device_name(0)}")

if not os.path.exists(MODEL_PT):
    raise SystemExit(f"\n⚠ ERRO: não encontrei '{MODEL_PT}'. Verifique o caminho.")

# --------------------------------------------------------------
# 3. EXPORTAÇÃO PARA TENSORRT (.engine)
# --------------------------------------------------------------
from ultralytics import YOLO

print("\n" + "=" * 55)
print("EXPORTANDO PARA TENSORRT")
print("=" * 55)
print("⏳ Isto leva de 2 a 10 minutos. A tela pode ficar parada —")
print("   é NORMAL, o TensorRT está testando otimizações. NÃO feche.\n")

model = YOLO(MODEL_PT)
print(f"Classes do modelo: {model.names}")

t0 = time.time()
try:
    engine_path = model.export(
        format="engine",
        half=HALF,
        device=0,
        imgsz=IMGSZ,
    )
    dur = time.time() - t0
    print(f"\n✓ Engine gerada com sucesso em {dur/60:.1f} min")
    print(f"  Arquivo: {engine_path}")

except Exception as e:
    print(f"\n⚠ A exportação falhou: {e}")
    print("\n  Causa mais comum: TensorRT não instalado.")
    print("  Solução: rode no terminal  ->  pip install tensorrt")
    print("  Depois execute este script de novo.")
    raise SystemExit("Exportação interrompida.")

# --------------------------------------------------------------
# 4. TESTE RÁPIDO — confirma que a engine carrega e infere
# --------------------------------------------------------------
print("\n" + "=" * 55)
print("TESTANDO A ENGINE GERADA")
print("=" * 55)

engine_file = MODEL_PT.replace(".pt", ".engine")
try:
    engine_model = YOLO(engine_file)
    # roda uma inferência de teste numa imagem preta só para validar
    import numpy as np
    dummy = np.zeros((IMGSZ, IMGSZ, 3), dtype=np.uint8)
    _ = engine_model.predict(dummy, imgsz=IMGSZ, half=HALF, verbose=False)
    print(f"✓ Engine '{engine_file}' carregou e rodou inferência sem erros.")
except Exception as e:
    print(f"⚠ A engine foi gerada mas deu erro ao testar: {e}")

# --------------------------------------------------------------
# 5. COMO USAR NA WEBCAM (referência)
# --------------------------------------------------------------
print("""
============== PRONTO! COMO USAR NA WEBCAM ==============

  from ultralytics import YOLO

  model = YOLO("best.engine")

  model.predict(
      source=0,        # 0 = webcam padrão
      conf=0.45,       # ajuste 0.35-0.55 conforme falsos positivos
      iou=0.5,
      imgsz=640,       # TEM que ser igual ao usado na exportação
      half=True,
      show=True,
      stream=True,
  )
========================================================
""")
