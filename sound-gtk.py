#!/usr/bin/env python3

import subprocess
import re
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


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
    """Получает текущую громкость дефолтного sink/source."""
    target = "@DEFAULT_SINK@" if kind == "sink" else "@DEFAULT_SOURCE@"
    command = "get-sink-volume" if kind == "sink" else "get-source-volume"
    output = pactl(command, target)
    match = re.search(r'(\d+)%', output)
    return int(match.group(1)) if match else 50


def get_mute_status(kind):
    """Возвращает True, если устройство выключено."""
    target = "@DEFAULT_SINK@" if kind == "sink" else "@DEFAULT_SOURCE@"
    command = "get-sink-mute" if kind == "sink" else "get-source-mute"
    output = pactl(command, target)
    return "yes" in output.lower()


class HugeVolumeMenu(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Управление звуком")

        # Аналог Qt.Popup + FramelessWindowHint.
        self.set_decorated(False)
        self.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        self.set_border_width(30)

        # Основной вертикальный контейнер.
        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=25
        )
        self.add(main_box)

        current_out = get_current_volume("sink")
        current_in = get_current_volume("source")
        is_out_muted = get_mute_status("sink")
        is_in_muted = get_mute_status("source")

        # ---------- Вывод ----------
        self.output_label = Gtk.Label(
            label=f"Громкость: {current_out}%"
        )
        self.output_label.set_halign(Gtk.Align.START)

        out_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=15
        )

        self.output_slider = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 5
        )
        self.output_slider.set_value(current_out)
        self.output_slider.set_digits(0)
        self.output_slider.set_hexpand(True)
        self.output_slider.set_size_request(700, 40)
        self.output_slider.connect(
            "value-changed", self.on_output_changed
        )

        self.output_mute_btn = Gtk.Button(
            label="Unmute" if is_out_muted else "Mute"
        )
        self.output_mute_btn.set_size_request(100, 40)
        self.output_mute_btn.connect(
            "clicked", self.on_output_mute
        )

        out_row.pack_start(self.output_slider, True, True, 0)
        out_row.pack_start(self.output_mute_btn, False, False, 0)

        # ---------- Микрофон ----------
        self.input_label = Gtk.Label(
            label=f"Микрофон: {current_in}%"
        )
        self.input_label.set_halign(Gtk.Align.START)

        in_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=15
        )

        self.input_slider = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 5
        )
        self.input_slider.set_value(current_in)
        self.input_slider.set_digits(0)
        self.input_slider.set_hexpand(True)
        self.input_slider.set_size_request(700, 40)
        self.input_slider.connect(
            "value-changed", self.on_input_changed
        )

        self.input_mute_btn = Gtk.Button(
            label="Unmute" if is_in_muted else "Mute"
        )
        self.input_mute_btn.set_size_request(100, 40)
        self.input_mute_btn.connect(
            "clicked", self.on_input_mute
        )

        in_row.pack_start(self.input_slider, True, True, 0)
        in_row.pack_start(self.input_mute_btn, False, False, 0)

        main_box.pack_start(self.output_label, False, False, 0)
        main_box.pack_start(out_row, False, False, 0)
        main_box.pack_start(self.input_label, False, False, 0)
        main_box.pack_start(in_row, False, False, 0)

        self.connect("focus-out-event", self.on_focus_out)

        self.show_all()

    def on_output_changed(self, slider):
        value = int(round(slider.get_value()))
        pactl("set-sink-volume", "@DEFAULT_SINK@", f"{value}%")
        self.output_label.set_text(f"Громкость: {value}%")

    def on_input_changed(self, slider):
        value = int(round(slider.get_value()))
        pactl("set-source-volume", "@DEFAULT_SOURCE@", f"{value}%")
        self.input_label.set_text(f"Микрофон: {value}%")

    def on_output_mute(self, button):
        pactl("set-sink-mute", "@DEFAULT_SINK@", "toggle")
        muted = get_mute_status("sink")
        button.set_label("Unmute" if muted else "Mute")

    def on_input_mute(self, button):
        pactl("set-source-mute", "@DEFAULT_SOURCE@", "toggle")
        muted = get_mute_status("source")
        button.set_label("Unmute" if muted else "Mute")

    def on_focus_out(self, *args):
        self.destroy()
        Gtk.main_quit()
        return False


if __name__ == "__main__":
    Gtk.init(None)
    window = HugeVolumeMenu()
    Gtk.main()
