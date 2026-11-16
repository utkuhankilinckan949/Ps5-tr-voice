"""Windows UI for audio monitoring, English transcription and Turkish translation."""
from __future__ import annotations
import queue
import sys
import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QMainWindow, QMessageBox, QPushButton, QProgressBar, QTextEdit, QVBoxLayout, QWidget
from .transcriber import EnglishTranscriber
from .translator import TranslationWorker

class UiSignals(QObject):
    text = Signal(str)
    translation = Signal(str)
    status = Signal(str)

class AudioMonitorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PS5 TR Voice")
        self.setMinimumSize(600, 680)
        self._stream: sd.InputStream | None = None
        self._levels: queue.Queue[float] = queue.Queue(maxsize=1)
        self._transcriber: EnglishTranscriber | None = None
        self._translator: TranslationWorker | None = None
        self._signals = UiSignals()
        self._signals.text.connect(self._append_text)
        self._signals.translation.connect(self._append_translation)
        self._signals.status.connect(self._set_status)
        root = QWidget()
        layout = QVBoxLayout(root)
        intro = QLabel("Ses girişini dinler, İngilizce konuşmayı metne dönüştürür ve bilgisayardaki çevrimdışı Argos modeliyle Türkçeye aktarır. Bu aşamada henüz seslendirme yoktur.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        layout.addWidget(QLabel("Ses giriş aygıtı"))
        self.device_combo = QComboBox()
        self._input_devices = self._load_input_devices()
        for device in self._input_devices:
            self.device_combo.addItem(f"{device['name']} ({device['channels']} kanal)", userData=device["index"])
        layout.addWidget(self.device_combo)
        self.level_label = QLabel("Giriş seviyesi: bekleniyor")
        layout.addWidget(self.level_label)
        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        layout.addWidget(self.level_bar)
        self.start_button = QPushButton("Dinlemeyi ve çeviriyi başlat")
        self.start_button.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_button)
        self.stop_button = QPushButton("Durdur")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_monitoring)
        layout.addWidget(self.stop_button)
        layout.addWidget(QLabel("Algılanan İngilizce metin"))
        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        layout.addWidget(self.transcript)
        layout.addWidget(QLabel("Türkçe çeviri"))
        self.translation_view = QTextEdit()
        self.translation_view.setReadOnly(True)
        layout.addWidget(self.translation_view)
        self.status_label = QLabel("Durum: hazır")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.setCentralWidget(root)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_level)
        self._timer.start(100)
        if not self._input_devices:
            self.start_button.setEnabled(False)
            self.status_label.setText("Ses girişi bulunamadı. USB ses giriş aygıtı gerekebilir.")

    @staticmethod
    def _load_input_devices() -> list[dict[str, object]]:
        found = []
        for index, device in enumerate(sd.query_devices()):
            channels = int(device.get("max_input_channels", 0))
            if channels > 0:
                found.append({"index": index, "name": str(device.get("name", f"Input {index}")), "channels": channels, "sample_rate": int(device.get("default_samplerate", 48000))})
        return found

    def start_monitoring(self) -> None:
        if self._stream is not None:
            return
        device_index = self.device_combo.currentData()
        if device_index is None:
            return
        device = next(item for item in self._input_devices if item["index"] == device_index)
        channels = min(2, int(device["channels"]))
        samplerate = int(device["sample_rate"])
        self._translator = TranslationWorker(
            on_translation=lambda value: self._signals.translation.emit(value),
            on_status=lambda value: self._signals.status.emit(value))
        self._translator.start()
        self._transcriber = EnglishTranscriber(
            on_text=self._on_recognized_text,
            on_status=lambda value: self._signals.status.emit(value))
        self._transcriber.start()

        def on_audio(indata: np.ndarray, frames: int, timing: object, status: object) -> None:
            del frames, timing, status
            mono = np.mean(indata, axis=1) if indata.ndim > 1 else indata
            rms = float(np.sqrt(np.mean(np.square(mono, dtype=np.float32))))
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
            if self._transcriber is not None:
                target_length = int(len(mono) * 16000 / samplerate)
                if target_length > 0:
                    positions = np.linspace(0, len(mono) - 1, target_length)
                    resampled = np.interp(positions, np.arange(len(mono)), mono).astype(np.float32)
                    self._transcriber.feed(resampled)
        try:
            self._stream = sd.InputStream(device=int(device_index), channels=channels, samplerate=samplerate, dtype="float32", callback=on_audio, blocksize=int(samplerate * 0.25))
            self._stream.start()
        except Exception as exc:
            self._stream = None
            if self._transcriber:
                self._transcriber.stop()
                self._transcriber = None
            if self._translator:
                self._translator.stop()
                self._translator = None
            QMessageBox.critical(self, "Ses girişi açılamadı", str(exc))
            return
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.device_combo.setEnabled(False)
        self._set_status("Modeller hazırlanıyor; ilk açılışta bekleyin.")

    def _on_recognized_text(self, value: str) -> None:
        self._signals.text.emit(value)
        if self._translator is not None:
            self._translator.submit(value)

    def _append_text(self, value: str) -> None:
        self.transcript.append(value)

    def _append_translation(self, value: str) -> None:
        self.translation_view.append(value)

    def _set_status(self, value: str) -> None:
        self.status_label.setText(f"Durum: {value}")

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
        if self._transcriber is not None:
            self._transcriber.stop()
            self._transcriber = None
        if self._translator is not None:
            self._translator.stop()
            self._translator = None
        self.start_button.setEnabled(bool(self._input_devices))
        self.stop_button.setEnabled(False)
        self.device_combo.setEnabled(True)
        self.level_bar.setValue(0)
        self.level_label.setText("Giriş seviyesi: bekleniyor")

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
