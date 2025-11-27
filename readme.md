# TypeFlow

Windows tray application that records typing activity in the background, stores encrypted history locally, and presents modern Fluent-style analytics built with Python, PyQt-Fluent-Widgets, and PyQtGraph/Matplotlib.

## Features
- Background keyboard hook via `pynput` (runs outside the UI thread).
- SQLite persistence with password-gated encryption for full typing history; non-sensitive aggregate stats stay visible without a password.
- Dashboards for key frequency, average typing speed, cumulative counts, and peak activity windows.
- Secure history viewer unlocked with the user’s password; first launch prompts for password creation.
- System tray experience: start/stop capture, quick glance stats, and opening the main dashboard.

## Getting started
1) Install dependencies (network access required):
   ```bash
   pip install -r requirements.txt
   ```
2) Run the app:
   ```bash
   python -m typeflow.app
   ```
3) On first launch, create an encryption password. Later, use that password to unlock the history view; aggregated stats remain available without it.

## Packaging to Windows .exe (PyInstaller)
From the project root:
```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed ^
  --name TypeFlow ^
  --icon typeflow\\assets\\icon.ico ^
  --add-data "typeflow\\assets;typeflow/assets" ^
  typeflow\\app.py
```
- Output binary: `dist/TypeFlow/TypeFlow.exe`.
- Run inside your virtual environment if you use one.
- Swap `--windowed` to `--console` if you prefer a console window for logs.

## Reset / uninstall
- Use the tray menu item “取消安装（清除数据）” to wipe the local database and password, pause capture, and return the app to first-run state.

## Architecture
- `typeflow/database.py`: SQLite persistence, aggregated stats tables, encrypted event storage.
- `typeflow/encryption.py`: PBKDF2-derived AES-GCM encryption with salted password verifier.
- `typeflow/stats.py`: Session segmentation (idle/engagement thresholds) and snapshot calculations.
- `typeflow/keyboard_hook.py`: Background `pynput` listener feeding the stats engine.
- `typeflow/ui/*`: PyQt-Fluent-Widgets windows (dashboard, history unlock), tray icon, plotting via PyQtGraph.
- `typeflow/assets/icon.ico`: 自定义图标，已用于主窗口和托盘。

## Notes
- Idle and engagement thresholds are configurable in `typeflow/config.py`.
- Typing history is encrypted at rest. Keep your password safe; it cannot be recovered if lost.
- New encrypted history is captured only after a password is set/unlocked; aggregated stats still accumulate without unlocking.
