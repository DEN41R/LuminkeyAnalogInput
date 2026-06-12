import os
import subprocess

print("Installing required build tools...")
subprocess.run(["pip", "install", "pyinstaller"])

print("Building LuminkeyAnalogInput...")
cmd = [
    "pyinstaller",
    "--noconfirm",
    "--windowed",
    "--onefile",
    "--name", "LuminkeyAnalogInput",
    "--icon", "app_icon.ico",
    "--uac-admin", 
    "--add-data", "app_icon.png;.",
    "--collect-all", "vgamepad",
    "--collect-all", "interception",
    "main.py"
]

subprocess.run(cmd)

print("Build complete! Check the 'dist' folder for LuminkeyAnalogInput.exe")
