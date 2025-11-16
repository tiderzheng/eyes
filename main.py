import sys
import os
import base64
import threading
import time
import cv2
import numpy as np
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox, QSlider
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRect, QTimer

class DummyEngine:
    def recognize(self, image_bgr):
        return ""

class OpenAIOCREngine:
    def __init__(self, endpoint, api_key, model, prompt, system_prompt=None):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
        self.system_prompt = system_prompt or ""
        self.session = requests.Session()

    def _encode_image(self, image_bgr):
        _, buf = cv2.imencode('.png', image_bgr)
        return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode('ascii')

    def recognize(self, image_bgr):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        image_url = self._encode_image(image_bgr)
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": self.prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        })
        payload = {"model": self.model, "messages": messages, "temperature": 0}
        try:
            r = self.session.post(self.endpoint.rstrip('/') + "/v1/chat/completions", headers=headers, json=payload, timeout=30)
            j = r.json()
            c = j.get("choices", [])
            if not c:
                return ""
            m = c[0].get("message", {})
            content = m.get("content", "")
            if isinstance(content, list) and content and isinstance(content[0], dict):
                t = content[0].get("text", "")
                return t.strip()
            if isinstance(content, str):
                return content.strip()
            return ""
        except Exception:
            return ""

def format_srt_timestamp(ms):
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    msr = ms % 1000
    return f"{h:02}:{m:02}:{s:02},{msr:03}"

def write_srt(entries, path):
    lines = []
    for i, e in enumerate(entries, 1):
        lines.append(str(i))
        lines.append(f"{format_srt_timestamp(e['start'])} --> {format_srt_timestamp(e['end'])}")
        lines.append(e['text'])
        lines.append("")
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

class VideoLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pix = None
        self.selecting = False
        self.rect = QRect()
        self.start_pos = None
        self.draw_rect = QRect()
        self.scale_x = 1.0
        self.scale_y = 1.0
        self._rect_cb = None

    def set_image(self, img_bgr):
        h, w, _ = img_bgr.shape
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        qimg = QImage(img_rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        self.pix = QPixmap.fromImage(qimg)
        self.setPixmap(self.pix)
        self.update()

    def mousePressEvent(self, e):
        if self.pix is None:
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self.selecting = True
            self.start_pos = e.position().toPoint()
            self.rect = QRect(self.start_pos, self.start_pos)
            self.update()

    def mouseMoveEvent(self, e):
        if self.selecting and self.pix is not None:
            cur = e.position().toPoint()
            self.rect = QRect(self.start_pos, cur).normalized()
            self.update()
            if self._rect_cb:
                r = self.get_selection_rect_in_image()
                if r:
                    self._rect_cb(r)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
            self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.pix is not None:
            p = QPainter(self)
            lw = self.width()
            lh = self.height()
            iw = self.pix.width()
            ih = self.pix.height()
            if iw > 0 and ih > 0 and lw > 0 and lh > 0:
                s = min(lw / iw, lh / ih)
                tw = int(iw * s)
                th = int(ih * s)
                ox = (lw - tw) // 2
                oy = (lh - th) // 2
                self.draw_rect = QRect(ox, oy, tw, th)
                self.scale_x = iw / max(1, tw)
                self.scale_y = ih / max(1, th)
                p.drawPixmap(self.draw_rect, self.pix)
            if not self.rect.isNull():
                p.setPen(QPen(QColor(255, 0, 0, 200), 2))
                p.drawRect(self.rect)

    def get_selection_rect_in_image(self):
        if self.pix is None or self.rect.isNull() or self.draw_rect.isNull():
            return None
        sel = self.rect.intersected(self.draw_rect)
        if sel.isNull():
            return None
        rx = sel.x() - self.draw_rect.x()
        ry = sel.y() - self.draw_rect.y()
        rw = sel.width()
        rh = sel.height()
        x = int(rx * self.scale_x)
        y = int(ry * self.scale_y)
        w = int(rw * self.scale_x)
        h = int(rh * self.scale_y)
        iw = self.pix.width()
        ih = self.pix.height()
        x = max(0, min(x, iw - 1))
        y = max(0, min(y, ih - 1))
        w = max(1, min(w, iw - x))
        h = max(1, min(h, ih - y))
        return x, y, w, h

    def set_rect_callback(self, cb):
        self._rect_cb = cb

class Extractor:
    def __init__(self, video_path, region, engine, sample_ms, min_duration_ms, output_path):
        self.video_path = video_path
        self.region = region
        self.engine = engine
        self.sample_ms = sample_ms
        self.min_duration_ms = min_duration_ms
        self.output_path = output_path
        self.progress = 0
        self.done = False
        self.error = None
        self.started_at = 0.0
        self.finished_at = 0.0
        self.elapsed_ms = 0
        self.frames_processed = 0
        self.total_frames = 0
        self.entries_count = 0

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            self.error = "无法打开视频"
            self.done = True
            return
        fps = cap.get(cv2.CAP_PROP_FPS)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.total_frames = total
        step = max(1, int(fps * self.sample_ms / 1000))
        entries = []
        prev_text = None
        cur_start_ms = None
        i = 0
        self.started_at = time.time()
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if i % step != 0:
                i += 1
                continue
            crop = frame
            if self.region is not None:
                x, y, w, h = self.region
                x = max(0, x)
                y = max(0, y)
                w = max(1, w)
                h = max(1, h)
                x2 = min(frame.shape[1], x + w)
                y2 = min(frame.shape[0], y + h)
                crop = frame[y:y2, x:x2]
            text = self.engine.recognize(crop).strip()
            t_ms = int((i / max(1, fps)) * 1000)
            if text and prev_text is None:
                prev_text = text
                cur_start_ms = t_ms
            elif text and prev_text is not None:
                if normalize_text(text) != normalize_text(prev_text):
                    end_ms = max(t_ms, cur_start_ms + self.min_duration_ms)
                    entries.append({"start": cur_start_ms, "end": end_ms, "text": prev_text})
                    prev_text = text
                    cur_start_ms = t_ms
            elif not text and prev_text is not None:
                end_ms = max(t_ms, cur_start_ms + self.min_duration_ms)
                entries.append({"start": cur_start_ms, "end": end_ms, "text": prev_text})
                prev_text = None
                cur_start_ms = None
            self.progress = int((i + 1) / max(1, total) * 100)
            self.frames_processed += 1
            i += 1
        if prev_text is not None and cur_start_ms is not None:
            end_ms = max(t_ms, cur_start_ms + self.min_duration_ms)
            entries.append({"start": cur_start_ms, "end": end_ms, "text": prev_text})
        cap.release()
        if entries:
            write_srt(entries, self.output_path)
        self.entries_count = len(entries)
        self.finished_at = time.time()
        self.elapsed_ms = int((self.finished_at - self.started_at) * 1000)
        self.done = True

def normalize_text(t):
    return ''.join(t.lower().split())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("字幕提取工具")
        self.video_path = None
        self.first_frame = None
        self.cap = None
        self.fps = 0.0
        self.frame_count = 0
        self.cur_index = 0
        self.label = VideoLabel()
        self.open_btn = QPushButton("打开视频")
        self.extract_btn = QPushButton("开始提取")
        self.status_label = QLabel("")
        self.coord_label = QLabel("")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(False)
        self.open_btn.clicked.connect(self.open_video)
        self.extract_btn.clicked.connect(self.start_extract)
        self.extract_btn.setEnabled(False)
        self.slider.valueChanged.connect(self.on_seek)
        self.label.set_rect_callback(self.on_rect_changed)
        w = QWidget()
        lay = QVBoxLayout()
        ctrl = QHBoxLayout()
        ctrl.addWidget(self.open_btn)
        ctrl.addWidget(self.extract_btn)
        lay.addLayout(ctrl)
        lay.addWidget(self.label)
        lay.addWidget(self.slider)
        info = QHBoxLayout()
        info.addWidget(self.status_label)
        info.addWidget(self.coord_label)
        lay.addLayout(info)
        w.setLayout(lay)
        self.setCentralWidget(w)
        self.timer = QTimer()
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.poll_extractor)
        self.extractor = None
        self.thread = None

    def open_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "视频文件 (*.mp4 *.mkv *.avi *.mov)")
        if not path:
            return
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "错误", "无法打开视频")
            return
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 0.0
        if self.fps <= 0:
            self.fps = 25.0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.critical(self, "错误", "无法读取视频帧")
            return
        self.video_path = path
        self.first_frame = frame
        self.label.set_image(frame)
        self.extract_btn.setEnabled(True)
        self.slider.setRange(0, max(0, self.frame_count - 1))
        self.slider.setValue(0)
        self.slider.setEnabled(True)
        self.cur_index = 0
        self.status_label.setText(self.format_time(self.cur_index))

    def build_engine(self):
        api_key = os.getenv("OCR_API_KEY", "")
        endpoint = os.getenv("OCR_API_ENDPOINT", "http://localhost:1234")
        model = os.getenv("OCR_API_MODEL", "qwen/qwen3-vl-8b")
        prompt = os.getenv("OCR_PROMPT", "只返回图片中的可读字幕文本")
        system_prompt = os.getenv("OCR_SYSTEM_PROMPT", "")
        return OpenAIOCREngine(endpoint, api_key, model, prompt, system_prompt)

    def start_extract(self):
        if not self.video_path:
            return
        r = self.label.get_selection_rect_in_image()
        base = os.path.splitext(os.path.basename(self.video_path))[0] + ".srt"
        out = os.path.join(os.path.dirname(self.video_path), base)
        engine = self.build_engine()
        self.extractor = Extractor(self.video_path, r, engine, 800, 1200, out)
        self.thread = threading.Thread(target=self.extractor.run, daemon=True)
        self.thread.start()
        self.timer.start()
        self.extract_btn.setEnabled(False)
        self.status_label.setText("正在提取…")

    def poll_extractor(self):
        if not self.extractor:
            return
        p = self.extractor.progress
        if self.extractor.started_at:
            elapsed = int((time.time() - self.extractor.started_at) * 1000)
            self.status_label.setText(f"进度 {p}% | 已用 {elapsed/1000:.1f}s")
        else:
            self.status_label.setText(f"进度 {p}%")
        if self.extractor.done:
            self.timer.stop()
            self.extract_btn.setEnabled(True)
            if self.extractor.error:
                QMessageBox.critical(self, "错误", self.extractor.error)
            else:
                detail = []
                detail.append(f"开始时间: {self.format_wall(self.extractor.started_at)}")
                detail.append(f"结束时间: {self.format_wall(self.extractor.finished_at)}")
                detail.append(f"总耗时: {self.extractor.elapsed_ms/1000:.1f}s")
                detail.append(f"处理帧数: {self.extractor.frames_processed}/{self.extractor.total_frames}")
                rect = self.label.get_selection_rect_in_image()
                if rect:
                    x, y, w, h = rect
                    detail.append(f"裁切区域: x={x} y={y} w={w} h={h}")
                detail.append(f"采样间隔: {self.extractor.sample_ms}ms")
                detail.append(f"最短字幕时长: {self.extractor.min_duration_ms}ms")
                detail.append(f"识别条目: {self.extractor.entries_count}")
                detail.append(f"输出文件: {self.extractor.output_path}")
                if isinstance(self.extractor.engine, OpenAIOCREngine):
                    detail.append(f"模型: {self.extractor.engine.model}")
                    detail.append(f"端点: {self.extractor.engine.endpoint}")
                QMessageBox.information(self, "完成", "\n".join(detail))
                self.status_label.setText("完成")

    def on_seek(self, idx):
        if not self.cap:
            return
        idx = int(idx)
        self.cur_index = idx
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = self.cap.read()
        if ret:
            self.label.set_image(frame)
            self.status_label.setText(self.format_time(idx))

    def on_rect_changed(self, rect):
        if rect:
            x, y, w, h = rect
            self.coord_label.setText(f"区域 x={x} y={y} w={w} h={h}")
        else:
            self.coord_label.setText("")

    def format_time(self, index):
        ms = int((index / max(1.0, self.fps)) * 1000)
        return f"时间 {format_srt_timestamp(ms)}"

    def format_wall(self, ts):
        if not ts:
            return ""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(960, 640)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
