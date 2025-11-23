import sys
import os
import base64
import threading
import time
import cv2
import numpy as np
import requests
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton,
                               QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox,
                               QSlider, QComboBox, QProgressBar, QTextEdit, QDialog,
                               QDialogButtonBox, QListWidget, QListWidgetItem,
                               QLineEdit, QPlainTextEdit, QInputDialog, QStyle, QStyleOptionComboBox)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRect, QTimer
from prompt_manager import PromptManager
from prompt_config_ui import PromptConfigDialog
from config_manager import ConfigManager, APIConfig
from api_config_ui import APIConfigDialog

class ArrowComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.arrow_label = QLabel("⬇️", self)
        self.arrow_label.setStyleSheet("background: transparent; font-size: 12px;")
        self.arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_arrow_position()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_arrow_position()

    def _update_arrow_position(self):
        opt = QStyleOptionComboBox()
        opt.initFrom(self)
        rect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, opt,
                                          QStyle.SubControl.SC_ComboBoxArrow, self)
        self.arrow_label.setGeometry(rect)


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

    def recognize(self, image_bgr, should_stop=None):
        """
        Recognize text with optional stop check
        should_stop: callable that returns True if should stop processing
        """
        # Quick check before making request
        if should_stop and should_stop():
            return ""

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

        # Use shorter timeout to allow more frequent stop checks
        timeout = 5  # Reduced from 30 to 5 seconds for very responsive stop

        try:
            r = self.session.post(self.endpoint.rstrip('/') + "/v1/chat/completions", headers=headers, json=payload, timeout=timeout)
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

def write_txt(entries, path):
    """Write entries as plain text article"""
    lines = []
    for i, e in enumerate(entries, 1):
        lines.append(e['text'])
        lines.append("")  # Add blank line between entries
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines).strip())

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
        self.stopped = False  # Add stop flag
        self.error = None
        self.started_at = 0.0
        self.finished_at = 0.0
        self.elapsed_ms = 0
        self.frames_processed = 0
        self.total_frames = 0
        self.entries_count = 0
        self.current_entries_count = 0  # Track current entries count during extraction

    def _filter_subtitle_text(self, text):
        """Filter out descriptive responses when no subtitles are present"""
        if not text:
            return ""

        # List of keywords that indicate no subtitles (in Chinese and English)
        no_subtitle_patterns = [
            # Chinese patterns
            "图中无", "没有字幕", "无字幕", "没有文字", "无文字",
            "没有可读", "无可读", "没有内容", "无内容",
            "图片中无", "图片中没有", "画面无", "画面中无",
            "未发现", "未找到", "不存在",
            # English patterns
            "no subtitle", "no text", "no readable",
            "no content", "nothing", "empty",
            # Common descriptive phrases
            "图中", "图片中", "画面", "此图", "该图",
            "截图", "视频", "帧",
        ]

        # Convert to lowercase for matching
        text_lower = text.lower()

        # Check if text contains no-subtitle patterns
        for pattern in no_subtitle_patterns:
            if pattern in text_lower:
                # Check if text is short (descriptive responses are usually short)
                if len(text) <= 20 or text_lower.strip() == pattern:
                    return ""

        # Additional check: if text looks like a description rather than subtitles
        # Subtitles usually contain dialogue, while descriptions explain the image
        description_indicators = [
            "字幕", "文字", "文本", "内容",
            "截图", "图片", "画面", "视频", "帧",
        ]

        # If text contains these words AND is short, it's likely a description
        if len(text) <= 15:
            for indicator in description_indicators:
                if indicator in text_lower:
                    return ""

        return text

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
            if self.stopped:
                cap.release()
                self.done = True
                return
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
            raw_text = self.engine.recognize(crop, should_stop=lambda: self.stopped).strip()
            # Post-process: filter out descriptive responses when no subtitles
            text = self._filter_subtitle_text(raw_text)
            t_ms = int((i / max(1, fps)) * 1000)
            if text and prev_text is None:
                prev_text = text
                cur_start_ms = t_ms
            elif text and prev_text is not None:
                if normalize_text(text) != normalize_text(prev_text):
                    end_ms = max(t_ms, cur_start_ms + self.min_duration_ms)
                    entries.append({"start": cur_start_ms, "end": end_ms, "text": prev_text})
                    self.current_entries_count += 1
                    prev_text = text
                    cur_start_ms = t_ms
            elif not text and prev_text is not None:
                end_ms = max(t_ms, cur_start_ms + self.min_duration_ms)
                entries.append({"start": cur_start_ms, "end": end_ms, "text": prev_text})
                self.current_entries_count += 1
                prev_text = None
                cur_start_ms = None
            self.progress = int((i + 1) / max(1, total) * 100)
            self.frames_processed += 1
            i += 1
        if prev_text is not None and cur_start_ms is not None:
            end_ms = max(t_ms, cur_start_ms + self.min_duration_ms)
            entries.append({"start": cur_start_ms, "end": end_ms, "text": prev_text})
            self.current_entries_count += 1
        self.entries = entries  # Store entries for potential save on stop
        cap.release()
        if entries:
            write_srt(entries, self.output_path)
            # Also write as plain text
            txt_path = self.output_path.replace('.srt', '.txt')
            write_txt(entries, txt_path)
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
        self.setStyleSheet(self.get_modern_stylesheet())
        self.video_path = None
        self.first_frame = None
        self.cap = None
        self.fps = 0.0
        self.frame_count = 0
        self.cur_index = 0
        self.label = VideoLabel()
        self.open_btn = QPushButton("打开视频")
        self.open_btn.setObjectName("open_btn")

        self.extract_btn = QPushButton("开始提取")
        self.extract_btn.setObjectName("extract_btn")

        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")

        self.coord_label = QLabel("")
        self.coord_label.setObjectName("coord_label")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(False)

        # API selection combo with light arrow
        self.api_combo = ArrowComboBox()
        self.api_combo.setEditable(True)
        self.api_combo.setObjectName("api_combo")

        self.api_btn = QPushButton("管理API")
        self.api_btn.setObjectName("api_btn")

        self.stop_btn = QPushButton("终止")
        self.stop_btn.setObjectName("stop_btn")

        # Prompt selection combo with light arrow
        self.prompt_combo = ArrowComboBox()
        self.prompt_combo.setObjectName("prompt_combo")

        self.suggest_prompt_btn = QPushButton("建议Prompt")
        self.suggest_prompt_btn.setObjectName("suggest_prompt_btn")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 10000)
        self.progress_bar.setFormat("0.00%")

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        self.open_btn.clicked.connect(self.open_video)
        self.extract_btn.clicked.connect(self.start_extract)
        self.extract_btn.setEnabled(False)
        self.slider.valueChanged.connect(self.on_seek)
        self.label.set_rect_callback(self.on_rect_changed)
        self.api_btn.clicked.connect(self.open_api_manager)
        self.stop_btn.clicked.connect(self.stop_extract)
        self.prompt_combo.currentIndexChanged.connect(self.on_prompt_preset_change)
        self.suggest_prompt_btn.clicked.connect(self.on_suggest_prompt)
        w = QWidget()
        lay = QVBoxLayout()
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        ctrl.addWidget(self.open_btn)
        ctrl.addWidget(self.extract_btn)
        ctrl.addWidget(self.api_combo, 2)
        ctrl.addWidget(self.api_btn)
        ctrl.addWidget(self.stop_btn)
        ctrl.addWidget(self.prompt_combo, 2)
        ctrl.addWidget(self.suggest_prompt_btn)

        lay.addLayout(ctrl)
        lay.addWidget(self.label)
        lay.addWidget(self.slider)
        lay.addWidget(self.progress_bar)

        info = QHBoxLayout()
        info.setSpacing(8)
        info.addWidget(self.status_label)
        info.addWidget(self.coord_label)

        lay.addLayout(info)
        lay.addWidget(self.log_view)
        w.setLayout(lay)
        self.setCentralWidget(w)
        self.timer = QTimer()
        self.timer.setInterval(100)  # Faster update for smoother UI (100ms instead of 500ms)
        self.timer.timeout.connect(self.poll_extractor)

        # Animation timer for status text flashing during stop
        self.anim_timer = QTimer()
        self.anim_timer.setInterval(200)  # Faster animation (200ms)
        self.anim_timer.timeout.connect(self.animate_stop_status)
        self._stop_animation = False
        self._stop_status_original = ""

        self.extractor = None
        self.thread = None
        self.manager = ConfigManager(os.getcwd())
        self.manager.register_listener(self.refresh_api_combo)
        self.log_last_index = 0
        self.last_progress_value = -1.0
        self.last_progress_ts = 0.0
        self.custom_prompt_override = None
        self.prompt_manager = PromptManager(os.path.join(os.getcwd(), "configs"))
        self.init_prompt_presets()
        self.refresh_api_combo()
        self.stop_btn.setEnabled(False)

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

    def open_api_manager(self):
        dialog = APIConfigDialog(self, self.manager)
        dialog.exec()

    def refresh_api_combo(self):
        """Refresh API configuration combo box"""
        self.api_combo.clear()
        configs = self.manager.list_configs()

        if not configs:
            # Add default entry if no configs exist
            self.api_combo.addItem("默认配置", None)
            return

        selected_id = self.manager.get_selected()
        selected_index = 0

        for i, config in enumerate(configs):
            display_name = f"{config.name}"
            if config.group and config.group != "default":
                display_name += f" ({config.group})"
            if config.id == selected_id:
                display_name += " ✓"
                selected_index = i

            self.api_combo.addItem(display_name, config.id)

        # Set current selection
        if selected_index < self.api_combo.count():
            self.api_combo.setCurrentIndex(selected_index)

    def init_prompt_presets(self):
        """Initialize prompt combo box with presets"""
        self.prompt_combo.clear()
        prompts = self.prompt_manager.get_all_prompts()

        for prompt in prompts:
            self.prompt_combo.addItem(prompt.name, prompt.id)

        # Add separator and manage option
        self.prompt_combo.addItem("---")
        self.prompt_combo.addItem("管理Prompt预设...", "manage")

    def on_prompt_preset_change(self, index):
        """Handle prompt preset selection change"""
        if index < 0:
            return

        data = self.prompt_combo.currentData()
        if data == "manage":
            # Open prompt management dialog
            self.prompt_combo.setCurrentIndex(0)  # Reset selection
            self.on_suggest_prompt()  # Reuse the suggest prompt dialog for management
        elif data:
            # Apply selected prompt
            prompt = self.prompt_manager.get_prompt_by_id(data)
            if prompt:
                self.custom_prompt_override = prompt.content

    def on_suggest_prompt(self):
        """Open prompt management dialog"""
        dialog = PromptConfigDialog(self, self.prompt_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh the combo if prompts were modified
            self.init_prompt_presets()

    def stop_extract(self):
        """Stop the extraction process with animation feedback"""
        if self.extractor and not self.extractor.done:
            self.extractor.stopped = True
            self.stop_btn.setEnabled(False)

            # Start animation for status text
            self._stop_status_original = self.status_label.text()
            self._stop_animation = True
            self.anim_timer.start()

            self.log_view.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ 用户请求终止提取...")

    def animate_stop_status(self):
        """Animate status text while stopping"""
        if not self._stop_animation or not self.extractor or self.extractor.done:
            self.anim_timer.stop()
            self._stop_animation = False
            return

        # Simple blink animation
        current = self.status_label.text()
        if current.startswith("⚠️"):
            self.status_label.setText("正在终止... ⚠️")
        else:
            self.status_label.setText("⚠️ 正在终止...")

    def start_extract(self):
        if not self.video_path:
            return
        # Clear log before starting
        self.log_view.clear()
        self._last_log_time = time.time()  # Initialize logging timer

        r = self.label.get_selection_rect_in_image()
        base = os.path.splitext(os.path.basename(self.video_path))[0] + ".srt"
        out = os.path.join(os.path.dirname(self.video_path), base)
        engine = self.build_engine()
        self.extractor = Extractor(self.video_path, r, engine, 800, 1200, out)
        self.extractor.current_entries_count = 0  # Initialize entry count

        # Log extraction start info
        self.log_view.append(f"[{time.strftime('%H:%M:%S')}] === 开始提取字幕 ===")
        self.log_view.append(f"视频文件: {self.video_path}")
        if r:
            x, y, w, h = r
            self.log_view.append(f"字幕区域: x={x} y={y} w={w} h={h}")
        else:
            self.log_view.append("字幕区域: 全屏")
        self.log_view.append(f"输出文件: {out}")
        self.log_view.append(f"模型: {engine.model}")
        self.log_view.append(f"采样间隔: {self.extractor.sample_ms}ms")
        self.log_view.append(f"最短字幕时长: {self.extractor.min_duration_ms}ms")
        self.log_view.append("" + "-" * 60)

        self.thread = threading.Thread(target=self.extractor.run, daemon=True)
        self.thread.start()
        self.timer.start()
        self.extract_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("正在提取…")

        # Force immediate UI update to show the initial logs
        QApplication.processEvents()

    def poll_extractor(self):
        if not self.extractor:
            return
        p = self.extractor.progress

        # Process UI events to ensure smooth UI updates (critical for responsive UI)
        QApplication.processEvents()

        # Update progress bar
        self.progress_bar.setValue(int(p * 100))
        self.progress_bar.setFormat(f"{p:.2f}%")

        # Update status label (unless animation is running)
        if not self._stop_animation:
            if self.extractor.started_at:
                elapsed = int((time.time() - self.extractor.started_at) * 1000)
                self.status_label.setText(f"进度 {p}% | 已用 {elapsed/1000:.1f}s | 已识别: {self.extractor.current_entries_count}")
            else:
                self.status_label.setText(f"进度 {p}%")

        # Real-time log updates - show updates every 500ms for good visibility
        current_entry_count = getattr(self.extractor, 'current_entries_count', 0)
        current_time = time.time()
        if current_time - self._last_log_time > 0.5:
            self._last_log_time = current_time
            log_entry = f"[{time.strftime('%H:%M:%S')}] 进度: {p:.1f}% | 已处理帧: {self.extractor.frames_processed}/{self.extractor.total_frames} | 识别条目: {current_entry_count}"
            self.log_view.append(log_entry)

        if self.extractor.done:
            # Stop animation when extraction is done
            if self._stop_animation:
                self.anim_timer.stop()
                self._stop_animation = False

            self.timer.stop()
            self.extract_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

            if self.extractor.error:
                self.log_view.append(f"[{time.strftime('%H:%M:%S')}] ❌ 错误: {self.extractor.error}")
                QMessageBox.critical(self, "错误", self.extractor.error)
                self.status_label.setText("发生错误")
            elif self.extractor.stopped:
                self.status_label.setText("已终止")
                self.log_view.append(f"[{time.strftime('%H:%M:%S')}] --- 提取已终止 ---")
                self.log_view.append(f"已处理帧数: {self.extractor.frames_processed}/{self.extractor.total_frames}")
                self.log_view.append(f"已识别条目: {current_entry_count}")
                if self.extractor.entries:
                    # Save partial results when stopped
                    write_srt(self.extractor.entries, self.extractor.output_path)
                    txt_path = self.extractor.output_path.replace('.srt', '.txt')
                    write_txt(self.extractor.entries, txt_path)
                    self.log_view.append(f"[⚠️] 已保存部分结果到文件")
                QMessageBox.information(self, "已终止", f"提取已终止。\n已处理 {self.extractor.frames_processed} 帧，识别 {current_entry_count} 条字幕")
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("0.00%")
            else:
                self.log_view.append(f"[{time.strftime('%H:%M:%S')}] === 提取完成 ===")
                self.log_view.append(f"总耗时: {self.extractor.elapsed_ms/1000:.1f}秒")
                self.log_view.append(f"处理帧数: {self.extractor.frames_processed}/{self.extractor.total_frames}")
                self.log_view.append(f"识别字幕条目: {self.extractor.entries_count}")
                self.log_view.append(f"输出文件 (SRT): {self.extractor.output_path}")
                self.log_view.append(f"输出文件 (TXT): {self.extractor.output_path.replace('.srt', '.txt')}")

                detail = []
                detail.append(f"总耗时: {self.extractor.elapsed_ms/1000:.1f}s")
                detail.append(f"处理帧数: {self.extractor.frames_processed}/{self.extractor.total_frames}")
                rect = self.label.get_selection_rect_in_image()
                if rect:
                    x, y, w, h = rect
                    detail.append(f"裁切区域: x={x} y={y} w={w} h={h}")
                detail.append(f"采样间隔: {self.extractor.sample_ms}ms")
                detail.append(f"最短字幕时长: {self.extractor.min_duration_ms}ms")
                detail.append(f"识别条目: {self.extractor.entries_count}")
                detail.append(f"SRT输出: {self.extractor.output_path}")
                detail.append(f"TXT输出: {self.extractor.output_path.replace('.srt', '.txt')}")
                if isinstance(self.extractor.engine, OpenAIOCREngine):
                    detail.append(f"模型: {self.extractor.engine.model}")
                    detail.append(f"端点: {self.extractor.engine.endpoint}")
                QMessageBox.information(self, "完成", "\n".join(detail))
                self.status_label.setText("完成")
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("0.00%")

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

    def get_modern_stylesheet(self):
        return """
        QMainWindow {
            background-color: #f5f7fa;
        }

        QWidget {
            background-color: #ffffff;
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            font-size: 14px;
            color: #2c3e50;
        }

        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
            min-height: 32px;
            margin: 2px;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }

        QPushButton:pressed {
            background-color: #1f5f8b;
        }

        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }

        QPushButton#extract_btn {
            background-color: #2ecc71;
            font-weight: bold;
        }

        QPushButton#extract_btn:hover {
            background-color: #27ae60;
        }

        QPushButton#extract_btn:pressed {
            background-color: #1e8449;
        }

        QPushButton#stop_btn {
            background-color: #e74c3c;
        }

        QPushButton#stop_btn:hover {
            background-color: #c0392b;
        }

        QPushButton#stop_btn:pressed {
            background-color: #a93226;
        }

        QLabel {
            background-color: transparent;
            padding: 4px;
        }

        QLabel#status_label, QLabel#coord_label {
            background-color: #ecf0f1;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 13px;
        }

        VideoLabel {
            background-color: #000000;
            border: 2px solid #bdc3c7;
            border-radius: 12px;
            padding: 4px;
        }

        QSlider::groove:horizontal {
            border: none;
            height: 6px;
            background: #ecf0f1;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            background: #3498db;
            border: none;
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }

        QSlider::handle:horizontal:hover {
            background: #2980b9;
        }

        QSlider::sub-page:horizontal {
            background: #3498db;
            border-radius: 3px;
        }

        QProgressBar {
            border: none;
            border-radius: 6px;
            background-color: #ecf0f1;
            height: 24px;
            text-align: center;
            font-weight: 500;
        }

        QProgressBar::chunk {
            background-color: #2ecc71;
            border-radius: 6px;
        }

        QComboBox {
            border: 1px solid #bdc3c7;
            border-radius: 6px;
            padding: 6px 12px;
            background-color: #ffffff;
            min-height: 32px;
        }

        QComboBox:hover {
            border-color: #3498db;
        }

        QComboBox::drop-down {
            border: none;
            width: 24px;
        }

        QComboBox::down-arrow {
            image: none;
            color: #7f8c8d;
        }

        QComboBox::down-arrow:on {
            color: #3498db;
        }

        QTextEdit {
            border: 1px solid #bdc3c7;
            border-radius: 8px;
            padding: 8px;
            background-color: #f8f9fa;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
        }

        QScrollBar:vertical {
            border: none;
            background: #ecf0f1;
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #bdc3c7;
            border-radius: 6px;
            min-height: 30px;
        }

        QScrollBar::handle:vertical:hover {
            background: #95a5a6;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar:horizontal {
            border: none;
            background: #ecf0f1;
            height: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:horizontal {
            background: #bdc3c7;
            border-radius: 6px;
            min-width: 30px;
        }

        QMessageBox {
            background-color: #ffffff;
        }

        QMessageBox QPushButton {
            min-width: 80px;
        }
        """

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(960, 640)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
