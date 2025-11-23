"""
Prompt Configuration UI
Dialog for managing prompt presets
"""

import sys
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                               QListWidgetItem, QPushButton, QLineEdit, QTextEdit,
                               QLabel, QMessageBox, QInputDialog, QDialogButtonBox,
                               QPlainTextEdit, QSplitter, QWidget, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from prompt_manager import PromptManager


class EditPromptDialog(QDialog):
    """Dialog for editing a single prompt"""

    def __init__(self, parent, manager: PromptManager, prompt_id=None):
        super().__init__(parent)
        self.manager = manager
        self.prompt_id = prompt_id
        self.setWindowTitle("编辑Prompt")
        self.resize(600, 400)
        self._setup_ui()

        # Load existing prompt if editing
        if prompt_id:
            self._load_prompt()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入Prompt名称")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Content editor
        layout.addWidget(QLabel("Prompt内容:"))
        self.content_edit = QPlainTextEdit()
        self.content_edit.setPlaceholderText("输入Prompt内容...")
        font = QFont("Consolas", 10)
        self.content_edit.setFont(font)
        layout.addWidget(self.content_edit)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_prompt(self):
        """Load existing prompt for editing"""
        prompt = self.manager.get_prompt_by_id(self.prompt_id)
        if prompt:
            self.name_edit.setText(prompt.name)
            self.content_edit.setPlainText(prompt.content)

    def _on_accept(self):
        """Validate and save"""
        name = self.name_edit.text().strip()
        content = self.content_edit.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "警告", "请输入Prompt名称")
            return

        if not content:
            QMessageBox.warning(self, "警告", "请输入Prompt内容")
            return

        if self.prompt_id:
            # Edit existing
            success = self.manager.update_prompt(self.prompt_id, name=name, content=content)
        else:
            # Create new
            prompt = self.manager.add_prompt(name, content)
            success = prompt is not None

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "错误", "保存失败")


class PromptConfigDialog(QDialog):
    """Main dialog for managing prompt presets"""

    def __init__(self, parent, manager: PromptManager):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("管理Prompt预设")
        self.resize(800, 500)
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # Left panel - prompt list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # List
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(QLabel("Prompt列表:"))
        left_layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self._on_add_prompt)
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._on_edit_prompt)
        self.edit_btn.setEnabled(False)
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._on_delete_prompt)
        self.delete_btn.setEnabled(False)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        left_layout.addLayout(btn_layout)

        # Right panel - preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.preview_name = QLabel("选择一个Prompt查看详情")
        self.preview_content = QTextEdit()
        self.preview_content.setReadOnly(True)
        self.preview_content.setMinimumHeight(300)

        font = QFont("Consolas", 10)
        self.preview_content.setFont(font)

        right_layout.addWidget(self.preview_name)
        right_layout.addWidget(QLabel("内容:"))
        right_layout.addWidget(self.preview_content)

        # Add panels to main layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def _refresh_list(self):
        """Refresh prompt list"""
        self.list_widget.clear()
        prompts = self.manager.get_all_prompts()

        for prompt in prompts:
            item = QListWidgetItem(f"{prompt.name} ({prompt.id})")
            item.setData(Qt.ItemDataRole.UserRole, prompt.id)
            self.list_widget.addItem(item)

    def _on_selection_changed(self):
        """Handle selection change"""
        selected = bool(self.list_widget.currentItem())
        self.edit_btn.setEnabled(selected)
        self.delete_btn.setEnabled(selected)

        if selected:
            prompt_id = self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
            self._show_prompt_details(prompt_id)

    def _show_prompt_details(self, prompt_id):
        """Show prompt details in preview panel"""
        prompt = self.manager.get_prompt_by_id(prompt_id)
        if prompt:
            self.preview_name.setText(f"名称: {prompt.name}")
            self.preview_content.setPlainText(prompt.content)

    def _on_add_prompt(self):
        """Add new prompt"""
        dialog = EditPromptDialog(self, self.manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_list()
            QMessageBox.information(self, "成功", "Prompt已添加")

    def _on_edit_prompt(self):
        """Edit selected prompt"""
        if not self.list_widget.currentItem():
            return

        prompt_id = self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        dialog = EditPromptDialog(self, self.manager, prompt_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_list()
            QMessageBox.information(self, "成功", "Prompt已更新")

    def _on_delete_prompt(self):
        """Delete selected prompt"""
        if not self.list_widget.currentItem():
            return

        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个Prompt吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        prompt_id = self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        if self.manager.delete_prompt(prompt_id):
            self._refresh_list()
            self.preview_name.setText("选择一个Prompt查看详情")
            self.preview_content.clear()
            QMessageBox.information(self, "成功", "Prompt已删除")
        else:
            QMessageBox.critical(self, "错误", "删除失败")
