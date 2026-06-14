import cv2
import time
import os
import json
import threading
from flask import Flask, Response, jsonify, send_from_directory, request
from flask_cors import CORS
from ultralytics import YOLO

# ============================================================
# Configurações
# ============================================================
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best.pt')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'captures')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

app = Flask(__name__)
CORS(app)

# YOLO
IMG_SIZE = 640          # Tamanho padrão para melhor precisão do YOLO (era 416)
CONF_THRESHOLD = 0.55
JPEG_QUALITY = 90       # Qualidade JPEG maior para melhor visualização (era 70)

COLORS = {
    'Oculos EPI': (0, 255, 0),
    'Oculos Comum': (0, 165, 255),
    'Sem Oculos EPI': (0, 0, 255)
}
CLASSES_MAP = {
    'oculos_epi': 'Oculos EPI',
    'oculos_comum': 'Oculos Comum',
    'sem_oculos': 'Sem Oculos EPI'
}


class Detector:
    """
    Arquitetura com 3 threads:
      1. _capture_thread  – lê a câmera o mais rápido possível
      2. _ai_thread       – roda YOLO a cada N frames, salva as detecções
      3. generate_frames  – pega o frame mais recente (com overlay) e envia ao browser
    """

    def _find_camera(self):
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"Câmera funcional encontrada no índice {i} (DSHOW)")
                    return cap
            cap.release()

        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"Câmera funcional encontrada no índice {i} (Padrão)")
                    return cap
            cap.release()

        return None

    def __init__(self):
        # Modelo
        try:
            self.model = YOLO(MODEL_PATH)
            print("Modelo YOLO carregado com sucesso.")
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            self.model = None

        # Câmera
        self.cap = self._find_camera()
        if self.cap:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Estado compartilhado (protegido por locks)
        self._lock = threading.Lock()
        self._raw_frame = None          # Frame cru da câmera
        self._display_frame = None      # Frame com overlay da IA (pronto para stream)
        self._running = True

        # Detecções (para overlay)
        self._detections = []           # Lista de (x1,y1,x2,y2,label,conf,color)

        # Histórico
        self.last_save_time = 0
        self.history_file = os.path.join(os.path.dirname(__file__), 'history.json')
        self.full_history = self._load_history()

        # JPEG encode params
        self._encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]

        # Iniciar threads
        self._capture_t = threading.Thread(target=self._capture_loop, daemon=True)
        self._ai_t = threading.Thread(target=self._ai_loop, daemon=True)
        self._capture_t.start()
        self._ai_t.start()
        print("Threads de captura e IA iniciadas.")

    # ----------------------------------------------------------
    # Histórico
    # ----------------------------------------------------------
    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_history(self):
        self.full_history = self.full_history[:1000]
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.full_history, f)
        except:
            pass

    # ----------------------------------------------------------
    # Thread 1: Captura de câmera (roda a ~30fps)
    # ----------------------------------------------------------
    def _capture_loop(self):
        while self._running:
            if self.cap is None or not self.cap.isOpened():
                self.cap = self._find_camera()
                if self.cap:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                else:
                    time.sleep(1)
                    continue

            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                self.cap = None
                time.sleep(0.5)
                continue

            frame = cv2.resize(frame, (1280, 720))

            # Desenhar overlay das últimas detecções da IA no frame
            display = frame.copy()
            with self._lock:
                dets = list(self._detections)

            for (x1, y1, x2, y2, label, conf, color) in dets:
                cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display, f"{label} {conf*100:.0f}%",
                            (x1, max(y1 - 10, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            with self._lock:
                self._raw_frame = frame
                self._display_frame = display

    # ----------------------------------------------------------
    # Thread 2: IA / YOLO (roda a cada ~150ms)
    # ----------------------------------------------------------
    def _ai_loop(self):
        while self._running:
            with self._lock:
                frame = self._raw_frame.copy() if self._raw_frame is not None else None

            if frame is None or self.model is None:
                time.sleep(0.1)
                continue

            # Rodar detecção
            results = self.model.track(
                frame, persist=True, imgsz=IMG_SIZE,
                conf=CONF_THRESHOLD, verbose=False
            )

            new_dets = []
            new_entries = []
            current_time = time.time()
            can_save = (current_time - self.last_save_time) >= 3.0

            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    label = CLASSES_MAP.get(self.model.names[cls_id], self.model.names[cls_id])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    color = COLORS.get(label, (255, 255, 255))
                    new_dets.append((x1, y1, x2, y2, label, conf, color))

                    if can_save and label in ['Oculos Comum', 'Sem Oculos EPI']:
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        clean_label = label.replace('Ó', 'O').replace(' ', '_').lower()
                        filename = f"demo_{clean_label}_seg{conf*100:.0f}_{timestamp}.jpg"
                        filepath = os.path.join(OUTPUT_DIR, filename)
                        cv2.imwrite(filepath, frame)

                        new_entries.append({
                            "tipo": label.replace('_', ' ').title(),
                            "data": time.strftime("%d/%m/%Y"),
                            "hora": time.strftime("%H:%M:%S"),
                            "confianca": f"{conf*100:.0f}%",
                            "imagem": filename
                        })

            # Atualizar detecções compartilhadas
            with self._lock:
                self._detections = new_dets

            # Salvar histórico
            if new_entries and can_save:
                self.last_save_time = current_time
                for entry in new_entries:
                    self.full_history.insert(0, entry)
                self._save_history()

            # Pequena pausa para não sobrecarregar a CPU
            time.sleep(0.05)

    # ----------------------------------------------------------
    # Gerador MJPEG para o Flask (stream fluido)
    # ----------------------------------------------------------
    def generate_frames(self):
        while self._running:
            with self._lock:
                frame = self._display_frame

            if frame is None:
                time.sleep(0.03)
                continue

            ret, buffer = cv2.imencode('.jpg', frame, self._encode_params)
            if not ret:
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            # ~30 fps de streaming
            time.sleep(0.033)

    # ----------------------------------------------------------
    # Desligar tudo (câmera + threads)
    # ----------------------------------------------------------
    def stop(self):
        print("Desligando detector...")
        self._running = False
        time.sleep(0.2)
        if self.cap and self.cap.isOpened():
            self.cap.release()
            print("Câmera liberada.")
        self.cap = None


# ============================================================
# Instância global
# ============================================================
detector = Detector()


# ============================================================
# Rotas Flask
# ============================================================
@app.route('/video_feed')
def video_feed():
    return Response(detector.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/history')
def history():
    return jsonify(detector._load_history())

@app.route('/captures/<path:filename>')
def serve_capture(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/clear_history')
def clear_history():
    detector.full_history = []
    detector._save_history()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.jpg'):
            try:
                os.remove(os.path.join(OUTPUT_DIR, f))
            except:
                pass
    return jsonify({"status": "success"})

@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    detector.stop()
    # Encerrar o processo Flask
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    else:
        # Forçar encerramento do processo
        import signal
        os.kill(os.getpid(), signal.SIGTERM)
    return jsonify({"status": "shutting_down"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)

