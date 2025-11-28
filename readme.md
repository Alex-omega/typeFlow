# TypeFlow

Windows 后台托盘应用，使用 Python、PyQt-Fluent-Widgets 和 PyQtGraph/Matplotlib 记录键盘输入，展示相关数据统计。

## 功能
- 后台 `pynput` 键盘监听（不阻塞 UI），可随托盘启动/暂停。
- SQLite 本地存储，完整输入历史 AES-GCM 加密；聚合统计无需密码即可查看。
- 仪表盘展示：按键频次、平均打字速率、累计按键、活跃时段/日统计。
- 首次启动要求设置加密密码；之后可通过输入密码解锁历史查看。
- Fluent 风格的主界面 + 托盘菜单；自定义图标已内置 (`typeflow/assets/icon.ico`)。

## 安装与运行
### 基于 Python 运行
0) 确认环境：
   1. 要求 Python 3.11.5 或更高版本；
   2. 本程序仅适用于 Windows 10 及以上。
1) 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2) 启动应用：
   ```bash
   python -m typeflow.app
   ```

### 基于可执行文件运行
详见项目 Release 页面。

## 取消安装 / 重置
- 托盘菜单选择“取消安装（清除数据）”，将清空本地数据库与密码，暂停捕获，并恢复到首次启动状态。

## 注意事项
- 加密密码无法找回，请妥善保存；未解锁时不会写入新的明文解密能力。
- 长时间运行建议保持 PyInstaller 打包版本以避免依赖缺失。
