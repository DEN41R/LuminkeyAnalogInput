import os
import subprocess

import sys

print("Installing required build tools and dependencies...")
subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "pywebview", "vgamepad", "hidapi"])

print("Building LuminkeyAnalogInput...")
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--windowed",
    "--onefile",
    "--name", "LuminkeyAnalogInput",
    "--icon", "assets/app_icon.ico",
    "--uac-admin", 
    "--add-data", "assets/app_icon.png;assets",
    "--add-data", "web;web",
    "--collect-all", "vgamepad",
    "--collect-all", "interception",
    "--collect-all", "hid",
    "main.py"
]

subprocess.run(cmd)

print("Build complete! Check the 'dist' folder for LuminkeyAnalogInput.exe")
