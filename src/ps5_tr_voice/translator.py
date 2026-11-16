"""Background English-to-Turkish translation worker."""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable

from deep_translator import GoogleTranslator


class TranslationWorker:
    """Translate recognized English phrases without blocking audio recognition."""

    def __init__(
        self,
        on_translation: Callable[[str], None],
        on_status: Callable[[str], None],
    ) -> None:
        self.on_translation = on_translation
        self.on_status = on_status
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def submit(self, text: str) -> None:
        cleaned = text.strip()
        if cleaned and not self._stop.is_set():
            self._queue.put(cleaned)

    def stop(self) -> None:
        self._stop.set()
        self._queue.put(None)

    def _run(self) -> None:
        translator = GoogleTranslator(source="en", target="tr")
        self.on_status("İngilizce-Türkçe çeviri hizmeti hazır.")
        while True:
            item = self._queue.get()
            if item is None:
                break
            try:
                translated = translator.translate(item)
                if translated:
                    self.on_translation(translated)
                else:
                    self.on_status("Çeviri boş yanıt verdi; sonraki cümle denenecek.")
            except Exception as exc:
                self.on_status(f"Çeviri bağlantı hatası: {exc}")
        self.on_status("Çeviri durduruldu.")
