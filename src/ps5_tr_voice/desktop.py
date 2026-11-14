"""First Windows UI: enumerate audio devices and monitor input level."""

from __future__ import annotations

import queue
import sys

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class AudioMonitorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PS5 TR Voice")
        self.setMinimumWidth(480)
        self._stream: sd.InputStream | None = None
        self._levels: queue.Queue[float] = queue.Queue(maxsize=1)

        root = QWidget()
        layout = QVBoxLayout(root)

        intro = QLabel(
            "İlk kurulum: PS5 sesinin laptop'a geldiği giriş aygıtını seçin.\n"
            "Bu sürüm yalnızca bağlantıyı ve ses seviyesini test eder."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        layout.addWidget(QLabel("Ses giriş aygıtı"))
        self.device_combo = QComboBox()
        self._input_devices = self._load_input_devices()
        for device in self._input_devices:
            self.device_combo.addItem(
                f"{device['name']}  ({device['channels']} kanal)",
                userData=device["index"],
            )
        layout.addWidget(self.device_combo)

        self.level_label = QLabel("Giriş seviyesi: bekleniyor")
        layout.addWidget(self.level_label)

        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setValue(0)
        layout.addWidget(self.level_bar)

        self.start_button = QPushButton("Ses girişini test et")
        self.start_button.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Durdur")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_monitoring)
        layout.addWidget(self.stop_button)

        self.status_label = QLabel("Durum: hazır")
        layout.addWidget(self.status_label)

        self.setCentralWidget(root)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_level)
        self._timer.start(100)

        if not self._input_devices:
            self.start_button.setEnabled(False)
            self.status_label.setText(
                "Durum: ses girişi bulunamadı. USB ses giriş adaptörü gerekebilir."
            )

    @staticmethod
    def _load_input_devices() -> list[dict[str, object]]:
        found: list[dict[str, object]] = []
        for index, device in enumerate(sd.query_devices()):
            channels = int(device.get("max_input_channels", 0))
            if channels > 0:
                found.append(
                    {
                        "index": index,
                        "name": str(device.get("name", f"Input {index}")),
                        "channels": channels,
                        "sample_rate": int(device.get("default_samplerate", 48000)),
                    }
                )
        return found

    def start_monitoring(self) -> None:
        if self._stream is not None:
            return
        device_index = self.device_combo.currentData()
        if device_index is None:
            return

        device = next(
            item for item in self._input_devices if item["index"] == device_index
        )
        channels = min(2, int(device["channels"]))
        samplerate = int(device["sample_rate"])

        def on_audio(indata: np.ndarray, frames: int, timing: object, status: object) -> None:
            del frames, timing, status
            rms = float(np.sqrt(np.mean(np.square(indata, dtype=np.float32))))
            level = min(1.0, rms * 5.0)
            try:
                self._levels.put_nowait(level)
            except queue.Full:
                try:
                    self._levels.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self._levels.put_nowait(level)
                except queue.Full:
                    pass

        try:
            self._stream = sd.InputStream(
                device=int(device_index),
                channels=channels,
                samplerate=samplerate,
                dtype="float32",
                callback=on_audio,
            )
            self._stream.start()
        except Exception as exc:
            self._stream = None
            QMessageBox.critical(self, "Ses girişi açılamadı", str(exc))
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.device_combo.setEnabled(False)
        self.status_label.setText("Durum: ses dinleniyor")

    def _refresh_level(self) -> None:
        try:
            level = self._levels.get_nowait()
        except queue.Empty:
            return
        percent = int(level * 100)
        self.level_bar.setValue(percent)
        self.level_label.setText(f"Giriş seviyesi: %{percent}")

    def stop_monitoring(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        self.start_button.setEnabled(bool(self._input_devices))
        self.stop_button.setEnabled(False)
        self.device_combo.setEnabled(True)
        self.level_bar.setValue(0)
        self.level_label.setText("Giriş seviyesi: bekleniyor")
        self.status_label.setText("Durum: durduruldu")

    def closeEvent(self, event: object) -> None:
        self.stop_monitoring()
        super().closeEvent(event)


def run() -> int:
    app = QApplication(sys.argv)
    window = AudioMonitorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
