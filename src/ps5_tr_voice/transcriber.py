""""Offline English speech recognition using faster-whisper."""

from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable

import numpy as np
from faster_whisper import WhisperModel


class EnglishTranscriber:
    """Consumes mono 16 kHz audio and emits recognized English text."""

    def __init__(
        self,
        on_text: Callable[[str], None],
        on_status: Callable[[str], None],
        model_size: str = "base.en",
    ) -> None:
        self.on_text = on_text
        self.on_status = on_status
        self.model_size = model_size
        # Keep every captured audio block; never discard a block to catch up.
        self.audio_queue: queue.Queue[np.ndarray | None] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._ready = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._ready.clear()
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def feed(self, audio: np.ndarray) -> None:
        if self._stop.is_set() or not self._ready.is_set():
            return
        self.audio_queue.put(np.asarray(audio, dtype=np.float32).reshape(-1).copy())

    def stop(self) -> None:
        self._stop.set()
        self._ready.clear()
        self.audio_queue.put(None)

    def _load_model(self) -> WhisperModel:
        self.on_status("İngilizce modeli hazırlanıyor (base.en / CPU int8)...")
        return WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def _run(self) -> None:
        try:
            self.on_status("İngilizce konuşma modeli yükleniyor; ilk açılışta indirilebilir...")
            model = self._load_model()
            self._ready.set()
            self.on_status("Dinleniyor: ses 3 saniyelik parçalarla işleniyor.")
            pending: list[np.ndarray] = []
            sample_count = 0
            while True:
                try:
                    chunk = self.audio_queue.get(timeout=0.2)
                except queue.Empty:
                    if self._stop.is_set():
                        break
                    continue
                if chunk is None:
                    break
                pending.append(chunk)
                sample_count += len(chunk)
                if sample_count < 3 * 16000:
                    continue
                audio = np.concatenate(pending)
                pending.clear()
                sample_count = 0
                started = time.perf_counter()
                segments, _ = model.transcribe(
                    audio,
                    language="en",
                    beam_size=1,
                    best_of=1,
                    vad_filter=False,
                    condition_on_previous_text=False,
                    temperature=0.0,
                )
                text = " ".join(segment.text.strip() for segment in segments).strip()
                elapsed = time.perf_counter() - started
                queued_seconds = self.audio_queue.qsize() * 0.25
                if text:
                    self.on_text(text)
                self.on_status(
                    f"İşlem: {elapsed:.1f} sn | Bekleyen ses: yaklaşık {queued_seconds:.1f} sn"
                )
            self.on_status("İngilizce konuşma algılama durduruldu.")
        except Exception as exc:
            self.on_status(f"Tanıma hatası: {exc}")
        finally:
            self._ready.clear()
