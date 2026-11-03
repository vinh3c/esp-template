# ESP template

Template ESP-IDF thuần để bắt đầu project mới, tham khảo workflow của
`deye-inverter-esp`. Không có Matter/HomeKit, Modbus hoặc cấu hình inverter.
Firmware chỉ log `Hello world` mỗi giây.

Mặc định: **ESP32-C3**, flash 4 MB, console USB Serial/JTAG, ESP-IDF **v5.4.1**,
Python **3.11.13**. Bộ lệnh dùng chung cho Windows, macOS và Linux.

## Bắt đầu

Cài Git và uv, sau đó chạy tại thư mục project:

```sh
uv run fw bootstrap
uv run fw build
uv run fw ports
uv run fw dev --port COM3
```

Thay `COM3` bằng cổng thực tế; macOS/Linux dùng `/dev/cu.usbmodem*` hoặc
`/dev/ttyACM0`. `dev` build, flash rồi mở monitor. Thoát monitor bằng **Ctrl + ]**.

Trên Linux cần có compiler hệ thống, CMake, Ninja, flex, bison, gperf,
libffi, OpenSSL và libusb development packages. Bootstrap tải SDK và toolchain;
không cần cài ESP-Matter, GN, WSL hoặc Docker. Đặt đường dẫn project và SDK
không có khoảng trắng để tương thích workflow đã chọn.

## Các lệnh

| Lệnh | Chức năng |
| --- | --- |
| `uv run fw bootstrap` | Cài SDK và toolchain |
| `uv run fw build` | Build firmware |
| `uv run fw test` | Kiểm tra công cụ flash, không truy cập phần cứng |
| `uv run fw menuconfig` | Chỉnh cấu hình ESP-IDF |
| `uv run fw ports` | Liệt kê cổng serial |
| `uv run fw flash --port COM3` | Flash bản đã build |
| `uv run fw deploy --port COM3` | Build rồi flash |
| `uv run fw dev --port COM3` | Build, flash và monitor |
| `uv run fw monitor --port COM3` | Xem log ở 115200 baud |
| `uv run fw clean` | Dọn kết quả biên dịch |

`erase-flash --port COM3` xóa toàn bộ flash; chỉ dùng khi chủ động muốn xóa dữ liệu.

SDK mặc định ở `.tools/sdk`. Có thể dùng SDK cùng phiên bản đã cài bằng biến
`ESP_SDK_ROOT`, trỏ đến thư mục chứa `esp-idf/` và `tools/`.

Build mặc định ở `build/esp32-c3/native-<platform>-<architecture>/`.
Dùng `--build-dir <path>` để đổi; truyền cùng đường dẫn khi build/flash/monitor.
Firmware có tên `esp32-c3.bin`. Flash đọc offsets và các binary từ
`flasher_args.json`, bao gồm bootloader và partition table.

## Tạo project mới

1. Copy các file nguồn của template sang thư mục mới; bỏ `.venv/`, `.tools/`,
   `.cache/`, `build/`, `*.egg-info/` và `.git/` nếu có.
2. Đổi `name` trong `pyproject.toml` theo project; giữ entry point `fw`.
3. Viết ứng dụng trong `main/app_main.cpp`, thêm source/dependency tại
   `main/CMakeLists.txt` và cấu hình mặc định tại `sdkconfig.defaults`.
4. Chạy bootstrap, build và flash như trên. Có thể chia sẻ SDK bằng `ESP_SDK_ROOT`.

`targets.json` là nguồn target dùng chung cho CLI và CI; hiện chỉ cấu hình ESP32-C3.
Khi chuyển board/chip cần cập nhật target, flash size, console và kiểm tra thực tế.
Template dùng partition table mặc định của ESP-IDF, chưa cấu hình OTA.

## CI

GitHub Actions chạy test và build native trên Windows, Ubuntu, Intel macOS và
Apple Silicon. Job Ubuntu đóng gói artifact `esp32-c3` gồm app, ELF, bootloader,
partition table, sdkconfig và flash manifest; giữ cấu trúc khi tải về để flash:

```sh
uv run fw flash --port COM3 --build-dir path/to/extracted/artifact
```

Không tự tạo GitHub Release. CI và runtime trên board cần được kiểm tra riêng
với kết quả build local.
