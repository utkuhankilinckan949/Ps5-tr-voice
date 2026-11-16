"""Background English-to-Turkish translation using a local Argos model."""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable


class TranslationWorker:
    """Translate recognized English phrases locally, without API rate limits."""

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

    def _load_translation_model(self):
        import argostranslate.package as argos_package
        import argostranslate.translate as argos_translate

        installed = argos_translate.get_installed_languages()
        english = next((language for language in installed if language.code == "en"), None)
        turkish = next((language for language in installed if language.code == "tr"), None)

        if english is None or turkish is None or english.get_translation(turkish) is None:
            self.on_status(
                "Çevrimdışı çeviri modeli indiriliyor (yaklaşık 120 MB; yalnızca ilk kullanımda)..."
            )
            argos_package.update_package_index()
            available = argos_package.get_available_packages()
            model = next(
                (
                    item
                    for item in available
                    if item.from_code == "en" and item.to_code == "tr"
                ),
                None,
            )
            if model is None:
                raise RuntimeError("Argos paket listesinde İngilizce-Türkçe modeli bulunamadı.")

            model_path = model.download()
            self.on_status("İngilizce-Türkçe modeli kuruluyor...")
            argos_package.install_from_path(model_path)

            installed = argos_translate.get_installed_languages()
            english = next((language for language in installed if language.code == "en"), None)
            turkish = next((language for language in installed if language.code == "tr"), None)

        if english is None or turkish is None:
            raise RuntimeError("İngilizce veya Türkçe dil modeli yüklenemedi.")

        translation = english.get_translation(turkish)
        if translation is None:
            raise RuntimeError("İngilizce-Türkçe çeviri bağlantısı oluşturulamadı.")
        return translation

    def _run(self) -> None:
        try:
            translator = self._load_translation_model()
        except Exception as exc:
            self.on_status(f"Çevrimdışı çeviri hazırlanamadı: {exc}")
            return

        self.on_status("Çevrimdışı İngilizce-Türkçe çeviri hazır.")
        while not self._stop.is_set():
            item = self._queue.get()
            if item is None:
                break
            try:
                translated = translator.translate(item)
                if translated:
                    self.on_translation(translated)
                else:
                    self.on_status("Çeviri boş sonuç verdi; sonraki cümle denenecek.")
            except Exception as exc:
                self.on_status(f"Yerel çeviri hatası: {exc}")

        self.on_status("Çeviri durduruldu.")
