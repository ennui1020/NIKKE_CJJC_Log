import sys
import os
import json
import zipfile
import csv
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QLineEdit, QHBoxLayout, QMessageBox, QListWidget, QListWidgetItem,
    QListView, QComboBox, QGroupBox, QTextEdit, QSplitter,
    QDialog, QTextBrowser, QToolTip, QFormLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QPixmap, QIcon, QDrag, QFont
from PyQt5.QtCore import QSize, Qt, QMimeData, QRegularExpression, QTimer, QPoint

DATA_DIR = "data"
IMG_DIR = os.path.join(DATA_DIR, "portraits")
CHAR_FILE = os.path.join(DATA_DIR, "characters.json")
MATCH_FILE = os.path.join(DATA_DIR, "matches.json")

os.makedirs(IMG_DIR, exist_ok=True)
if not os.path.exists(CHAR_FILE):
    with open(CHAR_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2, ensure_ascii=False)
if not os.path.exists(MATCH_FILE):
    with open(MATCH_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2, ensure_ascii=False)

BUTTON_STYLE = {
    "primary": """
        QPushButton {
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 6px 12px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
    """,
    "secondary": """
        QPushButton {
            background-color: #6c757d;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 6px 12px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #5a6268;
        }
    """,
    "notes": """
        QPushButton {
            background-color: white;
            color: black;
            border: none;
            border-radius: 3px;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #f0f0f0;
        }
    """
}

def get_character_image_path(character_name):
    try:
        with open(CHAR_FILE, "r", encoding="utf-8") as f:
            characters = json.load(f)
        for char in characters:
            if char["name"] == character_name:
                img_path = os.path.join(IMG_DIR, char["image"])
                if os.path.exists(img_path):
                    return img_path
    except Exception as e:
        print(f"获取图片路径失败: {e}")
    return None

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.parent_widget = parent

    def startDrag(self, supportedActions):
        is_filtered = False
        if self.parent_widget:
            is_filtered = (self.parent_widget.filter_type_combo.currentText() != "所有类型" or
                           self.parent_widget.filter_rank_combo.currentText() != "所有爆裂")

        drag = QDrag(self)
        mimeData = QMimeData()
        if self.currentItem():
            real_name = self.currentItem().data(Qt.UserRole)
            mimeData.setText(real_name)
            if not is_filtered:
                mimeData.setData("application/x-character-index", str(self.currentRow()).encode())
        drag.setMimeData(mimeData)
        drag.exec_(Qt.MoveAction | Qt.CopyAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-character-index"):
            if self.parent_widget:
                is_filtered = (self.parent_widget.filter_type_combo.currentText() != "所有类型" or
                               self.parent_widget.filter_rank_combo.currentText() != "所有爆裂")
                if is_filtered:
                    event.ignore()
                    return
            event.acceptProposedAction()
        elif event.mimeData().hasText():
            event.ignore()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-character-index"):
            if self.parent_widget:
                is_filtered = (self.parent_widget.filter_type_combo.currentText() != "所有类型" or
                               self.parent_widget.filter_rank_combo.currentText() != "所有爆裂")
                if is_filtered:
                    event.ignore()
                    return
            event.acceptProposedAction()
        elif event.mimeData().hasText():
            event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-character-index"):
            is_filtered = False
            if self.parent_widget:
                is_filtered = (self.parent_widget.filter_type_combo.currentText() != "所有类型" or
                               self.parent_widget.filter_rank_combo.currentText() != "所有爆裂")
            if is_filtered:
                event.ignore()
                return

            source_index = int(event.mimeData().data("application/x-character-index").data().decode())
            drop_row = self.indexAt(event.pos()).row()
            if drop_row == -1:
                drop_row = self.count()
            if source_index != drop_row and source_index != drop_row - 1:
                item = self.takeItem(source_index)
                self.insertItem(drop_row, item)
                self.setCurrentItem(item)
                if self.parent_widget:
                    self.parent_widget.update_character_order()
            event.acceptProposedAction()
        else:
            event.ignore()

class DropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.setStyleSheet("border: 2px dashed #aaa; background-color: #f8f8f8;")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.character_name = None
        self.parent_widget = parent

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            char_name = event.mimeData().text()
            self.character_name = char_name
            img_path = get_character_image_path(char_name)
            if img_path:
                pixmap = QPixmap(img_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setPixmap(pixmap)
                self.setStyleSheet("border: none;")
            else:
                self.setText(char_name)
            if self.parent_widget and hasattr(self.parent_widget, 'update_team_stats'):
                self.parent_widget.update_team_stats()
            event.accept()
        else:
            event.accept()

    def clear_label(self):
        self.clear()
        self.setStyleSheet("border: 2px dashed #aaa; background-color: #f8f8f8;")
        self.character_name = None
        if self.parent_widget and hasattr(self.parent_widget, 'update_team_stats'):
            self.parent_widget.update_team_stats()

class DroppableLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # 启用拖放支持
        self.setStyleSheet("""
            QLineEdit {
                font-family: Arial, sans-serif;
                font-size: 12px;
                padding: 5px;
                min-width: 200px;
            }
        """)

    def dragEnterEvent(self, event):
        # 接受包含文本的拖放操作
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        # 处理拖放事件，追加角色名称并确保空格分隔
        if event.mimeData().hasText():
            char_name = event.mimeData().text().strip()  # 清理首尾空格
            current_text = self.text().strip()  # 获取当前文本并清理
            if current_text:
                # 如果已有文本，追加空格和新名称
                new_text = f"{current_text} {char_name}"
            else:
                # 没有文本，直接设置新名称
                new_text = char_name
            self.setText(new_text)
            event.acceptProposedAction()
        else:
            event.ignore()

class EditCharacterDialog(QDialog):
    def __init__(self, char_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑角色")
        self.char_data = char_data
        self.selected_img_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(self.char_data["name"])
        self.name_input.setPlaceholderText("角色名称")
        form_layout.addRow("名称：", self.name_input)

        self.nickname_input = QLineEdit(self.char_data.get("nickname", ""))
        self.nickname_input.setPlaceholderText("昵称（可选）")
        form_layout.addRow("昵称：", self.nickname_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["类型", "火力型", "防御型", "辅助型"])
        current_type = self.char_data.get("type", "")
        self.type_combo.setCurrentText(current_type if current_type else "类型")
        form_layout.addRow("类型：", self.type_combo)

        self.rank_combo = QComboBox()
        self.rank_combo.addItems(["爆裂", "I", "II", "III", "Λ"])
        current_rank = self.char_data.get("rank", "")
        self.rank_combo.setCurrentText(current_rank if current_rank else "爆裂")
        form_layout.addRow("爆裂：", self.rank_combo)

        self.rl2_input = QLineEdit(str(self.char_data.get("2RL", "0")))
        self.rl2_input.setPlaceholderText("2RL 值")
        form_layout.addRow("2RL：", self.rl2_input)

        self.rl25_input = QLineEdit(str(self.char_data.get("2.5RL", "0")))
        self.rl25_input.setPlaceholderText("2.5RL 值")
        form_layout.addRow("2.5RL：", self.rl25_input)

        self.rl3_input = QLineEdit(str(self.char_data.get("3RL", "0")))
        self.rl3_input.setPlaceholderText("3RL 值")
        form_layout.addRow("3RL：", self.rl3_input)

        self.rl35_input = QLineEdit(str(self.char_data.get("3.5RL", "0")))
        self.rl35_input.setPlaceholderText("3.5RL 值")
        form_layout.addRow("3.5RL：", self.rl35_input)

        self.rl4_input = QLineEdit(str(self.char_data.get("4RL", "0")))
        self.rl4_input.setPlaceholderText("4RL 值")
        form_layout.addRow("4RL：", self.rl4_input)

        self.select_img_btn = QPushButton("选择图片")
        self.select_img_btn.setStyleSheet(BUTTON_STYLE["primary"])
        self.select_img_btn.clicked.connect(self.select_image)
        form_layout.addRow("图片：", self.select_img_btn)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(60, 60)
        self.preview_label.setStyleSheet("border: none;")
        img_path = os.path.join(IMG_DIR, self.char_data["image"])
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(pixmap)
        form_layout.addRow("预览：", self.preview_label)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(BUTTON_STYLE["primary"])
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(BUTTON_STYLE["secondary"])
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_img_path = path
            pixmap = QPixmap(path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(pixmap)

    def save_changes(self):
        name = self.name_input.text().strip()
        nickname = self.nickname_input.text().strip()
        char_type = self.type_combo.currentText()
        if char_type == "类型":
            char_type = ""
        rank = self.rank_combo.currentText()
        if rank == "爆裂":
            rank = ""

        try:
            rl2 = float(self.rl2_input.text().strip())
            rl25 = float(self.rl25_input.text().strip())
            rl3 = float(self.rl3_input.text().strip())
            rl35 = float(self.rl35_input.text().strip())
            rl4 = float(self.rl4_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的数字值")
            return

        if not name:
            QMessageBox.warning(self, "提示", "请输入角色名称")
            return

        try:
            with open(CHAR_FILE, "r", encoding="utf-8") as f:
                characters = json.load(f)
            for char in characters:
                if char["name"] == name and char["name"] != self.char_data["name"]:
                    QMessageBox.warning(self, "重复", f"角色 [{name}] 已存在")
                    return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取角色数据失败: {e}")
            return

        updated_data = {
            "name": name,
            "nickname": nickname,
            "type": char_type,
            "rank": rank,
            "image": self.char_data["image"],
            "2RL": rl2,
            "2.5RL": rl25,
            "3RL": rl3,
            "3.5RL": rl35,
            "4RL": rl4
        }

        if self.selected_img_path:
            ext = os.path.splitext(self.selected_img_path)[1]
            img_filename = f"{name}{ext}"
            img_dest_path = os.path.join(IMG_DIR, img_filename)
            try:
                with open(self.selected_img_path, "rb") as src, open(img_dest_path, "wb") as dst:
                    dst.write(src.read())
                if img_filename != self.char_data["image"]:
                    old_img_path = os.path.join(IMG_DIR, self.char_data["image"])
                    if os.path.exists(old_img_path):
                        os.remove(old_img_path)
                updated_data["image"] = img_filename
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存图片失败: {e}")
                return

        self.updated_data = updated_data
        self.accept()

class EditMatchDialog(QDialog):
    def __init__(self, match_data, characters_data, data_index, parent=None):
        super().__init__(parent)
        self.setWindowTitle("详细战绩")
        self.match_data = match_data
        self.characters_data = characters_data
        self.data_index = data_index
        self.team_a_labels = []
        self.team_b_labels = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        team_b_group = QGroupBox("防守方")
        team_b_layout = QHBoxLayout()
        for char_name in self.match_data.get("team_b", []):
            label = DropLabel(parent=self)
            label.character_name = char_name
            img_path = get_character_image_path(char_name)
            if img_path:
                pixmap = QPixmap(img_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
                label.setStyleSheet("border: none;")
            else:
                label.setText(char_name)
            self.team_b_labels.append(label)
            team_b_layout.addWidget(label)
        team_b_group.setLayout(team_b_layout)
        layout.addWidget(team_b_group)

        team_a_group = QGroupBox("进攻方")
        team_a_layout = QHBoxLayout()
        for char_name in self.match_data.get("team_a", []):
            label = DropLabel(parent=self)
            label.character_name = char_name
            img_path = get_character_image_path(char_name)
            if img_path:
                pixmap = QPixmap(img_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
                label.setStyleSheet("border: none;")
            else:
                label.setText(char_name)
            self.team_a_labels.append(label)
            team_a_layout.addWidget(label)
        team_a_group.setLayout(team_a_layout)
        layout.addWidget(team_a_group)

        self.stats_group = QGroupBox("队伍充能")
        stats_layout = QVBoxLayout()
        self.team_b_stats = QLabel("防守方: 2RL: 0 | 2.5RL: 0 | 3RL: 0 | 3.5RL: 0 | 4RL: 0")
        self.team_a_stats = QLabel("进攻方: 2RL: 0 | 2.5RL: 0 | 3RL: 0 | 3.5RL: 0 | 4RL: 0")
        stats_layout.addWidget(self.team_b_stats)
        stats_layout.addWidget(self.team_a_stats)
        self.stats_group.setLayout(stats_layout)
        layout.addWidget(self.stats_group)

        result_layout = QHBoxLayout()
        result_layout.addWidget(QLabel("结果："))
        self.result_combo = QComboBox()
        self.result_combo.addItems(["胜", "败"])
        self.result_combo.setCurrentText(self.match_data.get("result", "胜"))
        result_layout.addWidget(self.result_combo)
        layout.addLayout(result_layout)

        layout.addWidget(QLabel("备注："))
        self.notes_input = QTextEdit()
        self.notes_input.setMinimumHeight(60)
        self.notes_input.setPlainText(self.match_data.get("notes", ""))
        layout.addWidget(self.notes_input)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(BUTTON_STYLE["primary"])
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(BUTTON_STYLE["secondary"])
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setMinimumWidth(600)
        self.update_team_stats()

    def update_team_stats(self):
        def calculate_team_stats(labels):
            stats = {"2RL": 0, "2.5RL": 0, "3RL": 0, "3.5RL": 0, "4RL": 0}
            for label in labels:
                if label.character_name:
                    for char in self.characters_data:
                        if char["name"] == label.character_name:
                            for attr in stats:
                                stats[attr] += float(char.get(attr, 0))
            return stats

        def format_stat(value, stat_name, is_first_highlight):
            formatted_value = f"{value:.1f}"
            if is_first_highlight:
                return f"<span style='color: red; font-weight: bold;'>{stat_name}: {formatted_value}</span>"
            return f"{stat_name}: {formatted_value}"

        team_a_stats = calculate_team_stats(self.team_a_labels)
        team_b_stats = calculate_team_stats(self.team_b_labels)

        first_a_highlight = None
        for attr in ["2RL", "2.5RL", "3RL", "3.5RL", "4RL"]:
            if team_a_stats[attr] >= 100:
                first_a_highlight = attr
                break

        first_b_highlight = None
        for attr in ["2RL", "2.5RL", "3RL", "3.5RL", "4RL"]:
            if team_b_stats[attr] >= 100:
                first_b_highlight = attr
                break

        team_a_text = "进攻方: " + " | ".join(
            format_stat(team_a_stats[attr], attr, attr == first_a_highlight)
            for attr in ["2RL", "2.5RL", "3RL", "3.5RL", "4RL"]
        )

        team_b_text = "防守方: " + " | ".join(
            format_stat(team_b_stats[attr], attr, attr == first_b_highlight)
            for attr in ["2RL", "2.5RL", "3RL", "3.5RL", "4RL"]
        )

        self.team_a_stats.setText(team_a_text)
        self.team_b_stats.setText(team_b_text)

    def save_changes(self):
        team_a = [label.character_name for label in self.team_a_labels if label.character_name]
        team_b = [label.character_name for label in self.team_b_labels if label.character_name]
        result = self.result_combo.currentText()
        notes = self.notes_input.toPlainText().strip()

        if not team_a and not team_b:
            QMessageBox.warning(self, "提示", "请至少选择一个角色")
            return

        all_char_names = {char["name"] for char in self.characters_data}
        missing_chars = []
        for char_name in team_a + team_b:
            if char_name and char_name not in all_char_names:
                missing_chars.append(char_name)

        if missing_chars:
            QMessageBox.warning(self, "错误", f"以下角色不存在: {', '.join(set(missing_chars))}")
            return

        self.updated_data = {
            "team_a": team_a,
            "team_b": team_b,
            "result": result,
            "notes": notes
        }
        self.accept()

class DuplicateCharacterDialog(QDialog):
    def __init__(self, duplicates, existing_chars, parent=None):
        super().__init__(parent)
        self.setWindowTitle("处理重复角色")
        self.duplicates = duplicates
        self.existing_chars = existing_chars
        self.choices = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("以下角色名称已存在，请选择覆盖或跳过："))

        self.table = QTableWidget()
        self.table.setRowCount(len(self.duplicates))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["名称", "现有数据", "导入数据", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row, new_char in enumerate(self.duplicates):
            name = new_char["name"]
            existing_char = next((char for char in self.existing_chars if char["name"] == name), None)

            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, name_item)

            existing_data = (
                f"昵称: {existing_char.get('nickname', '')}, 类型: {existing_char.get('type', '')}, "
                f"爆裂: {existing_char.get('rank', '')}, "
                f"2RL: {existing_char.get('2RL', 0.0)}, 2.5RL: {existing_char.get('2.5RL', 0.0)}, "
                f"3RL: {existing_char.get('3RL', 0.0)}, 3.5RL: {existing_char.get('3.5RL', 0.0)}, "
                f"4RL: {existing_char.get('4RL', 0.0)}"
            )
            existing_item = QTableWidgetItem(existing_data)
            existing_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 1, existing_item)

            new_data = (
                f"昵称: {new_char.get('nickname', '')}, 类型: {new_char.get('type', '')}, "
                f"爆裂: {new_char.get('rank', '')}, "
                f"2RL: {new_char.get('2RL', 0.0)}, 2.5RL: {new_char.get('2.5RL', 0.0)}, "
                f"3RL: {new_char.get('3RL', 0.0)}, 3.5RL: {new_char.get('3.5RL', 0.0)}, "
                f"4RL: {new_char.get('4RL', 0.0)}"
            )
            new_item = QTableWidgetItem(new_data)
            new_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 2, new_item)

            combo = QComboBox()
            combo.addItems(["覆盖", "跳过"])
            combo.setCurrentText("跳过")
            combo.currentTextChanged.connect(lambda text, n=name: self.choices.update({n: text.lower()}))
            self.choices[name] = "skip"
            self.table.setCellWidget(row, 3, combo)

        layout.addWidget(self.table)

        select_layout = QHBoxLayout()
        select_all_overwrite = QPushButton("全部覆盖")
        select_all_overwrite.setStyleSheet(BUTTON_STYLE["primary"])
        select_all_overwrite.clicked.connect(self.select_all_overwrite)
        select_all_skip = QPushButton("全部跳过")
        select_all_skip.setStyleSheet(BUTTON_STYLE["secondary"])
        select_all_skip.clicked.connect(self.select_all_skip)
        select_layout.addWidget(select_all_overwrite)
        select_layout.addWidget(select_all_skip)
        layout.addLayout(select_layout)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(BUTTON_STYLE["primary"])
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(BUTTON_STYLE["secondary"])
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setMinimumWidth(800)
        self.setMinimumHeight(400)

    def select_all_overwrite(self):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 3)
            combo.setCurrentText("覆盖")
            name = self.table.item(row, 0).text()
            self.choices[name] = "overwrite"

    def select_all_skip(self):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 3)
            combo.setCurrentText("跳过")
            name = self.table.item(row, 0).text()
            self.choices[name] = "skip"

class MatchListItem(QWidget):
    def __init__(self, match_data, data_index, parent=None):
        super().__init__(parent)
        self.match_data = match_data
        self.data_index = data_index
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        team_a_layout = QHBoxLayout()
        for char_name in match_data.get("team_a", []):
            label = QLabel()
            label.setFixedSize(40, 40)
            img_path = get_character_image_path(char_name)
            if img_path:
                pixmap = QPixmap(img_path).scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
            else:
                label.setText(char_name)
                label.setStyleSheet("border: 1px solid #ccc;")
            team_a_layout.addWidget(label)
        self.layout.addLayout(team_a_layout)

        vs_label = QLabel("VS")
        vs_label.setStyleSheet("color: #00000B; font-size: 16px;")
        self.layout.addWidget(vs_label)

        team_b_layout = QHBoxLayout()
        for char_name in match_data.get("team_b", []):
            label = QLabel()
            label.setFixedSize(40, 40)
            img_path = get_character_image_path(char_name)
            if img_path:
                pixmap = QPixmap(img_path).scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
            else:
                label.setText(char_name)
                label.setStyleSheet("border: 1px solid #ccc;")
            team_b_layout.addWidget(label)
        self.layout.addLayout(team_b_layout)

        result = match_data.get("result", "未知")
        result_label = QLabel(result)
        result_style = (
            "font-family: 'Microsoft YaHei', Arial, sans-serif; "
            "font-weight: bold; "
            "font-size: 24px; "
        )
        if result == "胜":
            result_style += "color: #28a745;"
        elif result == "败":
            result_style += "color: #dc3545;"
        else:
            result_style += "color: #555;"
        result_label.setStyleSheet(result_style)
        self.layout.addWidget(result_label)

class LatestMatchPreview(QWidget):
    def __init__(self, matches_data=None, parent=None):
        super().__init__(parent)
        self.matches_data = matches_data if matches_data else []
        self.setup_ui()

    def setup_ui(self):
        if self.layout():
            QWidget().setLayout(self.layout())
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        title_label = QLabel("最新战绩预览")
        title_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        if not self.matches_data:
            no_match_label = QLabel("暂无战绩记录")
            no_match_label.setAlignment(Qt.AlignCenter)
            no_match_label.setStyleSheet("color: #555; font-style: italic;")
            layout.addWidget(no_match_label)
        else:
            for match_data in reversed(self.matches_data[-3:]):
                match_widget = MatchListItem(match_data, 0)
                layout.addWidget(match_widget)

        self.setLayout(layout)
        single_match_height = 50
        title_height = 30
        margins = 10
        self.setFixedHeight(title_height + single_match_height * 3 + margins)

    def update_preview(self, matches_data=None):
        self.matches_data = matches_data if matches_data else []
        self.setup_ui()

class MatchViewer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查看战绩")
        self.setMinimumSize(1000, 800)
        self.matches_data = []
        self.characters_data = []
        self.init_ui()
        self.load_matches()

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_panel = QWidget()
        left_layout = QVBoxLayout()

        search_group = QGroupBox("搜索战绩")
        search_layout = QVBoxLayout()
        search_input_layout = QHBoxLayout()
        self.search_input = DroppableLineEdit()
        self.search_input.setPlaceholderText("输入搜索内容角色名（a:进攻 d:防守 n:备注 空格为AND）")
        search_input_layout.addWidget(self.search_input)
        search_btn = QPushButton("搜索")
        search_btn.setStyleSheet(BUTTON_STYLE["primary"])
        search_btn.clicked.connect(self.search_matches)
        search_input_layout.addWidget(search_btn)
        clear_search_btn = QPushButton("清除")
        clear_search_btn.setStyleSheet(BUTTON_STYLE["secondary"])
        clear_search_btn.clicked.connect(self.clear_search_and_display_all)
        search_input_layout.addWidget(clear_search_btn)
        search_layout.addLayout(search_input_layout)
        search_group.setLayout(search_layout)
        left_layout.addWidget(search_group)

        drag_search_group = QGroupBox("拖放搜索")
        drag_search_layout = QVBoxLayout()
        team_b_search_layout = QHBoxLayout()
        team_b_search_layout.addWidget(QLabel("防守方："))
        self.team_b_search_labels = []
        for _ in range(5):
            label = DropLabel(parent=self)
            self.team_b_search_labels.append(label)
            team_b_search_layout.addWidget(label)
        drag_search_layout.addLayout(team_b_search_layout)
        team_a_search_layout = QHBoxLayout()
        team_a_search_layout.addWidget(QLabel("进攻方："))
        self.team_a_search_labels = []
        for _ in range(5):
            label = DropLabel(parent=self)
            self.team_a_search_labels.append(label)
            team_a_search_layout.addWidget(label)
        drag_search_layout.addLayout(team_a_search_layout)
        drag_search_btn_layout = QHBoxLayout()
        search_drag_btn = QPushButton("搜索")
        search_drag_btn.setStyleSheet(BUTTON_STYLE["primary"])
        search_drag_btn.clicked.connect(self.search_by_drag)
        clear_drag_btn = QPushButton("清除")
        clear_drag_btn.setStyleSheet(BUTTON_STYLE["secondary"])
        clear_drag_btn.clicked.connect(self.clear_drag_search)
        drag_search_btn_layout.addWidget(search_drag_btn)
        drag_search_btn_layout.addWidget(clear_drag_btn)
        drag_search_layout.addLayout(drag_search_btn_layout)
        drag_search_group.setLayout(drag_search_layout)
        left_layout.addWidget(drag_search_group)

        self.match_list_widget = QListWidget()
        self.match_list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        left_layout.addWidget(self.match_list_widget)

        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.setStyleSheet(BUTTON_STYLE["primary"])
        select_all_btn.clicked.connect(self.select_all_matches)
        edit_btn = QPushButton("详情")
        edit_btn.setStyleSheet(BUTTON_STYLE["primary"])
        edit_btn.clicked.connect(self.edit_match)
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet(BUTTON_STYLE["secondary"])
        delete_btn.clicked.connect(self.delete_match)
        export_btn = QPushButton("导出")
        export_btn.setStyleSheet(BUTTON_STYLE["primary"])
        export_btn.clicked.connect(self.export_matches)
        import_btn = QPushButton("导入")
        import_btn.setStyleSheet(BUTTON_STYLE["primary"])
        import_btn.clicked.connect(self.import_matches)
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(import_btn)
        left_layout.addLayout(button_layout)

        left_panel.setLayout(left_layout)
        left_panel.setMinimumWidth(560)
        left_panel.setMaximumWidth(560)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选类型："))
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["所有类型", "火力型", "防御型", "辅助型"])
        filter_layout.addWidget(self.filter_type_combo)
        filter_layout.addWidget(QLabel("筛选爆裂："))
        self.filter_rank_combo = QComboBox()
        self.filter_rank_combo.addItems(["所有爆裂", "I", "II", "III", "Λ"])
        filter_layout.addWidget(self.filter_rank_combo)
        right_layout.addLayout(filter_layout)
        char_list_group = QGroupBox("角色列表")
        char_list_layout = QVBoxLayout()
        self.list_widget = DraggableListWidget(parent=self)
        self.list_widget.setIconSize(QSize(60, 60))
        self.list_widget.setViewMode(QListView.IconMode)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        char_list_layout.addWidget(self.list_widget)
        char_list_group.setLayout(char_list_layout)
        right_layout.addWidget(char_list_group)
        right_panel.setLayout(right_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        self.filter_type_combo.currentTextChanged.connect(self.filter_characters)
        self.filter_rank_combo.currentTextChanged.connect(self.filter_characters)

    def filter_characters(self):
        self.list_widget.clear()
        QApplication.processEvents()
        selected_type = self.filter_type_combo.currentText()
        selected_rank = self.filter_rank_combo.currentText()
        is_filtered = (selected_type != "所有类型" or selected_rank != "所有爆裂")
        icon_cache = {}
        filtered_chars = []
        for char in self.characters_data:
            char_type = char.get("type", "")
            char_rank = char.get("rank", "")
            type_match = (selected_type == "所有类型" or char_type == selected_type)
            rank_match = (selected_rank == "所有爆裂" or char_rank == selected_rank)
            if type_match and rank_match:
                filtered_chars.append(char)
        for char in filtered_chars:
            name = char["name"]
            item = QListWidgetItem()
            img_path = os.path.join(IMG_DIR, char["image"])
            if img_path not in icon_cache:
                if os.path.exists(img_path):
                    icon_cache[img_path] = QIcon(img_path)
                else:
                    icon_cache[img_path] = QIcon()
            item.setIcon(icon_cache[img_path])
            item.setData(Qt.UserRole, name)
            font_metrics = self.list_widget.fontMetrics()
            elided_name = font_metrics.elidedText(name, Qt.ElideRight, 60)
            item.setText(elided_name)
            tooltip_text = (
                f"<p style='font-family: Arial; font-size: 12px;'>"
                f"<table>"
                f"<tr><td style='width: 80px;'>名称:</td><td>{char.get('name', '')}</td></tr>"
                f"<tr><td style='width: 80px;'>昵称:</td><td>{char.get('nickname', '') or 'none'}</td></tr>"
                f"<tr><td style='width: 80px;'>类型:</td><td>{char.get('type', '') or '未设置'}</td></tr>"
                f"<tr><td style='width: 80px;'>等级:</td><td>{char.get('rank', '') or '未设置'}</td></tr>"
                f"<tr><td style='width: 80px;'>2RL:</td><td>{char.get('2RL', 0):.1f}</td></tr>"
                f"<tr><td style='width: 80px;'>2.5RL:</td><td>{char.get('2.5RL', 0):.1f}</td></tr>"
                f"<tr><td style='width: 80px;'>3RL:</td><td>{char.get('3RL', 0):.1f}</td></tr>"
                f"<tr><td style='width: 80px;'>3.5RL:</td><td>{char.get('3.5RL', 0):.1f}</td></tr>"
                f"<tr><td style='width: 80px;'>4RL:</td><td>{char.get('4RL', 0):.1f}</td></tr>"
                f"</table>"
                f"</p>"
            )
            item.setToolTip(tooltip_text)
            item.setTextAlignment(Qt.AlignHCenter)
            item.setSizeHint(QSize(60, 80))
            self.list_widget.addItem(item)

    def select_all_matches(self):
        for i in range(self.match_list_widget.count()):
            item = self.match_list_widget.item(i)
            item.setSelected(True)

    def load_matches(self):
        try:
            with open(MATCH_FILE, "r", encoding="utf-8") as f:
                self.matches_data = json.load(f)
        except json.JSONDecodeError:
            self.matches_data = []
        try:
            with open(CHAR_FILE, "r", encoding="utf-8") as f:
                self.characters_data = json.load(f)
        except json.JSONDecodeError:
            self.characters_data = []
        self.display_matches()
        self.filter_characters()

    def display_matches(self, filtered_matches=None):
        self.match_list_widget.clear()
        matches_to_display = filtered_matches if filtered_matches is not None else self.matches_data
        for index, match in enumerate(self.matches_data):
            if filtered_matches is not None:
                if match not in filtered_matches:
                    continue
            else:
                # When not filtered, use the original index
                original_index = index
            # When filtered, find the original index in matches_data
            original_index = self.matches_data.index(match) if filtered_matches is not None else index
            item = QListWidgetItem(self.match_list_widget)
            custom_widget = MatchListItem(match, original_index)
            item.setSizeHint(custom_widget.sizeHint())
            self.match_list_widget.addItem(item)
            self.match_list_widget.setItemWidget(item, custom_widget)

    def edit_match(self):
        selected_items = self.match_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择一条战绩记录进行查看。")
            return
        if len(selected_items) > 1:
            QMessageBox.information(self, "提示", "一次只能查看一条战绩记录。")
            return

        item = selected_items[0]
        widget = self.match_list_widget.itemWidget(item)
        if not widget:
            QMessageBox.critical(self, "错误", "无法获取战绩数据。")
            return

        match_data = widget.match_data
        data_index = widget.data_index
        dialog = EditMatchDialog(match_data, self.characters_data, data_index, self)
        if dialog.exec_():
            updated_data = dialog.updated_data
            try:
                with open(MATCH_FILE, "r+", encoding="utf-8") as f:
                    matches = json.load(f)
                    if 0 <= data_index < len(matches):
                        matches[data_index] = updated_data
                    else:
                        raise IndexError("Invalid match index")
                    f.seek(0)
                    json.dump(matches, f, indent=2, ensure_ascii=False)
                    f.truncate()
                self.load_matches()
                if self.parent():
                    self.parent().update_match()
                QMessageBox.information(self, "成功", "战绩已更新。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新战绩失败: {e}")

    def search_matches(self):
        search_query = self.search_input.text().strip().lower()
        if not search_query:
            self.display_matches()
            return

        found_matches = []
        nickname_to_name = {char.get("nickname", "").lower(): char["name"] for char in self.characters_data if
                            char.get("nickname")}

        def resolve_term(term):
            term = term.strip()
            if term.startswith("a:"):
                return ("team_a", nickname_to_name.get(term[2:].lower(), term[2:]))
            elif term.startswith("d:"):
                return ("team_b", nickname_to_name.get(term[2:].lower(), term[2:]))
            elif term.startswith("n:"):
                return ("notes", term[2:])
            else:
                return ("any", nickname_to_name.get(term.lower(), term))

        def match_condition(team, value, match):
            value = value.lower()
            team_a = [m.lower() for m in match.get("team_a", [])]
            team_b = [m.lower() for m in match.get("team_b", [])]
            notes = match.get("notes", "").lower()
            if team == "team_a":
                return value in team_a
            elif team == "team_b":
                return value in team_b
            elif team == "notes":
                return value in notes
            elif team == "any":
                return value in team_a or value in team_b or value in notes
            return False

        terms = [t for t in search_query.split() if t]
        for match in self.matches_data:
            all_conditions_met = True
            for term in terms:
                team, value = resolve_term(term)
                if not match_condition(team, value, match):
                    all_conditions_met = False
                    break
            if all_conditions_met:
                found_matches.append(match)

        if not found_matches:
            QMessageBox.information(self, "搜索结果", f"没有找到匹配 '{search_query}' 的战绩记录。")
        else:
            self.display_matches(found_matches)

    def search_by_drag(self):

        try:
            team_a = [label.character_name for label in self.team_a_search_labels if label.character_name]
            team_b = [label.character_name for label in self.team_b_search_labels if label.character_name]
            if not team_a and not team_b:
                QMessageBox.information(self, "提示", "请至少拖放一个角色到进攻方或防守方")
                return
            query_parts = []
            for char in team_a:
                query_parts.append(f"a:{char}")
            for char in team_b:
                query_parts.append(f"d:{char}")
            search_query = " ".join(query_parts)
            self.search_input.setText(search_query)
            self.search_matches()
        except Exception as e:
            print(f"搜索错误: {e}")
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")

    def clear_search_and_display_all(self):
        self.search_input.clear()
        self.display_matches()

    def clear_drag_search(self):
        try:
            for label in self.team_a_search_labels + self.team_b_search_labels:
                label.clear_label()
            self.search_input.clear()
            self.display_matches()
        except Exception as e:
            print(f"清除拖放错误: {e}")
            QMessageBox.critical(self, "错误", f"清除拖放失败: {e}")

    def delete_match(self):
        selected_items = self.match_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择至少一条战绩记录。")
            return

        num_matches = len(selected_items)
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {num_matches} 条战绩记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        indices = []
        for item in selected_items:
            widget = self.match_list_widget.itemWidget(item)
            if widget:
                indices.append(widget.data_index)
        indices.sort(reverse=True)

        try:
            for index in indices:
                if 0 <= index < len(self.matches_data):
                    del self.matches_data[index]

            with open(MATCH_FILE, "w", encoding="utf-8") as f:
                json.dump(self.matches_data, f, indent=2, ensure_ascii=False)

            self.display_matches()

            if self.parent():
                self.parent().update_match()

            QMessageBox.information(self, "成功", f"已删除 {num_matches} 条战绩记录。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除战绩失败: {e}")

    def export_matches(self):
        selected_items = self.match_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请至少选择一条战绩进行导出。")
            return

        selected_matches = [self.match_list_widget.itemWidget(item).match_data for item in selected_items]
        file_path, _ = QFileDialog.getSaveFileName(self, "保存战绩文件", "", "JSON Files (*.json)")
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(selected_matches, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "导出成功", f"成功导出 {len(selected_matches)} 条战绩到 {file_path}。")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出战绩时发生错误: {e}")

    def import_matches(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "导入战绩文件", "", "JSON Files (*.json)")
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"无法解析 JSON 文件: {e}")
            return

        if not isinstance(import_data, list):
            QMessageBox.critical(self, "导入错误", "文件格式错误，必须是战绩列表。")
            return

        all_chars = {char["name"] for char in self.characters_data}
        valid_matches = []
        invalid_chars = set()
        for match in import_data:
            if not all(key in match for key in ["team_a", "team_b", "result"]):
                continue
            if not isinstance(match["team_a"], list) or not isinstance(match["team_b"], list):
                continue
            if match["result"] not in ["胜", "败"]:
                continue
            match_chars = set(match["team_a"] + match["team_b"])
            if all(char in all_chars for char in match_chars if char):
                valid_matches.append(match)
            else:
                invalid_chars.update(char for char in match_chars if char and char not in all_chars)

        if not valid_matches:
            QMessageBox.critical(self, "导入失败", "没有有效的战绩数据或所有角色无效。")
            return

        try:
            with open(MATCH_FILE, "r+", encoding="utf-8") as f:
                self.matches_data.extend(valid_matches)
                f.seek(0)
                json.dump(self.matches_data, f, indent=2, ensure_ascii=False)
                f.truncate()
            self.display_matches()
            message = f"成功导入了 {len(valid_matches)} 条战绩记录。"
            if invalid_chars:
                message += f"\n以下角色不存在，已跳过相关记录: {', '.join(invalid_chars)}"
            QMessageBox.information(self, "导入成功", message)
            if self.parent():
                self.parent().update_match()
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"保存战绩失败: {e}")

    def update_character_order(self):
        new_order = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            name = item.data(Qt.UserRole)
            for char in self.characters_data:
                if char["name"] == name:
                    new_order.append(char)
                    break
        self.characters_data = new_order
        try:
            with open(CHAR_FILE, "w", encoding="utf-8") as f:
                json.dump(self.characters_data, f, indent=2, ensure_ascii=False)
            if self.parent() and isinstance(self.parent(), CharacterManager):
                self.parent().load_characters()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存角色顺序失败: {e}")

class CharacterManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CJJC记录")
        self.characters_data = []
        self.init_ui()
        self.load_characters()
        self.update_match()
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        icon_path = os.path.join(base_path, "doro.ico")
        if not QIcon(icon_path).isNull():
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"警告: {icon_path} 未找到或无法加载。")

    def init_ui(self):
        self.main_layout = QHBoxLayout()
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        match_add_group = QGroupBox("添加战绩")
        match_add_layout = QVBoxLayout()
        team_b_layout = QHBoxLayout()
        team_b_layout.addWidget(QLabel("防守方："))
        self.team_b_labels = []
        for _ in range(5):
            label = DropLabel(parent=self)
            self.team_b_labels.append(label)
            team_b_layout.addWidget(label)
        match_add_layout.addLayout(team_b_layout)
        team_a_layout = QHBoxLayout()
        team_a_layout.addWidget(QLabel("进攻方："))
        self.team_a_labels = []
        for _ in range(5):
            label = DropLabel(parent=self)
            self.team_a_labels.append(label)
            team_a_layout.addWidget(label)
        match_add_layout.addLayout(team_a_layout)
        self.stats_group = QGroupBox("队伍充能")
        stats_layout = QVBoxLayout()
        self.team_b_stats = QLabel("防守方: 2RL: 0 | 2.5RL: 0 | 3RL: 0 | 3.5RL: 0 | 4RL: 0")
        self.team_a_stats = QLabel("进攻方: 2RL: 0 | 2.5RL: 0 | 3RL: 0 | 3.5RL: 0 | 4RL: 0")
        stats_layout.addWidget(self.team_b_stats)
        stats_layout.addWidget(self.team_a_stats)
        self.stats_group.setLayout(stats_layout)
        match_add_layout.addWidget(self.stats_group)
        result_layout = QHBoxLayout()
        result_layout.addWidget(QLabel("结果："))
        self.result_combo = QComboBox()
        self.result_combo.addItems(["胜", "败"])
        result_layout.addWidget(self.result_combo)
        match_add_layout.addLayout(result_layout)
        match_add_layout.addWidget(QLabel("备注："))
        self.notes_input = QTextEdit()
        self.notes_input.setMinimumHeight(60)
        match_add_layout.addWidget(self.notes_input)
        match_btn_layout = QHBoxLayout()
        self.add_match_btn = QPushButton("添加战绩")
        self.add_match_btn.setStyleSheet(BUTTON_STYLE["primary"])
        self.clear_match_input_btn = QPushButton("清除输入")
        self.clear_match_input_btn.setStyleSheet(BUTTON_STYLE["secondary"])
        match_btn_layout.addWidget(self.add_match_btn)
        match_btn_layout.addWidget(self.clear_match_input_btn)
        match_add_layout.addLayout(match_btn_layout)
        match_add_group.setLayout(match_add_layout)
        left_layout.addWidget(match_add_group)

        self.latest_match_preview = LatestMatchPreview()
        left_layout.addWidget(self.latest_match_preview)
        self.view_matches_btn = QPushButton("查看战绩")
        self.view_matches_btn.setStyleSheet(BUTTON_STYLE["primary"])
        left_layout.addWidget(self.view_matches_btn)
        left_panel.setLayout(left_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout()

        char_add_group = QGroupBox("添加角色")
        char_add_layout = QVBoxLayout()
        char_input_layout = QGridLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("名称")
        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("昵称（可选）")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["类型", "火力型", "防御型", "辅助型"])
        self.rank_combo = QComboBox()
        self.rank_combo.addItems(["爆裂", "I", "II", "III", "Λ"])
        self.rl2_input = QLineEdit("")
        self.rl2_input.setPlaceholderText("2RL值")
        self.rl25_input = QLineEdit("")
        self.rl25_input.setPlaceholderText("2.5RL值")
        self.rl3_input = QLineEdit("")
        self.rl3_input.setPlaceholderText("3RL值")
        self.rl35_input = QLineEdit("")
        self.rl35_input.setPlaceholderText("3.5RL值")
        self.rl4_input = QLineEdit("")
        self.rl4_input.setPlaceholderText("4RL值")
        self.select_img_btn = QPushButton("选择图片")
        self.select_img_btn.setStyleSheet(BUTTON_STYLE["primary"])
        self.add_char_btn = QPushButton("添加角色")
        self.add_char_btn.setStyleSheet(BUTTON_STYLE["primary"])
        self.clear_char_input_btn = QPushButton("清除输入")
        self.clear_char_input_btn.setStyleSheet(BUTTON_STYLE["secondary"])
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(60, 60)
        self.preview_label.setStyleSheet("border: none;")
        char_input_layout.addWidget(self.name_input, 0, 0)
        char_input_layout.addWidget(self.nickname_input, 0, 1)
        char_input_layout.addWidget(self.type_combo, 0, 2)
        char_input_layout.addWidget(self.rank_combo, 0, 3)
        char_input_layout.addWidget(self.clear_char_input_btn, 0, 4)
        char_input_layout.addWidget(self.select_img_btn, 0, 5)
        char_input_layout.addWidget(self.preview_label, 0, 6)
        char_input_layout.addWidget(self.rl2_input, 1, 0)
        char_input_layout.addWidget(self.rl25_input, 1, 1)
        char_input_layout.addWidget(self.rl3_input, 1, 2)
        char_input_layout.addWidget(self.rl35_input, 1, 3)
        char_input_layout.addWidget(self.rl4_input, 1, 4)
        char_input_layout.addWidget(self.add_char_btn, 1, 5)
        char_add_layout.addLayout(char_input_layout)
        char_add_group.setLayout(char_add_layout)
        right_layout.addWidget(char_add_group)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选类型："))
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["所有类型", "火力型", "防御型", "辅助型"])
        filter_layout.addWidget(self.filter_type_combo)
        filter_layout.addWidget(QLabel("筛选爆裂："))
        self.filter_rank_combo = QComboBox()
        self.filter_rank_combo.addItems(["所有爆裂", "I", "II", "III", "Λ"])
        filter_layout.addWidget(self.filter_rank_combo)
        right_layout.addLayout(filter_layout)

        char_list_group = QGroupBox("角色列表")
        char_list_layout = QVBoxLayout()
        self.list_widget = DraggableListWidget(parent=self)
        self.list_widget.setIconSize(QSize(60, 60))
        self.list_widget.setViewMode(QListView.IconMode)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        char_list_layout.addWidget(self.list_widget)

        char_btn_layout = QHBoxLayout()
        self.select_all_char_btn = QPushButton("全选")
        self.select_all_char_btn.setStyleSheet(BUTTON_STYLE["primary"])
        self.select_all_char_btn.clicked.connect(self.select_all_chars)
        self.edit_char_btn = QPushButton("编辑角色")
        self.edit_char_btn.setStyleSheet(BUTTON_STYLE["primary"])
        self.edit_char_btn.clicked.connect(self.edit_character)
        self.delete_char_btn = QPushButton("删除角色")
        self.delete_char_btn.setStyleSheet(BUTTON_STYLE["secondary"])
        self.delete_char_btn.clicked.connect(self.delete_character)
        self.export_char_btn = QPushButton("导出角色")
        self.export_char_btn.setStyleSheet(BUTTON_STYLE["primary"])
        self.export_char_btn.clicked.connect(self.export_characters)
        self.import_char_btn = QPushButton("导入角色")
        self.import_char_btn.setStyleSheet(BUTTON_STYLE["primary"])
        self.import_char_btn.clicked.connect(self.import_characters)
        char_btn_layout.addWidget(self.select_all_char_btn)
        char_btn_layout.addWidget(self.edit_char_btn)
        char_btn_layout.addWidget(self.delete_char_btn)
        char_btn_layout.addWidget(self.export_char_btn)
        char_btn_layout.addWidget(self.import_char_btn)
        char_list_layout.addLayout(char_btn_layout)
        char_list_group.setLayout(char_list_layout)
        right_layout.addWidget(char_list_group)

        right_panel.setLayout(right_layout)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        self.main_layout.addWidget(splitter)
        self.setLayout(self.main_layout)

        self.selected_img_path = None

        self.select_img_btn.clicked.connect(self.select_image)
        self.add_char_btn.clicked.connect(self.add_character)
        self.clear_char_input_btn.clicked.connect(self.clear_character_input)
        self.filter_type_combo.currentTextChanged.connect(self.filter_characters)
        self.filter_rank_combo.currentTextChanged.connect(self.filter_characters)
        self.add_match_btn.clicked.connect(self.add_match)
        self.clear_match_input_btn.clicked.connect(self.clear_match_input)
        self.view_matches_btn.clicked.connect(self.show_match_viewer)

    def clear_character_input(self):
        self.name_input.clear()
        self.nickname_input.clear()
        self.preview_label.clear()
        self.selected_img_path = None
        self.type_combo.setCurrentIndex(0)
        self.rank_combo.setCurrentIndex(0)
        self.rl2_input.setText("0")
        self.rl25_input.setText("0")
        self.rl3_input.setText("0")
        self.rl35_input.setText("0")
        self.rl4_input.setText("0")

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_img_path = path
            pixmap = QPixmap(path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(pixmap)

    def add_character(self):
        name = self.name_input.text().strip()
        nickname = self.nickname_input.text().strip()
        char_type = self.type_combo.currentText()
        if char_type == "类型":
            char_type = ""
        rank = self.rank_combo.currentText()
        if rank == "爆裂":
            rank = ""

        rl_values = {}
        for rl_key, rl_input in [
            ("2RL", self.rl2_input),
            ("2.5RL", self.rl25_input),
            ("3RL", self.rl3_input),
            ("3.5RL", self.rl35_input),
            ("4RL", self.rl4_input)
        ]:
            text = rl_input.text().strip()
            try:
                rl_values[rl_key] = float(text) if text else 0.0
            except ValueError:
                QMessageBox.warning(self, "错误", f"请输入有效的 {rl_key} 值（例如 0 或 100.0）")
                return

        if not name:
            QMessageBox.warning(self, "提示", "请输入角色名称")
            return
        try:
            with open(CHAR_FILE, "r", encoding="utf-8") as f:
                characters = json.load(f)
            for char in characters:
                if char["name"] == name:
                    QMessageBox.warning(self, "重复", f"角色 [{name}] 已存在")
                    return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取角色数据失败: {e}")
            return
        if not self.selected_img_path:
            QMessageBox.warning(self, "提示", "请选择角色图片")
            return
        ext = os.path.splitext(self.selected_img_path)[1]
        img_filename = f"{name}{ext}"
        img_dest_path = os.path.join(IMG_DIR, img_filename)
        try:
            with open(self.selected_img_path, "rb") as src, open(img_dest_path, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存图片失败: {e}")
            return
        new_char = {
            "name": name,
            "nickname": nickname,
            "type": char_type,
            "rank": rank,
            "image": img_filename,
            "2RL": rl_values["2RL"],
            "2.5RL": rl_values["2.5RL"],
            "3RL": rl_values["3RL"],
            "3.5RL": rl_values["3.5RL"],
            "4RL": rl_values["4RL"]
        }
        characters.append(new_char)
        try:
            with open(CHAR_FILE, "w", encoding="utf-8") as f:
                json.dump(characters, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存角色数据失败: {e}")
            return
        self.clear_character_input()
        self.load_characters()
        QMessageBox.information(self, "成功", f"角色 [{name}] 添加成功")

    def filter_characters(self):
        self.list_widget.clear()
        selected_type = self.filter_type_combo.currentText()
        selected_rank = self.filter_rank_combo.currentText()
        is_filtered = (selected_type != "所有类型" or selected_rank != "所有爆裂")
        icon_cache = {}
        filtered_chars = []
        for char in self.characters_data:
            name = char["name"]
            char_type = char.get("type", "")
            char_rank = char.get("rank", "")
            type_match = (selected_type == "所有类型" or char_type == selected_type)
            rank_match = (selected_rank == "所有爆裂" or char_rank == selected_rank)
            if type_match and rank_match:
                filtered_chars.append(char)
        for char in filtered_chars:
            name = char["name"]
            item = QListWidgetItem()
            img_path = os.path.join(IMG_DIR, char["image"])
            if img_path not in icon_cache:
                if os.path.exists(img_path):
                    icon_cache[img_path] = QIcon(img_path)
                else:
                    icon_cache[img_path] = QIcon()
            item.setIcon(icon_cache[img_path])
            item.setData(Qt.UserRole, name)
            font_metrics = self.list_widget.fontMetrics()
            elided_name = font_metrics.elidedText(name, Qt.ElideRight, 60)
            item.setText(elided_name)
            tooltip_text = (
                f"<p style='font-family: Arial; font-size: 12px;'>"
                f"<table>"
                f"<tr><td style='width: 80px;'>名称:</td><td>{char.get('name', '')}</td></tr>"
                f"<tr><td style='width: 80px;'>昵称:</td><td>{char.get('nickname', '') or 'none'}</td></tr>"
                f"<tr><td style='width: 80px;'>类型:</td><td>{char.get('type', '') or '未设置'}</td></tr>"
                f"<tr><td style='width: 80px;'>等级:</td><td>{char.get('rank', '') or '未设置'}</td></tr>"
                f"<tr><td style='width: 80px;'>2RL:</td><td>{char.get('2RL', 0):.1f}</td></tr>"
                f"<tr><td style='width: 80px;'>2.5RL:</td><td>{char.get('2.5RL', 0):.1f}</td></tr>"
                f"<tr><td style='width: 80px;'>3RL:</td><td>{char.get('3RL', 0):.1f}</td></tr>"
                f"<tr><td style='width: 80px;'>3.5RL:</td><td>{char.get('3.5RL', 0):.1f}</td></tr>"
                f"<tr><td style='width: 80px;'>4RL:</td><td>{char.get('4RL', 0):.1f}</td></tr>"
                f"</table>"
                f"</p>"
            )
            item.setToolTip(tooltip_text)
            item.setTextAlignment(Qt.AlignHCenter)
            item.setSizeHint(QSize(60, 80))
            self.list_widget.addItem(item)

    def select_all_chars(self):
        if self.list_widget.count() > 1000:
            reply = QMessageBox.question(
                self, "警告",
                f"角色列表包含 {self.list_widget.count()} 个项目，全选可能导致性能问题。是否继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.list_widget.blockSignals(True)
        try:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item is not None:
                    item.setSelected(True)
        finally:
            self.list_widget.blockSignals(False)

    def edit_character(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择一个角色进行编辑")
            return
        if len(selected_items) > 1:
            QMessageBox.information(self, "提示", "一次只能编辑一个角色")
            return

        char_name = selected_items[0].data(Qt.UserRole)
        char_data = next((char for char in self.characters_data if char["name"] == char_name), None)
        if not char_data:
            QMessageBox.critical(self, "错误", "无法获取角色数据")
            return

        dialog = EditCharacterDialog(char_data, self)
        if dialog.exec_():
            updated_data = dialog.updated_data
            try:
                with open(CHAR_FILE, "r+", encoding="utf-8") as f:
                    characters = json.load(f)
                    for i, char in enumerate(characters):
                        if char["name"] == char_data["name"]:
                            characters[i] = updated_data
                            break
                    f.seek(0)
                    json.dump(characters, f, indent=2, ensure_ascii=False)
                    f.truncate()
                self.load_characters()
                QMessageBox.information(self, "成功", f"角色 [{updated_data['name']}] 已更新")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新角色失败: {e}")

    def delete_character(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择至少一个角色")
            return

        char_names = [item.data(Qt.UserRole) for item in selected_items]
        char_list = "\n".join([f"- {name}" for name in char_names])

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {len(char_names)} 个角色吗？\n{char_list}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with open(CHAR_FILE, "r+", encoding="utf-8") as f:
                    characters = json.load(f)
                    remaining_chars = [c for c in characters if c["name"] not in char_names]
                    f.seek(0)
                    json.dump(remaining_chars, f, indent=2, ensure_ascii=False)
                    f.truncate()

                for name in char_names:
                    for fname in os.listdir(IMG_DIR):
                        if fname.startswith(name):
                            os.remove(os.path.join(IMG_DIR, fname))

                self.load_characters()
                QMessageBox.information(self, "成功", f"已删除 {len(char_names)} 个角色")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除角色失败: {e}")

    def export_characters(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要导出的角色")
            return

        selected_chars = [item.data(Qt.UserRole) for item in selected_items]
        export_data = [char for char in self.characters_data if char["name"] in selected_chars]
        file_path, _ = QFileDialog.getSaveFileName(self, "导出角色", "", "ZIP Files (*.zip)")
        if not file_path:
            return

        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8-sig', suffix='.csv',
                                             newline='') as csv_file:
                writer = csv.DictWriter(csv_file,
                                        fieldnames=["名称", "昵称", "类型", "爆裂", "2RL", "2.5RL", "3RL", "3.5RL",
                                                    "4RL"], quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                for char in export_data:
                    writer.writerow({
                        "名称": char.get("name", ""),
                        "昵称": char.get("nickname", ""),
                        "类型": char.get("type", ""),
                        "爆裂": char.get("rank", ""),
                        "2RL": str(char.get("2RL", 0.0)),
                        "2.5RL": str(char.get("2.5RL", 0.0)),
                        "3RL": str(char.get("3RL", 0.0)),
                        "3.5RL": str(char.get("3.5RL", 0.0)),
                        "4RL": str(char.get("4RL", 0.0))
                    })
                csv_file_path = csv_file.name

            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(csv_file_path, "characters.csv")
                for char in export_data:
                    img_path = os.path.join(IMG_DIR, char["image"])
                    if os.path.exists(img_path):
                        zf.write(img_path, char["image"])

            os.remove(csv_file_path)

            QMessageBox.information(self, "成功", f"成功导出 {len(selected_chars)} 个角色到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def import_characters(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "导入角色", "", "CSV or ZIP Files (*.csv *.zip)")
        if not file_path:
            return

        try:
            import tempfile
            import os
            temp_dir = None
            csv_path = None

            valid_types = {"火力型", "防御型", "辅助型", ""}
            valid_ranks = {"I", "II", "III", "Λ", ""}
            valid_extensions = {".png", ".jpg", ".jpeg"}

            if file_path.endswith('.zip'):
                temp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(file_path, "r") as zf:
                    zf.extractall(temp_dir)
                csv_path = os.path.join(temp_dir, "characters.csv")
                if not os.path.exists(csv_path):
                    raise ValueError("ZIP 文件缺少 characters.csv")
            else:
                csv_path = file_path

            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames or sorted(reader.fieldnames) != sorted(
                        ["名称", "昵称", "类型", "爆裂", "2RL", "2.5RL", "3RL", "3.5RL", "4RL"]):
                    raise ValueError("CSV 文件表头不正确，必须包含：名称,昵称,类型,爆裂,2RL,2.5RL,3RL,3.5RL,4RL")

                import_data = []
                duplicates = []
                skipped_chars = []
                missing_images = []
                invalid_data = []
                csv_dir = os.path.dirname(csv_path) if file_path.endswith('.csv') else temp_dir

                existing_names = {char["name"] for char in self.characters_data}

                for row in reader:
                    name = row["名称"].strip()
                    if not name:
                        invalid_data.append("空名称")
                        continue

                    nickname = row["昵称"].strip()
                    char_type = row["类型"].strip()
                    rank = row["爆裂"].strip()

                    if char_type not in valid_types:
                        invalid_data.append(f"{name}: 无效类型 {char_type}")
                        continue
                    if rank not in valid_ranks:
                        invalid_data.append(f"{name}: 无效爆裂 {rank}")
                        continue

                    try:
                        rl2 = float(row["2RL"].strip()) if row["2RL"].strip() else 0.0
                        rl25 = float(row["2.5RL"].strip()) if row["2.5RL"].strip() else 0.0
                        rl3 = float(row["3RL"].strip()) if row["3RL"].strip() else 0.0
                        rl35 = float(row["3.5RL"].strip()) if row["3.5RL"].strip() else 0.0
                        rl4 = float(row["4RL"].strip()) if row["4RL"].strip() else 0.0
                    except ValueError:
                        invalid_data.append(f"{name}: 无效RL值")
                        continue

                    img_path = None
                    for ext in valid_extensions:
                        candidate = os.path.join(csv_dir, f"{name}{ext}")
                        if os.path.exists(candidate):
                            img_path = candidate
                            img_ext = ext
                            break

                    if not img_path:
                        missing_images.append(name)
                        continue

                    img_filename = f"{name}{img_ext}"
                    char_data = {
                        "name": name,
                        "nickname": nickname,
                        "type": char_type,
                        "rank": rank,
                        "image": img_filename,
                        "2RL": rl2,
                        "2.5RL": rl25,
                        "3RL": rl3,
                        "3.5RL": rl35,
                        "4RL": rl4
                    }

                    if name in existing_names:
                        duplicates.append(char_data)
                    else:
                        import_data.append(char_data)

                overwrite_chars = []
                if duplicates:
                    dialog = DuplicateCharacterDialog(duplicates, self.characters_data, self)
                    if dialog.exec_() == QDialog.Accepted:
                        for dup_char in duplicates:
                            choice = dialog.choices.get(dup_char["name"], "skip")
                            if choice == "overwrite":
                                overwrite_chars.append(dup_char)
                            else:
                                skipped_chars.append(dup_char["name"])
                    else:
                        raise ValueError("导入已取消")

                if not (import_data or overwrite_chars):
                    error_msg = "没有有效角色可导入。"
                    if skipped_chars:
                        error_msg += f"\n跳过重复角色: {', '.join(skipped_chars)}"
                    if missing_images:
                        error_msg += f"\n缺少图片的角色: {', '.join(missing_images)}"
                    if invalid_data:
                        error_msg += f"\n无效数据: {', '.join(invalid_data)}"
                    raise ValueError(error_msg)

                with open(CHAR_FILE, "r+", encoding="utf-8") as f:
                    characters = json.load(f)

                    for overwrite_char in overwrite_chars:
                        old_char = next((char for char in characters if char["name"] == overwrite_char["name"]), None)
                        if old_char:
                            characters.remove(old_char)
                            if old_char["image"] != overwrite_char["image"]:
                                old_img_path = os.path.join(IMG_DIR, old_char["image"])
                                if os.path.exists(old_img_path):
                                    os.remove(old_img_path)
                            src_img_path = os.path.join(csv_dir, overwrite_char["image"])
                            dest_img_path = os.path.join(IMG_DIR, overwrite_char["image"])
                            shutil.copy2(src_img_path, dest_img_path)
                        characters.append(overwrite_char)

                    for new_char in import_data:
                        src_img_path = os.path.join(csv_dir, new_char["image"])
                        dest_img_path = os.path.join(IMG_DIR, new_char["image"])
                        shutil.copy2(src_img_path, dest_img_path)
                        characters.append(new_char)

                    f.seek(0)
                    json.dump(characters, f, indent=2, ensure_ascii=False)
                    f.truncate()

                self.load_characters()
                message = f"成功导入 {len(import_data)} 个新角色，覆盖 {len(overwrite_chars)} 个角色。"
                if skipped_chars:
                    message += f"\n跳过重复角色: {', '.join(skipped_chars)}"
                if missing_images:
                    message += f"\n缺少图片的角色: {', '.join(missing_images)}"
                if invalid_data:
                    message += f"\n无效数据: {', '.join(invalid_data)}"
                QMessageBox.information(self, "成功", message)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def load_characters(self):
        try:
            with open(CHAR_FILE, "r", encoding="utf-8") as f:
                self.characters_data = json.load(f)
        except json.JSONDecodeError:
            self.characters_data = []
        self.filter_characters()

    def add_match(self):
        team_a = self.get_team(self.team_a_labels)
        team_b = self.get_team(self.team_b_labels)
        result = self.result_combo.currentText()
        notes = self.notes_input.toPlainText().strip()

        if not team_a and not team_b:
            QMessageBox.critical(self, "提示", "请至少选择一个角色")
            return

        all_chars = {char["name"] for char in self.characters_data}
        missing_chars = []
        for char in team_a + team_b:
            if char and char not in all_chars:
                missing_chars.append(char)

        if missing_chars:
            QMessageBox.critical(self, "错误", f"以下角色不存在: {', '.join(sorted(set(missing_chars)))}")
            return

        match_record = {
            "team_a": team_a,
            "team_b": team_b,
            "result": result,
            "notes": notes
        }

        try:
            with open(MATCH_FILE, "r+", encoding="utf-8") as f:
                matches = json.load(f)
                matches.append(match_record)
                f.seek(0)
                json.dump(matches, f, indent=4, ensure_ascii=False)
                f.truncate()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存战绩失败: {e}")
            return

        self.clear_match_input()
        self.update_match()

    def clear_match_input(self):
        for label in self.team_a_labels + self.team_b_labels:
            label.clear_label()
        self.result_combo.setCurrentIndex(0)
        self.notes_input.clear()
        self.update_team_stats()

    def show_match_viewer(self):
        viewer = MatchViewer(self)
        viewer.exec_()

    def update_character_order(self):
        new_order = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            name = item.data(Qt.UserRole)
            for char in self.characters_data:
                if char["name"] == name:
                    new_order.append(char)
                    break
        self.characters_data = new_order
        try:
            with open(CHAR_FILE, "r+", encoding="utf-8") as f:
                f.seek(0)
                json.dump(self.characters_data, f, indent=2, ensure_ascii=False)
                f.truncate()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存角色顺序失败: {e}")

    def get_team(self, labels):
        return [label.character_name for label in labels if label.character_name]

    def update_team_stats(self):
        def calculate_team_stats(labels):
            stats = {"2RL": 0, "2.5RL": 0, "3RL": 0, "3.5RL": 0, "4RL": 0}
            for label in labels:
                if label.character_name:
                    for char in self.characters_data:
                        if char["name"] == label.character_name:
                            for attr in stats:
                                stats[attr] += float(char.get(attr, 0))
            return stats

        def format_stat(value, stat_name, is_first_highlight):
            formatted_value = f"{value:.1f}"
            if is_first_highlight:
                return f"<span style='color: red; font-weight: bold;'>{stat_name}: {formatted_value}</span>"
            return f"{stat_name}: {formatted_value}"

        team_a_stats = calculate_team_stats(self.team_a_labels)
        team_b_stats = calculate_team_stats(self.team_b_labels)

        first_a_highlight = None
        for attr in ["2RL", "2.5RL", "3RL", "3.5RL", "4RL"]:
            if team_a_stats[attr] >= 100:
                first_a_highlight = attr
                break

        first_b_highlight = None
        for attr in ["2RL", "2.5RL", "3RL", "3.5RL", "4RL"]:
            if team_b_stats[attr] >= 100:
                first_b_highlight = attr
                break

        team_a_text = "进攻方: " + " | ".join(
            format_stat(team_a_stats[attr], attr, attr == first_a_highlight)
            for attr in ["2RL", "2.5RL", "3RL", "3.5RL", "4RL"]
        )

        team_b_text = "防守方: " + " | ".join(
            format_stat(team_b_stats[attr], attr, attr == first_b_highlight)
            for attr in ["2RL", "2.5RL", "3RL", "3.5RL", "4RL"]
        )

        self.team_a_stats.setText(team_a_text)
        self.team_b_stats.setText(team_b_text)

    def update_match(self):
        try:
            with open(MATCH_FILE, "r", encoding="utf-8") as f:
                matches = json.load(f)
            self.latest_match_preview.update_preview(matches)
        except json.JSONDecodeError as e:
            print(f"JSON解码错误，文件：{MATCH_FILE}: {e}")
            self.latest_match_preview.update_preview([])
        except FileNotFoundError:
            print(f"文件未找到：{MATCH_FILE}")
            self.latest_match_preview.update_preview([])
        except Exception as e:
            print(f"加载比赛时发生错误: {e}")
            self.latest_match_preview.update_preview([])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QToolTip.setFont(QFont("Arial", 14))
    app.setStyleSheet("QToolTip { font-family: 'Arial'; font-size: 14px; }")
    window = CharacterManager()
    window.show()
    sys.exit(app.exec_())