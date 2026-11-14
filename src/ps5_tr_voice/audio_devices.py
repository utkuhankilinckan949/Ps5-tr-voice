"""Audio device discovery helpers for the Windows prototype."""

from __future__ import annotations

import sounddevice as sd


def list_input_devices() -> list[dict[str, object]]:
    """Return available audio input devices."""
    devices: list[dict[str, object]] = []
    for index, device in enumerate(sd.query_devices()):
        if int(device.get("max_input_channels", 0)) > 0:
            devices.append(
                {
                    "index": index,
                    "name": str(device.get("name", f"Input {index}")),
                    "channels": int(device.get("max_input_channels", 0)),
                    "sample_rate": int(device.get("default_samplerate", 0)),
                }
            )
    return devices


def list_output_devices() -> list[dict[str, object]]:
    """Return available audio output devices."""
    devices: list[dict[str, object]] = []
    for index, device in enumerate(sd.query_devices()):
        if int(device.get("max_output_channels", 0)) > 0:
            devices.append(
                {
                    "index": index,
                    "name": str(device.get("name", f"Output {index}")),
                    "channels": int(device.get("max_output_channels", 0)),
                    "sample_rate": int(device.get("default_samplerate", 0)),
                }
            )
    return devices
