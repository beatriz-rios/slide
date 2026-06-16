import cv2
import numpy as np
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
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best.engine')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'captures')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

app = Flask(__name__)
CORS(app)

# YOLO
IMG_SIZE = 320          # Deve ser igual ao usado na exportação do .engine
CONF_THRESHOLD = 0.40
JPEG_QUALITY = 70       # Menor = encoding mais rápido
CAM_WIDTH = 640         # Resolução menor = tudo mais leve
CAM_HEIGHT = 480
SMOOTH_FACTOR = 0.30    # Suavização das boxes (0 = sem suavização, 1 = sem movimento)
MAX_MATCH_DIST = 180    # Distância máxima (px) para associar uma box antiga a uma nova
STALE_FRAMES = 90       # Inferências sem match antes de remover (~1.5s a 60fps)
LABEL_HISTORY_SIZE = 20 # Quantos frames guardar para voto de maioria no label
MIN_HITS_TO_SHOW = 8    # Detecções mínimas antes de exibir a box (evita piscar)

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
        # Vai direto no índice 0 para abrir muito mais rápido
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
            ret, frame = cap.read()
            if ret and frame is not None:
                print("Câmera 0 (DSHOW) conectada.")
                return cap
        cap.release()

        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
            ret, frame = cap.read()
            if ret and frame is not None:
                print("Câmera 0 (Padrão) conectada.")
                return cap
        cap.release()

        return None

    def __init__(self):
        # Modelo
        try:
            self.model = YOLO(MODEL_PATH, task='detect')
            print("Modelo YOLO carregado com sucesso.")
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            self.model = None

        # Câmera
        self.cap = self._find_camera()
        if self.cap:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Estado compartilhado (protegido por locks)
        self._lock = threading.Lock()
        self._raw_frame = None          # Frame cru da câmera
        self._display_frame = None      # Frame com overlay da IA (pronto para stream)
        self._running = True

        # Boxes suavizadas — cada item é um dict:
        #   {x1, y1, x2, y2, label, conf, color, miss_count, hit_count, label_history}
        #   label_history: lista dos últimos N labels para voto de maioria
        #   hit_count: quantas vezes a box foi detectada (precisa de MIN_HITS_TO_SHOW)
        self._smooth_boxes = []       # Lista de boxes sendo interpoladas (lida pela capture)
        self._draw_boxes = []         # Snapshot das boxes prontas para desenhar
        self._boxes_lock = threading.Lock()  # Lock para _draw_boxes

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
    # Voto de maioria para estabilizar o label
    # ----------------------------------------------------------
    @staticmethod
    def _majority_label(label_history, colors_map):
        """Retorna o label mais frequente no histórico."""
        if not label_history:
            return None, None
        from collections import Counter
        counts = Counter(label_history)
        best_label = counts.most_common(1)[0][0]
        best_color = colors_map.get(best_label, (255, 255, 255))
        return best_label, best_color

    # ----------------------------------------------------------
    # Processar novas detecções da IA (chamado APENAS pela AI thread)
    # ----------------------------------------------------------
    def _process_new_detections(self, new_dets):
        """Matching por distância + estabilização de label. Chamado 1x por inferência."""
        targets = new_dets

        if not targets:
            # IA não detectou nada — incrementar miss (1x por inferência, não 30x/s)
            remaining = []
            for sb in self._smooth_boxes:
                sb['miss_count'] = sb.get('miss_count', 0) + 1
                if sb['miss_count'] < STALE_FRAMES:
                    remaining.append(sb)
            self._smooth_boxes = remaining
            self._publish_draw_boxes()
            return

        # --- Helpers ---
        def center(b):
            return ((b['x1'] + b['x2']) / 2, (b['y1'] + b['y2']) / 2)

        def dist(c1, c2):
            return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5

        # Converter targets para dicts
        target_dicts = []
        for t in targets:
            target_dicts.append({
                'x1': t[0], 'y1': t[1], 'x2': t[2], 'y2': t[3],
                'label': t[4], 'conf': t[5], 'color': t[6]
            })

        # --- Matching greedy por distância mínima ---
        used_smooth = set()
        used_target = set()
        matches = []

        pairs = []
        for si, sb in enumerate(self._smooth_boxes):
            sc = center(sb)
            for ti, td in enumerate(target_dicts):
                tc = center(td)
                d = dist(sc, tc)
                if d <= MAX_MATCH_DIST:
                    pairs.append((d, si, ti))

        pairs.sort(key=lambda x: x[0])
        for d, si, ti in pairs:
            if si in used_smooth or ti in used_target:
                continue
            matches.append((si, ti))
            used_smooth.add(si)
            used_target.add(ti)

        # --- Interpolar boxes que deram match ---
        alpha = SMOOTH_FACTOR
        new_smooth = []
        for si, ti in matches:
            sb = self._smooth_boxes[si]
            td = target_dicts[ti]

            # Atualizar histórico de labels (voto de maioria)
            history = list(sb.get('label_history', []))
            history.append(td['label'])
            if len(history) > LABEL_HISTORY_SIZE:
                history = history[-LABEL_HISTORY_SIZE:]

            stable_label, stable_color = self._majority_label(history, COLORS)

            new_smooth.append({
                'x1': int(sb['x1'] * alpha + td['x1'] * (1 - alpha)),
                'y1': int(sb['y1'] * alpha + td['y1'] * (1 - alpha)),
                'x2': int(sb['x2'] * alpha + td['x2'] * (1 - alpha)),
                'y2': int(sb['y2'] * alpha + td['y2'] * (1 - alpha)),
                'label': stable_label,
                'conf': td['conf'],
                'color': stable_color,
                'miss_count': 0,
                'hit_count': sb.get('hit_count', 0) + 1,
                'label_history': history,
            })

        # --- Boxes antigas sem match → incrementar miss ---
        for si, sb in enumerate(self._smooth_boxes):
            if si not in used_smooth:
                sb['miss_count'] = sb.get('miss_count', 0) + 1
                if sb['miss_count'] < STALE_FRAMES:
                    new_smooth.append(sb)

        # --- Targets sem match → adicionar como novas boxes ---
        for ti, td in enumerate(target_dicts):
            if ti not in used_target:
                td['miss_count'] = 0
                td['hit_count'] = 1
                td['label_history'] = [td['label']]
                new_smooth.append(td)

        self._smooth_boxes = new_smooth
        self._publish_draw_boxes()

    def _publish_draw_boxes(self):
        """Publica snapshot das boxes visíveis para a capture thread desenhar."""
        visible = []
        for b in self._smooth_boxes:
            if b.get('hit_count', 0) >= MIN_HITS_TO_SHOW:
                visible.append(dict(b))  # cópia
        with self._boxes_lock:
            self._draw_boxes = visible

    # ----------------------------------------------------------
    # Thread 1: Captura de câmera (roda a ~30fps)
    # ----------------------------------------------------------
    def _capture_loop(self):
        while self._running:
            if self.cap is None or not self.cap.isOpened():
                self.cap = self._find_camera()
                if self.cap:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
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

            frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))

            # IMPORTANTE: salvar frame LIMPO para a IA (sem boxes desenhadas)
            with self._lock:
                self._raw_frame = frame.copy()

            # Desenhar boxes APENAS no frame de exibição (cópia separada)
            display = frame.copy()
            with self._boxes_lock:
                boxes_to_draw = list(self._draw_boxes)

            for box in boxes_to_draw:
                x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
                label, conf, color = box['label'], box['conf'], box['color']
                cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display, f"{label}",
                            (x1, max(y1 - 10, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            with self._lock:
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

            # Rodar detecção na GPU com TensorRT (FP16)
            results = self.model.predict(
                frame, imgsz=IMG_SIZE,
                conf=CONF_THRESHOLD, half=True,
                device=0, verbose=False
            )

            new_dets = []
            new_entries = []
            current_time = time.time()
            can_save = (current_time - self.last_save_time) >= 60.0

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

            # Processar detecções: matching + estabilização (1x por inferência)
            self._process_new_detections(new_dets)

            # Salvar histórico
            if new_entries and can_save:
                self.last_save_time = current_time
                for entry in new_entries:
                    self.full_history.insert(0, entry)
                self._save_history()

            # Sem pausa — rodar o mais rápido possível

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

            # Streaming rápido sem delay fixo
            time.sleep(0.016)

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

