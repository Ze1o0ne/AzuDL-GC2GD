!apt update -qq
!apt install -y aria2 ffmpeg
!pip install -q tqdm requests yt-dlp

import os
import re
import json
import time
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import requests
from tqdm.notebook import tqdm
from google.colab import drive
from yt_dlp import YoutubeDL


class AzuDlGC2GD:
    def __init__(self):
        self.project_name = "AzuDl - GC2GD"
        self.project_subtitle = "Azizi Universal Downloader - Google Colab to Google Drive"
        self.version = "1.0.1"

        self.drive_mount_path = Path("/content/drive")
        self.my_drive_path = self.drive_mount_path / "MyDrive"

        self.base_dir = self.my_drive_path / "AzuDl-GC2GD"
        self.torrent_dir = self.base_dir / "TorrentDownloads"
        self.youtube_dir = self.base_dir / "YouTubeDownloads"
        self.direct_dir = self.base_dir / "DirectDownloads"
        self.batch_dir = self.base_dir / "BatchDownloads"
        self.logs_dir = self.base_dir / "Logs"
        self.history_file = self.logs_dir / "download_history.json"

        self.rpc_url = "http://localhost:6800/jsonrpc"

    def setup(self):
        self.print_banner()
        self.mount_google_drive()
        self.prepare_directories()
        self.start_aria2_rpc()

    def print_banner(self):
        print("=" * 70)
        print(self.project_name)
        print(self.project_subtitle)
        print("Version:", self.version)
        print("=" * 70)

    def mount_google_drive(self):
        if self.my_drive_path.exists():
            print("Google Drive already mounted")
            return

        attempts = [
            {"force_remount": False, "label": "standard mount"},
            {"force_remount": True, "label": "force remount"}
        ]

        last_error = None

        for attempt in attempts:
            try:
                print("Trying Google Drive", attempt["label"])
                drive.mount(str(self.drive_mount_path), force_remount=attempt["force_remount"])

                if self.my_drive_path.exists():
                    print("Google Drive mounted successfully")
                    return

            except Exception as error:
                last_error = error
                print("Mount attempt failed:", error)
                time.sleep(2)

        self.print_drive_mount_help()
        raise RuntimeError(f"Google Drive mount failed: {last_error}")

    def print_drive_mount_help(self):
        print("")
        print("=" * 70)
        print("Google Drive mount failed")
        print("=" * 70)
        print("Try these fixes:")
        print("1. Runtime > Restart session")
        print("2. Run this in a separate cell: from google.colab import drive; drive.flush_and_unmount()")
        print("3. Use only one Google account in your browser")
        print("4. Open Colab in Incognito mode")
        print("5. Make sure third-party cookies are not blocked")
        print("6. Reconnect Google Drive manually from the Colab file panel")
        print("=" * 70)
        print("")

    def prepare_directories(self):
        dirs = [
            self.base_dir,
            self.torrent_dir,
            self.youtube_dir,
            self.direct_dir,
            self.batch_dir,
            self.logs_dir
        ]

        for item in dirs:
            item.mkdir(parents=True, exist_ok=True)

    def is_port_open(self, host="127.0.0.1", port=6800):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0

    def start_aria2_rpc(self):
        if self.is_port_open():
            print("aria2 RPC already running")
            return

        cmd = [
            "aria2c",
            "--enable-rpc=true",
            "--rpc-listen-all=false",
            "--rpc-listen-port=6800",
            "--rpc-allow-origin-all=true",
            "--daemon=true",
            "--seed-time=0",
            "--file-allocation=none",
            "--continue=true",
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
                print("aria2 RPC started")
                return
            time.sleep(0.5)

        raise RuntimeError("Failed to start aria2 RPC server.")

    def rpc(self, method, params=None):
        payload = {
            "jsonrpc": "2.0",
            "id": "azudl-gc2gd",
            "method": method,
            "params": params or []
        }

        response = requests.post(self.rpc_url, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(data["error"])

        return data["result"]

    def sanitize_name(self, name):
        name = str(name or "").strip()
        name = re.sub(r'[\/\\:*?"<>|]', "_", name)
        name = re.sub(r"\s+", " ", name)
        return name or f"Download_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"

    def format_bytes(self, value):
        value = float(value or 0)

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024:
                return f"{value:.2f} {unit}"
            value /= 1024

        return f"{value:.2f} PB"

    def detect_link_type(self, value):
        value = value.strip()
        lower = value.lower()

        if lower.startswith("magnet:?"):
            return "torrent"

        parsed = urlparse(value)
        host = parsed.netloc.lower()

        youtube_hosts = [
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "music.youtube.com"
        ]

        if any(host == item or host.endswith("." + item) for item in youtube_hosts):
            return "youtube"

        if lower.startswith(("http://", "https://", "ftp://")):
            return "direct"

        return "unknown"

    def save_history(self, item):
        history = []

        if self.history_file.exists():
            try:
                history = json.loads(self.history_file.read_text())
            except Exception:
                history = []

        item["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history.append(item)

        self.history_file.write_text(json.dumps(history, indent=2, ensure_ascii=False))

    def print_history(self):
        if not self.history_file.exists():
            print("No history found")
            return

        try:
            history = json.loads(self.history_file.read_text())
        except Exception:
            print("History file is invalid")
            return

        if not history:
            print("No history found")
            return

        for index, item in enumerate(history[-50:], 1):
            print("-" * 80)
            print("Index:", index)
            print("Type:", item.get("type", "unknown"))
            print("Time:", item.get("time", "unknown"))
            print("Source:", item.get("source", "unknown"))
            print("Output:", item.get("output", "unknown"))
            print("Status:", item.get("status", "unknown"))

            if item.get("format"):
                print("Format:", item.get("format"))

            if item.get("error"):
                print("Error:", item.get("error"))

    def list_downloads(self):
        folders = [
            self.torrent_dir,
            self.youtube_dir,
            self.direct_dir,
            self.batch_dir
        ]

        for folder in folders:
            print("")
            print(str(folder))
            print("-" * 80)

            if not folder.exists():
                print("Folder does not exist")
                continue

            items = sorted(
                folder.glob("**/*"),
                key=lambda x: x.stat().st_mtime if x.exists() else 0,
                reverse=True
            )

            files = [item for item in items if item.is_file()]

            if not files:
                print("No files")
                continue

            for item in files[:100]:
                size = self.format_bytes(item.stat().st_size)
                print(f"{size:<12} {item}")

    def add_aria2_download(self, uris, save_dir, speed_limit="", extra_options=None):
        options = {
            "dir": str(save_dir),
            "file-allocation": "none",
            "continue": "true",
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

        return self.rpc("aria2.addUri", [uris, options])

    def get_aria2_status(self, gid):
        keys = [
            "gid",
            "status",
            "totalLength",
            "completedLength",
            "downloadSpeed",
            "uploadSpeed",
            "connections",
            "numSeeders",
            "errorCode",
            "errorMessage",
            "files",
            "bittorrent"
        ]

        return self.rpc("aria2.tellStatus", [gid, keys])

    def wait_for_torrent_metadata(self, gid):
        bar = tqdm(total=1, desc="Fetching metadata", unit="step")

        while True:
            status = self.get_aria2_status(gid)

            if status.get("status") == "error":
                bar.close()
                raise RuntimeError(status.get("errorMessage") or "Metadata fetch failed.")

            files = status.get("files", [])
            total = int(status.get("totalLength", "0"))

            if files and total > 0:
                bar.update(1)
                bar.close()
                return

            time.sleep(1)

    def monitor_aria2(self, gid, label):
        last_completed = 0
        progress = None

        while True:
            status = self.get_aria2_status(gid)

            state = status.get("status")
            total = int(status.get("totalLength", "0"))
            completed = int(status.get("completedLength", "0"))
            speed = int(status.get("downloadSpeed", "0"))
            seeders = status.get("numSeeders", "0")
            connections = status.get("connections", "0")

            if state == "error":
                if progress:
                    progress.close()
                raise RuntimeError(status.get("errorMessage") or "Download failed.")

            if progress is None and total > 0:
                progress = tqdm(
                    total=total,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=label
                )

            if progress:
                delta = completed - last_completed

                if delta > 0:
                    progress.update(delta)

                postfix = {
                    "speed": self.format_bytes(speed) + "/s",
                    "connections": connections
                }

                if seeders != "0":
                    postfix["seeders"] = seeders

                progress.set_postfix(postfix)

            last_completed = completed

            if state == "complete":
                if progress:
                    progress.n = total
                    progress.refresh()
                    progress.close()
                return status

            time.sleep(1)

    def download_magnet(self, magnet, folder_name="", speed_limit=""):
        magnet = magnet.strip()
        folder_name = self.sanitize_name(folder_name)
        save_dir = self.torrent_dir / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        if not magnet.startswith("magnet:?xt=urn:btih:"):
            raise ValueError("Invalid magnet link.")

        options = {
            "seed-time": "0",
            "enable-dht": "true",
            "enable-dht6": "true",
            "enable-peer-exchange": "true",
            "bt-enable-lpd": "true",
            "bt-save-metadata": "true",
            "bt-load-saved-metadata": "true"
        }

        gid = self.add_aria2_download([magnet], save_dir, speed_limit, options)

        print("Torrent added")
        print("Output:", save_dir)

        self.wait_for_torrent_metadata(gid)
        self.monitor_aria2(gid, "Torrent")

        self.save_history({
            "type": "torrent",
            "source": magnet,
            "output": str(save_dir),
            "status": "completed"
        })

        print("Download completed")
        print("Saved to:", save_dir)

    def download_direct(self, url, folder_name="", file_name="", speed_limit="", headers=None):
        url = url.strip()
        folder_name = self.sanitize_name(folder_name)
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

        print("Direct download added")
        print("Output:", save_dir)

        self.monitor_aria2(gid, "Direct")

        self.save_history({
            "type": "direct",
            "source": url,
            "output": str(save_dir),
            "status": "completed"
        })

        print("Download completed")
        print("Saved to:", save_dir)

    def list_youtube_formats(self, url):
        with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get("formats", [])
        rows = []

        for item in formats:
            format_id = item.get("format_id")
            ext = item.get("ext")
            height = item.get("height")
            width = item.get("width")
            fps = item.get("fps")
            vcodec = item.get("vcodec")
            acodec = item.get("acodec")
            filesize = item.get("filesize") or item.get("filesize_approx")
            note = item.get("format_note") or ""

            if not format_id:
                continue

            kind = "video+audio"

            if vcodec != "none" and acodec == "none":
                kind = "video"
            elif vcodec == "none" and acodec != "none":
                kind = "audio"

            size = self.format_bytes(filesize) if filesize else "unknown"

            rows.append({
                "id": format_id,
                "kind": kind,
                "ext": ext or "",
                "resolution": f"{width or ''}x{height or ''}".strip("x") if height else "audio",
                "fps": fps or "",
                "size": size,
                "note": note
            })

        return rows

    def print_youtube_formats(self, url):
        rows = self.list_youtube_formats(url)

        print("Available formats:")
        print("-" * 110)
        print(f"{'ID':<12} {'TYPE':<12} {'EXT':<8} {'RESOLUTION':<14} {'FPS':<6} {'SIZE':<14} NOTE")
        print("-" * 110)

        for row in rows:
            print(
                f"{row['id']:<12} "
                f"{row['kind']:<12} "
                f"{row['ext']:<8} "
                f"{row['resolution']:<14} "
                f"{str(row['fps']):<6} "
                f"{row['size']:<14} "
                f"{row['note']}"
            )

        print("-" * 110)

    def build_youtube_format(self, quality, audio_only, custom_format):
        quality = quality.strip().lower()
        custom_format = custom_format.strip()

        if custom_format:
            return custom_format

        if audio_only:
            return "bestaudio/best"

        if quality == "best":
            return "bv*+ba/best"

        if quality in ["4320", "2160", "1440", "1080", "720", "480", "360"]:
            return f"bv*[height<={quality}]+ba/best[height<={quality}]/best"

        return "bv*+ba/best"

    def download_youtube(self, url, folder_name="", quality="best", audio_only=False, custom_format="", playlist=True):
        url = url.strip()
        folder_name = self.sanitize_name(folder_name)
        save_dir = self.youtube_dir / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

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
                print("Processing file")

        selected_format = self.build_youtube_format(quality, audio_only, custom_format)

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
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4"
                }
            ]

        options = {
            "format": selected_format,
            "outtmpl": str(save_dir / "%(playlist_index|)s%(playlist_index& - |)s%(title).200s.%(ext)s"),
            "merge_output_format": "mp4",
            "noplaylist": not playlist,
            "ignoreerrors": False,
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "progress_hooks": [hook],
            "postprocessors": postprocessors,
            "quiet": True,
            "no_warnings": True
        }

        print("YouTube download started")
        print("Format:", selected_format)
        print("Output:", save_dir)

        with YoutubeDL(options) as ydl:
            ydl.download([url])

        self.save_history({
            "type": "youtube",
            "source": url,
            "output": str(save_dir),
            "format": selected_format,
            "status": "completed"
        })

        print("Download completed")
        print("Saved to:", save_dir)

    def auto_download(self, value):
        link_type = self.detect_link_type(value)

        if link_type == "unknown":
            raise ValueError("Unknown link type.")

        print("Detected:", link_type)

        folder_name = input("Folder name optional: ").strip()

        if link_type == "torrent":
            speed_limit = input("Speed limit optional, example 5M: ").strip()
            self.download_magnet(value, folder_name, speed_limit)

        elif link_type == "youtube":
            show_formats = input("Show available formats? y/n: ").strip().lower()

            if show_formats == "y":
                self.print_youtube_formats(value)

            audio = input("Audio only? y/n: ").strip().lower()
            audio_only = audio == "y"

            if audio_only:
                quality = "best"
            else:
                quality = input("Quality best, 4320, 2160, 1440, 1080, 720, 480, 360: ").strip() or "best"

            custom_format = input("Custom format ID optional: ").strip()
            playlist_answer = input("Download playlist if detected? y/n: ").strip().lower()
            playlist = playlist_answer != "n"

            self.download_youtube(
                url=value,
                folder_name=folder_name,
                quality=quality,
                audio_only=audio_only,
                custom_format=custom_format,
                playlist=playlist
            )

        elif link_type == "direct":
            file_name = input("File name optional: ").strip()
            speed_limit = input("Speed limit optional, example 5M: ").strip()
            self.download_direct(value, folder_name, file_name, speed_limit)

    def batch_download(self):
        print("Enter links one by one")
        print("Submit an empty line to start")

        links = []

        while True:
            value = input("Link: ").strip()

            if not value:
                break

            links.append(value)

        if not links:
            print("No links entered")
            return

        folder_name = input("Batch folder name optional: ").strip()
        folder_name = self.sanitize_name(folder_name)
        speed_limit = input("Speed limit for direct and torrent optional, example 5M: ").strip()

        for index, link in enumerate(links, 1):
            print("")
            print("=" * 80)
            print("Item:", index, "of", len(links))
            print("Link:", link)

            link_type = self.detect_link_type(link)
            batch_folder = f"{folder_name}_{index}"

            try:
                if link_type == "torrent":
                    self.download_magnet(link, batch_folder, speed_limit)

                elif link_type == "youtube":
                    self.download_youtube(
                        url=link,
                        folder_name=batch_folder,
                        quality="best",
                        audio_only=False,
                        custom_format="",
                        playlist=True
                    )

                elif link_type == "direct":
                    self.download_direct(link, batch_folder, "", speed_limit)

                else:
                    print("Skipped unknown link")

            except Exception as error:
                print("Failed:", error)

                self.save_history({
                    "type": link_type,
                    "source": link,
                    "output": batch_folder,
                    "status": "failed",
                    "error": str(error)
                })

    def print_developer(self):
        text = """
Developer

Project:
AzuDl - GC2GD

Full Name:
Azizi Universal Downloader - Google Colab to Google Drive

Developer:
The Azizi

X:
https://x.com/the_azzi

GitHub:
https://github.com/TheGreatAzizi

Telegram:
https://t.me/luluch_code

Git:
https://git.theazizi.ir/TheAzizi

Website:
https://theazizi.ir
"""
        print(text.strip())

    def print_help(self):
        text = """
AzuDl - GC2GD Help

Project:
AzuDl - GC2GD

Full Name:
Azizi Universal Downloader - Google Colab to Google Drive

Main options:
1. Auto detect link
2. Torrent magnet
3. YouTube video or playlist
4. Direct link
5. Batch download
6. Download history
7. List downloaded files
8. Developer
9. Help
10. Exit

Auto detect:
Paste any supported link.
The app detects torrent magnet, YouTube URL, or direct URL automatically.

Storage paths:
Base:
/content/drive/MyDrive/AzuDl-GC2GD

Torrent files:
/content/drive/MyDrive/AzuDl-GC2GD/TorrentDownloads

YouTube files:
/content/drive/MyDrive/AzuDl-GC2GD/YouTubeDownloads

Direct files:
/content/drive/MyDrive/AzuDl-GC2GD/DirectDownloads

Batch files:
/content/drive/MyDrive/AzuDl-GC2GD/BatchDownloads

Logs:
/content/drive/MyDrive/AzuDl-GC2GD/Logs

Torrent magnet example:
magnet:?xt=urn:btih:EXAMPLE_HASH

YouTube quality values:
best
4320
2160
1440
1080
720
480
360

YouTube custom format examples:
137+140
248+251
22
18
best

YouTube audio:
Select audio only to save MP3 audio.

Direct link examples:
https://example.com/file.zip
https://example.com/video.mp4
https://example.com/archive.rar
https://example.com/document.pdf

Speed limit examples:
500K
2M
10M

Folder name:
Leave empty to auto-create a folder name.

File name:
Available for direct links.
Leave empty to keep the original file name.

Batch download:
Paste multiple links.
Empty line starts the batch process.

Drive mount error fixes:
Runtime > Restart session
Use only one Google account
Open Colab in Incognito mode
Allow third-party cookies
Run drive.flush_and_unmount before retrying

Notes:
Use only content you have the right to download.
Some YouTube videos may require cookies or may not be available in Colab.
Some direct links may require headers, authentication, or temporary tokens.
Torrent speed depends on seeders and peers.
"""
        print(text.strip())


def main():
    app = AzuDlGC2GD()

    try:
        app.setup()
    except Exception as error:
        print("Startup failed:", error)
        return

    while True:
        print("")
        print("=" * 70)
        print(app.project_name)
        print("=" * 70)
        print("1. Auto detect link")
        print("2. Torrent magnet")
        print("3. YouTube video or playlist")
        print("4. Direct link")
        print("5. Batch download")
        print("6. Download history")
        print("7. List downloaded files")
        print("8. Developer")
        print("9. Help")
        print("10. Exit")

        choice = input("Select option: ").strip()

        try:
            if choice == "1":
                value = input("Link: ").strip()
                app.auto_download(value)

            elif choice == "2":
                magnet = input("Magnet link: ").strip()
                folder_name = input("Folder name optional: ").strip()
                speed_limit = input("Speed limit optional, example 5M: ").strip()
                app.download_magnet(magnet, folder_name, speed_limit)

            elif choice == "3":
                url = input("YouTube URL: ").strip()
                folder_name = input("Folder name optional: ").strip()
                show_formats = input("Show available formats? y/n: ").strip().lower()

                if show_formats == "y":
                    app.print_youtube_formats(url)

                audio = input("Audio only? y/n: ").strip().lower()
                audio_only = audio == "y"

                if audio_only:
                    quality = "best"
                else:
                    quality = input("Quality best, 4320, 2160, 1440, 1080, 720, 480, 360: ").strip() or "best"

                custom_format = input("Custom format ID optional: ").strip()
                playlist_answer = input("Download playlist if detected? y/n: ").strip().lower()
                playlist = playlist_answer != "n"

                app.download_youtube(
                    url=url,
                    folder_name=folder_name,
                    quality=quality,
                    audio_only=audio_only,
                    custom_format=custom_format,
                    playlist=playlist
                )

            elif choice == "4":
                url = input("Direct URL: ").strip()
                folder_name = input("Folder name optional: ").strip()
                file_name = input("File name optional: ").strip()
                speed_limit = input("Speed limit optional, example 5M: ").strip()
                app.download_direct(url, folder_name, file_name, speed_limit)

            elif choice == "5":
                app.batch_download()

            elif choice == "6":
                app.print_history()

            elif choice == "7":
                app.list_downloads()

            elif choice == "8":
                app.print_developer()

            elif choice == "9":
                app.print_help()

            elif choice == "10":
                print("Exit")
                break

            else:
                print("Invalid option")

        except KeyboardInterrupt:
            print("Cancelled")

        except Exception as error:
            print("Error:", error)


main()
