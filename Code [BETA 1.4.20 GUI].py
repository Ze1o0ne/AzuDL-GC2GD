import os
import re
import json
import time
import socket
import base64
import shutil
import hashlib
import secrets
import subprocess
import sys
import contextlib
import io
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse


def run_bootstrap_command(cmd, label):
    print(f"[SETUP] {label}")
    subprocess.run(cmd, check=True)


def ensure_system_tools():
    missing = []

    for tool in ["aria2c", "ffmpeg", "7z"]:
        if shutil.which(tool) is None:
            missing.append(tool)

    if missing:
        run_bootstrap_command(["apt-get", "update", "-qq"], "Preparing Colab package index")
        run_bootstrap_command(
            ["apt-get", "install", "-y", "aria2", "ffmpeg", "p7zip-full"],
            "Installing required system tools: aria2, ffmpeg, 7z"
        )


def ensure_python_package(import_name, package_name=None):
    package_name = package_name or import_name

    try:
        __import__(import_name)
    except ModuleNotFoundError:
        run_bootstrap_command(
            [sys.executable, "-m", "pip", "install", "-q", package_name],
            "Installing Python package: " + package_name
        )


ensure_system_tools()
ensure_python_package("requests")
ensure_python_package("tqdm")
ensure_python_package("yt_dlp", "yt-dlp")
ensure_python_package("ipywidgets")

import requests
import ipywidgets as widgets
from tqdm.notebook import tqdm
from IPython.display import display
from google.colab import drive
from yt_dlp import YoutubeDL


class AzuDlGC2GD:
    def __init__(self):
        self.project_name = "AzuDl - GC2GD"
        self.project_subtitle = "Azizi Universal Downloader - Google Colab to Google Drive"
        self.version = "1.4.20 GUI Beta"

        self.drive_mount_path = Path("/content/drive")
        self.my_drive_path = self.drive_mount_path / "MyDrive"

        self.base_dir = self.my_drive_path / "AzuDl-GC2GD"
        self.torrent_dir = self.base_dir / "TorrentDownloads"
        self.youtube_dir = self.base_dir / "YouTubeDownloads"
        self.direct_dir = self.base_dir / "DirectDownloads"
        self.batch_dir = self.base_dir / "BatchDownloads"
        self.github_dir = self.base_dir / "GitHubDownloads"
        self.archive_dir = self.base_dir / "Archives"
        self.logs_dir = self.base_dir / "Logs"
        self.temp_dir = Path("/content/AzuDl-GC2GD-Temp")
        self.history_file = self.logs_dir / "download_history.json"
        self.aria2_session_file = self.logs_dir / "aria2.session"
        self.aria2_secret_file = self.logs_dir / "aria2_rpc_secret.txt"
        self.youtube_cookies_file = self.logs_dir / "youtube_cookies.txt"
        self.youtube_po_token_file = self.logs_dir / "youtube_po_token.txt"
        self.youtube_visitor_data_file = self.logs_dir / "youtube_visitor_data.txt"
        self.github_token_file = self.logs_dir / "github_token.txt"

        self.rpc_url = "http://127.0.0.1:6800/jsonrpc"
        self.rpc_secret = None
        self.official_github_repo_url = "https://github.com/TheGreatAzizi/AzuDL-GC2GD"
        self.console_width = 78
        self.color_enabled = (
            not os.environ.get("NO_COLOR", "").strip()
            and not os.environ.get("AZUDL_NO_COLOR", "").strip()
        )

    def setup(self):
        self.print_banner()
        self.mount_google_drive()
        self.wait_for_drive_sync()
        self.prepare_directories()
        self.load_or_create_rpc_secret()
        self.start_aria2_rpc()

    def style(self, text, code):
        text = str(text)

        if not self.color_enabled:
            return text

        return f"\033[{code}m{text}\033[0m"

    def print_section(self, title, subtitle=""):
        print("")
        print(self.style("=" * self.console_width, "36"))
        print(self.style(title, "1;36"))

        if subtitle:
            print(self.style(subtitle, "90"))

        print(self.style("=" * self.console_width, "36"))

    def print_subsection(self, title):
        print("")
        print(self.style(title, "1;37"))
        print(self.style("-" * self.console_width, "90"))

    def print_status(self, message, tone="info"):
        labels = {
            "info": ("INFO", "36"),
            "success": ("DONE", "32"),
            "warning": ("WARN", "33"),
            "error": ("ERROR", "31")
        }
        label, code = labels.get(tone, labels["info"])
        print(f"{self.style('[' + label + ']', code)} {message}")

    def print_kv(self, label, value):
        print(f"{self.style(str(label) + ':', '1;37')} {value}")

    def print_menu(self, title, options):
        self.print_section(title)

        for key, label in options:
            print(f"{str(key).rjust(2)}. {label}")

    def prompt(self, label):
        return input(self.style(f"{label}: ", "1;36")).strip()

    def wait_for_drive_sync(self, delay=3):
        if self.my_drive_path.exists():
            self.print_status("Waiting briefly for Google Drive sync.")
            time.sleep(delay)

    def ensure_drive_ready(self):
        if not self.my_drive_path.exists():
            raise RuntimeError("Google Drive is not mounted.")

        self.logs_dir.mkdir(parents=True, exist_ok=True)
        test_file = self.logs_dir / ".azudl_drive_write_test"

        try:
            test_file.write_text("ok")
            if not test_file.exists() or test_file.read_text() != "ok":
                raise RuntimeError("Google Drive write test failed.")
        finally:
            try:
                test_file.unlink()
            except Exception:
                pass

    def force_drive_sync(self):
        try:
            subprocess.run(["sync"], check=False)
        except Exception:
            pass

        time.sleep(2)

    def verify_drive_file_visible(self, path, expected_size=None, timeout=45):
        path = Path(path)
        start = time.time()

        while time.time() - start < timeout:
            try:
                if path.exists() and path.is_file():
                    size = path.stat().st_size

                    if size > 0 and (expected_size is None or size == expected_size):
                        with path.open("rb") as handle:
                            handle.read(1)

                        return True
            except Exception:
                pass

            self.force_drive_sync()
            time.sleep(1)

        return False

    def print_drive_visibility_note(self, folder):
        self.print_status("Files are verified on the Colab Google Drive mount.", "success")
        self.print_status("If the Google Drive web/app UI does not show them immediately, refresh Drive or wait for sync.", "warning")
        self.print_kv("Drive folder", folder)

    def wait_file_stable(self, path, checks=3, delay=0.75):
        path = Path(path)

        if not path.exists() or not path.is_file():
            return False

        last_size = -1
        stable_count = 0

        for _ in range(max(checks * 4, 8)):
            try:
                current_size = path.stat().st_size
            except Exception:
                return False

            if current_size > 0 and current_size == last_size:
                stable_count += 1
            else:
                stable_count = 0

            if stable_count >= checks:
                return True

            last_size = current_size
            time.sleep(delay)

        return False

    def is_temporary_output_file(self, path):
        path = Path(path)
        name = path.name.lower()
        suffix = path.suffix.lower()

        if suffix in [".part", ".ytdl", ".temp", ".tmp", ".aria2"]:
            return True

        if name.endswith(".part") or name.endswith(".ytdl") or name.endswith(".tmp"):
            return True

        return False

    def get_unique_destination(self, destination):
        destination = Path(destination)

        if not destination.exists():
            return destination

        stem = destination.stem
        suffix = destination.suffix
        parent = destination.parent
        counter = 1

        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"

            if not candidate.exists():
                return candidate

            counter += 1

    def safe_transfer_to_drive(self, source, destination_dir, remove_source=True):
        source = Path(source)
        destination_dir = Path(destination_dir)

        if not source.exists() or not source.is_file():
            raise FileNotFoundError(f"Source file does not exist: {source}")

        if self.is_temporary_output_file(source):
            return None

        if not self.wait_file_stable(source):
            raise RuntimeError(f"Source file is not stable or is incomplete: {source}")

        self.ensure_drive_ready()
        destination_dir.mkdir(parents=True, exist_ok=True)

        source_size = source.stat().st_size
        destination = destination_dir / self.sanitize_name(source.name)
        destination = self.get_unique_destination(destination)
        tmp_destination = destination.with_name(destination.name + ".azudl_copying")

        if tmp_destination.exists():
            try:
                tmp_destination.unlink()
            except Exception:
                pass

        with source.open("rb") as src_handle:
            with tmp_destination.open("wb") as dst_handle:
                with tqdm(total=source_size, unit="B", unit_scale=True, unit_divisor=1024, desc="Drive copy") as bar:
                    while True:
                        chunk = src_handle.read(1024 * 1024)

                        if not chunk:
                            break

                        dst_handle.write(chunk)
                        bar.update(len(chunk))

                dst_handle.flush()
                os.fsync(dst_handle.fileno())

        if not tmp_destination.exists() or tmp_destination.stat().st_size != source_size:
            raise RuntimeError(f"Google Drive temporary copy verification failed for: {source}")

        tmp_destination.replace(destination)
        self.force_drive_sync()

        if not self.verify_drive_file_visible(destination, expected_size=source_size, timeout=60):
            raise RuntimeError(f"File was copied but could not be verified on Google Drive mount: {destination}")

        if remove_source:
            try:
                source.unlink()
            except Exception:
                pass

        return destination

    def collect_final_files(self, folder):
        folder = Path(folder)

        if not folder.exists():
            return []

        files = []

        for item in folder.glob("**/*"):
            if item.is_file() and not self.is_temporary_output_file(item):
                try:
                    if item.stat().st_size > 0:
                        files.append(item)
                except Exception:
                    pass

        return sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)

    def transfer_folder_contents_to_drive(self, source_dir, destination_dir):
        source_dir = Path(source_dir)
        destination_dir = Path(destination_dir)
        transferred = []

        if not source_dir.exists():
            return transferred

        files = self.collect_final_files(source_dir)

        for item in files:
            moved = self.safe_transfer_to_drive(item, destination_dir, remove_source=True)

            if moved:
                transferred.append(moved)

        try:
            shutil.rmtree(source_dir, ignore_errors=True)
        except Exception:
            pass

        return transferred

    def verify_output_files(self, folder, label="download", min_count=1):
        folder = Path(folder)
        files = self.collect_final_files(folder)

        if len(files) < min_count:
            raise RuntimeError(f"{label} finished, but no valid output file was found in: {folder}")

        self.print_subsection("Verified Output Files")

        for item in files[:20]:
            try:
                size = self.format_bytes(item.stat().st_size)
            except Exception:
                size = "unknown"
            print(f"{size:<12} {item}")

        if len(files) > 20:
            print(" - ...", len(files) - 20, "more files")

        return files

    def verify_aria2_status_files(self, status, label="aria2 download"):
        files = status.get("files", []) if status else []
        verified = []

        for file_item in files:
            path = file_item.get("path", "")

            if not path:
                continue

            item = Path(path)

            if item.exists() and item.is_file() and item.stat().st_size > 0:
                verified.append(item)

        if not verified:
            raise RuntimeError(f"{label} completed, but aria2 output files were not found on Google Drive.")

        self.print_subsection("Verified aria2 Files")

        for item in verified[:20]:
            print(f"{self.format_bytes(item.stat().st_size):<12} {item}")

        if len(verified) > 20:
            print(" - ...", len(verified) - 20, "more files")

        return verified

    def print_banner(self):
        self.print_section(self.project_name, self.project_subtitle)
        self.print_kv("Version", self.version)
        self.print_kv("Default output", self.base_dir)
        self.print_status("Ready for Google Colab. Google Drive is used as persistent storage.")

    def mount_google_drive(self):
        if self.my_drive_path.exists():
            self.print_status("Google Drive is already mounted.", "success")
            self.print_drive_storage_summary()
            return

        attempts = [
            {"force_remount": False, "label": "standard mount"},
            {"force_remount": True, "label": "force remount"}
        ]

        last_error = None

        for attempt in attempts:
            try:
                self.print_status(f"Requesting Google Drive access ({attempt['label']}).")
                drive.mount(str(self.drive_mount_path), force_remount=attempt["force_remount"])

                if self.my_drive_path.exists():
                    self.print_status("Google Drive mounted successfully.", "success")
                    self.print_drive_storage_summary()
                    return

            except Exception as error:
                last_error = error
                self.print_status(f"Mount attempt failed: {error}", "warning")
                time.sleep(2)

        self.print_drive_mount_help()
        raise RuntimeError(f"Google Drive mount failed: {last_error}")

    def print_drive_mount_help(self):
        self.print_section("Google Drive Mount Failed", "Use these checks before running the notebook again.")
        print("1. Runtime > Restart session")
        print("2. Run this in a separate cell: from google.colab import drive; drive.flush_and_unmount()")
        print("3. Keep only the intended Google account active in the browser.")
        print("4. Try Colab in a private/incognito browser window.")
        print("5. Make sure third-party cookies are allowed for Colab.")
        print("6. Reconnect Drive manually from the Colab file panel.")
        print("")

    def prepare_directories(self):
        dirs = [
            self.base_dir,
            self.torrent_dir,
            self.youtube_dir,
            self.direct_dir,
            self.batch_dir,
            self.github_dir,
            self.archive_dir,
            self.logs_dir
        ]

        for item in dirs:
            item.mkdir(parents=True, exist_ok=True)

        self.temp_dir.mkdir(parents=True, exist_ok=True)

        if not self.aria2_session_file.exists():
            self.aria2_session_file.write_text("")

        self.ensure_youtube_cookie_file()
        self.ensure_youtube_po_token_files()
        self.ensure_github_token_file()

    def ensure_youtube_cookie_file(self):
        if self.youtube_cookies_file.exists():
            return

        text = """# Netscape HTTP Cookie File
# This file is created by AzuDl.
# Replace this file content with your exported YouTube cookies.
"""
        self.youtube_cookies_file.write_text(text)

        try:
            os.chmod(self.youtube_cookies_file, 0o600)
        except Exception:
            pass

        self.print_status("Created YouTube cookies template.", "success")
        self.print_kv("Template path", self.youtube_cookies_file)

    def ensure_youtube_po_token_files(self):
        if not self.youtube_po_token_file.exists():
            text = """# Put YouTube PO Token here.
# Example:
# web+YOUR_PO_TOKEN
# or:
# mweb+YOUR_PO_TOKEN
"""
            self.youtube_po_token_file.write_text(text)

            try:
                os.chmod(self.youtube_po_token_file, 0o600)
            except Exception:
                pass

            self.print_status("Created YouTube PO Token template.", "success")
            self.print_kv("Template path", self.youtube_po_token_file)

        if not self.youtube_visitor_data_file.exists():
            text = """# Put YouTube Visitor Data here if your PO Token setup needs it.
"""
            self.youtube_visitor_data_file.write_text(text)

            try:
                os.chmod(self.youtube_visitor_data_file, 0o600)
            except Exception:
                pass

            self.print_status("Created YouTube Visitor Data template.", "success")
            self.print_kv("Template path", self.youtube_visitor_data_file)

    def ensure_github_token_file(self):
        if self.github_token_file.exists():
            return

        text = """# Optional GitHub token.
# Paste a fine-grained GitHub token here if private repositories or higher API limits are needed.
# Keep this file private.
"""
        self.github_token_file.write_text(text)

        try:
            os.chmod(self.github_token_file, 0o600)
        except Exception:
            pass

    def get_github_token(self):
        env_token = os.environ.get("AZUDL_GITHUB_TOKEN", "").strip()

        if env_token:
            return env_token

        return self.read_first_useful_line(self.github_token_file)

    def save_github_token_text(self, token):
        token = str(token or "").strip()

        if not token:
            raise ValueError("GitHub token is empty.")

        self.github_token_file.write_text(token + "\n")

        try:
            os.chmod(self.github_token_file, 0o600)
        except Exception:
            pass

        os.environ["AZUDL_GITHUB_TOKEN"] = token
        self.print_status("GitHub token saved for this runtime.", "success")
        self.print_kv("Token file", self.github_token_file)

    def clear_github_token(self):
        if self.github_token_file.exists():
            self.github_token_file.unlink()

        os.environ.pop("AZUDL_GITHUB_TOKEN", None)
        self.ensure_github_token_file()
        self.print_status("GitHub token was cleared.", "success")

    def load_or_create_rpc_secret(self):
        if self.aria2_secret_file.exists():
            secret = self.aria2_secret_file.read_text().strip()
            if secret:
                self.rpc_secret = secret
                return

        self.rpc_secret = secrets.token_urlsafe(32)
        self.aria2_secret_file.write_text(self.rpc_secret)

        try:
            os.chmod(self.aria2_secret_file, 0o600)
        except Exception:
            pass

    def is_port_open(self, host="127.0.0.1", port=6800):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0

    def wait_until_port_closed(self, timeout=10):
        start = time.time()

        while time.time() - start < timeout:
            if not self.is_port_open():
                return True
            time.sleep(0.5)

        return not self.is_port_open()

    def start_aria2_rpc(self):
        if self.is_port_open():
            try:
                options = self.rpc("aria2.getGlobalOption")
                save_session = str(options.get("save-session", ""))
                input_file = str(options.get("input-file", ""))

                if str(self.aria2_session_file) in [save_session, input_file]:
                    self.print_status("aria2 RPC is already running for this session.", "success")
                    return

                self.print_status("aria2 RPC is running with old options; restarting it.", "warning")

                try:
                    self.rpc("aria2.shutdown")
                except Exception:
                    pass

                self.wait_until_port_closed(timeout=10)

            except Exception:
                pass

        if self.is_port_open():
            subprocess.run(["pkill", "-f", "aria2c.*6800"], check=False)
            self.wait_until_port_closed(timeout=10)

        cmd = [
            "aria2c",
            "--enable-rpc=true",
            "--rpc-listen-all=false",
            "--rpc-listen-port=6800",
            "--rpc-allow-origin-all=false",
            f"--rpc-secret={self.rpc_secret}",
            "--daemon=true",
            "--seed-time=0",
            "--seed-ratio=0.0",
            "--file-allocation=none",
            "--continue=true",
            "--always-resume=true",
            "--auto-save-interval=10",
            "--save-session-interval=10",
            f"--input-file={self.aria2_session_file}",
            f"--save-session={self.aria2_session_file}",
            "--force-save=true",
            "--max-tries=0",
            "--retry-wait=10",
            "--timeout=60",
            "--connect-timeout=60",
            "--enable-dht=true",
            "--enable-dht6=true",
            "--enable-peer-exchange=true",
            "--bt-enable-lpd=true",
            "--bt-save-metadata=true",
            "--bt-load-saved-metadata=true",
            "--console-log-level=warn"
        ]

        subprocess.run(cmd, check=True)

        for _ in range(30):
            if self.is_port_open():
                self.print_status("aria2 RPC server is ready.", "success")
                self.print_kv("Session file", self.aria2_session_file)
                return
            time.sleep(0.5)

        raise RuntimeError("Failed to start aria2 RPC server.")

    def rpc(self, method, params=None):
        final_params = []

        if self.rpc_secret:
            final_params.append(f"token:{self.rpc_secret}")

        if params:
            final_params.extend(params)

        payload = {
            "jsonrpc": "2.0",
            "id": "azudl-gc2gd",
            "method": method,
            "params": final_params
        }

        response = requests.post(self.rpc_url, json=payload, timeout=30)

        if response.status_code != 200:
            message = response.text[:1000]
            raise RuntimeError(f"aria2 RPC HTTP {response.status_code}: {message}")

        try:
            data = response.json()
        except Exception:
            raise RuntimeError(f"Invalid aria2 RPC response: {response.text[:1000]}")

        if "error" in data:
            raise RuntimeError(data["error"])

        return data["result"]

    def save_aria2_session(self):
        try:
            result = self.rpc("aria2.saveSession")
            self.print_status("aria2 session saved.", "success")
            return result
        except Exception as error:
            message = str(error)

            if "Filename is not given" in message:
                return None

            self.print_status(f"Failed to save aria2 session: {error}", "warning")
            return None

    def sanitize_name(self, name):
        name = str(name or "").strip()
        name = re.sub(r'[\/\\:*?"<>|]', "_", name)
        name = re.sub(r"\s+", " ", name)
        name = name.strip(". ")
        return name or f"Download_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"

    def normalize_folder_name(self, folder_name, default_name):
        folder_name = str(folder_name or "").strip()

        if not folder_name:
            return self.sanitize_name(default_name)

        return self.sanitize_name(folder_name)

    def format_bytes(self, value):
        value = float(value or 0)

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024:
                return f"{value:.2f} {unit}"
            value /= 1024

        return f"{value:.2f} PB"

    def get_drive_usage(self):
        try:
            return shutil.disk_usage(str(self.my_drive_path))
        except Exception as error:
            self.print_status(f"Could not read Google Drive storage details: {error}", "warning")
            return None

    def print_drive_storage_summary(self):
        usage = self.get_drive_usage()

        if not usage:
            return

        total, used, free = usage
        used_percent = used * 100 / total if total else 0

        self.print_subsection("Google Drive Storage")
        self.print_kv("Mounted path", self.my_drive_path)
        self.print_kv("Total space", self.format_bytes(total))
        self.print_kv("Used space", f"{self.format_bytes(used)} ({used_percent:.1f}%)")
        self.print_kv("Free space", self.format_bytes(free))

    def format_seconds(self, seconds):
        seconds = int(seconds or 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"

        return f"{minutes:02d}:{secs:02d}"

    def get_recent_files(self, folder, since=0):
        folder = Path(folder)

        if not folder.exists():
            return []

        files = []

        for item in folder.glob("**/*"):
            if item.is_file():
                try:
                    if item.stat().st_mtime >= since:
                        files.append(item)
                except Exception:
                    pass

        return sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)

    def move_tree_contents(self, source_dir, destination_dir):
        source_dir = Path(source_dir)
        destination_dir = Path(destination_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        moved = []

        if not source_dir.exists():
            return moved

        for item in source_dir.glob("**/*"):
            if not item.is_file():
                continue

            rel = item.relative_to(source_dir)
            target = destination_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)

            if target.exists():
                stem = target.stem
                suffix = target.suffix
                counter = 1

                while target.exists():
                    target = target.parent / f"{stem}_{counter}{suffix}"
                    counter += 1

            shutil.move(str(item), str(target))
            moved.append(target)

        try:
            shutil.rmtree(source_dir, ignore_errors=True)
        except Exception:
            pass

        return moved

    def verify_download_outputs(self, folder, since=0, label="download"):
        files = self.get_recent_files(folder, since=since)

        if not files:
            raise RuntimeError(f"{label} finished, but no output file was found in: {folder}")

        self.print_subsection("Verified Output Files")

        for item in files[:15]:
            try:
                size = self.format_bytes(item.stat().st_size)
            except Exception:
                size = "unknown"
            print(f"{size:<12} {item}")

        if len(files) > 15:
            print(" - ...", len(files) - 15, "more files")

        return files

    def detect_link_type(self, value):
        value = str(value or "").strip()
        lower = value.lower()

        if lower.startswith("magnet:?"):
            return "torrent"

        parsed = urlparse(value)
        host = parsed.netloc.lower()
        path = parsed.path.lower()

        youtube_hosts = [
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "music.youtube.com"
        ]

        if any(host == item or host.endswith("." + item) for item in youtube_hosts):
            return "youtube"

        if path.endswith(".torrent"):
            return "torrent_file"

        if lower.startswith(("http://", "https://", "ftp://")):
            return "direct"

        if Path(value).suffix.lower() == ".torrent":
            return "torrent_file"

        return "unknown"

    def atomic_write_json(self, path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        tmp.replace(path)

    def save_history(self, item):
        history = []

        if self.history_file.exists():
            try:
                history = json.loads(self.history_file.read_text())

                if not isinstance(history, list):
                    history = []

            except Exception:
                backup = self.logs_dir / f"download_history_corrupt_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

                try:
                    shutil.copy2(self.history_file, backup)
                    self.print_status(f"History file was invalid. Backup saved: {backup}", "warning")
                except Exception:
                    pass

                history = []

        item["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history.append(item)
        self.atomic_write_json(self.history_file, history)

    def print_history(self):
        self.print_section("Download History", "Showing the latest 50 recorded operations.")

        if not self.history_file.exists():
            self.print_status("No download history was found yet.", "info")
            return

        try:
            history = json.loads(self.history_file.read_text())
        except Exception:
            self.print_status("Download history exists, but the JSON file is invalid.", "error")
            return

        if not history:
            self.print_status("No download history was found yet.", "info")
            return

        for index, item in enumerate(history[-50:], 1):
            print(self.style("-" * self.console_width, "90"))
            self.print_kv("Index", index)
            self.print_kv("Type", item.get("type", "unknown"))
            self.print_kv("Time", item.get("time", "unknown"))
            self.print_kv("Source", item.get("source", "unknown"))
            self.print_kv("Output", item.get("output", "unknown"))
            self.print_kv("Status", item.get("status", "unknown"))

            if item.get("format"):
                self.print_kv("Format", item.get("format"))

            if item.get("seed") is not None:
                self.print_kv("Seed", item.get("seed"))

            if item.get("error"):
                self.print_kv("Error", item.get("error"))

    def get_all_downloaded_files(self, max_scan=5000):
        folders = [
            self.torrent_dir,
            self.youtube_dir,
            self.direct_dir,
            self.batch_dir,
            self.github_dir,
            self.archive_dir
        ]

        files = []

        for folder in folders:
            if not folder.exists():
                continue

            count = 0

            for item in folder.glob("**/*"):
                if item.is_file():
                    files.append(item)
                    count += 1

                    if count >= max_scan:
                        self.print_status(f"Scan limit reached for {folder}.", "warning")
                        break

        return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)

    def get_latest_file(self):
        files = self.get_all_downloaded_files()

        if not files:
            return None

        return files[0]

    def get_latest_downloaded_file(self):
        return self.get_latest_file()

    def get_latest_downloaded_folder(self):
        folders = [
            self.torrent_dir,
            self.youtube_dir,
            self.direct_dir,
            self.batch_dir,
            self.archive_dir
        ]

        all_dirs = []

        for folder in folders:
            if folder.exists():
                all_dirs.extend([item for item in folder.glob("**/*") if item.is_dir()])

        if not all_dirs:
            return None

        return max(all_dirs, key=lambda item: item.stat().st_mtime)

    def list_downloads(self, limit_per_folder=100):
        self.print_section("Downloaded Files", f"Showing up to {limit_per_folder} files per project folder.")

        folders = [
            self.torrent_dir,
            self.youtube_dir,
            self.direct_dir,
            self.batch_dir,
            self.archive_dir
        ]

        for folder in folders:
            self.print_subsection(str(folder))

            if not folder.exists():
                self.print_status("Folder does not exist yet.", "info")
                continue

            items = sorted(
                folder.glob("**/*"),
                key=lambda x: x.stat().st_mtime if x.exists() else 0,
                reverse=True
            )

            files = [item for item in items if item.is_file()]

            if not files:
                self.print_status("No files in this folder.", "info")
                continue

            for item in files[:limit_per_folder]:
                size = self.format_bytes(item.stat().st_size)
                print(f"{size:<12} {item}")

    def print_latest_file(self):
        latest = self.get_latest_downloaded_file()

        if not latest:
            self.print_status("No downloaded files were found.", "info")
            return

        self.print_section("Latest Downloaded File")
        self.print_kv("Path", latest)
        self.print_kv("Size", self.format_bytes(latest.stat().st_size))
        self.print_kv("Modified", datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"))

    def select_file(self):
        files = self.get_all_downloaded_files()

        if not files:
            self.print_status("No downloaded files were found.", "info")
            return None

        self.print_section("Select a File", "Showing the 100 most recent files.")

        for index, item in enumerate(files[:100], 1):
            print(f"{index:<4} {self.format_bytes(item.stat().st_size):<12} {item}")

        value = self.prompt("File number")

        if not value.isdigit():
            self.print_status("Enter a valid file number from the list.", "warning")
            return None

        index = int(value)

        if index < 1 or index > min(len(files), 100):
            self.print_status("Enter a valid file number from the list.", "warning")
            return None

        return files[index - 1]

    def add_aria2_download(self, uris, save_dir, speed_limit="", extra_options=None):
        options = {
            "dir": str(save_dir),
            "file-allocation": "none",
            "continue": "true",
            "always-resume": "true",
            "max-tries": "0",
            "retry-wait": "10",
            "timeout": "60",
            "connect-timeout": "60",
            "allow-overwrite": "false",
            "auto-file-renaming": "true",
            "max-connection-per-server": "16",
            "split": "16",
            "min-split-size": "1M"
        }

        if speed_limit:
            options["max-overall-download-limit"] = speed_limit.strip()

        if extra_options:
            options.update(extra_options)

        gid = self.rpc("aria2.addUri", [uris, options])
        self.save_aria2_session()
        return gid

    def add_aria2_torrent(self, torrent_bytes, save_dir, speed_limit="", extra_options=None):
        torrent_base64 = base64.b64encode(torrent_bytes).decode("utf-8")

        options = {
            "dir": str(save_dir),
            "file-allocation": "none",
            "continue": "true",
            "always-resume": "true",
            "max-tries": "0",
            "retry-wait": "10",
            "timeout": "60",
            "connect-timeout": "60",
            "allow-overwrite": "false",
            "auto-file-renaming": "true",
            "seed-time": "0",
            "seed-ratio": "0.0",
            "enable-dht": "true",
            "enable-dht6": "true",
            "enable-peer-exchange": "true",
            "bt-enable-lpd": "true"
        }

        if speed_limit:
            options["max-overall-download-limit"] = speed_limit.strip()

        if extra_options:
            options.update(extra_options)

        gid = self.rpc("aria2.addTorrent", [torrent_base64, [], options])
        self.save_aria2_session()
        return gid

    def fetch_torrent_file_bytes(self, source):
        source = source.strip()

        headers = {
            "User-Agent": "Mozilla/5.0 AzuDl-GC2GD/1.4.0",
            "Accept": "application/x-bittorrent,application/octet-stream,*/*"
        }

        if source.startswith(("http://", "https://")):
            self.print_status("Downloading torrent file metadata.")
            response = requests.get(source, headers=headers, timeout=60, allow_redirects=True)
            response.raise_for_status()
            content = response.content
        else:
            path = Path(source)

            if not path.exists():
                raise FileNotFoundError(f"Torrent file not found: {path}")

            content = path.read_bytes()

        if not content:
            raise ValueError("Torrent file is empty")

        stripped = content.lstrip()

        if not stripped.startswith(b"d"):
            preview = content[:300].decode("utf-8", errors="replace")
            raise ValueError(
                "Downloaded file is not a valid .torrent file. "
                "The server may have returned HTML, an error page, or blocked the request.\n"
                f"Preview:\n{preview}"
            )

        infohash = self.get_torrent_infohash(content)

        if not infohash:
            raise ValueError("Invalid torrent file: missing or invalid info dictionary.")

        return content

    def skip_bencode_value(self, data, index):
        if index >= len(data):
            raise ValueError("Unexpected end of bencode data")

        token = data[index:index + 1]

        if token == b"i":
            end = data.index(b"e", index)
            return end + 1

        if token in [b"l", b"d"]:
            index += 1

            while index < len(data) and data[index:index + 1] != b"e":
                index = self.skip_bencode_value(data, index)

            if index >= len(data):
                raise ValueError("Unterminated bencode list or dictionary")

            return index + 1

        if token.isdigit():
            colon = data.index(b":", index)
            length = int(data[index:colon])
            return colon + 1 + length

        raise ValueError("Invalid bencode data")

    def get_torrent_infohash(self, torrent_bytes):
        data = torrent_bytes

        if not data.startswith(b"d"):
            return ""

        try:
            index = 1

            while index < len(data) and data[index:index + 1] != b"e":
                key_start = index
                key_end = self.skip_bencode_value(data, key_start)
                key_data = data[key_start:key_end]

                colon = key_data.index(b":")
                key = key_data[colon + 1:]

                value_start = key_end
                value_end = self.skip_bencode_value(data, value_start)

                if key == b"info":
                    return hashlib.sha1(data[value_start:value_end]).hexdigest()

                index = value_end

        except Exception:
            return ""

        return ""

    def find_existing_torrent_by_infohash(self, infohash):
        if not infohash:
            return None

        target = str(infohash).lower()
        active, waiting, stopped = self.get_aria2_items()

        for item in active + waiting + stopped:
            bittorrent = item.get("bittorrent", {})
            current = str(bittorrent.get("infoHash", "")).lower()

            if current == target:
                return item

        return None

    def remove_existing_torrent_gid(self, gid):
        if not gid:
            return False

        try:
            self.rpc("aria2.remove", [gid])
            self.save_aria2_session()
            return True
        except Exception:
            pass

        try:
            self.rpc("aria2.removeDownloadResult", [gid])
            self.save_aria2_session()
            return True
        except Exception:
            return False

    def build_torrent_options(self, private=False, seed=False):
        seed_time = "525600" if seed else "0"
        seed_ratio = "999.0" if seed else "0.0"

        options = {
            "seed-time": seed_time,
            "seed-ratio": seed_ratio,
            "bt-save-metadata": "true",
            "bt-load-saved-metadata": "true",
            "bt-request-peer-speed-limit": "50K"
        }

        if private:
            options.update({
                "enable-dht": "false",
                "enable-dht6": "false",
                "enable-peer-exchange": "false",
                "bt-enable-lpd": "false"
            })
        else:
            options.update({
                "enable-dht": "true",
                "enable-dht6": "true",
                "enable-peer-exchange": "true",
                "bt-enable-lpd": "true"
            })

        return options

    def get_aria2_status(self, gid):
        keys = [
            "gid",
            "status",
            "totalLength",
            "completedLength",
            "downloadSpeed",
            "uploadSpeed",
            "uploadLength",
            "connections",
            "numSeeders",
            "shareRatio",
            "errorCode",
            "errorMessage",
            "files",
            "bittorrent",
            "followedBy",
            "following",
            "belongsTo"
        ]

        return self.rpc("aria2.tellStatus", [gid, keys])

    def get_aria2_items(self):
        keys = [
            "gid",
            "status",
            "totalLength",
            "completedLength",
            "downloadSpeed",
            "uploadSpeed",
            "uploadLength",
            "connections",
            "numSeeders",
            "shareRatio",
            "errorCode",
            "errorMessage",
            "files",
            "bittorrent",
            "followedBy",
            "following",
            "belongsTo"
        ]

        active = self.rpc("aria2.tellActive", [keys])
        waiting = self.rpc("aria2.tellWaiting", [0, 100, keys])
        stopped = self.rpc("aria2.tellStopped", [0, 100, keys])

        return active, waiting, stopped

    def get_active_waiting_stopped(self):
        return self.get_aria2_items()

    def print_aria2_item_paths(self, item):
        files = item.get("files", []) if item else []

        if not files:
            return

        self.print_subsection("aria2 Output Paths")

        for file_item in files[:10]:
            path = file_item.get("path", "")

            if path:
                print(" -", path)

        if len(files) > 10:
            print(" - ...", len(files) - 10, "more files")

    def print_aria2_status(self):
        active, waiting, stopped = self.get_aria2_items()
        groups = [
            ("Active", active),
            ("Waiting", waiting),
            ("Stopped", stopped)
        ]

        for title, items in groups:
            self.print_subsection(f"aria2 {title}")

            if not items:
                self.print_status("No items in this queue.", "info")
                continue

            for item in items:
                gid = item.get("gid", "")
                status = item.get("status", "")
                total = int(item.get("totalLength", "0") or 0)
                completed = int(item.get("completedLength", "0") or 0)
                speed = int(item.get("downloadSpeed", "0") or 0)
                upload_speed = int(item.get("uploadSpeed", "0") or 0)
                uploaded = int(item.get("uploadLength", "0") or 0)
                share_ratio = item.get("shareRatio", "0")
                connections = item.get("connections", "0")
                seeders = item.get("numSeeders", "0")
                bittorrent = item.get("bittorrent", {})
                infohash = bittorrent.get("infoHash", "")

                percent = completed * 100 / total if total > 0 else 0
                files = item.get("files", [])
                name = ""

                if files:
                    name = Path(files[0].get("path", "")).name

                self.print_kv("GID", gid)
                self.print_kv("Status", status)
                self.print_kv("Name", name or "unknown")
                self.print_kv("InfoHash", infohash or "unknown")
                self.print_kv("Progress", f"{percent:.2f}%")
                self.print_kv("Completed", f"{self.format_bytes(completed)} / {self.format_bytes(total)}")
                self.print_kv("Download speed", self.format_bytes(speed) + "/s")
                self.print_kv("Upload speed", self.format_bytes(upload_speed) + "/s")
                self.print_kv("Uploaded", self.format_bytes(uploaded))
                self.print_kv("Ratio", share_ratio)
                self.print_kv("Connections", connections)
                self.print_kv("Seeders", seeders)

                if files:
                    print("Files:")

                    for file_item in files[:5]:
                        print(" -", file_item.get("path", ""))

                    if len(files) > 5:
                        print(" - ...", len(files) - 5, "more files")

                if item.get("errorMessage"):
                    self.print_kv("Error", item.get("errorMessage"))

                print(self.style("-" * self.console_width, "90"))

    def purge_aria2_stopped(self):
        try:
            result = self.rpc("aria2.purgeDownloadResult")
            self.save_aria2_session()
            self.print_status("Stopped aria2 download results were cleared.", "success")
            print(result)
        except Exception as error:
            self.print_status(f"Failed to clear stopped aria2 results: {error}", "error")

    def remove_aria2_gid(self):
        gid = self.prompt("GID to remove")

        if not gid:
            self.print_status("No GID was entered.", "warning")
            return

        removed = self.remove_existing_torrent_gid(gid)

        if removed:
            self.print_status(f"GID removed: {gid}", "success")
        else:
            self.print_status(f"Failed to remove GID: {gid}", "error")

    def find_real_torrent_gid(self, metadata_gid, save_dir):
        save_dir = str(save_dir)

        for _ in range(120):
            try:
                status = self.get_aria2_status(metadata_gid)
            except Exception:
                status = {}

            followed_by = status.get("followedBy", [])

            if followed_by:
                real_gid = followed_by[0]
                self.print_status("Torrent metadata resolved.", "success")
                self.print_kv("Download GID", real_gid)
                return real_gid

            active, waiting, stopped = self.get_active_waiting_stopped()
            candidates = active + waiting + stopped

            for item in candidates:
                gid = item.get("gid")

                if gid == metadata_gid:
                    continue

                belongs_to = item.get("belongsTo")
                following = item.get("following")

                if belongs_to == metadata_gid or following == metadata_gid:
                    self.print_kv("Download GID", gid)
                    return gid

                files = item.get("files", [])

                for file_item in files:
                    path = file_item.get("path", "")

                    if path and str(path).startswith(save_dir):
                        total = int(item.get("totalLength", "0") or 0)

                        if total > 0:
                            self.print_kv("Download GID", gid)
                            return gid

            state = status.get("status")

            if state == "error":
                raise RuntimeError(status.get("errorMessage") or "Metadata failed.")

            time.sleep(1)

        self.print_status("Could not detect a separate download GID; using the original GID.", "warning")
        return metadata_gid

    def wait_for_torrent_metadata(self, gid, timeout=300):
        start = time.time()
        bar = tqdm(total=1, desc="Fetching metadata", unit="step")

        try:
            while True:
                if time.time() - start > timeout:
                    raise TimeoutError("Torrent metadata fetch timed out.")

                status = self.get_aria2_status(gid)

                if status.get("status") == "error":
                    raise RuntimeError(status.get("errorMessage") or "Metadata fetch failed.")

                followed_by = status.get("followedBy", [])
                files = status.get("files", [])
                total = int(status.get("totalLength", "0") or 0)

                if followed_by:
                    bar.update(1)
                    self.save_aria2_session()
                    return

                if files and total > 0:
                    bittorrent = status.get("bittorrent", {})
                    info = bittorrent.get("info", {})

                    if info:
                        bar.update(1)
                        self.save_aria2_session()
                        return

                if status.get("status") == "complete" and files and total > 0:
                    bar.update(1)
                    self.save_aria2_session()
                    return

                time.sleep(1)

        finally:
            bar.close()

    def monitor_aria2(self, gid, label, seed=False):
        last_completed = 0
        progress = None
        last_state = None
        printed_file = None
        seeding_notice_printed = False
        seed_started_at = None
        seed_bar = None
        last_session_save = time.time()

        while True:
            status = self.get_aria2_status(gid)

            state = status.get("status")
            total = int(status.get("totalLength", "0") or 0)
            completed = int(status.get("completedLength", "0") or 0)
            speed = int(status.get("downloadSpeed", "0") or 0)
            upload_speed = int(status.get("uploadSpeed", "0") or 0)
            uploaded = int(status.get("uploadLength", "0") or 0)
            seeders = status.get("numSeeders", "0")
            connections = status.get("connections", "0")
            share_ratio = status.get("shareRatio", "0")
            files = status.get("files", [])

            if time.time() - last_session_save >= 30:
                self.save_aria2_session()
                last_session_save = time.time()

            if state != last_state:
                self.print_kv("Status", state)
                last_state = state

            if files:
                first_file = files[0].get("path", "")

                if first_file and first_file != printed_file:
                    self.print_kv("File", Path(first_file).name)
                    printed_file = first_file

            if state == "error":
                if progress is not None:
                    progress.close()

                if seed_bar is not None:
                    seed_bar.close()

                self.save_aria2_session()
                raise RuntimeError(status.get("errorMessage") or "Download failed.")

            if progress is None and total > 0 and not (seed and completed >= total):
                progress = tqdm(
                    total=total,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=label
                )

            if progress is not None:
                if completed < last_completed:
                    last_completed = 0
                    progress.n = 0

                delta = completed - last_completed

                if delta > 0:
                    progress.update(delta)

                percent = completed * 100 / total if total > 0 else 0

                postfix = {
                    "percent": f"{percent:.2f}%",
                    "down": self.format_bytes(speed) + "/s",
                    "up": self.format_bytes(upload_speed) + "/s",
                    "uploaded": self.format_bytes(uploaded),
                    "ratio": str(share_ratio),
                    "connections": connections
                }

                if str(seeders) != "0":
                    postfix["seeders"] = seeders

                progress.set_postfix(postfix)

            last_completed = completed

            if seed and total > 0 and completed >= total:
                if seed_started_at is None:
                    seed_started_at = time.time()

                if not seeding_notice_printed:
                    self.print_status("Download completed. Seeding is now active.", "success")
                    self.print_status("Keep this Colab runtime connected while you want seeding to continue.")
                    self.print_status("Interrupt the cell when you want to stop seeding.", "warning")
                    seeding_notice_printed = True

                    if progress is not None:
                        progress.n = total
                        progress.refresh()
                        progress.close()
                        progress = None

                    seed_bar = tqdm(total=1, unit="step", desc="Seeding Upload")
                    self.save_aria2_session()

                if seed_bar is not None:
                    elapsed = self.format_seconds(time.time() - seed_started_at)
                    seed_bar.n = 0
                    seed_bar.set_postfix({
                        "up": self.format_bytes(upload_speed) + "/s",
                        "uploaded": self.format_bytes(uploaded),
                        "ratio": str(share_ratio),
                        "connections": connections,
                        "seeders": seeders,
                        "time": elapsed
                    })
                    seed_bar.refresh()

            if state == "complete" and not seed:
                if progress is not None:
                    progress.n = total
                    progress.refresh()
                    progress.close()

                self.save_aria2_session()
                return status

            if state == "complete" and seed:
                time.sleep(5)
                continue

            time.sleep(1)

    def download_magnet(self, magnet, folder_name="", speed_limit="", private=False, seed=False):
        magnet = magnet.strip()
        folder_name = self.normalize_folder_name(folder_name, "Torrent")
        save_dir = self.torrent_dir / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        if not magnet.startswith("magnet:?xt=urn:btih:"):
            raise ValueError("Invalid magnet link.")

        options = self.build_torrent_options(private=private, seed=seed)
        gid = self.add_aria2_download([magnet], save_dir, speed_limit, options)

        self.print_section("Torrent Magnet Added")
        self.print_kv("Output folder", save_dir)
        self.print_kv("Metadata GID", gid)
        self.print_kv("Private mode", "enabled" if private else "disabled")
        self.print_kv("Seeding", "enabled" if seed else "disabled")

        self.wait_for_torrent_metadata(gid)
        real_gid = self.find_real_torrent_gid(gid, save_dir)

        self.print_status("Starting torrent download monitor.")
        self.print_kv("Download GID", real_gid)

        status = self.monitor_aria2(real_gid, "Torrent Download", seed=seed)

        self.print_aria2_item_paths(status)
        if not seed:
            self.verify_aria2_status_files(status, label="Torrent magnet download")
        if not seed:
            self.verify_download_outputs(save_dir, since=0, label="Torrent download")

        self.save_history({
            "type": "private_torrent_magnet" if private else "torrent",
            "source": magnet,
            "output": str(save_dir),
            "status": "completed",
            "seed": seed
        })

        self.print_status("Download completed.", "success")
        self.print_kv("Saved to", save_dir)

    def download_torrent_file(self, source, folder_name="", speed_limit="", private=False, seed=False):
        source = source.strip()
        folder_name = self.normalize_folder_name(folder_name, "TorrentFile")
        save_dir = self.torrent_dir / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        torrent_bytes = self.fetch_torrent_file_bytes(source)
        infohash = self.get_torrent_infohash(torrent_bytes)

        if infohash:
            self.print_kv("Torrent InfoHash", infohash)
            existing = self.find_existing_torrent_by_infohash(infohash)

            if existing:
                existing_gid = existing.get("gid")
                existing_status = existing.get("status", "unknown")

                self.print_status("This torrent is already registered in aria2.", "warning")
                self.print_kv("Existing GID", existing_gid)
                self.print_kv("Existing status", existing_status)
                self.print_aria2_item_paths(existing)

                if existing_status == "error":
                    self.print_status("Existing torrent is in an error state; removing it before retrying.", "warning")
                    removed = self.remove_existing_torrent_gid(existing_gid)

                    if not removed:
                        raise RuntimeError("Could not remove existing errored torrent GID")

                else:
                    self.print_status("Using the existing torrent instead of adding a duplicate.")
                    status = self.monitor_aria2(existing_gid, "Torrent Resume", seed=seed)
                    self.print_aria2_item_paths(status)

                    self.save_history({
                        "type": "private_torrent_file_resume" if private else "torrent_file_resume",
                        "source": source,
                        "output": str(save_dir),
                        "status": "resumed",
                        "seed": seed
                    })

                    self.print_status("Torrent handled with the existing GID.", "success")
                    return

        options = self.build_torrent_options(private=private, seed=seed)

        try:
            gid = self.add_aria2_torrent(torrent_bytes, save_dir, speed_limit, options)
        except Exception as error:
            message = str(error)

            if "already registered" in message:
                self.print_status("This torrent is already registered in aria2.", "warning")
                self.print_status("Open Torrent Tools > aria2 status, remove the existing GID, then try again.")
                raise RuntimeError(message)

            debug_file = self.logs_dir / f"failed_torrent_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.torrent"
            debug_file.write_bytes(torrent_bytes)

            self.print_status("Failed to pass torrent data to aria2.", "error")
            self.print_kv("Debug torrent file", debug_file)

            raise error

        self.print_section("Torrent File Added")
        self.print_kv("Output folder", save_dir)
        self.print_kv("Download GID", gid)
        self.print_kv("Private mode", "enabled" if private else "disabled")
        self.print_kv("Seeding", "enabled" if seed else "disabled")

        try:
            status = self.monitor_aria2(gid, "Torrent File Download", seed=seed)
            self.print_aria2_item_paths(status)
            if not seed:
                self.verify_aria2_status_files(status, label="Torrent file download")
            if not seed:
                self.verify_download_outputs(save_dir, since=0, label="Torrent file download")
        except Exception as error:
            message = str(error)

            if "already registered" in message:
                self.print_status(f"Duplicate torrent detected after adding. Removing GID: {gid}", "warning")
                self.remove_existing_torrent_gid(gid)
                raise RuntimeError("Torrent already exists in aria2. Removed duplicate GID. Try again or use aria2 status.")

            raise error

        self.save_history({
            "type": "private_torrent_file" if private else "torrent_file",
            "source": source,
            "output": str(save_dir),
            "status": "completed",
            "seed": seed
        })

        self.print_status("Download completed.", "success")
        self.print_kv("Saved to", save_dir)

    def download_private_torrent(self):
        self.print_section("Private Torrent")
        print("Recommended: use a .torrent file from your private tracker.")
        print("Private mode disables DHT, DHT6, PEX, and LPD.")
        print("Seeding works only while the Colab runtime is alive.")
        print("For long-term seeding, use a seedbox or VPS.")

        source = self.prompt("Private .torrent URL, local path, or magnet")
        folder_name = self.prompt("Output folder name (optional)")
        speed_limit = self.prompt("Speed limit (optional, example 5M)")
        seed_answer = self.prompt("Keep seeding after download? y/n").lower()
        seed = seed_answer == "y"

        if not source:
            self.print_status("No torrent source was entered.", "warning")
            return

        if source.startswith("magnet:?"):
            self.print_status("Magnet links are not recommended for private trackers; use a .torrent file when possible.", "warning")
            self.download_magnet(
                magnet=source,
                folder_name=folder_name,
                speed_limit=speed_limit,
                private=True,
                seed=seed
            )
            return

        self.download_torrent_file(
            source=source,
            folder_name=folder_name,
            speed_limit=speed_limit,
            private=True,
            seed=seed
        )

    def torrent_menu(self):
        while True:
            self.print_menu("Torrent Tools", [
                ("1", "Add magnet link"),
                ("2", "Add .torrent file or URL"),
                ("3", "Private tracker torrent"),
                ("4", "Show aria2 status"),
                ("5", "Remove aria2 GID"),
                ("6", "Clear stopped aria2 results"),
                ("7", "Save aria2 session"),
                ("8", "Back to main menu")
            ])

            choice = self.prompt("Select torrent option")

            try:
                if choice == "1":
                    magnet = self.prompt("Magnet link")
                    folder_name = self.prompt("Output folder name (optional)")
                    speed_limit = self.prompt("Speed limit (optional, example 5M)")
                    seed_answer = self.prompt("Keep seeding after download? y/n").lower()
                    seed = seed_answer == "y"

                    self.download_magnet(
                        magnet=magnet,
                        folder_name=folder_name,
                        speed_limit=speed_limit,
                        private=False,
                        seed=seed
                    )

                elif choice == "2":
                    source = self.prompt(".torrent file URL or local path")
                    folder_name = self.prompt("Output folder name (optional)")
                    speed_limit = self.prompt("Speed limit (optional, example 5M)")
                    seed_answer = self.prompt("Keep seeding after download? y/n").lower()
                    seed = seed_answer == "y"

                    self.download_torrent_file(
                        source=source,
                        folder_name=folder_name,
                        speed_limit=speed_limit,
                        private=False,
                        seed=seed
                    )

                elif choice == "3":
                    self.download_private_torrent()

                elif choice == "4":
                    self.print_aria2_status()

                elif choice == "5":
                    self.remove_aria2_gid()

                elif choice == "6":
                    self.purge_aria2_stopped()

                elif choice == "7":
                    self.save_aria2_session()

                elif choice == "8":
                    break

                else:
                    self.print_status("Invalid torrent option. Choose a number from the menu.", "warning")

            except KeyboardInterrupt:
                self.save_aria2_session()
                self.print_status("Operation cancelled by user.", "warning")

            except Exception as error:
                self.save_aria2_session()
                self.print_status(f"Error: {error}", "error")

    def read_first_useful_line(self, path):
        path = Path(path)

        if not path.exists() or not path.is_file():
            return ""

        try:
            for line in path.read_text(errors="ignore").splitlines():
                value = line.strip()

                if value and not value.startswith("#"):
                    return value
        except Exception:
            return ""

        return ""

    def get_youtube_po_token(self):
        env_value = os.environ.get("AZUDL_YOUTUBE_PO_TOKEN", "").strip()

        if env_value:
            return env_value

        return self.read_first_useful_line(self.youtube_po_token_file)

    def get_youtube_visitor_data(self):
        env_value = os.environ.get("AZUDL_YOUTUBE_VISITOR_DATA", "").strip()

        if env_value:
            return env_value

        return self.read_first_useful_line(self.youtube_visitor_data_file)

    def get_youtube_player_client(self):
        value = os.environ.get("AZUDL_YOUTUBE_PLAYER_CLIENT", "").strip()

        if value:
            return value

        po_token = self.get_youtube_po_token()

        if po_token.startswith("mweb+"):
            return "mweb"

        if po_token.startswith("web+"):
            return "web"

        return ""

    def get_youtube_extractor_args(self):
        po_token = self.get_youtube_po_token()
        visitor_data = self.get_youtube_visitor_data()
        player_client = self.get_youtube_player_client()

        youtube_args = {}

        if player_client:
            youtube_args["player_client"] = [player_client]

        if po_token:
            youtube_args["po_token"] = [po_token]

        if visitor_data:
            youtube_args["visitor_data"] = [visitor_data]
            youtube_args["player_skip"] = ["webpage", "configs"]

        if youtube_args:
            return {"youtube": youtube_args}

        return None

    def get_youtube_auth_status(self):
        cookie_file = self.get_youtube_cookie_file()
        po_token = self.get_youtube_po_token()
        visitor_data = self.get_youtube_visitor_data()
        player_client = self.get_youtube_player_client()

        return {
            "cookie_file": str(cookie_file) if cookie_file else "",
            "po_token": bool(po_token),
            "visitor_data": bool(visitor_data),
            "player_client": player_client or ""
        }

    def print_youtube_auth_status(self):
        status = self.get_youtube_auth_status()
        self.print_section("YouTube Authentication Status")
        self.print_kv("Cookies file", status["cookie_file"] or "not configured")
        self.print_kv("PO Token", "configured" if status["po_token"] else "not configured")
        self.print_kv("Visitor Data", "configured" if status["visitor_data"] else "not configured")
        self.print_kv("Player client", status["player_client"] or "auto")
        self.print_status("Use cookies for most authenticated YouTube downloads. PO Token is an advanced fallback.", "info")

    def save_youtube_cookies_text(self, text):
        text = str(text or "").strip()

        if not text:
            raise ValueError("Cookies text is empty.")

        if "Netscape HTTP Cookie File" not in text and "\t" not in text:
            self.print_status("The provided text does not look like a Netscape cookies.txt export. It will still be saved.", "warning")

        self.youtube_cookies_file.write_text(text + "\n")

        try:
            os.chmod(self.youtube_cookies_file, 0o600)
        except Exception:
            pass

        self.print_status("YouTube cookies file saved.", "success")
        self.print_kv("Path", self.youtube_cookies_file)

    def save_youtube_po_token_text(self, po_token="", visitor_data="", player_client=""):
        po_token = str(po_token or "").strip()
        visitor_data = str(visitor_data or "").strip()
        player_client = str(player_client or "").strip()

        if po_token:
            if player_client and "+" not in po_token:
                po_token = f"{player_client}+{po_token}"

            self.youtube_po_token_file.write_text(po_token + "\n")

            try:
                os.chmod(self.youtube_po_token_file, 0o600)
            except Exception:
                pass

            self.print_status("YouTube PO Token saved.", "success")
            self.print_kv("PO Token file", self.youtube_po_token_file)

        if visitor_data:
            self.youtube_visitor_data_file.write_text(visitor_data + "\n")

            try:
                os.chmod(self.youtube_visitor_data_file, 0o600)
            except Exception:
                pass

            self.print_status("YouTube Visitor Data saved.", "success")
            self.print_kv("Visitor Data file", self.youtube_visitor_data_file)

        if not po_token and not visitor_data:
            raise ValueError("Enter a PO Token, Visitor Data, or both.")

    def clear_youtube_auth_files(self):
        for path in [self.youtube_cookies_file, self.youtube_po_token_file, self.youtube_visitor_data_file]:
            try:
                if path.exists():
                    path.unlink()
            except Exception as error:
                self.print_status(f"Could not remove {path}: {error}", "warning")

        self.ensure_youtube_cookie_file()
        self.ensure_youtube_po_token_files()
        self.ensure_github_token_file()
        self.print_status("YouTube authentication files were reset to templates.", "success")

    def print_youtube_po_token_help(self):
        self.print_section("YouTube PO Token Support")
        print("PO Token cannot be safely generated as a permanent static value by this script.")
        print("Use it only when anonymous access and cookies.txt both fail.")
        self.print_kv("PO Token file", self.youtube_po_token_file)
        self.print_kv("Optional Visitor Data file", self.youtube_visitor_data_file)
        print("Environment variables also work:")
        print("AZUDL_YOUTUBE_PO_TOKEN")
        print("AZUDL_YOUTUBE_VISITOR_DATA")
        print("AZUDL_YOUTUBE_PLAYER_CLIENT")
        self.print_kv("Recommended client", "mweb")
        self.print_kv("Example token line", "mweb+YOUR_PO_TOKEN")
        self.print_status("Keep token files private. Never upload real tokens to GitHub.", "warning")
        print("")

    def get_youtube_cookie_file(self):
        candidates = []

        env_path = os.environ.get("AZUDL_YOUTUBE_COOKIES", "").strip()

        if env_path:
            candidates.append(Path(env_path))

        candidates.extend([
            Path("/content/cookies.txt"),
            Path("/content/youtube_cookies.txt"),
            self.youtube_cookies_file,
            self.base_dir / "youtube_cookies.txt",
            self.base_dir / "cookies.txt"
        ])

        for path in candidates:
            try:
                if path.exists() and path.is_file() and path.stat().st_size > 0:
                    content = path.read_text(errors="ignore")
                    useful_lines = [
                        line for line in content.splitlines()
                        if line.strip() and not line.strip().startswith("#")
                    ]

                    if useful_lines:
                        return path
            except Exception:
                pass

        return None

    def print_youtube_cookie_help(self):
        self.print_section("YouTube Cookies Required")
        print("Create a Netscape cookies.txt file from a logged-in YouTube browser session.")
        print("Then put it in one of these paths:")
        print("/content/cookies.txt")
        print("/content/youtube_cookies.txt")
        print(str(self.youtube_cookies_file))
        print(str(self.base_dir / "youtube_cookies.txt"))
        print(str(self.base_dir / "cookies.txt"))
        print("You can also set:")
        print("os.environ['AZUDL_YOUTUBE_COOKIES'] = '/path/to/cookies.txt'")
        print("Then run the program again.")
        self.print_status("Keep cookies private. Never upload real cookies to GitHub.", "warning")
        print("")

    def parse_headers_json(self, text):
        text = str(text or "").strip()

        if not text:
            return None

        try:
            data = json.loads(text)
        except Exception:
            self.print_status("Invalid headers JSON was ignored.", "warning")
            return None

        if not isinstance(data, dict):
            self.print_status("Headers JSON must be an object; value was ignored.", "warning")
            return None

        cleaned = {}

        for key, value in data.items():
            key = str(key).strip()
            value = str(value).strip()

            if key and value:
                cleaned[key] = value

        return cleaned or None

    def download_direct(self, url, folder_name="", file_name="", speed_limit="", headers=None):
        url = url.strip()
        folder_name = self.normalize_folder_name(folder_name, "Direct")
        file_name = file_name.strip()
        save_dir = self.direct_dir / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        if not url.startswith(("http://", "https://", "ftp://")):
            raise ValueError("Invalid direct link.")

        options = {}

        if file_name:
            options["out"] = self.sanitize_name(file_name)

        if headers:
            header_lines = []

            for key, value in headers.items():
                if key and value:
                    header_lines.append(f"{key}: {value}")

            if header_lines:
                options["header"] = header_lines

        gid = self.add_aria2_download([url], save_dir, speed_limit, options)

        self.print_section("Direct Download Added")
        self.print_kv("Output folder", save_dir)

        status = self.monitor_aria2(gid, "Direct")
        self.print_aria2_item_paths(status)
        self.verify_aria2_status_files(status, label="Direct download")
        self.verify_download_outputs(save_dir, since=time.time() - 86400, label="Direct download")

        self.save_history({
            "type": "direct",
            "source": url,
            "output": str(save_dir),
            "status": "completed"
        })

        self.print_status("Download completed.", "success")
        self.print_kv("Saved to", save_dir)

    def get_youtube_available_qualities(self, url):
        cookie_file = self.get_youtube_cookie_file()
        ydl_options = {
            "quiet": True,
            "no_warnings": True
        }

        if cookie_file:
            ydl_options["cookiefile"] = str(cookie_file)
            self.print_kv("Using YouTube cookies", cookie_file)

        extractor_args = self.get_youtube_extractor_args()

        if extractor_args:
            ydl_options["extractor_args"] = extractor_args
            self.print_status("Using YouTube extractor args for PO Token.")

        with YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get("formats", [])
        standard_heights = [4320, 2160, 1440, 1080, 720, 480, 360, 240, 144]

        available_heights = set()

        for f in formats:
            h = f.get("height")
            vcodec = f.get("vcodec", "none")

            if h and vcodec and vcodec != "none":
                available_heights.add(int(h))

        qualities = ["best"]

        for h in standard_heights:
            if h in available_heights:
                qualities.append(str(h))

        return qualities, info

    def select_youtube_quality(self, url):
        self.print_status("Fetching YouTube video information.")

        try:
            qualities, info = self.get_youtube_available_qualities(url)
        except Exception as error:
            self.print_status(f"Could not fetch video information: {error}", "warning")

            if "Sign in to confirm" in str(error) or "not a bot" in str(error) or "cookies" in str(error).lower():
                self.print_youtube_cookie_help()
                self.print_youtube_po_token_help()

            self.print_status("Falling back to best available quality.", "warning")
            return "best", False

        title = info.get("title", "")
        duration = info.get("duration", 0)
        uploader = info.get("uploader", "")

        self.print_subsection("YouTube Video")

        if title:
            self.print_kv("Title", title)

        if uploader:
            self.print_kv("Channel", uploader)

        if duration:
            self.print_kv("Duration", self.format_seconds(int(duration)))

        audio_answer = self.prompt("Audio only? y/n").lower()

        if audio_answer == "y":
            return "best", True

        self.print_subsection("Available Qualities")

        for i, q in enumerate(qualities, 1):
            label = "Best available" if q == "best" else f"{q}p"
            print(f"  {i}. {label}")

        choice = self.prompt(f"Select quality (1-{len(qualities)}, default 1)")

        if choice.isdigit():
            idx = int(choice) - 1

            if 0 <= idx < len(qualities):
                selected = qualities[idx]
                label = "Best available" if selected == "best" else f"{selected}p"
                self.print_kv("Selected quality", label)
                return selected, False

        self.print_status("Invalid selection. Using best available quality.", "warning")
        return "best", False

    def build_youtube_format(self, quality, audio_only):
        quality = str(quality or "best").strip().lower()

        if audio_only:
            return "bestaudio/best"

        if quality == "best":
            return "bestvideo[vcodec*=?vp9]+bestaudio/bestvideo[vcodec*=?avc]+bestaudio/best"

        if quality in ["4320", "2160", "1440", "1080", "720", "480", "360", "240", "144"]:
            return (
                # 1. Exact height with VP9
                f"bestvideo[height={quality}][vcodec*=?vp9]+bestaudio/"
                # 2. Exact height with AVC (H.264)
                f"bestvideo[height={quality}][vcodec*=?avc]+bestaudio/"
                # 3. Exact height with any codec (fallback if neither VP9/AVC exists at this specific res)
                f"bestvideo[height={quality}][vcodec!=none]+bestaudio/"
                # 4. Nearest lower height with VP9
                f"bestvideo[height<={quality}][vcodec*=?vp9]+bestaudio/"
                # 5. Nearest lower height with AVC
                f"bestvideo[height<={quality}][vcodec*=?avc]+bestaudio/"
                # 6. Absolute final fallback
                f"best[height<={quality}]/best"
            )

        return "bestvideo[vcodec*=?vp9]+bestaudio/bestvideo[vcodec*=?avc]+bestaudio/best"

    def download_youtube(self, url, folder_name="", quality="best", audio_only=False, playlist=True, metadata=False):
        url = url.strip()

        if not url:
            raise ValueError("YouTube URL is required.")

        folder_name = self.normalize_folder_name(folder_name, "YouTube")
        save_dir = self.youtube_dir / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + secrets.token_hex(4)
        work_dir = self.temp_dir / "YouTube" / run_id
        work_dir.mkdir(parents=True, exist_ok=True)

        progress_state = {
            "bar": None,
            "last": 0
        }

        def hook(data):
            if data.get("status") == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes") or 0
                speed = data.get("speed") or 0

                if total and progress_state["bar"] is None:
                    progress_state["bar"] = tqdm(
                        total=total,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        desc="YouTube"
                    )

                if progress_state["bar"]:
                    if downloaded < progress_state["last"]:
                        progress_state["bar"].n = 0
                        progress_state["last"] = 0

                    delta = downloaded - progress_state["last"]

                    if delta > 0:
                        progress_state["bar"].update(delta)

                    progress_state["bar"].set_postfix({
                        "speed": self.format_bytes(speed) + "/s"
                    })

                progress_state["last"] = downloaded

            elif data.get("status") == "finished":
                if progress_state["bar"]:
                    progress_state["bar"].close()
                    progress_state["bar"] = None

                progress_state["last"] = 0
                self.print_status("Download stage finished. Processing media.")

        selected_format = self.build_youtube_format(quality, audio_only)

        if audio_only:
            postprocessors = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320"
                }
            ]
        else:
            postprocessors = [
                {
                    "key": "FFmpegMetadata"
                }
            ]

        options = {
            "format": selected_format,
            "outtmpl": str(work_dir / "%(playlist_index|)s%(playlist_index& - |)s%(title).200s.%(ext)s"),
            "merge_output_format": "mp4",
            "paths": {
                "home": str(work_dir),
                "temp": str(work_dir)
            },
            "noplaylist": not playlist,
            "ignoreerrors": bool(playlist),
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "concurrent_fragment_downloads": 4,
            "progress_hooks": [hook],
            "postprocessors": postprocessors,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "writeinfojson": metadata,
            "writethumbnail": metadata,
            "windowsfilenames": True,
            "restrictfilenames": False,
            "overwrites": False
        }

        cookie_file = self.get_youtube_cookie_file()

        if cookie_file:
            options["cookiefile"] = str(cookie_file)
            self.print_kv("Using YouTube cookies", cookie_file)

        extractor_args = self.get_youtube_extractor_args()

        if extractor_args:
            options["extractor_args"] = extractor_args
            self.print_status("Using YouTube extractor args for PO Token.")

        self.print_section("YouTube Download Started")
        self.print_kv("Format", selected_format)
        self.print_kv("Output folder", save_dir)
        self.print_kv("Temporary folder", work_dir)

        transferred_files = []

        try:
            with YoutubeDL(options) as ydl:
                result = ydl.download([url])

            if result not in [0, None]:
                raise RuntimeError(f"yt-dlp returned a non-zero result: {result}")

            local_files = self.collect_final_files(work_dir)

            if not local_files:
                raise RuntimeError(f"YouTube download finished, but no final media file was produced in temporary folder: {work_dir}")

            self.print_subsection("Local Files Ready for Transfer")

            for item in local_files[:20]:
                self.print_kv("Local", f"{self.format_bytes(item.stat().st_size)}  {item}")

            transferred_files = self.transfer_folder_contents_to_drive(work_dir, save_dir)

            if not transferred_files:
                raise RuntimeError("No files were transferred to Google Drive.")

            verified_files = self.verify_output_files(save_dir, label="YouTube download")

        except Exception as error:
            try:
                if progress_state["bar"]:
                    progress_state["bar"].close()
            except Exception:
                pass

            try:
                if work_dir.exists():
                    remaining_files = self.collect_final_files(work_dir)

                    if remaining_files:
                        self.print_status(f"Temporary files were kept for inspection: {work_dir}", "warning")
            except Exception:
                pass

            if "Sign in to confirm" in str(error) or "not a bot" in str(error) or "cookies" in str(error).lower():
                self.print_youtube_cookie_help()
                self.print_youtube_po_token_help()

            self.save_history({
                "type": "youtube",
                "source": url,
                "output": str(save_dir),
                "format": selected_format,
                "status": "failed",
                "error": str(error)
            })
            raise error

        self.save_history({
            "type": "youtube",
            "source": url,
            "output": str(save_dir),
            "format": selected_format,
            "status": "completed",
            "files": [str(item) for item in transferred_files]
        })

        self.force_drive_sync()
        self.print_status("Download completed, transferred, and verified on Google Drive.", "success")
        self.print_kv("Saved to", save_dir)
        self.print_drive_visibility_note(save_dir)

    def auto_download(self, value):
        link_type = self.detect_link_type(value)

        if link_type == "unknown":
            raise ValueError("Unknown link type.")

        self.print_kv("Detected link type", link_type)

        folder_name = self.prompt("Output folder name (optional)")

        if link_type == "torrent":
            speed_limit = self.prompt("Speed limit (optional, example 5M)")
            seed_answer = self.prompt("Keep seeding after download? y/n").lower()
            seed = seed_answer == "y"

            self.download_magnet(
                value,
                folder_name,
                speed_limit,
                private=False,
                seed=seed
            )

        elif link_type == "torrent_file":
            speed_limit = self.prompt("Speed limit (optional, example 5M)")
            seed_answer = self.prompt("Keep seeding after download? y/n").lower()
            seed = seed_answer == "y"

            self.download_torrent_file(
                value,
                folder_name,
                speed_limit,
                private=False,
                seed=seed
            )

        elif link_type == "youtube":
            quality, audio_only = self.select_youtube_quality(value)
            playlist_answer = self.prompt("Download playlist if detected? y/n").lower()
            playlist = playlist_answer != "n"
            metadata_answer = self.prompt("Save YouTube metadata and thumbnail? y/n").lower()
            metadata = metadata_answer == "y"

            self.download_youtube(
                url=value,
                folder_name=folder_name,
                quality=quality,
                audio_only=audio_only,
                playlist=playlist,
                metadata=metadata
            )

        elif link_type == "direct":
            file_name = self.prompt("File name (optional)")
            speed_limit = self.prompt("Speed limit (optional, example 5M)")
            headers_text = self.prompt('Headers JSON (optional, example {"User-Agent":"Mozilla/5.0"})')
            headers = self.parse_headers_json(headers_text)
            self.download_direct(value, folder_name, file_name, speed_limit, headers)

    def batch_download(self):
        self.print_section("Batch Download", "Enter one link per prompt. Submit an empty line to start.")

        links = []

        while True:
            value = self.prompt("Link")

            if not value:
                break

            links.append(value)

        if not links:
            self.print_status("No links were entered.", "warning")
            return

        folder_name = self.prompt("Batch folder name (optional)")
        folder_name = self.normalize_folder_name(folder_name, "Batch")
        speed_limit = self.prompt("Speed limit for direct/torrent downloads (optional, example 5M)")

        for index, link in enumerate(links, 1):
            self.print_section(f"Batch Item {index} of {len(links)}")
            self.print_kv("Link", link)

            link_type = self.detect_link_type(link)
            batch_folder = f"{folder_name}_{index}"

            try:
                if link_type == "torrent":
                    self.download_magnet(link, batch_folder, speed_limit, private=False, seed=False)

                elif link_type == "torrent_file":
                    self.download_torrent_file(link, batch_folder, speed_limit, private=False, seed=False)

                elif link_type == "youtube":
                    self.download_youtube(
                        url=link,
                        folder_name=batch_folder,
                        quality="best",
                        audio_only=False,
                        playlist=True,
                        metadata=False
                    )

                elif link_type == "direct":
                    self.download_direct(link, batch_folder, "", speed_limit)

                else:
                    self.print_status("Skipped link because the type could not be detected.", "warning")

            except Exception as error:
                self.print_status(f"Batch item failed: {error}", "error")

                self.save_history({
                    "type": link_type,
                    "source": link,
                    "output": batch_folder,
                    "status": "failed",
                    "error": str(error)
                })

    def parse_github_repo(self, value):
        value = str(value or "").strip()

        if not value:
            raise ValueError("GitHub repository URL is required.")

        if value.startswith("git@github.com:"):
            value = value.replace("git@github.com:", "https://github.com/", 1)

        if value.endswith(".git"):
            value = value[:-4]

        parsed = urlparse(value)

        if parsed.netloc.lower() not in ["github.com", "www.github.com"]:
            raise ValueError("Only github.com repository URLs are supported.")

        parts = [part for part in parsed.path.strip("/").split("/") if part]

        if len(parts) < 2:
            raise ValueError("Invalid GitHub repository URL. Expected https://github.com/owner/repo")

        owner = parts[0]
        repo = parts[1]

        owner = re.sub(r"[^A-Za-z0-9_.-]", "", owner)
        repo = re.sub(r"[^A-Za-z0-9_.-]", "", repo)

        if not owner or not repo:
            raise ValueError("Invalid GitHub owner or repository name.")

        return owner, repo

    def github_api_get(self, url):
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "AzuDl-GC2GD"
        }

        token = self.get_github_token()

        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)

        if response.status_code == 404:
            raise RuntimeError("GitHub resource was not found or is private.")

        if response.status_code == 403:
            raise RuntimeError("GitHub API rate limit or access restriction. Set AZUDL_GITHUB_TOKEN if needed.")

        response.raise_for_status()
        return response.json()

    def get_github_rate_limit(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "AzuDl-GC2GD"
        }

        token = self.get_github_token()

        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get("https://api.github.com/rate_limit", headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def print_github_auth_status(self):
        token = self.get_github_token()
        self.print_section("GitHub Authentication")
        self.print_kv("Token", "configured" if token else "not configured")
        self.print_kv("Token file", self.github_token_file)

        try:
            data = self.get_github_rate_limit()
            core = data.get("resources", {}).get("core", {})
            self.print_kv("Rate limit", core.get("limit", "unknown"))
            self.print_kv("Remaining", core.get("remaining", "unknown"))
            reset = core.get("reset")

            if reset:
                self.print_kv("Reset", datetime.fromtimestamp(int(reset)).strftime("%Y-%m-%d %H:%M:%S"))

        except Exception as error:
            self.print_status(f"Could not read GitHub rate limit: {error}", "warning")

    def make_github_default_branch_source_target(self, owner, repo, repo_info):
        branch = repo_info.get("default_branch", "main")

        return {
            "url": f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip",
            "name": f"{repo}-{branch}-source.zip",
            "group": "repository-source",
            "optional": False
        }

    def get_github_release_by_tag(self, owner, repo, tag):
        tag = str(tag or "").strip()

        if not tag:
            return None

        url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
        return self.github_api_get(url)

    def get_github_repo_info(self, repo_url):
        owner, repo = self.parse_github_repo(repo_url)
        repo_api = f"https://api.github.com/repos/{owner}/{repo}"
        releases_api = f"https://api.github.com/repos/{owner}/{repo}/releases"

        repo_info = self.github_api_get(repo_api)

        try:
            releases = self.github_api_get(releases_api)
        except Exception:
            releases = []

        return owner, repo, repo_info, releases

    def print_official_project_repo_info(self):
        self.print_github_repo_info(self.official_github_repo_url)

    def download_official_project_repository(self, mode="latest", include_assets=True, include_source=True, folder_name="", include_readme=True, include_license=False):
        return self.download_github_repository(
            repo_url=self.official_github_repo_url,
            mode=mode,
            include_assets=include_assets,
            include_source=include_source,
            folder_name=folder_name or "AzuDL-GC2GD-Official",
            release_tag="",
            include_readme=include_readme,
            include_license=include_license
        )

    def print_github_repo_info(self, repo_url):
        owner, repo, repo_info, releases = self.get_github_repo_info(repo_url)

        self.print_section("GitHub Repository")
        self.print_kv("Repository", f"{owner}/{repo}")
        self.print_kv("Name", repo_info.get("name", "unknown"))
        self.print_kv("Description", repo_info.get("description") or "none")
        self.print_kv("Default branch", repo_info.get("default_branch", "unknown"))
        self.print_kv("Stars", repo_info.get("stargazers_count", 0))
        self.print_kv("Forks", repo_info.get("forks_count", 0))
        self.print_kv("Open issues", repo_info.get("open_issues_count", 0))
        self.print_kv("Visibility", repo_info.get("visibility", "unknown"))
        self.print_kv("Archived", repo_info.get("archived", False))
        self.print_kv("Latest release", releases[0].get("tag_name", "none") if releases else "none")
        self.print_kv("Release count", len(releases))

        if releases:
            self.print_subsection("Recent Releases")

            for item in releases[:10]:
                tag = item.get("tag_name", "unknown")
                name = item.get("name") or tag
                assets = item.get("assets", [])
                published = item.get("published_at", "unknown")
                prerelease = "pre-release" if item.get("prerelease") else "release"
                print(f"{tag:<24} {published:<24} {len(assets)} asset(s)  {prerelease}  {name}")

    def get_github_download_targets(self, repo_url, mode="latest", include_assets=True, include_source=True, release_tag="", include_readme=False, include_license=False):
        owner, repo, repo_info, releases = self.get_github_repo_info(repo_url)
        mode = str(mode or "latest").strip().lower()

        targets = []
        selected_releases = []

        if mode == "tag":
            release = self.get_github_release_by_tag(owner, repo, release_tag)

            if not release:
                raise RuntimeError(f"Release tag was not found: {release_tag}")

            selected_releases = [release]

        elif mode in ["latest", "all_releases"]:
            selected_releases = releases[:1] if mode == "latest" else releases

        for release in selected_releases:
            tag = release.get("tag_name") or "release"

            if include_assets:
                for asset in release.get("assets", []):
                    url = asset.get("browser_download_url")
                    name = asset.get("name") or Path(urlparse(url).path).name

                    if url:
                        targets.append({
                            "url": url,
                            "name": name,
                            "group": f"releases/{self.sanitize_name(tag)}/assets",
                            "optional": False
                        })

            if include_source:
                zip_url = release.get("zipball_url")
                tar_url = release.get("tarball_url")

                if zip_url:
                    targets.append({
                        "url": zip_url,
                        "name": f"{repo}-{tag}-source.zip",
                        "group": f"releases/{self.sanitize_name(tag)}/source",
                        "optional": False
                    })

                if tar_url:
                    targets.append({
                        "url": tar_url,
                        "name": f"{repo}-{tag}-source.tar.gz",
                        "group": f"releases/{self.sanitize_name(tag)}/source",
                        "optional": False
                    })

        if mode in ["repo_source", "default_branch"]:
            targets.append(self.make_github_default_branch_source_target(owner, repo, repo_info))

        if include_readme:
            branch = repo_info.get("default_branch", "main")
            targets.append({
                "url": f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md",
                "name": "README.md",
                "group": "repository-files",
                "optional": True
            })

        if include_license:
            branch = repo_info.get("default_branch", "main")

            for candidate in ["LICENSE", "LICENSE.md", "LICENSE.txt"]:
                targets.append({
                    "url": f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{candidate}",
                    "name": candidate,
                    "group": "repository-files/license-candidates",
                    "optional": True
                })

        required_targets = [item for item in targets if not item.get("optional")]

        if not required_targets and mode in ["latest", "tag"] and include_source:
            self.print_status("No release asset or release source archive was found. Falling back to default branch source ZIP.", "warning")
            targets.append(self.make_github_default_branch_source_target(owner, repo, repo_info))

        return owner, repo, repo_info, releases, targets

    def download_file_requests(self, url, destination_file):
        destination_file = Path(destination_file)
        destination_file.parent.mkdir(parents=True, exist_ok=True)

        headers = {
            "User-Agent": "AzuDl-GC2GD"
        }

        token = self.get_github_token()

        if token:
            headers["Authorization"] = f"Bearer {token}"

        with requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True) as response:
            if response.status_code == 403:
                raise RuntimeError("GitHub download was blocked by rate limit or access restriction.")

            response.raise_for_status()

            total = int(response.headers.get("content-length", "0") or 0)

            with destination_file.open("wb") as handle:
                with tqdm(total=total if total > 0 else None, unit="B", unit_scale=True, unit_divisor=1024, desc=destination_file.name) as bar:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue

                        handle.write(chunk)
                        bar.update(len(chunk))

        if not destination_file.exists() or destination_file.stat().st_size <= 0:
            raise RuntimeError(f"Downloaded file is empty: {destination_file}")

        return destination_file

    def download_github_repository(self, repo_url, mode="latest", include_assets=True, include_source=True, folder_name="", release_tag="", include_readme=False, include_license=False):
        owner, repo, repo_info, releases, targets = self.get_github_download_targets(
            repo_url=repo_url,
            mode=mode,
            include_assets=include_assets,
            include_source=include_source,
            release_tag=release_tag,
            include_readme=include_readme,
            include_license=include_license
        )

        if not targets:
            raise RuntimeError("No downloadable GitHub targets were found for the selected options.")

        folder_name = self.normalize_folder_name(folder_name, f"{owner}_{repo}")
        final_base = self.github_dir / folder_name
        work_dir = self.temp_dir / "GitHub" / (datetime.now().strftime("%Y%m%d_%H%M%S_") + secrets.token_hex(4))
        work_dir.mkdir(parents=True, exist_ok=True)

        self.print_section("GitHub Download Started")
        self.print_kv("Repository", f"{owner}/{repo}")
        self.print_kv("Mode", mode)
        self.print_kv("Targets", len(targets))
        self.print_kv("Output folder", final_base)
        self.print_kv("Temporary folder", work_dir)

        transferred = []

        try:
            for index, target in enumerate(targets, 1):
                name = self.sanitize_name(target["name"])
                group = Path(target.get("group", "downloads"))
                local_file = work_dir / group / name

                self.print_subsection(f"GitHub Target {index} of {len(targets)}")
                self.print_kv("File", name)
                self.print_kv("Source", target["url"])

                try:
                    downloaded = self.download_file_requests(target["url"], local_file)
                except Exception as error:
                    if target.get("optional"):
                        self.print_status(f"Optional file skipped: {name}", "warning")
                        continue
                    raise error

                drive_target_dir = final_base / group
                moved = self.safe_transfer_to_drive(downloaded, drive_target_dir, remove_source=True)

                if moved:
                    transferred.append(moved)
                    self.print_kv("Saved", moved)

            if not transferred:
                raise RuntimeError("GitHub download finished but no files were transferred to Google Drive.")

            self.verify_output_files(final_base, label="GitHub download")

        finally:
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

        self.save_history({
            "type": "github",
            "source": repo_url,
            "output": str(final_base),
            "status": "completed",
            "mode": mode,
            "files": [str(item) for item in transferred]
        })

        self.force_drive_sync()
        self.print_status("GitHub files downloaded, transferred, and verified on Google Drive.", "success")
        self.print_kv("Saved to", final_base)
        self.print_drive_visibility_note(final_base)

    def storage_report(self):
        self.print_section("Storage Report")
        self.print_drive_storage_summary()
        self.print_subsection("Project Folders")

        folders = [
            self.torrent_dir,
            self.youtube_dir,
            self.direct_dir,
            self.batch_dir,
            self.github_dir,
            self.archive_dir,
            self.logs_dir
        ]

        for folder in folders:
            print(f"{self.format_bytes(self.folder_size(folder)):<12} {folder}")

    def folder_size(self, folder):
        folder = Path(folder)

        if not folder.exists():
            return 0

        total = 0

        for item in folder.glob("**/*"):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except Exception:
                    pass

        return total

    def sha256_file(self, file_path):
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if not file_path.is_file():
            raise ValueError("Path is not a file")

        h = hashlib.sha256()
        total = file_path.stat().st_size

        with file_path.open("rb") as f, tqdm(total=total, unit="B", unit_scale=True, unit_divisor=1024, desc="SHA256") as bar:
            while True:
                chunk = f.read(1024 * 1024)

                if not chunk:
                    break

                h.update(chunk)
                bar.update(len(chunk))

        return h.hexdigest()

    def hash_latest_file(self):
        latest = self.get_latest_file()

        if not latest:
            self.print_status("No downloaded files were found.", "info")
            return

        self.print_section("SHA256 - Latest File")
        self.print_kv("File", latest)
        self.print_kv("Size", self.format_bytes(latest.stat().st_size))

        digest = self.sha256_file(latest)

        self.print_kv("SHA256", digest)

    def sha256_selected_file(self):
        file_path = self.select_file()

        if not file_path:
            return

        digest = self.sha256_file(file_path)

        self.print_section("SHA256 - Selected File")
        self.print_kv("File", file_path)
        self.print_kv("SHA256", digest)

    def zip_folder(self):
        source = self.prompt("Folder path to zip")

        if not source:
            self.print_status("No folder path was entered.", "warning")
            return

        source_path = Path(source)

        if not source_path.exists():
            self.print_status("Folder does not exist.", "error")
            return

        if not source_path.is_dir():
            self.print_status("Path is not a folder.", "error")
            return

        output_name = self.prompt("Output ZIP name (optional)")

        if not output_name:
            output_name = source_path.name + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        output_name = self.sanitize_name(output_name)
        output_base = self.archive_dir / output_name

        self.print_status("Creating ZIP archive.")
        result = shutil.make_archive(str(output_base), "zip", str(source_path))

        self.print_status("ZIP archive created.", "success")
        self.print_kv("Archive", result)

        self.save_history({
            "type": "zip",
            "source": str(source_path),
            "output": result,
            "status": "completed"
        })

    def zip_latest_folder(self):
        latest_folder = self.get_latest_downloaded_folder()

        if not latest_folder:
            self.print_status("No downloaded folders were found.", "info")
            return

        self.print_section("ZIP Latest Folder")
        self.print_kv("Latest folder", latest_folder)

        confirm = self.prompt("Create a ZIP archive from this folder? y/n").lower()

        if confirm != "y":
            self.print_status("ZIP operation cancelled.", "warning")
            return

        output_name = latest_folder.name + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_name = self.sanitize_name(output_name)
        output_base = self.archive_dir / output_name

        self.print_status("Creating ZIP archive.")
        result = shutil.make_archive(str(output_base), "zip", str(latest_folder))

        self.print_status("ZIP archive created.", "success")
        self.print_kv("Archive", result)

        self.save_history({
            "type": "zip",
            "source": str(latest_folder),
            "output": result,
            "status": "completed"
        })

    def print_developer(self):
        self.print_section("Project Links", "Official links, version details, and support channels.")
        self.print_kv("Project", self.project_name)
        self.print_kv("Full name", self.project_subtitle)
        self.print_kv("Version", self.version)
        self.print_kv("Developer", "The Azizi")
        self.print_kv("GitHub", "https://github.com/TheGreatAzizi")
        self.print_kv("Official repository", self.official_github_repo_url)
        self.print_kv("Git", "https://git.theazizi.ir/TheAzizi")
        self.print_kv("Website", "https://theazizi.ir")
        self.print_kv("X", "https://x.com/the_azzi")
        self.print_kv("Telegram", "https://t.me/luluch_code")
        self.print_status("Keep authentication files private.", "warning")

    def run_system_diagnostic_test(self):
        self.print_section("AzuDl Diagnostic Test")

        tests = [
            {
                "name": "Direct Download",
                "type": "direct",
                "value": "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore"
            },
            {
                "name": "GitHub Repository",
                "type": "github",
                "value": self.official_github_repo_url
            },
            {
                "name": "YouTube Access",
                "type": "youtube",
                "value": "https://www.youtube.com/watch?v=jNQXAC9IVRw"
            },
            {
                "name": "Torrent Magnet",
                "type": "torrent",
                "value": "magnet:?xt=urn:btih:5a3d1b149e9c5d7f6b1f0f9d4a6e7b2c3d4e5f60&dn=ubuntu-test"
            }
        ]

        results = []

        for item in tests:
            name = item["name"]
            kind = item["type"]

            try:
                self.print_subsection(name)

                if kind == "direct":
                    response = requests.get(item["value"], timeout=20)
                    response.raise_for_status()

                    if response.text:
                        self.print_status("Direct download access OK.", "success")
                        results.append((name, True, "OK"))
                    else:
                        raise RuntimeError("Empty response")

                elif kind == "github":
                    owner, repo, repo_info, releases = self.get_github_repo_info(item["value"])

                    self.print_status(f"GitHub API OK for {owner}/{repo}", "success")
                    results.append((name, True, f"{len(releases)} release(s)"))

                elif kind == "youtube":
                    with YoutubeDL({
                        "quiet": True,
                        "no_warnings": True,
                        "skip_download": True
                    }) as ydl:
                        info = ydl.extract_info(item["value"], download=False)

                    title = info.get("title", "unknown")
                    self.print_status(f"YouTube access OK: {title}", "success")
                    results.append((name, True, title))

                elif kind == "torrent":
                    gid = self.add_aria2_download(
                        [item["value"]],
                        self.base_dir / "DiagnosticTorrent",
                        "",
                        self.build_torrent_options(private=False, seed=False)
                    )

                    time.sleep(5)

                    status = self.get_aria2_status(gid)
                    state = status.get("status", "unknown")

                    self.remove_existing_torrent_gid(gid)

                    if state in ["active", "waiting", "complete"]:
                        self.print_status("aria2 torrent engine OK.", "success")
                        results.append((name, True, state))
                    else:
                        raise RuntimeError(f"Unexpected aria2 state: {state}")

            except Exception as error:
                self.print_status(f"{name} failed: {error}", "error")
                results.append((name, False, str(error)))

        self.print_section("Diagnostic Summary")

        ok_count = 0

        for name, success, details in results:
            status = "PASS" if success else "FAIL"

            if success:
                ok_count += 1

            print(f"{status:<6} {name:<24} {details}")

        print("")
        self.print_kv("Passed", f"{ok_count}/{len(results)}")

        if ok_count == len(results):
            self.print_status("All systems are operational.", "success")
        else:
            self.print_status("One or more systems failed. Review the diagnostic log above.", "warning")

    def print_help(self):
        self.print_section("AzuDl - GC2GD User Guide")
        text = """
AzuDl - GC2GD User Guide

What it does
AzuDl - GC2GD is a single-cell Google Colab downloader that saves files directly to Google Drive. It supports direct links, magnet links, .torrent files, YouTube videos and playlists, batch downloads, resumable aria2 sessions, download history, storage reports, SHA256 checksums, and ZIP archive creation.

Default output folder
/content/drive/MyDrive/AzuDl-GC2GD

Quick start in Google Colab
1. Run the notebook cell.
2. Allow Google Drive access when Colab asks for permission.
3. Use the GUI tabs to choose Dashboard, Auto, Direct, YouTube, Auth, Torrent, Batch, GitHub, Files, Archives, Maintenance, Project, or Guide.
4. Keep the Colab runtime connected while active downloads or torrent seeding are running.

Interface modes
The GUI is the default interface for public Colab users.

Run the GUI:
launch_gui()

Run the classic CLI:
main()

Force CLI before running the cell:
os.environ["AZUDL_INTERFACE"] = "cli"

Auto mode
Paste one link and AzuDl detects the type automatically:
- Direct HTTP/HTTPS/FTP links
- YouTube videos and playlists
- Magnet links
- .torrent URLs and local .torrent files

Direct downloads
Direct mode supports optional output folders, custom filenames, speed limits, and HTTP headers.

Header example:
{"User-Agent":"Mozilla/5.0","Referer":"https://example.com"}

Speed limit examples:
500K
2M
10M

YouTube downloads
YouTube mode can download videos, playlists, audio-only MP3 files, thumbnails, and metadata. Quality can be set to best available or a target resolution such as 1080p or 720p. Video and audio are merged automatically with ffmpeg.
YouTube downloads are processed in local Colab temporary storage first, then safely copied to Google Drive and verified. If the file is not visible on Drive after transfer, AzuDl reports an error instead of showing a false success.
AzuDl downloads YouTube media into local Colab temporary storage first, then moves the finished output to Google Drive. This improves reliability and prevents post-processing issues on mounted Drive paths.

YouTube cookies
Some YouTube downloads may require authentication because Colab runs on data-center IP addresses. Use a Netscape-format cookies.txt file exported from your own browser session.

Accepted cookie paths:
/content/cookies.txt
/content/youtube_cookies.txt
/content/drive/MyDrive/AzuDl-GC2GD/Logs/youtube_cookies.txt
/content/drive/MyDrive/AzuDl-GC2GD/youtube_cookies.txt
/content/drive/MyDrive/AzuDl-GC2GD/cookies.txt

Environment variable alternative:
AZUDL_YOUTUBE_COOKIES=/path/to/cookies.txt

Cookie safety
cookies.txt can grant access to your logged-in session. Never publish it, share it, or commit it to GitHub.

YouTube PO Token
PO Token support is available for advanced yt-dlp YouTube setups. Use it only when anonymous access and cookies.txt both fail.

Token file:
/content/drive/MyDrive/AzuDl-GC2GD/Logs/youtube_po_token.txt

Recommended token line format:
mweb+YOUR_PO_TOKEN

Optional visitor data file:
/content/drive/MyDrive/AzuDl-GC2GD/Logs/youtube_visitor_data.txt

Torrent downloads
Torrent mode supports magnet links, .torrent URLs, local .torrent files, private tracker mode, optional seeding, aria2 status, GID removal, stopped-result cleanup, and session saving.

Private torrents
For private trackers, prefer a .torrent file and enable private mode. Private mode disables DHT, DHT6, PEX, and LPD. Magnet links are not recommended for private trackers because they may not preserve private-tracker metadata reliably.

Seeding note
Seeding only continues while the Colab runtime is alive. Google Colab is not suitable for permanent seeding. Use a seedbox or VPS for long-term seeding.

Resume support
AzuDl uses aria2 session persistence.

Session file:
/content/drive/MyDrive/AzuDl-GC2GD/Logs/aria2.session

If Colab disconnects, run the notebook again and open Maintenance > aria2 status to inspect or continue active downloads. AzuDl cannot bypass Google Colab runtime limits.

Duplicate torrent handling
AzuDl reads the torrent InfoHash before adding .torrent files. If the same torrent already exists in aria2, AzuDl resumes or monitors the existing GID instead of adding a duplicate. If the existing torrent is in an error state, AzuDl removes it and retries.

Batch downloads
Batch mode accepts one link per line. Each link is detected automatically and saved into numbered batch folders.

GitHub downloads
The GitHub tab accepts a public GitHub repository URL such as:
https://github.com/owner/repository

Official project tab:
The Official tab is dedicated to the AzuDl project repository:
https://github.com/TheGreatAzizi/AzuDL-GC2GD

Use it to download official releases or the default branch source archive without entering the repository URL manually. If no release files are available, AzuDl falls back to the default branch source ZIP.

System diagnostic:
The Maintenance tab includes a Run diagnostic button.
It automatically tests:
- aria2 torrent engine
- Direct downloads
- YouTube access
- GitHub API and repository access

Google Drive visibility:
AzuDl verifies files on the Colab Google Drive mount. The Google Drive web/app UI may still need a refresh or a short sync delay. The Maintenance tab includes Force Drive sync.

Available GitHub modes:
- Latest release: downloads the newest release assets and optional source archives
- All releases: downloads assets and source archives from all releases returned by GitHub
- Default branch source: downloads a ZIP archive of the default branch

Private repositories or higher API limits:
Paste a GitHub token in the GitHub tab and click Save token. Environment variable AZUDL_GITHUB_TOKEN also works.

Extra GitHub options:
- Specific release tag downloads a selected release tag
- README downloads README.md from the default branch
- License tries common license filenames from the default branch

Files and archives
The Files tab lists downloaded files, shows the latest file, and computes SHA256 checksums. The Archives tab creates ZIP files and stores them in the Archives folder.

Maintenance
The Maintenance tab includes aria2 status, stopped-result cleanup, GID removal, session saving, and storage reporting.

Validation behavior
Required fields are checked before each operation. Missing or invalid inputs are shown as clean warning messages in the Output panel instead of raw Python tracebacks.

Privacy
Cookies, PO tokens, visitor data, and account files are private credentials. Do not share them publicly.

Responsible use
Use AzuDl only for content that is owned, permitted by the rights holder, or otherwise legally accessible. Respect website terms, copyright rules, private tracker rules, and local laws.
"""
        print(text.strip())


class AzuDlGC2GDGUI:
    def __init__(self, app):
        self.app = app
        self.output = widgets.Output(layout=widgets.Layout(
            height="470px",
            overflow_y="auto",
            padding="12px"
        ))
        self.output.add_class("azudl-output")
        self.storage_html = widgets.HTML()
        self.status_html = widgets.HTML()
        self.root = self.build()

    def css(self):
        return widgets.HTML(value="""
        <style>
        :root {
            --azudl-bg: #f4f7fb;
            --azudl-shell: #eaf0f7;
            --azudl-surface: #ffffff;
            --azudl-surface-soft: #f8fbff;
            --azudl-field: #ffffff;
            --azudl-field-focus: #f7fbff;
            --azudl-border: #d4deea;
            --azudl-border-strong: #b8c7d9;
            --azudl-text: #172033;
            --azudl-muted: #66758a;
            --azudl-primary: #2563eb;
            --azudl-primary-dark: #1d4ed8;
            --azudl-primary-soft: #dbeafe;
            --azudl-accent: #0f766e;
            --azudl-success: #16a34a;
            --azudl-success-dark: #15803d;
            --azudl-warning: #f59e0b;
            --azudl-warning-dark: #b45309;
            --azudl-danger: #ef4444;
            --azudl-danger-dark: #b91c1c;
            --azudl-purple: #7c3aed;
            --azudl-slate: #475569;
            --azudl-note-bg: #eff6ff;
            --azudl-note-border: #60a5fa;
            --azudl-console: #111827;
            --azudl-console-text: #f9fafb;
        }

        .azudl-root {
            background: var(--azudl-bg) !important;
            border: 1px solid var(--azudl-border) !important;
            border-radius: 16px !important;
            padding: 14px !important;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
            color: var(--azudl-text) !important;
        }

        .azudl-hero {
            border: 1px solid rgba(255,255,255,.26) !important;
            border-radius: 16px !important;
            padding: 20px 22px !important;
            background: linear-gradient(135deg, #172554 0%, #2563eb 55%, #0f766e 100%) !important;
            color: #ffffff !important;
            margin-bottom: 12px !important;
            box-shadow: 0 12px 30px rgba(23, 37, 84, .18) !important;
        }
        .azudl-title {
            font-size: 26px !important;
            font-weight: 800 !important;
            letter-spacing: -.02em !important;
            line-height: 1.15 !important;
            color: #ffffff !important;
        }
        .azudl-subtitle {
            font-size: 13px !important;
            color: #dbeafe !important;
            margin-top: 6px !important;
            max-width: 760px !important;
        }
        .azudl-badge {
            display: inline-block !important;
            margin-top: 12px !important;
            padding: 4px 10px !important;
            border-radius: 999px !important;
            background: rgba(255,255,255,.15) !important;
            border: 1px solid rgba(255,255,255,.30) !important;
            font-size: 12px !important;
            color: #ffffff !important;
        }

        .azudl-panel {
            border: 1px solid var(--azudl-border) !important;
            border-radius: 16px !important;
            background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%) !important;
            padding: 16px !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, .065) !important;
        }
        .azudl-panel-title {
            font-weight: 760 !important;
            color: var(--azudl-text) !important;
            font-size: 16px !important;
            margin-bottom: 3px !important;
        }
        .azudl-panel-copy {
            color: var(--azudl-muted) !important;
            font-size: 12.5px !important;
            margin-bottom: 10px !important;
            line-height: 1.45 !important;
        }
        .azudl-note {
            border-left: 4px solid var(--azudl-note-border) !important;
            background: var(--azudl-note-bg) !important;
            color: #1e3a8a !important;
            padding: 10px 12px !important;
            border-radius: 10px !important;
            font-size: 12.5px !important;
            line-height: 1.45 !important;
        }

        .azudl-stat-row {
            display: grid !important;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)) !important;
            gap: 10px !important;
            margin-bottom: 10px !important;
        }
        .azudl-stat {
            border: 1px solid var(--azudl-border) !important;
            border-radius: 12px !important;
            background: var(--azudl-surface) !important;
            padding: 11px 12px !important;
            box-shadow: 0 2px 10px rgba(15, 23, 42, .04) !important;
        }
        .azudl-stat-label {
            color: var(--azudl-muted) !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: .055em !important;
        }
        .azudl-stat-value {
            color: var(--azudl-text) !important;
            font-weight: 760 !important;
            font-size: 15px !important;
            margin-top: 4px !important;
            word-break: break-word !important;
        }
        .azudl-meter {
            height: 10px !important;
            border-radius: 999px !important;
            overflow: hidden !important;
            background: #dbeafe !important;
            margin-bottom: 12px !important;
        }
        .azudl-meter-fill {
            height: 100% !important;
            background: linear-gradient(90deg, var(--azudl-primary), var(--azudl-accent)) !important;
        }
        .azudl-output {
            border: 1px solid #1f2937 !important;
            border-radius: 14px !important;
            background: radial-gradient(circle at top left, #1f2937 0%, #111827 36%, #030712 100%) !important;
            color: var(--azudl-console-text) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 10px 24px rgba(15,23,42,.14) !important;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
            line-height: 1.55 !important;
        }
        .azudl-output pre,
        .azudl-output code,
        .azudl-output .output_text,
        .azudl-output .jp-OutputArea-output {
            color: #f9fafb !important;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
            font-size: 12.5px !important;
        }

        .azudl-button {
            position: relative !important;
            overflow: hidden !important;
            border-radius: 14px !important;
            font-weight: 850 !important;
            border: 1px solid transparent !important;
            min-height: 44px !important;
            font-size: 14px !important;
            letter-spacing: .01em !important;
            text-shadow: none !important;
            box-shadow: 0 8px 18px rgba(15, 23, 42, .10), inset 0 1px 0 rgba(255,255,255,.18) !important;
            transition: transform .14s ease, box-shadow .14s ease, filter .14s ease, border-color .14s ease !important;
        }
        .azudl-button:before {
            content: "" !important;
            position: absolute !important;
            inset: 0 !important;
            background: linear-gradient(180deg, rgba(255,255,255,.18), rgba(255,255,255,0)) !important;
            pointer-events: none !important;
        }
        .azudl-button:hover {
            transform: translateY(-1px) !important;
            filter: brightness(1.04) saturate(1.04) !important;
            box-shadow: 0 14px 28px rgba(15, 23, 42, .16), inset 0 1px 0 rgba(255,255,255,.22) !important;
        }
        .azudl-button:active {
            transform: translateY(0) scale(.99) !important;
            box-shadow: 0 6px 14px rgba(15, 23, 42, .12) !important;
        }
        .azudl-button:disabled {
            opacity: .56 !important;
            filter: grayscale(.18) saturate(.7) !important;
            transform: none !important;
            cursor: not-allowed !important;
            box-shadow: none !important;
        }
        .azudl-start {
            min-height: 58px !important;
            font-size: 15.5px !important;
            border-radius: 18px !important;
            padding: 0 18px !important;
            box-shadow: 0 18px 36px rgba(22, 163, 74, .28), inset 0 1px 0 rgba(255,255,255,.22) !important;
        }
        .azudl-start:hover {
            box-shadow: 0 22px 42px rgba(22, 163, 74, .34), inset 0 1px 0 rgba(255,255,255,.24) !important;
        }
        .azudl-primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 52%, #1d4ed8 100%) !important;
            color: #ffffff !important;
            border-color: rgba(37, 99, 235, .42) !important;
        }
        .azudl-info {
            background: linear-gradient(135deg, #06b6d4 0%, #2563eb 60%, #1d4ed8 100%) !important;
            color: #ffffff !important;
            border-color: rgba(37, 99, 235, .38) !important;
        }
        .azudl-success {
            background: linear-gradient(135deg, #34d399 0%, #22c55e 42%, #16a34a 72%, #15803d 100%) !important;
            color: #ffffff !important;
            border-color: rgba(34, 197, 94, .45) !important;
        }
        .azudl-warning {
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 58%, #b45309 100%) !important;
            color: #ffffff !important;
            border-color: rgba(245, 158, 11, .42) !important;
        }
        .azudl-danger {
            background: linear-gradient(135deg, #fb7185 0%, #ef4444 54%, #b91c1c 100%) !important;
            color: #ffffff !important;
            border-color: rgba(239, 68, 68, .42) !important;
        }
        .azudl-neutral {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 55%, #eef2f7 100%) !important;
            border-color: var(--azudl-border-strong) !important;
            color: #1e293b !important;
            box-shadow: 0 6px 14px rgba(15, 23, 42, .07), inset 0 1px 0 rgba(255,255,255,.80) !important;
        }
        .azudl-neutral:hover {
            background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%) !important;
            border-color: var(--azudl-primary) !important;
            color: var(--azudl-primary-dark) !important;
        }
        .azudl-soft {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
            color: #334155 !important;
            border-color: #cbd5e1 !important;
        }
        .azudl-action-row {
            gap: 10px !important;
            flex-flow: row wrap !important;
            align-items: center !important;
        }
        .azudl-danger-zone {
            border: 1px solid #fecaca !important;
            background: #fff1f2 !important;
            border-radius: 12px !important;
            padding: 10px !important;
        }

        .azudl-link-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 44px;
            padding: 0 18px;
            border-radius: 14px;
            font-weight: 850;
            text-decoration: none !important;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 55%, #eef2f7 100%);
            color: #1e293b !important;
            border: 1px solid var(--azudl-border-strong);
            box-shadow: 0 6px 14px rgba(15, 23, 42, .07), inset 0 1px 0 rgba(255,255,255,.80);
        }
        .azudl-link-button:hover {
            border-color: var(--azudl-primary);
            color: var(--azudl-primary-dark) !important;
        }

        .azudl-tabs {
            max-width: 100% !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            -webkit-overflow-scrolling: touch !important;
        }
        .azudl-tabs > .p-TabBar,
        .azudl-tabs > .lm-TabBar,
        .azudl-tabs .p-TabBar-content,
        .azudl-tabs .lm-TabBar-content {
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            max-width: 100% !important;
            scrollbar-width: thin !important;
        }
        .azudl-tabs .p-TabBar-tab,
        .azudl-tabs .lm-TabBar-tab,
        .azudl-tabs .p-TabBar-tabLabel,
        .azudl-tabs .lm-TabBar-tabLabel {
            flex: 0 0 auto !important;
            min-width: max-content !important;
            max-width: none !important;
            width: auto !important;
            white-space: nowrap !important;
            overflow: visible !important;
            text-overflow: clip !important;
        }
        .azudl-tabs .widget-tab-contents,
        .azudl-tabs .p-Widget,
        .azudl-tabs .lm-Widget {
            max-width: 100% !important;
        }
        @media (max-width: 640px) {
            .azudl-card {
                padding: 12px !important;
                border-radius: 14px !important;
            }
            .azudl-title {
                font-size: 24px !important;
            }
            .azudl-button,
            .azudl-start,
            .azudl-link-button {
                width: 100% !important;
                min-width: 100% !important;
            }
            .azudl-action-row {
                display: flex !important;
                flex-direction: column !important;
                align-items: stretch !important;
                width: 100% !important;
            }
        }

        .azudl-tabs,
        .azudl-tabs .widget-tab,
        .azudl-tabs .widget-tab-contents,
        .azudl-tabs .p-TabPanel,
        .azudl-tabs .p-TabPanel-stackedPanel,
        .azudl-tabs .lm-TabPanel,
        .azudl-tabs .lm-TabPanel-stackedPanel,
        .azudl-tabs .lm-Widget {
            background: var(--azudl-shell) !important;
            color: var(--azudl-text) !important;
        }
        .azudl-tabs .widget-tab > .p-TabBar,
        .azudl-tabs .widget-tab > .lm-TabBar,
        .azudl-tabs .p-TabBar,
        .azudl-tabs .lm-TabBar {
            background: var(--azudl-shell) !important;
            border: 0 !important;
            padding: 6px 6px 0 6px !important;
        }
        .azudl-tabs .p-TabBar-content,
        .azudl-tabs .lm-TabBar-content {
            background: transparent !important;
        }
        .azudl-tabs .p-TabBar-tab,
        .azudl-tabs .lm-TabBar-tab {
            background: #f8fafc !important;
            color: #334155 !important;
            border: 1px solid var(--azudl-border) !important;
            border-bottom-color: var(--azudl-border-strong) !important;
            border-radius: 12px 12px 0 0 !important;
            margin: 0 4px 0 0 !important;
            min-height: 38px !important;
            padding: 0 16px !important;
            box-shadow: none !important;
        }
        .azudl-tabs .p-TabBar-tab:hover,
        .azudl-tabs .lm-TabBar-tab:hover {
            background: #eef6ff !important;
            color: var(--azudl-primary-dark) !important;
        }
        .azudl-tabs .p-TabBar-tab.p-mod-current,
        .azudl-tabs .lm-TabBar-tab.lm-mod-current,
        .azudl-tabs .lm-TabBar-tab.p-mod-current,
        .azudl-tabs .p-TabBar-tab.lm-mod-current {
            background: #ffffff !important;
            color: var(--azudl-primary-dark) !important;
            font-weight: 800 !important;
            border-color: var(--azudl-border-strong) !important;
            border-top: 3px solid var(--azudl-primary) !important;
            border-bottom-color: #ffffff !important;
        }
        .azudl-tabs .p-TabBar-tabLabel,
        .azudl-tabs .lm-TabBar-tabLabel {
            color: inherit !important;
            font-weight: inherit !important;
            font-size: 13px !important;
        }

        .azudl-root .widget-text,
        .azudl-root .widget-textarea,
        .azudl-root .widget-dropdown,
        .azudl-root .widget-checkbox,
        .azudl-root .widget-hbox,
        .azudl-root .widget-vbox {
            color: var(--azudl-text) !important;
        }
        .azudl-root .widget-label,
        .azudl-root label,
        .azudl-root .widget-inline-hbox .widget-label {
            color: var(--azudl-muted) !important;
            font-weight: 650 !important;
        }
        .azudl-root input,
        .azudl-root textarea,
        .azudl-root select,
        .azudl-root .widget-text input,
        .azudl-root .widget-textarea textarea,
        .azudl-root .widget-dropdown select {
            background: var(--azudl-field) !important;
            color: var(--azudl-text) !important;
            border: 1px solid var(--azudl-border-strong) !important;
            border-radius: 10px !important;
            box-shadow: inset 0 1px 2px rgba(15, 23, 42, .04) !important;
        }
        .azudl-root input:focus,
        .azudl-root textarea:focus,
        .azudl-root select:focus,
        .azudl-root .widget-text input:focus,
        .azudl-root .widget-textarea textarea:focus,
        .azudl-root .widget-dropdown select:focus {
            background: var(--azudl-field-focus) !important;
            border-color: var(--azudl-primary) !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, .14) !important;
            outline: none !important;
        }
        .azudl-root input::placeholder,
        .azudl-root textarea::placeholder {
            color: #94a3b8 !important;
            opacity: 1 !important;
        }
        .azudl-root .widget-checkbox input[type="checkbox"] {
            accent-color: var(--azudl-primary) !important;
        }
        </style>
        """)

    def build(self):
        header = widgets.HTML(value=f"""
        <div class="azudl-hero">
          <div class="azudl-title">{self.app.project_name}</div>
          <div class="azudl-subtitle">Universal downloader for Google Colab with Google Drive storage</div>
          <span class="azudl-badge">Version {self.app.version}</span>
        </div>
        """)

        tabs = widgets.Tab(children=[
            self.build_dashboard_tab(),
            self.build_auto_tab(),
            self.build_direct_tab(),
            self.build_youtube_tab(),
            self.build_auth_tab(),
            self.build_torrent_tab(),
            self.build_batch_tab(),
            self.build_github_tab(),
            self.build_official_project_tab(),
            self.build_files_tab(),
            self.build_archives_tab(),
            self.build_maintenance_tab(),
            self.build_developer_tab(),
            self.build_guide_tab()
        ])
        tabs.add_class("azudl-tabs")

        titles = [
            "Dashboard",
            "Auto",
            "Direct",
            "YouTube",
            "Auth",
            "Torrent",
            "Batch",
            "GitHub",
            "Official",
            "Files",
            "Archives",
            "Maintenance",
            "Developer",
            "Guide"
        ]

        for index, title in enumerate(titles):
            tabs.set_title(index, title)

        refresh_button = self.button("â†» Refresh storage", "info", "150px")
        refresh_button.on_click(lambda button: self.refresh_storage())
        clear_button = self.button("Clear output", "neutral", "130px")
        clear_button.on_click(lambda button: self.output.clear_output())
        save_button = self.button("Save session", "success", "130px")
        save_button.on_click(self.handle_save_session)

        root = widgets.VBox([
            self.css(),
            header,
            self.storage_html,
            self.action_row([refresh_button, clear_button, save_button]),
            self.status_html,
            tabs,
            widgets.HTML(value="<div class='azudl-panel-title' style='margin-top:10px'>Output</div>"),
            self.output
        ], layout=widgets.Layout(gap="10px"))
        root.add_class("azudl-root")
        return root

    def action_row(self, children):
        box = widgets.HBox(children, layout=widgets.Layout(gap="10px", flex_flow="row wrap", align_items="center"))
        box.add_class("azudl-action-row")
        return box

    def panel(self, title, copy, children):
        box = widgets.VBox([
            widgets.HTML(value=f"""
            <div class="azudl-panel-title">{title}</div>
            <div class="azudl-panel-copy">{copy}</div>
            """),
            *children
        ], layout=widgets.Layout(gap="8px", padding="14px", margin="0 0 10px 0"))
        box.add_class("azudl-panel")
        return box

    def note(self, text):
        return widgets.HTML(value=f"<div class='azudl-note'>{text}</div>")

    def text(self, description, placeholder="", width="100%"):
        return widgets.Text(
            description=description,
            placeholder=placeholder,
            layout=widgets.Layout(width=width),
            style={"description_width": "155px"}
        )

    def textarea(self, description, placeholder="", rows=5):
        return widgets.Textarea(
            description=description,
            placeholder=placeholder,
            rows=rows,
            layout=widgets.Layout(width="100%"),
            style={"description_width": "155px"}
        )

    def checkbox(self, description, value=False, width="240px"):
        return widgets.Checkbox(
            value=value,
            description=description,
            indent=False,
            layout=widgets.Layout(width=width)
        )

    def button(self, description, kind="primary", width="180px", start=False):
        label = str(description)

        icons = {
            "Start": "â–¶",
            "Download": "â¬‡",
            "Save": "âœ“",
            "Clear": "Ã—",
            "Remove": "Ã—",
            "Fetch": "â†»",
            "Repo": "âŒ",
            "Official": "â˜…",
            "Token": "â—†",
            "Storage": "â—·",
            "History": "â‰¡",
            "Files": "â–£",
            "Latest": "â—",
            "Guide": "?",
            "Project": "â˜…",
            "Create": "â–¦",
            "ZIP": "â–¦",
            "SHA256": "#",
            "aria2": "â†¯"
        }

        if not any(label.startswith(prefix + " ") for prefix in icons.values()):
            for key, icon in icons.items():
                if label.startswith(key):
                    label = f"{icon} {label}"
                    break

        item = widgets.Button(
            description=label,
            button_style="",
            layout=widgets.Layout(width=width)
        )
        item.add_class("azudl-button")
        item.add_class(f"azudl-{kind}")

        if start:
            item.add_class("azudl-start")

        return item

    def quality_dropdown(self):
        return widgets.Dropdown(
            description="Quality",
            options=[
                ("Best available", "best"),
                ("4320p", "4320"),
                ("2160p", "2160"),
                ("1440p", "1440"),
                ("1080p", "1080"),
                ("720p", "720"),
                ("480p", "480"),
                ("360p", "360"),
                ("240p", "240"),
                ("144p", "144")
            ],
            value="best",
            layout=widgets.Layout(width="320px"),
            style={"description_width": "90px"}
        )

    def build_dashboard_tab(self):
        actions = [
            ("aria2 status", "info", self.handle_aria2_status),
            ("Storage report", "info", self.handle_storage_report),
            ("Download history", "neutral", self.handle_history),
            ("List files", "neutral", self.handle_list_files),
            ("Latest file", "neutral", self.handle_latest_file),
            ("Auth status", "neutral", self.handle_youtube_auth_status),
            ("Help", "neutral", self.handle_help)
        ]
        buttons = []

        for label, kind, handler in actions:
            item = self.button(label, kind, "155px")
            item.on_click(handler)
            buttons.append(item)

        return self.panel(
            "Dashboard",
            "Quick access to download status, storage, history, and file tools.",
            [
                self.note("All downloads are saved under /content/drive/MyDrive/AzuDl-GC2GD unless you choose a custom folder name."),
                widgets.HBox(buttons[:3], layout=widgets.Layout(gap="8px", flex_flow="row wrap")),
                widgets.HBox(buttons[3:6], layout=widgets.Layout(gap="8px", flex_flow="row wrap")),
                widgets.HBox(buttons[6:], layout=widgets.Layout(gap="8px", flex_flow="row wrap"))
            ]
        )

    def build_auto_tab(self):
        self.auto_link = self.text("Link", "Paste a direct URL, YouTube URL, magnet, or .torrent URL")
        self.auto_folder = self.text("Folder", "Optional output folder name")
        self.auto_file_name = self.text("File name", "Optional, direct links only")
        self.auto_speed = self.text("Speed limit", "Optional, example 5M")
        self.auto_headers = self.textarea("Headers JSON", '{"User-Agent":"Mozilla/5.0"}', rows=3)
        self.auto_quality = self.quality_dropdown()
        self.auto_audio_only = self.checkbox("Audio only", False)
        self.auto_playlist = self.checkbox("Download playlist if detected", True, "260px")
        self.auto_metadata = self.checkbox("Save YouTube metadata", False)
        self.auto_seed = self.checkbox("Keep torrent seeding", False)
        self.auto_private = self.checkbox("Private torrent mode", False)
        start = self.button("Start download", "success", "280px", start=True)
        start.on_click(self.handle_auto_download)

        return self.panel(
            "Auto-detect link",
            "Paste a link once. AzuDl detects direct files, YouTube links, magnets, and .torrent sources automatically.",
            [
                self.auto_link,
                self.auto_folder,
                self.action_row([self.auto_quality, self.auto_audio_only, self.auto_playlist, self.auto_metadata]),
                self.action_row([self.auto_seed, self.auto_private]),
                self.auto_file_name,
                self.auto_speed,
                self.auto_headers,
                start
            ]
        )

    def build_direct_tab(self):
        self.direct_url = self.text("Direct URL", "https://example.com/file.zip")
        self.direct_folder = self.text("Folder", "Optional output folder name")
        self.direct_file_name = self.text("File name", "Optional output file name")
        self.direct_speed = self.text("Speed limit", "Optional, example 5M")
        self.direct_headers = self.textarea("Headers JSON", '{"User-Agent":"Mozilla/5.0"}', rows=4)
        start = self.button("Start download", "success", "280px", start=True)
        start.on_click(self.handle_direct_download)

        return self.panel(
            "Direct URL download",
            "Download HTTP, HTTPS, or FTP files with optional custom filenames, speed limits, and request headers.",
            [
                self.direct_url,
                self.direct_folder,
                self.direct_file_name,
                self.direct_speed,
                self.direct_headers,
                start
            ]
        )

    def build_youtube_tab(self):
        self.youtube_url = self.text("YouTube URL", "https://www.youtube.com/watch?v=...")
        self.youtube_folder = self.text("Folder", "Optional output folder name")
        self.youtube_quality = self.quality_dropdown()
        self.youtube_audio_only = self.checkbox("Audio only", False)
        self.youtube_playlist = self.checkbox("Download playlist if detected", True, "260px")
        self.youtube_metadata = self.checkbox("Save metadata and thumbnail", False, "260px")
        fetch = self.button("Fetch qualities", "info", "160px")
        fetch.on_click(self.handle_fetch_youtube_qualities)
        start = self.button("Start download", "success", "280px", start=True)
        start.on_click(self.handle_youtube_download)
        cookies = self.button("Cookie guide", "neutral", "140px")
        cookies.on_click(self.handle_cookie_help)
        po_token = self.button("PO Token guide", "neutral", "150px")
        po_token.on_click(self.handle_po_token_help)

        return self.panel(
            "YouTube video or playlist",
            "Download YouTube videos, playlists, audio-only MP3 files, thumbnails, metadata, and authenticated content when cookies are provided.",
            [
                self.youtube_url,
                self.youtube_folder,
                self.action_row([self.youtube_quality, fetch]),
                self.action_row([self.youtube_audio_only, self.youtube_playlist, self.youtube_metadata]),
                self.action_row([start, cookies, po_token])
            ]
        )

    def build_auth_tab(self):
        self.auth_cookies = self.textarea("cookies.txt", "Paste Netscape-format YouTube cookies.txt content here", rows=8)
        self.auth_po_token = self.text("PO Token", "Example: mweb+YOUR_PO_TOKEN")
        self.auth_visitor_data = self.text("Visitor Data", "Optional")
        self.auth_player_client = widgets.Dropdown(
            description="Client",
            options=[
                ("Auto", ""),
                ("mweb", "mweb"),
                ("web", "web")
            ],
            value="mweb",
            layout=widgets.Layout(width="260px"),
            style={"description_width": "90px"}
        )

        status_button = self.button("Auth status", "info", "135px")
        status_button.on_click(self.handle_youtube_auth_status)
        save_cookies = self.button("Save cookies", "success", "145px")
        save_cookies.on_click(self.handle_save_youtube_cookies)
        save_token = self.button("Save token", "success", "155px")
        save_token.on_click(self.handle_save_youtube_po_token)
        reset_auth = self.button("Reset auth", "danger", "155px")
        reset_auth.on_click(self.handle_reset_youtube_auth)
        cookie_help = self.button("Cookie guide", "neutral", "135px")
        cookie_help.on_click(self.handle_cookie_help)
        token_help = self.button("PO Token guide", "neutral", "145px")
        token_help.on_click(self.handle_po_token_help)

        return self.panel(
            "YouTube authentication",
            "Add or check YouTube authentication files used when YouTube requires sign-in verification.",
            [
                self.note("These values are private credentials. Keep real cookies and tokens private."),
                self.action_row([status_button, cookie_help, token_help]),
                self.auth_cookies,
                self.action_row([save_cookies]),
                self.action_row([self.auth_po_token, self.auth_player_client]),
                self.auth_visitor_data,
                self.action_row([save_token, reset_auth])
            ]
        )

    def build_torrent_tab(self):
        self.torrent_source = self.text("Torrent source", "Required: magnet:?xt=... or https://example.com/file.torrent or /content/file.torrent")
        self.torrent_folder = self.text("Folder", "Optional output folder name")
        self.torrent_speed = self.text("Speed limit", "Optional, example 5M")
        self.torrent_private = self.checkbox("Private torrent mode", False)
        self.torrent_seed = self.checkbox("Keep seeding after download", False, "260px")
        start = self.button("Start torrent", "success", "270px", start=True)
        start.on_click(self.handle_torrent_download)
        status = self.button("aria2 status", "info", "140px")
        status.on_click(self.handle_aria2_status)

        return self.panel(
            "Torrent tools",
            "Add magnet links or .torrent files, enable private-tracker mode, seed while Colab is alive, and inspect aria2 status.",
            [
                self.note("Torrent source is required. Paste a magnet link, a .torrent URL, or a local .torrent file path before pressing Start torrent."),
                self.note("For private trackers, prefer a .torrent file and enable private mode. Seeding only continues while the Colab runtime is alive."),
                self.torrent_source,
                self.torrent_folder,
                self.torrent_speed,
                self.action_row([self.torrent_private, self.torrent_seed]),
                self.action_row([start, status])
            ]
        )

    def build_batch_tab(self):
        self.batch_links = self.textarea("Links", "One link per line", rows=8)
        self.batch_folder = self.text("Batch folder", "Optional batch folder prefix")
        self.batch_speed = self.text("Speed limit", "Optional, example 5M")
        start = self.button("Start batch", "success", "270px", start=True)
        start.on_click(self.handle_batch_download)

        return self.panel(
            "Batch download",
            "Paste one link per line. Each item is detected automatically and saved into a numbered batch folder.",
            [
                self.batch_links,
                self.batch_folder,
                self.batch_speed,
                start
            ]
        )

    def build_github_tab(self):
        self.github_repo_url = self.text("Repository URL", "https://github.com/owner/repository")
        self.github_folder = self.text("Folder", "Optional output folder name")
        self.github_token = self.text("GitHub token", "Optional token for private repos or higher rate limits")
        self.github_tag = self.text("Release tag", "Optional, example v1.0.0")
        self.github_mode = widgets.Dropdown(
            description="Download",
            options=[
                ("Latest release", "latest"),
                ("Specific release tag", "tag"),
                ("All releases", "all_releases"),
                ("Default branch source", "repo_source")
            ],
            value="latest",
            layout=widgets.Layout(width="340px"),
            style={"description_width": "90px"}
        )
        self.github_assets = self.checkbox("Release assets", True)
        self.github_source = self.checkbox("Source archive", True)
        self.github_readme = self.checkbox("README", True)
        self.github_license = self.checkbox("License", False)

        info_button = self.button("Repo info", "info", "165px")
        info_button.on_click(self.handle_github_info)
        auth_button = self.button("Token status", "neutral", "145px")
        auth_button.on_click(self.handle_github_auth_status)
        save_token = self.button("Save token", "success", "145px")
        save_token.on_click(self.handle_save_github_token)
        clear_token = self.button("Clear token", "danger", "135px")
        clear_token.on_click(self.handle_clear_github_token)
        start_button = self.button("Start GitHub download", "success", "290px", start=True)
        start_button.on_click(self.handle_github_download)
        return self.panel(
            "GitHub repository downloader",
            "Fetch repository information and download release assets, source archives, README, and license files directly to Google Drive.",
            [
                self.note("GitHub token is optional. It is useful for private repositories and higher API limits."),
                self.github_repo_url,
                self.github_folder,
                self.action_row([self.github_mode, self.github_assets, self.github_source, self.github_readme, self.github_license]),
                self.github_tag,
                self.github_token,
                self.action_row([start_button, info_button]),
                self.action_row([auth_button, save_token, clear_token])
            ]
        )

    def build_official_project_tab(self):
        self.official_folder = self.text("Folder", "AzuDL-GC2GD-Official")
        self.official_mode = widgets.Dropdown(
            description="Download",
            options=[
                ("Default branch source", "repo_source"),
                ("Latest release", "latest"),
                ("All releases", "all_releases")
            ],
            value="repo_source",
            layout=widgets.Layout(width="340px"),
            style={"description_width": "90px"}
        )
        self.official_assets = self.checkbox("Release assets", True)
        self.official_source = self.checkbox("Source archive", True)
        self.official_readme = self.checkbox("README", False)
        self.official_license = self.checkbox("License", False)

        info_button = self.button("Official info", "info", "170px")
        info_button.on_click(self.handle_official_repo_info)
        download_button = self.button("Download official project", "success", "300px", start=True)
        download_button.on_click(self.handle_official_repo_download)

        open_link = widgets.HTML(value=f"""
        <a class="azudl-link-button" href="{self.app.official_github_repo_url}" target="_blank" rel="noopener noreferrer">
        Open repository
        </a>
        """)

        return self.panel(
            "Official AzuDl repository",
            "Download official project releases or source archives directly to Google Drive.",
            [
                self.note(self.app.official_github_repo_url),
                self.official_folder,
                self.official_mode,
                self.action_row([self.official_assets, self.official_source, self.official_readme, self.official_license]),
                self.action_row([download_button, info_button, open_link])
            ]
        )

    def build_files_tab(self):
        self.hash_path = self.text("File path", "Optional file path for SHA256")
        list_button = self.button("List downloaded files", "info", "185px")
        list_button.on_click(self.handle_list_files)
        latest_button = self.button("Show latest file", "neutral", "155px")
        latest_button.on_click(self.handle_latest_file)
        hash_latest_button = self.button("SHA256 latest", "neutral", "150px")
        hash_latest_button.on_click(self.handle_sha_latest)
        hash_button = self.button("SHA256 check", "info", "160px")
        hash_button.on_click(self.handle_sha256)

        return self.panel(
            "Files and checksums",
            "List downloads, show the newest file, and calculate SHA256 checksums.",
            [
                self.action_row([list_button, latest_button, hash_latest_button]),
                self.hash_path,
                hash_button
            ]
        )

    def build_archives_tab(self):
        self.zip_path = self.text("Folder path", "/content/drive/MyDrive/AzuDl-GC2GD/...")
        zip_button = self.button("Create ZIP", "success", "140px")
        zip_button.on_click(self.handle_zip_folder)
        zip_latest_button = self.button("ZIP latest", "success", "160px")
        zip_latest_button.on_click(self.handle_zip_latest)

        return self.panel(
            "Archives",
            "Create ZIP archives from any folder or from the latest downloaded folder.",
            [
                self.zip_path,
                self.action_row([zip_button, zip_latest_button])
            ]
        )

    def build_maintenance_tab(self):
        status = self.button("aria2 status", "info", "160px")
        status.on_click(self.handle_aria2_status)

        purge = self.button("Clear stopped", "warning", "165px")
        purge.on_click(self.handle_clear_stopped)

        save_session = self.button("Save session", "success", "165px")
        save_session.on_click(self.handle_save_session)

        storage = self.button("Storage report", "info", "165px")
        storage.on_click(self.handle_storage_report)

        diagnostic = self.button("Run diagnostic", "success", "240px", start=True)
        diagnostic.on_click(self.handle_run_diagnostic)

        force_sync = self.button("Force Drive sync", "warning", "190px")
        force_sync.on_click(self.handle_force_drive_sync)

        self.remove_gid_value = self.text("aria2 GID", "GID to remove")
        remove_gid = self.button("Remove GID", "danger", "165px")
        remove_gid.on_click(self.handle_remove_gid)

        save_close = self.button("Save and close aria2", "danger", "220px")
        save_close.on_click(self.handle_close_gui)

        return self.panel(
            "Maintenance",
            "Manage aria2 queues, Drive sync, storage, and system diagnostics.",
            [
                self.action_row([diagnostic]),
                self.action_row([status, purge, save_session, storage, force_sync]),
                self.remove_gid_value,
                self.action_row([remove_gid, save_close])
            ]
        )


    def build_developer_tab(self):
        developer_button = self.button("Project links", "info", "175px")
        developer_button.on_click(self.handle_developer)
        help_button = self.button("Full guide", "neutral", "135px")
        help_button.on_click(self.handle_help)
        safety = widgets.HTML(value="""
        <div class="azudl-note">
        Privacy reminder: keep cookies, PO tokens, visitor data, and account files private.
        </div>
        """)

        return self.panel(
            "Project information",
            "Official links, version details, and contact channels.",
            [
                self.action_row([developer_button, help_button]),
                safety
            ]
        )

    def build_guide_tab(self):
        help_button = self.button("Full guide", "info", "135px")
        help_button.on_click(self.handle_help)
        developer_button = self.button("Developer", "neutral", "135px")
        developer_button.on_click(self.handle_developer)
        cookie_button = self.button("YouTube cookies", "neutral", "155px")
        cookie_button.on_click(self.handle_cookie_help)
        po_button = self.button("PO Token", "neutral", "135px")
        po_button.on_click(self.handle_po_token_help)
        cli_note = widgets.HTML(value="""
        <div class="azudl-note">
        Classic CLI mode is available for users who prefer a text-based interface.
        </div>
        """)

        return self.panel(
            "Guide and project information",
            "Open the complete user guide and YouTube authentication helpers.",
            [
                self.action_row([help_button, developer_button, cookie_button, po_button]),
                cli_note
            ]
        )

    def display(self):
        self.refresh_storage()
        display(self.root)
        return self

    def refresh_storage(self):
        usage = self.app.get_drive_usage()

        if not usage:
            self.storage_html.value = """
            <div class="azudl-note">
            Google Drive storage details are not available yet.
            </div>
            """
            self.status_html.value = ""
            return

        total, used, free = usage
        used_percent = used * 100 / total if total else 0
        used_width = min(max(used_percent, 0), 100)
        self.storage_html.value = f"""
        <div class="azudl-stat-row">
          <div class="azudl-stat">
            <div class="azudl-stat-label">Mounted path</div>
            <div class="azudl-stat-value">{self.app.my_drive_path}</div>
          </div>
          <div class="azudl-stat">
            <div class="azudl-stat-label">Total</div>
            <div class="azudl-stat-value">{self.app.format_bytes(total)}</div>
          </div>
          <div class="azudl-stat">
            <div class="azudl-stat-label">Used</div>
            <div class="azudl-stat-value">{self.app.format_bytes(used)} ({used_percent:.1f}%)</div>
          </div>
          <div class="azudl-stat">
            <div class="azudl-stat-label">Free</div>
            <div class="azudl-stat-value">{self.app.format_bytes(free)}</div>
          </div>
        </div>
        <div class="azudl-meter"><div class="azudl-meter-fill" style="width:{used_width:.1f}%"></div></div>
        """
        self.status_html.value = f"""
        <div class="azudl-note">
        Drive is ready. {self.app.format_bytes(free)} free space is available for new downloads.
        </div>
        """

    def run_action(self, button, title, action, clear=True):
        if button:
            button.disabled = True

        try:
            with self.output:
                if clear:
                    self.output.clear_output(wait=True)

                self.app.print_section(title)

                try:
                    action()
                    self.refresh_storage()
                except KeyboardInterrupt:
                    self.app.print_status("Operation interrupted by user.", "warning")
                except ValueError as error:
                    self.app.print_status(str(error), "warning")
                except FileNotFoundError as error:
                    self.app.print_status(f"File or folder was not found: {error}", "error")
                except BaseException as error:
                    self.app.print_status(f"Error: {error}", "error")

        finally:
            if button:
                button.disabled = False

    def handle_auto_download(self, button):
        def action():
            value = self.auto_link.value.strip()

            if not value:
                raise ValueError("A link is required. Paste a direct URL, YouTube URL, magnet link, or .torrent URL.")

            link_type = self.app.detect_link_type(value)
            self.app.print_kv("Detected link type", link_type)

            if link_type == "unknown":
                raise ValueError("Unknown link type.")

            folder = self.auto_folder.value.strip()
            speed = self.auto_speed.value.strip()

            if link_type == "youtube":
                self.app.download_youtube(
                    url=value,
                    folder_name=folder,
                    quality=self.auto_quality.value,
                    audio_only=self.auto_audio_only.value,
                    playlist=self.auto_playlist.value,
                    metadata=self.auto_metadata.value
                )
            elif link_type == "direct":
                headers = self.app.parse_headers_json(self.auto_headers.value)
                self.app.download_direct(value, folder, self.auto_file_name.value.strip(), speed, headers)
            elif link_type == "torrent":
                self.app.download_magnet(value, folder, speed, private=self.auto_private.value, seed=self.auto_seed.value)
            elif link_type == "torrent_file":
                self.app.download_torrent_file(value, folder, speed, private=self.auto_private.value, seed=self.auto_seed.value)

        self.run_action(button, "Auto Download", action)

    def handle_youtube_auth_status(self, button):
        self.run_action(button, "YouTube Authentication Status", self.app.print_youtube_auth_status)

    def handle_save_youtube_cookies(self, button):
        def action():
            self.app.save_youtube_cookies_text(self.auth_cookies.value)

        self.run_action(button, "Save YouTube Cookies", action)

    def handle_save_youtube_po_token(self, button):
        def action():
            self.app.save_youtube_po_token_text(
                po_token=self.auth_po_token.value,
                visitor_data=self.auth_visitor_data.value,
                player_client=self.auth_player_client.value
            )

        self.run_action(button, "Save YouTube PO Token", action)

    def handle_reset_youtube_auth(self, button):
        self.run_action(button, "Reset YouTube Authentication Files", self.app.clear_youtube_auth_files)

    def handle_direct_download(self, button):
        def action():
            headers = self.app.parse_headers_json(self.direct_headers.value)
            self.app.download_direct(
                self.direct_url.value.strip(),
                self.direct_folder.value.strip(),
                self.direct_file_name.value.strip(),
                self.direct_speed.value.strip(),
                headers
            )

        self.run_action(button, "Direct Download", action)

    def handle_fetch_youtube_qualities(self, button):
        def action():
            url = self.youtube_url.value.strip()

            if not url:
                raise ValueError("A YouTube URL is required before fetching qualities.")

            qualities, info = self.app.get_youtube_available_qualities(url)
            options = [("Best available", "best")]

            for quality in qualities:
                if quality != "best":
                    options.append((f"{quality}p", quality))

            self.youtube_quality.options = options
            self.youtube_quality.value = "best"
            self.app.print_kv("Title", info.get("title", "unknown"))
            self.app.print_kv("Channel", info.get("uploader", "unknown"))

            if info.get("duration"):
                self.app.print_kv("Duration", self.app.format_seconds(int(info.get("duration"))))

            self.app.print_status("Quality list updated.", "success")

        self.run_action(button, "Fetch YouTube Qualities", action)

    def handle_youtube_download(self, button):
        def action():
            self.app.download_youtube(
                url=self.youtube_url.value.strip(),
                folder_name=self.youtube_folder.value.strip(),
                quality=self.youtube_quality.value,
                audio_only=self.youtube_audio_only.value,
                playlist=self.youtube_playlist.value,
                metadata=self.youtube_metadata.value
            )

        self.run_action(button, "YouTube Download", action)

    def handle_torrent_download(self, button):
        def action():
            source = self.torrent_source.value.strip()

            if not source:
                raise ValueError("Torrent source is required. Paste a magnet link, a .torrent URL, or a local .torrent file path.")

            if source.startswith("magnet:?"):
                self.app.download_magnet(
                    source,
                    self.torrent_folder.value.strip(),
                    self.torrent_speed.value.strip(),
                    private=self.torrent_private.value,
                    seed=self.torrent_seed.value
                )
            else:
                self.app.download_torrent_file(
                    source,
                    self.torrent_folder.value.strip(),
                    self.torrent_speed.value.strip(),
                    private=self.torrent_private.value,
                    seed=self.torrent_seed.value
                )

        self.run_action(button, "Torrent Download", action)

    def handle_batch_download(self, button):
        def action():
            links = [line.strip() for line in self.batch_links.value.splitlines() if line.strip()]

            if not links:
                raise ValueError("Batch list is empty. Paste at least one link, one per line.")

            folder_name = self.app.normalize_folder_name(self.batch_folder.value.strip(), "Batch")
            speed_limit = self.batch_speed.value.strip()

            for index, link in enumerate(links, 1):
                self.app.print_section(f"Batch Item {index} of {len(links)}")
                self.app.print_kv("Link", link)
                link_type = self.app.detect_link_type(link)
                batch_folder = f"{folder_name}_{index}"

                try:
                    if link_type == "torrent":
                        self.app.download_magnet(link, batch_folder, speed_limit, private=False, seed=False)
                    elif link_type == "torrent_file":
                        self.app.download_torrent_file(link, batch_folder, speed_limit, private=False, seed=False)
                    elif link_type == "youtube":
                        self.app.download_youtube(link, batch_folder, quality="best", audio_only=False, playlist=True, metadata=False)
                    elif link_type == "direct":
                        self.app.download_direct(link, batch_folder, "", speed_limit)
                    else:
                        self.app.print_status("Skipped link because the type could not be detected.", "warning")
                except Exception as error:
                    self.app.print_status(f"Batch item failed: {error}", "error")
                    self.app.save_history({
                        "type": link_type,
                        "source": link,
                        "output": batch_folder,
                        "status": "failed",
                        "error": str(error)
                    })

        self.run_action(button, "Batch Download", action)

    def handle_github_auth_status(self, button):
        self.run_action(button, "GitHub Authentication Status", self.app.print_github_auth_status)

    def handle_save_github_token(self, button):
        def action():
            self.app.save_github_token_text(self.github_token.value)

        self.run_action(button, "Save GitHub Token", action)

    def handle_clear_github_token(self, button):
        self.run_action(button, "Clear GitHub Token", self.app.clear_github_token)

    def handle_official_repo_info(self, button):
        self.run_action(button, "Official AzuDl Repository", self.app.print_official_project_repo_info)

    def handle_official_repo_download(self, button):
        def action():
            folder_value = getattr(self, "official_folder", None)
            mode_value = getattr(self, "official_mode", None)
            assets_value = getattr(self, "official_assets", None)
            source_value = getattr(self, "official_source", None)
            readme_value = getattr(self, "official_readme", None)
            license_value = getattr(self, "official_license", None)

            self.app.download_official_project_repository(
                mode=mode_value.value if mode_value else "latest",
                include_assets=assets_value.value if assets_value else True,
                include_source=source_value.value if source_value else True,
                folder_name=(folder_value.value.strip() if folder_value else "") or "AzuDL-GC2GD-Official",
                include_readme=readme_value.value if readme_value else True,
                include_license=license_value.value if license_value else False
            )

        self.run_action(button, "Download Official AzuDl Repository", action)

    def handle_github_info(self, button):
        def action():
            repo_url = self.github_repo_url.value.strip()

            if not repo_url:
                raise ValueError("GitHub repository URL is required.")

            self.app.print_github_repo_info(repo_url)

        self.run_action(button, "GitHub Repository Info", action)

    def handle_github_download(self, button):
        def action():
            repo_url = self.github_repo_url.value.strip()

            if not repo_url:
                raise ValueError("GitHub repository URL is required.")

            self.app.download_github_repository(
                repo_url=repo_url,
                mode=self.github_mode.value,
                include_assets=self.github_assets.value,
                include_source=self.github_source.value,
                folder_name=self.github_folder.value.strip(),
                release_tag=self.github_tag.value.strip(),
                include_readme=self.github_readme.value,
                include_license=self.github_license.value
            )

        self.run_action(button, "GitHub Download", action)

    def handle_purge_stopped(self, button):
        self.run_action(button, "Clear Stopped aria2 Results", self.app.purge_aria2_stopped)

    def handle_save_close(self, button):
        def action():
            self.app.save_aria2_session()
            self.app.print_status("aria2 session saved. Runtime can be closed safely.", "success")

        self.run_action(button, "Save and Close aria2", action)

    def handle_storage(self, button):
        return self.handle_storage_report(button)

    def handle_run_diagnostic(self, button):
        def action():
            self.app.run_system_diagnostic_test()

        self.run_action(button, "System Diagnostic", action)

    def handle_force_drive_sync(self, button):
        def action():
            self.app.force_drive_sync()
            self.app.print_status("Drive sync command completed.", "success")

        self.run_action(button, "Force Google Drive Sync", action)

    def handle_aria2_status(self, button):
        self.run_action(button, "aria2 Status", self.app.print_aria2_status)

    def handle_storage_report(self, button):
        self.run_action(button, "Storage Report", self.app.storage_report)

    def handle_list_files(self, button):
        self.run_action(button, "Downloaded Files", self.app.list_downloads)

    def handle_history(self, button):
        self.run_action(button, "Download History", self.app.print_history)

    def handle_latest_file(self, button):
        self.run_action(button, "Latest File", self.app.print_latest_file)

    def handle_save_session(self, button):
        self.run_action(button, "Save Session", self.app.save_aria2_session)

    def handle_clear_stopped(self, button):
        self.run_action(button, "Clear Stopped Results", self.app.purge_aria2_stopped)

    def handle_help(self, button):
        self.run_action(button, "Help", self.app.print_help)

    def handle_developer(self, button):
        self.run_action(button, "Project Information", self.app.print_developer)

    def handle_cookie_help(self, button):
        self.run_action(button, "YouTube Cookie Help", self.app.print_youtube_cookie_help)

    def handle_po_token_help(self, button):
        self.run_action(button, "YouTube PO Token Help", self.app.print_youtube_po_token_help)

    def handle_close_gui(self, button):
        def action():
            self.app.save_aria2_session()
            self.app.print_status("Session saved. Closing GUI widget.", "success")

        self.run_action(button, "Close GUI", action)
        self.root.close()

    def handle_remove_gid(self, button):
        def action():
            gid = self.remove_gid.value.strip()

            if not gid:
                raise ValueError("Enter an aria2 GID first.")

            if self.app.remove_existing_torrent_gid(gid):
                self.app.print_status(f"GID removed: {gid}", "success")
            else:
                self.app.print_status(f"Failed to remove GID: {gid}", "error")

        self.run_action(button, "Remove aria2 GID", action)

    def handle_zip_folder(self, button):
        def action():
            source = Path(self.zip_path.value.strip())

            if not source.exists():
                raise FileNotFoundError(source)

            if not source.is_dir():
                raise ValueError("The selected path is not a folder.")

            output_name = self.app.sanitize_name(source.name + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            output_base = self.app.archive_dir / output_name
            result = shutil.make_archive(str(output_base), "zip", str(source))
            self.app.save_history({
                "type": "zip",
                "source": str(source),
                "output": result,
                "status": "completed"
            })
            self.app.print_status("ZIP archive created.", "success")
            self.app.print_kv("Archive", result)

        self.run_action(button, "ZIP Folder", action)

    def handle_zip_latest(self, button):
        def action():
            latest_folder = self.app.get_latest_downloaded_folder()

            if not latest_folder:
                self.app.print_status("No downloaded folders were found.", "info")
                return

            output_name = self.app.sanitize_name(latest_folder.name + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            output_base = self.app.archive_dir / output_name
            result = shutil.make_archive(str(output_base), "zip", str(latest_folder))
            self.app.save_history({
                "type": "zip",
                "source": str(latest_folder),
                "output": result,
                "status": "completed"
            })
            self.app.print_kv("Latest folder", latest_folder)
            self.app.print_status("ZIP archive created.", "success")
            self.app.print_kv("Archive", result)

        self.run_action(button, "ZIP Latest Folder", action)

    def handle_sha256(self, button):
        def action():
            path = self.hash_path.value.strip()

            if path:
                file_path = Path(path)

                if not file_path.exists():
                    raise FileNotFoundError(file_path)

                digest = self.app.sha256_file(file_path)
                self.app.print_kv("File", file_path)
                self.app.print_kv("SHA256", digest)
            else:
                self.app.hash_latest_file()

        self.run_action(button, "SHA256", action)

    def handle_sha_latest(self, button):
        self.run_action(button, "SHA256 Latest File", self.app.hash_latest_file)


def launch_gui():
    app = AzuDlGC2GD()
    startup_log = io.StringIO()

    try:
        with contextlib.redirect_stdout(startup_log):
            app.setup()
    except Exception as error:
        app.print_status(f"Startup failed: {error}", "error")
        return None

    gui = AzuDlGC2GDGUI(app)
    gui.display()
    return gui



def main():
    app = AzuDlGC2GD()

    try:
        app.setup()
    except Exception as error:
        app.print_status(f"Startup failed: {error}", "error")
        return

    while True:
        app.print_menu(app.project_name, [
            ("1", "Auto-detect and download a link"),
            ("2", "Torrent tools"),
            ("3", "YouTube video or playlist"),
            ("4", "Direct URL download"),
            ("5", "Batch download"),
            ("6", "Download history"),
            ("7", "List downloaded files"),
            ("8", "Storage report"),
            ("9", "SHA256 for latest file"),
            ("10", "SHA256 for selected file"),
            ("11", "ZIP a folder"),
            ("12", "ZIP latest downloaded folder"),
            ("13", "Show latest file"),
            ("14", "Project links"),
            ("15", "Help"),
            ("16", "Save session and exit"),
            ("17", "GitHub repository downloader"),
            ("18", "Download official project repository"),
            ("19", "Launch Colab GUI")
        ])

        choice = app.prompt("Select option")

        try:
            if choice == "1":
                value = app.prompt("Link")
                app.auto_download(value)

            elif choice == "2":
                app.torrent_menu()

            elif choice == "3":
                url = app.prompt("YouTube URL")
                folder_name = app.prompt("Output folder name (optional)")
                quality, audio_only = app.select_youtube_quality(url)
                playlist_answer = app.prompt("Download playlist if detected? y/n").lower()
                playlist = playlist_answer != "n"
                metadata_answer = app.prompt("Save metadata and thumbnail? y/n").lower()
                metadata = metadata_answer == "y"

                app.download_youtube(
                    url=url,
                    folder_name=folder_name,
                    quality=quality,
                    audio_only=audio_only,
                    playlist=playlist,
                    metadata=metadata
                )

            elif choice == "4":
                url = app.prompt("Direct URL")
                folder_name = app.prompt("Output folder name (optional)")
                file_name = app.prompt("File name (optional)")
                speed_limit = app.prompt("Speed limit (optional, example 5M)")
                headers_text = app.prompt('Headers JSON (optional, example {"User-Agent":"Mozilla/5.0"})')
                headers = app.parse_headers_json(headers_text)
                app.download_direct(url, folder_name, file_name, speed_limit, headers)

            elif choice == "5":
                app.batch_download()

            elif choice == "6":
                app.print_history()

            elif choice == "7":
                app.list_downloads()

            elif choice == "8":
                app.storage_report()

            elif choice == "9":
                app.hash_latest_file()

            elif choice == "10":
                app.sha256_selected_file()

            elif choice == "11":
                app.zip_folder()

            elif choice == "12":
                app.zip_latest_folder()

            elif choice == "13":
                app.print_latest_file()

            elif choice == "14":
                app.print_developer()

            elif choice == "15":
                app.print_help()

            elif choice == "16":
                app.save_aria2_session()
                app.print_status("Session saved. Goodbye.", "success")
                break

            elif choice == "17":
                repo_url = app.prompt("GitHub repository URL")
                mode = app.prompt("Mode: latest / all_releases / repo_source") or "latest"
                folder_name = app.prompt("Output folder name (optional)")
                assets_answer = app.prompt("Download release assets? y/n").lower()
                source_answer = app.prompt("Download source archive? y/n").lower()
                app.download_github_repository(
                    repo_url=repo_url,
                    mode=mode,
                    include_assets=assets_answer != "n",
                    include_source=source_answer != "n",
                    folder_name=folder_name
                )

            elif choice == "18":
                mode = app.prompt("Mode: latest / all_releases / repo_source") or "latest"
                app.download_official_project_repository(
                    mode=mode,
                    include_assets=True,
                    include_source=True,
                    folder_name="AzuDL-GC2GD-Official",
                    include_readme=True,
                    include_license=False
                )

            elif choice == "19":
                gui = AzuDlGC2GDGUI(app)
                gui.display()
                app.print_status("GUI launched. The CLI loop is now closed.", "success")
                break

            else:
                app.print_status("Invalid option. Choose a number from the menu.", "warning")

        except KeyboardInterrupt:
            app.save_aria2_session()
            app.print_status("Operation cancelled by user.", "warning")

        except Exception as error:
            app.save_aria2_session()
            app.print_status(f"Error: {error}", "error")


if __name__ == "__main__":
    interface = os.environ.get("AZUDL_INTERFACE", "gui").strip().lower()

    if interface in ["gui", "ui", "widgets"]:
        launch_gui()
    else:
        main()
