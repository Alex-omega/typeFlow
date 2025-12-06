import os
from pathlib import Path

# 锁文件位置
lock_path = Path.home() / ".typeflow" / "typeflow.lock"

# 检查锁文件是否存在并删除
if lock_path.exists():
    try:
        os.remove(lock_path)
        print(f"成功删除锁文件: {lock_path}")
    except Exception as e:
        print(f"删除锁文件时出错: {e}")
else:
    print("锁文件不存在，无需删除")
