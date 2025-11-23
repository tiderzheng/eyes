import os
import time
import json
import requests
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QMessageBox, QLabel, QFormLayout, QSpinBox, QComboBox, QDialogButtonBox, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from config_manager import ConfigManager, APIConfig

class EditConfigDialog(QDialog):
    def __init__(self, parent, manager: ConfigManager, cfg: APIConfig|None=None):
        super().__init__(parent)
        self.manager = manager
        self.cfg = cfg
        self.setWindowTitle("编辑API配置")
        f = QFormLayout()
        self.name = QLineEdit()
        self.url = QLineEdit()
        self.model = QLineEdit()
        self.group = QLineEdit()
        self.note = QLineEdit()
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 600)
        self.timeout.setValue(30)
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.mode = QComboBox()
        self.mode.addItems(["OpenAI兼容"])
        self.api_base = QLineEdit()
        self.api_path = QLineEdit()
        self.full_label = QLineEdit()
        self.full_label.setReadOnly(True)
        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText("例如：只返回图片中的可读字幕文本")
        self.prompt.setFixedHeight(60)
        self.system_prompt = QTextEdit()
        self.system_prompt.setPlaceholderText("例如：你是字幕提取助手，仅输出清晰可读的字幕文本")
        self.system_prompt.setFixedHeight(60)
        self.toggle_btn = QPushButton("👁")
        self.copy_btn = QPushButton("复制")
        self.test_btn = QPushButton("测试")
        self.result_label = QLabel("")
        self.detail_btn = QPushButton("展开结果")
        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        self.detail_view.setVisible(False)
        self.showing = False
        f.addRow("名称", self.name)
        f.addRow("API 模式", self.mode)
        f.addRow("API 主机", self.api_base)
        f.addRow("API 路径", self.api_path)
        f.addRow("完整地址", self.full_label)
        f.addRow("模型", self.model)
        f.addRow("分组", self.group)
        f.addRow("备注", self.note)
        f.addRow("超时", self.timeout)
        ak = QHBoxLayout()
        ak.addWidget(self.api_key)
        ak.addWidget(self.toggle_btn)
        ak.addWidget(self.copy_btn)
        f.addRow("密钥", ak)
        f.addRow("Prompt", self.prompt)
        f.addRow("System Prompt", self.system_prompt)
        tl = QHBoxLayout()
        tl.addWidget(self.test_btn)
        tl.addWidget(self.result_label)
        f.addRow("测试", tl)
        f.addRow("详情", self.detail_btn)
        f.addRow("", self.detail_view)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay = QVBoxLayout()
        lay.addLayout(f)
        lay.addWidget(bb)
        self.setLayout(lay)
        if cfg:
            self.name.setText(cfg.name)
            self.url.setText(cfg.url)
            self.model.setText(cfg.model)
            self.group.setText(cfg.group)
            self.note.setText(cfg.note)
            self.timeout.setValue(cfg.timeout)
            dec = self.manager.decrypt_key(cfg.api_key_enc)
            self.api_key.setText(dec)
            self.api_base.setText(cfg.api_base or cfg.url)
            self.api_path.setText(cfg.api_path or "/v1/chat/completions")
            self.mode.setCurrentIndex(0)
            self.prompt.setPlainText(cfg.prompt or "")
            self.system_prompt.setPlainText(cfg.system_prompt or "")
        self.toggle_btn.clicked.connect(self.on_toggle)
        self.copy_btn.clicked.connect(self.on_copy)
        self.test_btn.clicked.connect(self.on_test)
        self.detail_btn.clicked.connect(self.on_toggle_detail)
        self.api_base.textChanged.connect(self.update_full)
        self.api_path.textChanged.connect(self.update_full)
        self.update_full()

    def build(self) -> APIConfig:
        enc = self.manager.encrypt_key(self.api_key.text())
        if self.cfg:
            return APIConfig(id=self.cfg.id, name=self.name.text(), url=self.url.text(), api_key_enc=enc, model=self.model.text(), timeout=self.timeout.value(), group=self.group.text() or "default", note=self.note.text(), prompt=self.prompt.toPlainText().strip(), system_prompt=self.system_prompt.toPlainText().strip(), api_base=self.api_base.text().strip(), api_path=(self.api_path.text().strip() or "/v1/chat/completions"), mode="openai")
        return APIConfig(name=self.name.text(), url=self.url.text(), api_key_enc=enc, model=self.model.text(), timeout=self.timeout.value(), group=self.group.text() or "default", note=self.note.text(), prompt=self.prompt.toPlainText().strip(), system_prompt=self.system_prompt.toPlainText().strip(), api_base=self.api_base.text().strip(), api_path=(self.api_path.text().strip() or "/v1/chat/completions"), mode="openai")

    def update_full(self):
        base = (self.api_base.text() or "").rstrip('/')
        path = (self.api_path.text() or "").lstrip('/')
        full = base + ('/' + path if base and path else '')
        self.full_label.setText(full)

    def on_toggle(self):
        self.showing = not self.showing
        self.api_key.setEchoMode(QLineEdit.EchoMode.Normal if self.showing else QLineEdit.EchoMode.Password)

    def on_copy(self):
        QApplication.clipboard().setText(self.api_key.text() or "")

    def on_toggle_detail(self):
        v = not self.detail_view.isVisible()
        self.detail_view.setVisible(v)
        self.detail_btn.setText("收起结果" if v else "展开结果")

    def on_test(self):
        self.result_label.setText("测试中…")
        self.result_label.setStyleSheet("color:#666;")
        QApplication.processEvents()
        base = (self.api_base.text().strip() or self.url.text().strip() or "")
        model = self.model.text() or ""
        timeout = self.timeout.value() or 30
        key = self.api_key.text() or ""
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        t0 = time.perf_counter()
        status = ""
        code = None
        body = {}
        models_candidates = []
        if base:
            models_candidates.append(base.rstrip('/') + '/v1/models')
            models_candidates.append(base.rstrip('/') + '/models')
        r = None
        for url_models in models_candidates:
            try:
                rr = requests.get(url_models, headers=headers, timeout=timeout)
                r = rr
                if rr.ok:
                    break
            except Exception:
                continue
        if r is not None and r.ok:
            code = r.status_code
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"text": r.text}
            status = "成功"
        else:
            path = (self.api_path.text().strip() or "/v1/chat/completions")
            full_chat = base.rstrip('/') + '/' + path.lstrip('/') if base else ''
            payload = {"model": model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}
            try:
                r = requests.post(full_chat, headers=headers, json=payload, timeout=timeout)
                code = r.status_code
                body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"text": r.text}
                status = "成功" if r.ok else "失败"
            except Exception as e:
                status = f"失败: {type(e).__name__}"
                body = {"error": str(e)}
        t1 = time.perf_counter()
        ms = int((t1 - t0) * 1000)
        self.result_label.setText(f"{status} | {ms}ms | code={code if code is not None else '-'}")
        if status.startswith("成功"):
            self.result_label.setStyleSheet("color:#0a0;")
        else:
            self.result_label.setStyleSheet("color:#a00;")
        try:
            self.detail_view.setPlainText(json.dumps({"result": body, "base": base, "path": (self.api_path.text().strip() or "/v1/chat/completions")}, ensure_ascii=False, indent=2))
        except Exception:
            self.detail_view.setPlainText(str(body))

class APIConfigDialog(QDialog):
    def __init__(self, parent, manager: ConfigManager):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("API配置管理")
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索配置")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["名称", "模型", "地址", "分组", "超时"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.btn_add = QPushButton("添加")
        self.btn_edit = QPushButton("修改")
        self.btn_del = QPushButton("删除")
        self.btn_imp = QPushButton("导入")
        self.btn_exp = QPushButton("导出")
        self.btn_use = QPushButton("设为当前")
        top = QHBoxLayout()
        top.addWidget(self.search)
        btns = QHBoxLayout()
        for b in [self.btn_add, self.btn_edit, self.btn_del, self.btn_imp, self.btn_exp, self.btn_use]:
            btns.addWidget(b)
        lay = QVBoxLayout()
        lay.addLayout(top)
        lay.addWidget(self.table)
        lay.addLayout(btns)
        self.setLayout(lay)
        self.search.textChanged.connect(self.refresh)
        self.btn_add.clicked.connect(self.on_add)
        self.btn_edit.clicked.connect(self.on_edit)
        self.btn_del.clicked.connect(self.on_del)
        self.btn_imp.clicked.connect(self.on_imp)
        self.btn_exp.clicked.connect(self.on_exp)
        self.btn_use.clicked.connect(self.on_use)
        self.refresh()

    def refresh(self):
        items = self.manager.search(self.search.text())
        self.table.setRowCount(0)
        for c in items:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(c.name))
            self.table.setItem(r, 1, QTableWidgetItem(c.model))
            base = c.api_base or c.url
            path = c.api_path or "/v1/chat/completions"
            full = (base.rstrip('/') + '/' + path.lstrip('/')) if base else ''
            self.table.setItem(r, 2, QTableWidgetItem(full))
            self.table.setItem(r, 3, QTableWidgetItem(c.group))
            self.table.setItem(r, 4, QTableWidgetItem(str(c.timeout)))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> str|None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        name = self.table.item(row, 0).text()
        full = self.table.item(row, 2).text()
        for c in self.manager.list_configs():
            base = c.api_base or c.url
            path = c.api_path or "/v1/chat/completions"
            cur_full = (base.rstrip('/') + '/' + path.lstrip('/')) if base else ''
            if c.name == name and cur_full == full:
                return c.id
        return None

    def on_add(self):
        d = EditConfigDialog(self, self.manager)
        if d.exec() == QDialog.DialogCode.Accepted:
            cfg = d.build()
            self.manager.add_config(cfg)
            self.refresh()

    def on_edit(self):
        idv = self._selected_id()
        if not idv:
            QMessageBox.warning(self, "提示", "请选择要修改的配置")
            return
        cur = None
        for c in self.manager.list_configs():
            if c.id == idv:
                cur = c
                break
        d = EditConfigDialog(self, self.manager, cur)
        if d.exec() == QDialog.DialogCode.Accepted:
            cfg = d.build()
            self.manager.update_config(cfg)
            self.refresh()

    def on_del(self):
        idv = self._selected_id()
        if not idv:
            QMessageBox.warning(self, "提示", "请选择要删除的配置")
            return
        self.manager.delete_config(idv)
        self.refresh()

    def on_imp(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入", "", "JSON (*.json)")
        if not path:
            return
        self.manager.import_configs(path)
        self.refresh()

    def on_exp(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出", "", "JSON (*.json)")
        if not path:
            return
        self.manager.export_configs(path)

    def on_use(self):
        idv = self._selected_id()
        if not idv:
            QMessageBox.warning(self, "提示", "请选择配置")
            return
        self.manager.select(idv)
        QMessageBox.information(self, "完成", "已设为当前配置")
