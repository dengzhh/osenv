#!/usr/bin/env python3
"""
显示当前工作目录和操作系统信息
"""

import os
import platform
import sys


def main():
    print("=" * 60)
    print("AI 编程开发环境信息")
    print("=" * 60)
    print()

    # 工作目录
    print("工作目录:")
    print(f"  当前目录: {os.getcwd()}")
    print(f"  用户主目录: {os.path.expanduser('~')}")
    print()

    # 操作系统信息
    print("操作系统信息:")
    print(f"  系统: {platform.system()}")
    print(f"  发行版本: {platform.release()}")
    print(f"  版本: {platform.version()}")
    print(f"  构建信息: {platform.platform()}")
    print(f"  机器类型: {platform.machine()}")
    print(f"  处理器: {platform.processor()}")
    print()

    # Python 信息
    print("Python 环境:")
    print(f"  版本: {sys.version}")
    print(f"  可执行文件: {sys.executable}")
    print()

    # 环境变量（部分关键信息）
    print("关键环境变量:")
    env_vars = ["SHELL", "PWD", "HOME", "USER", "LANG", "TERM"]
    for var in env_vars:
        value = os.environ.get(var, "未设置")
        print(f"  {var}: {value}")
    print()

    # WSL 特定信息
    if "WSL" in platform.release() or "microsoft" in platform.release():
        print("WSL 信息:")
        print("  检测到运行在 WSL 环境中")
        if os.path.exists("/proc/version"):
            with open("/proc/version", "r") as f:
                wsl_info = f.read().strip()
                print(f"  {wsl_info}")
        print()

    print("=" * 60)


if __name__ == "__main__":
    main()