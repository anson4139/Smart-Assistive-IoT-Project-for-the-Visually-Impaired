from __future__ import annotations

from typing import Sequence


def _format_versions(core: object, device: str) -> str:
    try:
        versions = core.get_versions(device)
    except Exception as exc:
        return f"{device}: not available ({exc})"
    return f"{device}: {versions.get(device)}"


def main() -> int:
    print("OpenVINO verification tool")
    try:
        from openvino import Core, get_version  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment issue
        print("`openvino` is not installed. Run `python -m pip install openvino==2025.3.0`.")
        print(str(exc))
        return 1

    print(f"Installed OpenVINO: {get_version()}\n")

    core = Core()
    devices = list(core.available_devices)
    if not devices:
        print("No devices detected. Check your OpenVINO installation and hardware.")
    else:
        print("Available devices:", ", ".join(devices))

    targets: Sequence[str] = ["CPU", "GPU", "MYRIAD"]
    for device in targets:
        if device not in devices:
            print(f"{device}: not detected (skipped)")
            continue
        print(_format_versions(core, device))

    if "MYRIAD" not in devices:
        print(
            "\nTo enable NCS2, ensure the MYRIAD device is connected, install the OpenVINO VPU plugin,"
            " and re-run this script."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
