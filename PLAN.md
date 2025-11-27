## TypeFlow typing analytics tool - work plan

### Goal
- Build a Windows tray application in Python that logs keyboard events via `pynput`, stores them (SQLite with encryption for sensitive text), and presents modern Fluent-style analytics UI using PyQt-Fluent-Widgets and PyQtGraph/Matplotlib. Sensitive typing history is unlocked with a user password; aggregate stats remain visible without it.

### Milestones & status
1) Workspace audit & planning — ✅ (context captured, plan drafted)
2) Project scaffolding & dependencies — ✅ (`typeflow/` package, `requirements.txt`, config defaults)
3) Data/encryption layer & keyboard hook service — ✅ (SQLite schema, crypto manager, stats engine, pynput listener)
4) Analytics computations & visual components — ✅ (dashboard cards + PyQtGraph chart, history unlock UI)
5) Tray app entrypoint, password flows, wiring — ✅ (controller, tray actions, startup password prompt)
6) Documentation & final review — ✅ (README, AST sanity check)

### Immediate next steps
- Install dependencies (`pip install -r requirements.txt`) and run locally to validate UI/keyboard hook.
- Provide a real icon asset and tweak styles once dependencies are available.

### Risks / considerations
- Restricted network may block installing PyQt-Fluent-Widgets/cryptography; code will be structured but untested here.
- Keyboard hook must avoid blocking UI; use background thread with safe queue dispatch into DB.
- Need clear idle/active thresholds to segment typing sessions for accurate speed metrics.
