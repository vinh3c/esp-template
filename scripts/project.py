#!/usr/bin/env python3
"""Native ESP-IDF development commands. Requires Python 3.11 and Git."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
# uv runs this CLI in the project's venv. IDF must create its SDK venv using
# the underlying interpreter, rather than nesting it inside the project venv.
BASE_PYTHON = getattr(sys, "_base_executable", sys.executable)
TARGETS = json.loads((ROOT / "targets.json").read_text(encoding="utf-8"))
DEFAULT_TARGET = "esp32-c3"
IDF_VERSION = "v5.4.1"
WINDOWS = sys.platform == "win32"
SDK = Path(os.environ.get("ESP_SDK_ROOT", ROOT / ".tools" / "sdk")).expanduser().resolve()
IDF = SDK / "esp-idf"
TOOLS = SDK / "tools"
VENV = TOOLS / "python_env" / "idf5.4_py3.11_env"
PYTHON = VENV / ("Scripts/python.exe" if WINDOWS else "bin/python")
BUILD = ROOT / "build" / f"native-{sys.platform}-{platform.machine().lower()}"


def run(args, *, cwd=ROOT, env=None, capture=False):
    args = [str(arg) for arg in args]
    if env is not None and not os.path.isabs(args[0]):
        # Windows CreateProcess does not search the PATH passed through env.
        args[0] = shutil.which(args[0], path=env["PATH"]) or args[0]
    if not capture:
        print("+ " + subprocess.list2cmdline(args), flush=True)
    return subprocess.run(args, cwd=cwd, env=env, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def base_env():
    env = os.environ.copy()
    # Ignore an SDK previously exported by the user's shell.
    for key in ("IDF_PYTHON_ENV_PATH", "IDF_PATH", "ESP_MATTER_PATH", "VIRTUAL_ENV"):
        env.pop(key, None)
    env.update(IDF_PATH=str(IDF), IDF_TOOLS_PATH=str(TOOLS), PYTHONUTF8="1")
    # Per-process Git options also apply to recursively cloned submodules.
    index = int(env.get("GIT_CONFIG_COUNT", "0"))
    for key, value in (("core.longpaths", "true"), ("core.autocrlf", "false")):
        env[f"GIT_CONFIG_KEY_{index}"] = key
        env[f"GIT_CONFIG_VALUE_{index}"] = value
        index += 1
    env["GIT_CONFIG_COUNT"] = str(index)
    return env


def checkout(path, url, revision, env):
    if not (path / ".git").exists():
        path.mkdir(parents=True, exist_ok=True)
        run(["git", "init", path], env=env)
        run(["git", "-C", path, "remote", "add", "origin", url], env=env)
    head = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                          env=env, text=True, capture_output=True)
    expected = subprocess.run(["git", "-C", str(path), "rev-parse", revision + "^{commit}"],
                              env=env, text=True, capture_output=True)
    if expected.returncode != 0:
        ref = f"refs/tags/{revision}:refs/tags/{revision}" if revision.startswith("v") else revision
        run(["git", "-C", path, "fetch", "--depth", "1", "origin", ref], env=env)
        expected = subprocess.run(["git", "-C", str(path), "rev-parse", revision + "^{commit}"],
                                  env=env, text=True, capture_output=True)
    if head.returncode == 0:
        if expected.returncode != 0 or head.stdout.strip() != expected.stdout.strip():
            raise RuntimeError(f"Unexpected SDK revision in {path}; use a separate ESP_SDK_ROOT.")
        return
    run(["git", "-C", path, "checkout", "--detach", revision], env=env)


def bootstrap(target=DEFAULT_TARGET):
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError("Use Python 3.11: uv run fw bootstrap")
    for path in (ROOT, SDK):
        if any(c.isspace() for c in str(path)):
            raise RuntimeError(f"This SDK requires paths without whitespace: {path}")
    sdk_tools = ["required", "cmake"]
    if sys.platform == "linux" and platform.machine().lower() in ("arm64", "aarch64"):
        if not shutil.which("ninja"):
            raise RuntimeError("Install native Ninja first (for example: sudo apt-get install ninja-build).")
    else:
        sdk_tools.append("ninja")
    env = base_env()
    checkout(IDF, "https://github.com/espressif/esp-idf.git", IDF_VERSION, env)
    run(["git", "-C", IDF, "submodule", "update", "--init", "--recursive", "--depth", "1", "--jobs", "8"], env=env)
    run([BASE_PYTHON, IDF / "tools/idf_tools.py", "install", "--targets", TARGETS[target]["idf_target"], *sdk_tools], env=env)
    run([BASE_PYTHON, IDF / "tools/idf_tools.py", "install-python-env", "--features", "core"], env=env)
    print(f"Native SDK ready. Run: uv run fw build --target {target}")


def build_env():
    if not PYTHON.exists() or not (IDF / "tools/idf.py").is_file():
        raise RuntimeError("SDK missing. Run: uv run fw bootstrap")
    env = base_env()
    exports = run([BASE_PYTHON, IDF / "tools/idf_tools.py", "export", "--format", "key-value"], env=env, capture=True)
    for line in exports.splitlines():
        key, sep, value = line.partition("=")
        if sep and (key.isidentifier()):
            env[key] = value.replace("%PATH%", env["PATH"]).replace("$PATH", env["PATH"])
    env["PATH"] = os.pathsep.join([str(PYTHON.parent), env["PATH"]])
    env["VIRTUAL_ENV"] = str(VENV)
    env.setdefault("CCACHE_DIR", str(ROOT / ".cache/ccache"))
    return env


def idf(action, build_dir, target=DEFAULT_TARGET):
    build_dir.mkdir(parents=True, exist_ok=True)
    run([PYTHON, IDF / "tools/idf.py", "-B", build_dir,
         "-D", f"IDF_TARGET={TARGETS[target]['idf_target']}",
         "-D", f"SDKCONFIG={(build_dir / 'sdkconfig').as_posix()}",
         "-D", f"Python3_EXECUTABLE={PYTHON.as_posix()}", action], env=build_env())


def serial_command(module, args):
    # Also works on a machine with downloaded CI artifacts and no SDK.
    run(["uv", "run", "--isolated", "--no-project", "--python", "3.11",
         "--with", "esptool==4.8.1", "--with", "pyserial==3.5", "python", "-m", module, *args])


def flash(build_dir, port, baud, target=DEFAULT_TARGET):
    manifest = build_dir / "flasher_args.json"
    if not manifest.is_file():
        raise RuntimeError(f"No firmware in {build_dir}. Build first or use --build-dir with extracted CI artifacts.")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    chip = TARGETS[target]["idf_target"]
    manifest_chip = data.get("extra_esptool_args", {}).get("chip", chip)
    if manifest_chip != chip:
        raise RuntimeError(f"Firmware is for {manifest_chip}, but --target selects {target}.")
    args = ["--chip", chip, "--port", port, "--baud", str(baud),
            "--before", "default_reset", "--after", "hard_reset", "write_flash",
            *data["write_flash_args"]]
    for offset, name in data["flash_files"].items():
        binary = (build_dir / name).resolve()
        if not binary.is_relative_to(build_dir.resolve()) or not binary.is_file():
            raise RuntimeError(f"Missing or invalid flash binary: {name}")
        args.extend([offset, str(binary)])
    serial_command("esptool", args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["targets", "test", "bootstrap", "build", "menuconfig", "clean", "ports", "flash", "deploy", "monitor", "dev", "erase-flash"])
    parser.add_argument("--target", choices=TARGETS, default=DEFAULT_TARGET)
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--port", help="COM3, /dev/cu.usbmodem*, or /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=460800, help="flash baud rate (monitor uses 115200)")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 11):
        parser.error("Use Python 3.11: uv run fw " + args.command)
    if args.command in ("flash", "deploy", "monitor", "dev", "erase-flash") and not args.port:
        parser.error("--port is required; use the ports command to list devices")
    build_dir = (args.build_dir or (ROOT / "build" / args.target / BUILD.name)).expanduser().resolve()
    if args.command == "targets":
        print(json.dumps(list(TARGETS)))
    elif args.command == "test":
        run([sys.executable, "-m", "unittest", "discover", "-s", ROOT / "scripts", "-p", "test_*.py"])
    elif args.command == "bootstrap":
        bootstrap(args.target)
    elif args.command == "ports":
        serial_command("serial.tools.list_ports", ["-v"])
    elif args.command == "erase-flash":
        serial_command("esptool", ["--chip", TARGETS[args.target]["idf_target"], "--port", args.port, "erase_flash"])
    else:
        if args.command in ("build", "deploy", "dev", "menuconfig", "clean"):
            idf({"menuconfig": "menuconfig", "clean": "clean"}.get(args.command, "build"), build_dir, args.target)
        if args.command in ("flash", "deploy", "dev"):
            flash(build_dir, args.port, args.baud, args.target)
        if args.command in ("monitor", "dev"):
            serial_command("serial.tools.miniterm", [args.port, "115200"])


def cli():
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    cli()
