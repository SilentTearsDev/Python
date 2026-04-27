import json
import os
import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QTextEdit, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QComboBox,
    QDoubleSpinBox, QColorDialog, QMessageBox, QInputDialog,
    QSplitter, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


DEFAULT_DATA = {
    "settings": {
        "speakers": ["Player", "Narrator", "Boglar", "Unknown"],
        "panel_styles": ["Dark", "Light", "Angry", "Whisper"],
        "panel_moving_options": ["None", "Ping-pong", "Shake", "Float", ]
    },
    "entries": []
}


def print_log(msg):
    print("[DialogueEditor]", msg)


class DialogueEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        print_log("App started")

        self.setWindowTitle("Silent Tears Dialogue Editor")
        self.resize(1250, 760)

        self.current_file = None
        self.data = json.loads(json.dumps(DEFAULT_DATA))
        self.current_index = -1
        self.loading_ui = False

        self._build_ui()
        self._refresh_all_lists()
        self._set_editor_enabled(False)

    def _build_ui(self):
        root = QWidget()
        main_layout = QVBoxLayout(root)

        top_bar = QHBoxLayout()
        self.new_btn = QPushButton("New")
        self.open_btn = QPushButton("Open JSON")
        self.save_btn = QPushButton("Save")
        self.save_as_btn = QPushButton("Save As")

        self.new_btn.clicked.connect(self.new_file)
        self.open_btn.clicked.connect(self.open_file)
        self.save_btn.clicked.connect(self.save_file)
        self.save_as_btn.clicked.connect(self.save_as_file)

        top_bar.addWidget(self.new_btn)
        top_bar.addWidget(self.open_btn)
        top_bar.addWidget(self.save_btn)
        top_bar.addWidget(self.save_as_btn)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Dialogue entries"))

        self.entry_list = QListWidget()
        self.entry_list.currentRowChanged.connect(self.entry_selected)
        left_layout.addWidget(self.entry_list)

        entry_buttons = QHBoxLayout()
        self.add_entry_btn = QPushButton("Add")
        self.duplicate_entry_btn = QPushButton("Duplicate")
        self.delete_entry_btn = QPushButton("Delete")
        self.move_up_btn = QPushButton("Up")
        self.move_down_btn = QPushButton("Down")

        self.add_entry_btn.clicked.connect(self.add_entry)
        self.duplicate_entry_btn.clicked.connect(self.duplicate_entry)
        self.delete_entry_btn.clicked.connect(self.delete_entry)
        self.move_up_btn.clicked.connect(self.move_entry_up)
        self.move_down_btn.clicked.connect(self.move_entry_down)

        for btn in [
            self.add_entry_btn,
            self.duplicate_entry_btn,
            self.delete_entry_btn,
            self.move_up_btn,
            self.move_down_btn
        ]:
            entry_buttons.addWidget(btn)

        left_layout.addLayout(entry_buttons)

        editor = QWidget()
        editor_layout = QVBoxLayout(editor)

        desc = QLabel(""
            )
        desc.setWordWrap(True)
        editor_layout.addWidget(desc)

        entry_group = QGroupBox("Selected entry")
        entry_form = QVBoxLayout(entry_group)

        entry_form.addWidget(QLabel("Speaker - választható karakter / beszélő"))
        speaker_row = QHBoxLayout()
        self.speaker_combo = QComboBox()
        self.add_speaker_btn_top = QPushButton("+")
        self.add_speaker_btn_top.setFixedWidth(42)
        self.speaker_combo.currentTextChanged.connect(self.update_current_entry)
        self.add_speaker_btn_top.clicked.connect(self.add_speaker_from_top)
        speaker_row.addWidget(self.speaker_combo)
        speaker_row.addWidget(self.add_speaker_btn_top)
        entry_form.addLayout(speaker_row)

        entry_form.addWidget(QLabel("Content - maga a dialogue szöveg"))
        self.content_edit = QTextEdit()
        self.content_edit.textChanged.connect(self.update_current_entry)
        entry_form.addWidget(self.content_edit)

        entry_form.addWidget(QLabel("Text color - a szöveg színe hex formában"))
        color_row = QHBoxLayout()
        self.color_line = QLineEdit("#ffffff")
        self.color_btn = QPushButton("Pick color")
        self.color_line.textChanged.connect(self.update_current_entry)
        self.color_btn.clicked.connect(self.pick_color)
        color_row.addWidget(self.color_line)
        color_row.addWidget(self.color_btn)
        entry_form.addLayout(color_row)

        entry_form.addWidget(QLabel("Text speed - betűnkénti megjelenés sebessége, másodperc / karakter"))
        self.text_speed_spin = QDoubleSpinBox()
        self.text_speed_spin.setRange(0.001, 5.0)
        self.text_speed_spin.setDecimals(3)
        self.text_speed_spin.setSingleStep(0.005)
        self.text_speed_spin.setValue(0.03)
        self.text_speed_spin.valueChanged.connect(self.update_current_entry)
        entry_form.addWidget(self.text_speed_spin)

        entry_form.addWidget(QLabel("Panel moving - a játékodban lévő panel mozgás opció"))
        moving_row = QHBoxLayout()
        self.panel_moving_combo = QComboBox()
        self.add_moving_btn_top = QPushButton("+")
        self.add_moving_btn_top.setFixedWidth(42)
        self.panel_moving_combo.currentTextChanged.connect(self.update_current_entry)
        self.add_moving_btn_top.clicked.connect(self.add_panel_moving_from_top)
        moving_row.addWidget(self.panel_moving_combo)
        moving_row.addWidget(self.add_moving_btn_top)
        entry_form.addLayout(moving_row)

        entry_form.addWidget(QLabel("Panel style - vizuális panel preset / style"))
        style_row = QHBoxLayout()
        self.panel_style_combo = QComboBox()
        self.add_style_btn_top = QPushButton("+")
        self.add_style_btn_top.setFixedWidth(42)
        self.panel_style_combo.currentTextChanged.connect(self.update_current_entry)
        self.add_style_btn_top.clicked.connect(self.add_panel_style_from_top)
        style_row.addWidget(self.panel_style_combo)
        style_row.addWidget(self.add_style_btn_top)
        entry_form.addLayout(style_row)

        editor_layout.addWidget(entry_group)

        splitter.addWidget(left)
        splitter.addWidget(editor)
        splitter.setSizes([360, 890])

        main_layout.addWidget(splitter)
        self.setCentralWidget(root)

    def _default_entry(self):
        speakers = self.data["settings"].get("speakers", ["Player"])
        styles = self.data["settings"].get("panel_styles", ["Default"])
        moving = self.data["settings"].get("panel_moving_options", ["None"])

        return {
            "speaker": speakers[0] if speakers else "Player",
            "content": "",
            "text_color": "#ffffff",
            "text_speed": 0.03,
            "panel_moving": moving[0] if moving else "None",
            "panel_style": styles[0] if styles else "Default",
            "seen_entry": False
        }

    def _set_editor_enabled(self, enabled):
        for widget in [
            self.speaker_combo,
            self.add_speaker_btn_top,
            self.content_edit,
            self.color_line,
            self.color_btn,
            self.text_speed_spin,
            self.panel_moving_combo,
            self.add_moving_btn_top,
            self.panel_style_combo,
            self.add_style_btn_top
        ]:
            widget.setEnabled(enabled)

    def _refresh_all_lists(self):
        self._refresh_entry_list()
        self._refresh_dropdowns()

    def _refresh_entry_list(self):
        self.entry_list.blockSignals(True)
        self.entry_list.clear()

        for i, entry in enumerate(self.data.get("entries", [])):
            speaker = entry.get("speaker", "???")
            content = entry.get("content", "").replace("\n", " ")
            preview = content[:40] + "..." if len(content) > 40 else content
            self.entry_list.addItem(f"{i + 1}. {speaker}: {preview}")

        self.entry_list.blockSignals(False)

    def _refresh_dropdowns(self):
        current_speaker = self.speaker_combo.currentText()
        current_style = self.panel_style_combo.currentText()
        current_moving = self.panel_moving_combo.currentText()

        self.speaker_combo.blockSignals(True)
        self.panel_style_combo.blockSignals(True)
        self.panel_moving_combo.blockSignals(True)

        self.speaker_combo.clear()
        self.panel_style_combo.clear()
        self.panel_moving_combo.clear()

        self.speaker_combo.addItems(self.data["settings"].get("speakers", []))
        self.panel_style_combo.addItems(self.data["settings"].get("panel_styles", []))
        self.panel_moving_combo.addItems(self.data["settings"].get("panel_moving_options", []))

        if current_speaker:
            self.speaker_combo.setCurrentText(current_speaker)
        if current_style:
            self.panel_style_combo.setCurrentText(current_style)
        if current_moving:
            self.panel_moving_combo.setCurrentText(current_moving)

        self.speaker_combo.blockSignals(False)
        self.panel_style_combo.blockSignals(False)
        self.panel_moving_combo.blockSignals(False)

    def new_file(self):
        print_log("New file created")
        self.current_file = None
        self.data = json.loads(json.dumps(DEFAULT_DATA))
        self.current_index = -1
        self._refresh_all_lists()
        self._clear_editor()
        self._set_editor_enabled(False)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open dialogue JSON", "", "JSON files (*.json)")
        if not path:
            print_log("Open cancelled")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            self.data = self._normalize_loaded_data(loaded)
            self.current_file = path
            self.current_index = -1

            print_log(f"Opened file: {path}")
            self._refresh_all_lists()
            self._clear_editor()
            self._set_editor_enabled(False)

        except Exception as e:
            print_log(f"Open failed: {e}")
            QMessageBox.critical(self, "Open failed", str(e))

    def _normalize_loaded_data(self, loaded):
        data = json.loads(json.dumps(DEFAULT_DATA))

        if isinstance(loaded, dict):
            if "settings" in loaded:
                data["settings"].update(loaded.get("settings", {}))
            if "entries" in loaded:
                data["entries"] = loaded.get("entries", [])
            elif isinstance(loaded.get("dialogue"), list):
                data["entries"] = loaded.get("dialogue", [])

        for entry in data["entries"]:
            entry.setdefault("speaker", "Player")
            entry.setdefault("content", "")
            entry.setdefault("text_color", "#ffffff")
            entry.setdefault("text_speed", 0.03)
            entry.setdefault("panel_moving", "None")
            entry.setdefault("panel_style", "Default")
            entry.setdefault("seen_entry", False)

        data["settings"].setdefault("speakers", ["Player"])
        data["settings"].setdefault("panel_styles", ["Default"])
        data["settings"].setdefault("panel_moving_options", ["None", "Ping-pong"])

        return data

    def save_file(self):
        if not self.current_file:
            self.save_as_file()
            return

        self._save_to_path(self.current_file)

    def save_as_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save dialogue JSON", "dialogue.json", "JSON files (*.json)")
        if not path:
            print_log("Save cancelled")
            return

        if not path.lower().endswith(".json"):
            path += ".json"

        self.current_file = path
        self._save_to_path(path)

    def _save_to_path(self, path):
        try:
            for entry in self.data.get("entries", []):
                entry.setdefault("seen_entry", False)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)

            print_log(f"Saved JSON: {path}")
            print_log(f"Entries saved: {len(self.data.get('entries', []))}")
            print_log(f"Speakers: {self.data['settings'].get('speakers', [])}")
            print_log(f"Panel moving options: {self.data['settings'].get('panel_moving_options', [])}")
            print_log(f"Panel styles: {self.data['settings'].get('panel_styles', [])}")

            return True

        except Exception as e:
            print_log(f"Save failed: {e}")
            QMessageBox.critical(self, "Save failed", str(e))
            return False

    def add_entry(self):
        entry = self._default_entry()
        self.data["entries"].append(entry)
        self.current_index = len(self.data["entries"]) - 1

        print_log(f"Entry added at index {self.current_index}")

        self._refresh_entry_list()
        self.entry_list.setCurrentRow(self.current_index)

    def duplicate_entry(self):
        if self.current_index < 0:
            print_log("Duplicate failed: no selected entry")
            return

        src = self.data["entries"][self.current_index]
        dup = json.loads(json.dumps(src))

        self.data["entries"].insert(self.current_index + 1, dup)
        self.current_index += 1

        print_log(f"Entry duplicated to index {self.current_index}")

        self._refresh_entry_list()
        self.entry_list.setCurrentRow(self.current_index)

    def delete_entry(self):
        if self.current_index < 0:
            print_log("Delete failed: no selected entry")
            return

        removed = self.data["entries"].pop(self.current_index)
        print_log(f"Entry deleted: {removed}")

        if self.current_index >= len(self.data["entries"]):
            self.current_index = len(self.data["entries"]) - 1

        self._refresh_entry_list()

        if self.current_index >= 0:
            self.entry_list.setCurrentRow(self.current_index)
        else:
            self._clear_editor()
            self._set_editor_enabled(False)

    def move_entry_up(self):
        i = self.current_index
        if i <= 0:
            print_log("Move up ignored")
            return

        self.data["entries"][i - 1], self.data["entries"][i] = self.data["entries"][i], self.data["entries"][i - 1]
        self.current_index -= 1

        print_log(f"Entry moved up to index {self.current_index}")

        self._refresh_entry_list()
        self.entry_list.setCurrentRow(self.current_index)

    def move_entry_down(self):
        i = self.current_index
        if i < 0 or i >= len(self.data["entries"]) - 1:
            print_log("Move down ignored")
            return

        self.data["entries"][i + 1], self.data["entries"][i] = self.data["entries"][i], self.data["entries"][i + 1]
        self.current_index += 1

        print_log(f"Entry moved down to index {self.current_index}")

        self._refresh_entry_list()
        self.entry_list.setCurrentRow(self.current_index)

    def entry_selected(self, row):
        self.current_index = row

        if row < 0 or row >= len(self.data.get("entries", [])):
            self._clear_editor()
            self._set_editor_enabled(False)
            return

        print_log(f"Entry selected: {row}")

        self._set_editor_enabled(True)
        self._load_entry_into_ui(row)

    def _clear_editor(self):
        self.loading_ui = True

        self.speaker_combo.setCurrentIndex(-1)
        self.content_edit.clear()
        self.color_line.setText("#ffffff")
        self.text_speed_spin.setValue(0.03)
        self.panel_moving_combo.setCurrentIndex(-1)
        self.panel_style_combo.setCurrentIndex(-1)

        self.loading_ui = False

    def _load_entry_into_ui(self, index):
        entry = self.data["entries"][index]

        self.loading_ui = True
        self._refresh_dropdowns()

        self.speaker_combo.setCurrentText(entry.get("speaker", "Player"))
        self.content_edit.setPlainText(entry.get("content", ""))
        self.color_line.setText(entry.get("text_color", "#ffffff"))
        self.text_speed_spin.setValue(float(entry.get("text_speed", 0.03)))
        self.panel_moving_combo.setCurrentText(entry.get("panel_moving", "None"))
        self.panel_style_combo.setCurrentText(entry.get("panel_style", "Default"))

        self.loading_ui = False

    def update_current_entry(self):
        if self.loading_ui:
            return

        if self.current_index < 0 or self.current_index >= len(self.data.get("entries", [])):
            return

        entry = self.data["entries"][self.current_index]

        entry["speaker"] = self.speaker_combo.currentText()
        entry["content"] = self.content_edit.toPlainText()
        entry["text_color"] = self.color_line.text()
        entry["text_speed"] = float(self.text_speed_spin.value())
        entry["panel_moving"] = self.panel_moving_combo.currentText()
        entry["panel_style"] = self.panel_style_combo.currentText()
        entry.setdefault("seen_entry", False)

        print_log(f"Entry updated at index {self.current_index}")

        self._refresh_entry_list()

        self.entry_list.blockSignals(True)
        self.entry_list.setCurrentRow(self.current_index)
        self.entry_list.blockSignals(False)

    def pick_color(self):
        current = QColor(self.color_line.text())
        color = QColorDialog.getColor(current, self, "Pick text color")

        if color.isValid():
            self.color_line.setText(color.name())
            print_log(f"Color picked: {color.name()}")

    def add_speaker_from_top(self):
        text, ok = QInputDialog.getText(self, "Add speaker", "Speaker name:")

        if not ok or not text.strip():
            print_log("Add speaker cancelled")
            return

        text = text.strip()
        speakers = self.data["settings"].setdefault("speakers", [])

        if text not in speakers:
            speakers.append(text)
            print_log(f"Speaker added: {text}")
        else:
            print_log(f"Speaker already exists: {text}")

        self._refresh_dropdowns()
        self.speaker_combo.setCurrentText(text)
        self.update_current_entry()

    def add_panel_moving_from_top(self):
        text, ok = QInputDialog.getText(self, "Add panel moving", "Panel moving option:")

        if not ok or not text.strip():
            print_log("Add panel moving cancelled")
            return

        text = text.strip()
        options = self.data["settings"].setdefault("panel_moving_options", [])

        if text not in options:
            options.append(text)
            print_log(f"Panel moving option added: {text}")
        else:
            print_log(f"Panel moving option already exists: {text}")

        self._refresh_dropdowns()
        self.panel_moving_combo.setCurrentText(text)
        self.update_current_entry()

    def add_panel_style_from_top(self):
        text, ok = QInputDialog.getText(self, "Add panel style", "Panel style:")

        if not ok or not text.strip():
            print_log("Add panel style cancelled")
            return

        text = text.strip()
        styles = self.data["settings"].setdefault("panel_styles", [])

        if text not in styles:
            styles.append(text)
            print_log(f"Panel style added: {text}")
        else:
            print_log(f"Panel style already exists: {text}")

        self._refresh_dropdowns()
        self.panel_style_combo.setCurrentText(text)
        self.update_current_entry()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DialogueEditor()
    window.show()
    sys.exit(app.exec())