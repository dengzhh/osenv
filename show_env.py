#!/usr/bin/env python3
"""显示当前工作目录和操作系统信息"""

import os
import platform
import sys


def show_environment():
    """显示环境信息"""
    print("=" * 60)
    print("环境信息")
    print("=" * 60)

    # 工作目录
    print(f"\n📁 当前工作目录:")
    print(f"   {os.getcwd()}")

    # 操作系统信息
    print(f"\n💻 操作系统信息:")
    print(f"   系统: {platform.system()}")
    print(f"   版本: {platform.version()}")
    print(f"   发行版: {platform.platform()}")
    print(f"   架构: {platform.machine()}")
    print(f"   处理器: {platform.processor()}")

    # Python 信息
    print(f"\n🐍 Python 信息:")
    print(f"   版本: {sys.version.split()[0]}")
    print(f"   可执行文件: {sys.executable}")

    # 用户信息
    print(f"\n👤 用户信息:")
    print(f"   用户名: {os.getenv('USER', '未知')}")
    print(f"   HOME: {os.getenv('HOME', '未知')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    show_environment()