"""Manifest flashing checks; never opens serial hardware."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import project


class FlashTests(unittest.TestCase):
    def test_wrong_target_is_rejected_before_opening_device(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "flasher_args.json").write_text(json.dumps({
                "write_flash_args": [], "flash_files": {},
                "extra_esptool_args": {"chip": "esp32s3"},
            }))
            with patch.object(project, "serial_command") as serial:
                with self.assertRaisesRegex(RuntimeError, "Firmware is for esp32s3"):
                    project.flash(root, "COM99", 460800, target="esp32-c3")
                serial.assert_not_called()

    def test_flash_uses_manifest_offsets_and_options(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bootloader").mkdir()
            (root / "bootloader/bootloader.bin").write_bytes(b"boot")
            (root / "app.bin").write_bytes(b"app")
            (root / "flasher_args.json").write_text(json.dumps({
                "write_flash_args": ["--flash_mode", "dio", "--flash_size", "4MB"],
                "flash_files": {"0x0": "bootloader/bootloader.bin", "0x123000": "app.bin"},
            }))
            with patch.object(project, "serial_command") as serial:
                project.flash(root, "COM99", 460800)
            module, args = serial.call_args.args
            self.assertEqual(module, "esptool")
            self.assertIn("COM99", args)
            self.assertEqual(args[args.index("0x123000") + 1], str((root / "app.bin").resolve()))
            self.assertEqual(args[args.index("--flash_mode") + 1], "dio")

    def test_missing_binary_fails_before_opening_device(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "flasher_args.json").write_text(json.dumps({
                "write_flash_args": [], "flash_files": {"0x0": "missing.bin"},
            }))
            with patch.object(project, "serial_command") as serial:
                with self.assertRaisesRegex(RuntimeError, "Missing or invalid"):
                    project.flash(root, "COM99", 460800)
                serial.assert_not_called()

    def test_manifest_cannot_flash_a_file_outside_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "outside.bin").write_bytes(b"outside")
            build = root / "artifact"
            build.mkdir()
            (build / "flasher_args.json").write_text(json.dumps({
                "write_flash_args": [], "flash_files": {"0x0": "../outside.bin"},
            }))
            with patch.object(project, "serial_command") as serial:
                with self.assertRaisesRegex(RuntimeError, "Missing or invalid"):
                    project.flash(build, "COM99", 460800)
                serial.assert_not_called()


if __name__ == "__main__":
    unittest.main()
