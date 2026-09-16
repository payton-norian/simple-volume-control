#!/usr/bin/env python3

import subprocess
import sys
import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QPushButton
)

def pactl(*args):
    """Выполняет команду pactl и возвращает вывод."""
    result = subprocess.run(
        ["pactl", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    return result.stdout

def get_current_volume(kind):
    """Получает текущую громкость дефолтного устройства (sink или source)."""
    target = "@DEFAULT_SINK@" if kind == "sink" else "@DEFAULT_SOURCE@"
    output = pactl("get-sink-volume" if kind == "sink" else "get-source-volume", target)
    match = re.search(r'(\d+)%', output)
    return int(match.group(1)) if match else 50

def get_mute_status(kind):
    """Проверяет, выключен ли звук (Mute). Возвращает True, если звук выключен."""
    target = "@DEFAULT_SINK@" if kind == "sink" else "@DEFAULT_SOURCE@"
    output = pactl("get-sink-mute" if kind == "sink" else "get-source-mute", target)
    return "yes" in output.lower()

class HugeVolumeMenu(QWidget):
    def __init__(self):
        super().__init__()

        # --- Настройки Окна ---
        self.setWindowTitle("Управление звуком")
        
        # Флаги: делаем окно всплывающим (Popup), убираем рамки, оставляя его независимым
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Главный вертикальный слой с большими отступами
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # Считываем реальные значения из системы
        current_out = get_current_volume("sink")
        current_in = get_current_volume("source")
        is_out_muted = get_mute_status("sink")
        is_in_muted = get_mute_status("source")

        # --- СЕКЦИЯ 1: Вывод (Громкость) ---
        self.output_label = QLabel(f"Громкость: {current_out}%")
        self.output_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # Горизонтальный ряд для слайдера и кнопки Mute
        out_row = QHBoxLayout()
        
        self.output_slider = QSlider(Qt.Horizontal)
        self.output_slider.setMinimumWidth(700)  # Огромная длина слайдера
        self.output_slider.setRange(0, 100)
        self.output_slider.setSingleStep(5)
        self.output_slider.setPageStep(5)
        self.output_slider.setValue(current_out)
        self.output_slider.setStyleSheet("height: 40px;")  # Делаем сам слайдер крупнее
        
        self.output_mute_btn = QPushButton("Mute" if not is_out_muted else "Unmute")
        self.output_mute_btn.setFixedSize(100, 40)
        if is_out_muted:
            self.output_mute_btn.setStyleSheet("background-color: #ff4d4d; color: white;")

        out_row.addWidget(self.output_slider)
        out_row.addWidget(self.output_mute_btn)

        # --- СЕКЦИЯ 2: Ввод (Микрофон) ---
        self.input_label = QLabel(f"Микрофон: {current_in}%")
        self.input_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # Горизонтальный ряд для микрофона
        in_row = QHBoxLayout()
        
        self.input_slider = QSlider(Qt.Horizontal)
        self.input_slider.setMinimumWidth(700)
        self.input_slider.setRange(0, 100)
        self.input_slider.setSingleStep(5)
        self.input_slider.setPageStep(5)
        self.input_slider.setValue(current_in)
        self.input_slider.setStyleSheet("height: 40px;")
        
        self.input_mute_btn = QPushButton("Mute" if not is_in_muted else "Unmute")
        self.input_mute_btn.setFixedSize(100, 40)
        if is_in_muted:
            self.input_mute_btn.setStyleSheet("background-color: #ff4d4d; color: white;")

        in_row.addWidget(self.input_slider)
        in_row.addWidget(self.input_mute_btn)

        # Собираем всё в главный слой
        main_layout.addWidget(self.output_label)
        main_layout.addLayout(out_row)
        main_layout.addWidget(self.input_label)
        main_layout.addLayout(in_row)

        # --- Подключение сигналов (Событий) ---
        self.output_slider.valueChanged.connect(lambda val: self.set_volume("sink", val))
        self.input_slider.valueChanged.connect(lambda val: self.set_volume("source", val))
        
        self.output_mute_btn.clicked.connect(lambda: self.toggle_mute("sink"))
        self.input_mute_btn.clicked.connect(lambda: self.toggle_mute("source"))

        # Позиционируем окно на экране
        self.center_on_screen()

    def center_on_screen(self):
        """Размещает окно в правом нижнем углу экрана (над панелью LXQt)."""
        screen = QApplication.primaryScreen().geometry()
        self.adjustSize()  # Даем Qt посчитать реальный размер гигантского окна
        
        # Вычисляем координаты: правый край минус ширина окна, нижний край минус высота окна
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 60  # Оставляем место под панель задач
        
        self.move(x, y)

    def set_volume(self, kind, value):
        if kind == "sink":
            pactl("set-sink-volume", "@DEFAULT_SINK@", f"{value}%")
            self.output_label.setText(f"Громкость: {value}%")
        else:
            pactl("set-source-volume", "@DEFAULT_SOURCE@", f"{value}%")
            self.input_label.setText(f"Микрофон: {value}%")

    def toggle_mute(self, kind):
        if kind == "sink":
            pactl("set-sink-mute", "@DEFAULT_SINK@", "toggle")
            muted = get_mute_status("sink")
            self.output_mute_btn.setText("Unmute" if muted else "Mute")
            self.output_mute_btn.setStyleSheet("background-color: #ff4d4d; color: white;" if muted else "")
        else:
            pactl("set-source-mute", "@DEFAULT_SOURCE@", "toggle")
            muted = get_mute_status("source")
            self.input_mute_btn.setText("Unmute" if muted else "Mute")
            self.input_mute_btn.setStyleSheet("background-color: #ff4d4d; color: white;" if muted else "")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HugeVolumeMenu()
    window.show()
    sys.exit(app.exec_())

