"""Low-latency offline English speech recognition using faster-whisper."""

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
        model_size: str = "tiny.en",
    ) -> None:
        self.on_text = on_text
        self.on_status = on_status
        self.model_size = model_size
        # Never discard captured audio: an unbounded queue preserves every chunk.
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
        # Use CPU int8 for reliability on Windows. CUDA may appear available
        # while its cuBLAS/cuDNN runtime DLLs are missing, causing inference to fail.
        self.on_status("Kararlı CPU modu hazırlanıyor (int8)...")
        return WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def _run(self) -> None:
        try:
            self.on_status("Hızlı İngilizce modeli hazırlanıyor (ilk açılışta indirilir)...")
            model = self._load_model()
            self._ready.set()
            self.on_status("Dinleniyor: ses alınıyor, 3 saniyelik parçalar tanınıyor.")
            pending: list[np.ndarray] = []
            sample_count = 0
            while not self._stop.is_set():
                try:
                    chunk = self.audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                if chunk is None:
                    break
                pending.append(chunk)
                sample_count += len(chunk)
                # Process every ~2 seconds instead of waiting five seconds.
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
                )
                text = " ".join(segment.text.strip() for segment in segments).strip()
                elapsed = time.perf_counter() - started
                if text:
                    self.on_text(text)
                    self.on_status(f"Metin algılandı ({elapsed:.1f} sn).")
                else:
                    self.on_status(f"Ses işlendi ({elapsed:.1f} sn); bu parçada anlaşılır konuşma bulunamadı.")
                if elapsed > 3.0:
                    self.on_status(
                        f"Tanıma {elapsed:.1f} saniye sürdü; ses kaydı korunuyor, "
                        "işleme kuyruğu birikebilir."
                    )
            self.on_status("İngilizce konuşma algılama durduruldu.")
        except Exception as exc:
            self.on_status(f"Tanıma hatası: {exc}")
        finally:
            self._ready.clear()
