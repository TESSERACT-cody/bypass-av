import sys
import os
import ctypes
import winreg
import psutil
from pathlib import Path


def _run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
        )
        sys.exit(0)

_TARGET_PROCESSES = {
    "qhactivatwdefence.exe",
    "desktopplus64.exe",
    "cefutil.exe",
    "promoutil.exe",
    "qhsafetray.exe",
    "qhsafemain.exe",
    "qhwatchdog.exe"
}

_TARGET_STARTUP_PATHS = {
    r"C:\Program Files (x86)\360\Total Security\safemon\360Tray.exe",
    r"C:\ProgramData\360TotalSecurity\DesktopPlus\DesktopPlus64.exe"
}

for proc in psutil.process_iter(['name']):
    try:
        name = proc.info['name'].lower()
        if name in _TARGET_PROCESSES:
            proc.kill()
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass 

for hive, key_path in (
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
):
    try:
        with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            i = 0
            while True:
                try:
                    val_name, val_data, _ = winreg.EnumValue(key, i)
                    i += 1
                    if val_data.lower() in {p.lower() for p in _TARGET_STARTUP_PATHS}:
                        winreg.DeleteValue(key, val_name)
                except OSError:
                    break
    except OSError:
        pass 

for folder in (
    Path(os.environ['APPDATA']) / r"Microsoft\Windows\Start Menu\Programs\Startup",
    Path(os.environ['PROGRAMDATA']) / r"Microsoft\Windows\Start Menu\Programs\Startup"
):
    if not folder.exists():
        continue
    for entry in folder.iterdir():
        try:
            resolved = str(entry.resolve()).lower()
            if resolved in {p.lower() for p in _TARGET_STARTUP_PATHS}:
                entry.unlink()
        except Exception:
            pass 

_run_as_admin()