# ESP template

A general-purpose ESP-IDF starter based on the development workflow from
`deye-inverter-esp`. The application logs `Hello world` once per second.
It has no Matter/HomeKit, Modbus, or inverter configuration.

Defaults: **ESP32-C3**, 4 MB flash, USB Serial/JTAG console, ESP-IDF **v5.4.1**,
and Python **3.11.13**. The CLI supports native Windows, macOS, and Linux workflows.

## Getting started

Install Git and uv, then run from the project root:

```sh
uv run fw bootstrap
uv run fw build
uv run fw ports
uv run fw dev --port COM3
```

Replace `COM3` with the actual port. On macOS/Linux, use `/dev/cu.usbmodem*` or
`/dev/ttyACM0`. `dev` builds, flashes, and opens the monitor. Exit with **Ctrl + ]**.

Linux requires a system compiler, CMake, Ninja, flex, bison, gperf, and development
packages for libffi, OpenSSL, and libusb. Bootstrap downloads the SDK and toolchain.
ESP-Matter, GN, WSL, and Docker are not required. Keep project and SDK paths free
of whitespace for compatibility with the selected workflow.

## Commands

| Command | Purpose |
| --- | --- |
| `uv run fw bootstrap` | Install the SDK and toolchain |
| `uv run fw build` | Build firmware |
| `uv run fw test` | Test flash tooling without accessing hardware |
| `uv run fw menuconfig` | Configure ESP-IDF |
| `uv run fw ports` | List serial ports |
| `uv run fw flash --port COM3` | Flash an existing build |
| `uv run fw deploy --port COM3` | Build and flash |
| `uv run fw dev --port COM3` | Build, flash, and monitor |
| `uv run fw monitor --port COM3` | Monitor serial output at 115200 baud |
| `uv run fw clean` | Clean compilation output |

`uv run fw erase-flash --port COM3` erases all flash contents. Use it only when
you intend to delete stored data.

The SDK defaults to `.tools/sdk`. To reuse an existing SDK of the same version,
set `ESP_SDK_ROOT` to the directory containing `esp-idf/` and `tools/`.

Build output defaults to `build/esp32-c3/native-<platform>-<architecture>/`.
Override it with `--build-dir <path>` and use the same path for build, flash, and
monitor commands. The firmware is named `esp32-c3.bin`. Flashing reads offsets
and binary paths from `flasher_args.json`, including the bootloader and partition
table.

## Starting a new project

1. Copy the template source into a new directory. Exclude `.venv/`, `.tools/`,
   `.cache/`, `build/`, `*.egg-info/`, and `.git/` if present.
2. Update `name` in `pyproject.toml` for the project, keeping the `fw` entry point.
3. Implement the application in `main/app_main.cpp`, add sources and dependencies
   to `main/CMakeLists.txt`, and set defaults in `sdkconfig.defaults`.
4. Bootstrap, build, and flash as above. Use `ESP_SDK_ROOT` to share an SDK.

`targets.json` is shared by the CLI and CI. Only ESP32-C3 is currently configured.
When changing boards or chips, review the target, flash size, and console settings
and verify them on hardware. This template uses the default ESP-IDF partition
table and does not configure OTA.

## CI

GitHub Actions runs tooling tests and native builds on Windows, Ubuntu, Intel
macOS, and Apple Silicon. The Ubuntu job uploads the `esp32-c3` artifact containing
the application, ELF, bootloader, partition table, sdkconfig, and flash manifest.
Preserve the directory structure when extracting it:

```sh
uv run fw flash --port COM3 --build-dir path/to/extracted/artifact
```

The workflow does not create GitHub Releases. CI and on-board runtime results
must be verified separately from local builds.
