# Working on esp-template

- Communicate with the user in Vietnamese. Keep this file in English.
- This is a general-purpose ESP-IDF starter. The default application only logs
  `Hello world` once per second. Do not add Matter/HomeKit, inverter logic,
  networking, credentials, or hardware features without a request.
- Use native Windows, macOS, and Linux workflows and short `uv run fw ...` commands.
  No WSL or Docker requirement. Preserve ESP-IDF v5.4.1 and Python 3.11.13 unless
  an upgrade is requested or required for the task.
- `main/app_main.cpp` is the app; `main/CMakeLists.txt` lists dependencies.
  `sdkconfig.defaults` holds generic defaults. `targets.json` is shared by CLI/CI;
  the configured default is ESP32-C3, 4 MB flash, USB Serial/JTAG console.
- `scripts/project.py` handles SDK bootstrap, build/menuconfig, serial and flash.
  The SDK is in `.tools/sdk` or `ESP_SDK_ROOT`; do not depend on sibling projects.
  Use the base Python interpreter to create the SDK venv, not a nested project venv.
- Build output is `build/<target>/native-<platform>-<architecture>/` by default.
  Never mix CMake caches between hosts or targets. Firmware names follow targets.
- Flash using `flasher_args.json` offsets and binaries. Preserve artifact layout.
  Do not flash/erase hardware, push, tag, or publish without relevant authorization.
- For firmware changes, build the configured target. For tooling changes, run
  `uv run fw test` and affected commands. Do not add trivial tests for log wording.
  Report build, CI, flash, and runtime verification separately.
- CI builds on Windows, Ubuntu, Intel macOS and Apple Silicon; only Ubuntu uploads
  the flashable artifact named after its target. Do not claim unobserved CI success.
- Keep generated output, SDKs, virtualenvs, caches and local secrets out of source.
