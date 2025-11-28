# TypeFlow

A Windows background system tray application built with **Python**, **PyQt-Fluent-Widgets**, and **PyQtGraph/Matplotlib** to record keyboard input and visualize typing statistics.

## Features

* Background keyboard monitoring via `pynput` (non-blocking for the UI), with start/pause control from the system tray.
* Local SQLite storage with **AES-GCM encryption** for full input history; aggregated statistics can be viewed without a password.
* Dashboard visualizations:

  * Key frequency
  * Average typing speed
  * Total keystrokes
  * Active time periods and daily activity
* Password setup required on first launch; encrypted history can only be accessed after unlocking.
* Fluent-style main interface with system tray menu.
* Custom built-in icon (`typeflow/assets/icon.ico`).

## Installation & Usage

### Run with Python

**0) Environment Requirements:**

1. Python **3.11.5 or higher**
2. **Windows 10 or later only**

**1) Install dependencies:**

```bash
pip install -r requirements.txt
```

**2) Launch the application:**

```bash
python -m typeflow.app
```

---

### Run as an Executable

Please refer to the **Release** page for the packaged standalone executable.

---

## Uninstall / Reset

* Select **"Uninstall (Clear Data)"** from the system tray menu to:

  * Delete the local database and password
  * Stop keyboard capture
  * Restore the app to its first-launch state

---

## Notes

* The encryption password **cannot be recovered**. Please store it securely.
* When not unlocked, no plaintext decryption capability is available.
* For long-term usage, the **PyInstaller packaged version** is recommended to avoid dependency issues.
