"""Offline English speech recognition using faster-whisper."""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable

import numpy as np
from faster_whisper import WhisperModel


class EnglishTranscriber:
    """Consumes mono 16 kHz audio chunks and emits recognized English text."""

    def __init__(
        self,
        on_text: Callable[[str], None],
        on_status: Callable[[str], None],
        model_size: str = "base.en",
    ) -> None:
        self.on_text = on_text
        self.on_status = on_status
        self.model_size = model_size
        # A short queue prevents old audio accumulating when inference is slower.
        self.audio_queue: queue.Queue[np.ndarray | None] = queue.Queue(maxsize=12)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._overflow_reported = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._ready.clear()
        self._overflow_reported = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def feed(self, audio: np.ndarray) -> None:
        # Do not buffer audio while the model is downloading/loading.
        if self._stop.is_set() or not self._ready.is_set():
            return
        chunk = np.asarray(audio, dtype=np.float32).reshape(-1).copy()
        try:
            self.audio_queue.put_nowait(chunk)
        except queue.Full:
            # Drop the oldest chunk rather than building an ever-growing delay.
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.audio_queue.put_nowait(chunk)
            except queue.Full:
                pass
            if not self._overflow_reported:
                self._overflow_reported = True
                self.on_status(
                    "Tanıma hızı düşük; gecikmeyi azaltmak için eski ses parçaları atlanıyor."
                )

    def stop(self) -> None:
        self._stop.set()
        self._ready.clear()
        try:
            self.audio_queue.put_nowait(None)
        except queue.Full:
            pass

    def _run(self) -> None:
        try:
            self.on_status("Hafif İngilizce modeli hazırlanıyor (ilk açılışta indirilir)...")
            model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            self._ready.set()
            self.on_status("Dinleniyor: daha doğru tanıma için biraz daha uzun ses parçaları işleniyor.")
            pending: list[np.ndarray] = []
            sample_count = 0
            while not self._stop.is_set():
                try:
                    chunk = self.audio_queue.get(timeout=0.25)
                except queue.Empty:
                    continue
                if chunk is None:
                    break
                pending.append(chunk)
                sample_count += len(chunk)
                if sample_count < 5 * 16000:
                    continue
                audio = np.concatenate(pending)
                pending.clear()
                sample_count = 0
                segments, _ = model.transcribe(
                    audio,
                    language="en",
                    beam_size=3,
                    vad_filter=True,
                    condition_on_previous_text=False,
                )
                text = " ".join(segment.text.strip() for segment in segments).strip()
                if text:
                    self.on_text(text)
            self.on_status("İngilizce konuşma algılama durduruldu.")
        except Exception as exc:
            self.on_status(f"Tanıma hatası: {exc}")
        finally:
            self._ready.clear()
