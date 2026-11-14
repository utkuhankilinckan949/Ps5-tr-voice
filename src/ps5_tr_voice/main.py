"""Initial diagnostic entry point.

Run with:
    python -m ps5_tr_voice.main
"""

from __future__ import annotations

from .audio_devices import list_input_devices, list_output_devices


def main() -> None:
    print("\nPS5 TR Voice - ses aygıtı kontrolü\n")
    print("Ses girişleri:")
    inputs = list_input_devices()
    if not inputs:
        print("  Kullanılabilir ses girişi bulunamadı.")
    for device in inputs:
        print(
            f"  [{device['index']}] {device['name']} "
            f"({device['channels']} kanal, {device['sample_rate']} Hz)"
        )

    print("\nSes çıkışları:")
    outputs = list_output_devices()
    if not outputs:
        print("  Kullanılabilir ses çıkışı bulunamadı.")
    for device in outputs:
        print(
            f"  [{device['index']}] {device['name']} "
            f"({device['channels']} kanal, {device['sample_rate']} Hz)"
        )

    print("\nBu ilk tanılama sürümüdür; henüz canlı çeviri yapmaz.")


if __name__ == "__main__":
    main()
