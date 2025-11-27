# TypeFlow (中文说明)

Windows 后台托盘应用，使用 Python、PyQt-Fluent-Widgets 和 PyQtGraph/Matplotlib 记录键盘输入，提供现代化可视化仪表盘，并将完整输入历史以用户密码加密存储到本地 SQLite。

## 功能亮点
- 后台 `pynput` 键盘监听（不阻塞 UI），可随托盘启动/暂停。
- SQLite 本地存储，完整输入历史 AES-GCM 加密；聚合统计无需密码即可查看。
- 仪表盘展示：按键频次、平均打字速率、累计按键、活跃时段/日统计。
- 首次启动要求设置加密密码；之后可通过输入密码解锁历史查看。
- Fluent 风格的主界面 + 托盘菜单；自定义图标已内置 (`typeflow/assets/icon.ico`)。

## 安装与运行
1) 安装依赖（需联网）：
   ```bash
   pip install -r requirements.txt
   ```
2) 启动应用：
   ```bash
   python -m typeflow.app
   ```
3) 首次启动会提示设置加密密码。再次进入历史页时输入密码即可解锁；未解锁时仍可查看聚合统计。

## 打包为 exe（PyInstaller）
在项目根目录运行：
```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed ^
  --name TypeFlow ^
  --icon typeflow\\assets\\icon.ico ^
  --add-data \"typeflow\\assets;typeflow/assets\" ^
  typeflow\\app.py
```
- 生成的可执行文件位于 `dist/TypeFlow/TypeFlow.exe`。
- 若使用虚拟环境，请在虚拟环境中执行以上命令。
- 若需要控制台日志，将 `--windowed` 改为 `--console`。

## 目录结构
- `typeflow/app.py`: 应用入口，托盘与主窗体。
- `typeflow/ui/*`: Fluent 界面（仪表盘、历史解锁、托盘）。
- `typeflow/keyboard_hook.py`: 后台键盘监听。
- `typeflow/stats.py`: 打字会话分段与统计。
- `typeflow/database.py`: SQLite 存储/查询。
- `typeflow/encryption.py`: PBKDF2 + AES-GCM 加密。
- `typeflow/assets/`: 应用图标资源。
- `typeflow/config.py`: 阈值和路径配置。

## 取消安装 / 重置
- 托盘菜单选择“取消安装（清除数据）”，将清空本地数据库与密码，暂停捕获，并恢复到首次启动状态。

## 注意事项
- 加密密码无法找回，请妥善保存；未解锁时不会写入新的明文解密能力。
- 长时间运行建议保持 PyInstaller 打包版本以避免依赖缺失。
