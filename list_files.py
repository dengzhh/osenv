#!/usr/bin/env python3
"""列出工作目录的所有文件和目录"""

import os
from pathlib import Path
from typing import List, Tuple


def list_directory(path: str = ".", show_hidden: bool = False) -> List[Tuple[str, str]]:
    """
    列出指定路径下的所有文件和目录

    Args:
        path: 要列出的目录路径，默认为当前目录
        show_hidden: 是否显示隐藏文件

    Returns:
        包含 (name, type) 元组的列表，type 为 'file' 或 'dir'
    """
    items = []
    p = Path(path)

    if not p.exists():
        print(f"错误: 路径 '{path}' 不存在")
        return items

    if not p.is_dir():
        print(f"错误: '{path}' 不是目录")
        return items

    for item in p.iterdir():
        # 跳过隐藏文件（除非明确要求显示）
        if not show_hidden and item.name.startswith('.'):
            continue

        item_type = 'dir' if item.is_dir() else 'file'
        items.append((item.name, item_type))

    # 按类型排序（目录优先），然后按名称排序
    items.sort(key=lambda x: (x[1] != 'dir', x[0]))

    return items


def print_directory_tree(path: str = ".", show_hidden: bool = False, max_depth: int = None, current_depth: int = 0):
    """
    以树形结构打印目录内容

    Args:
        path: 要列出的目录路径
        show_hidden: 是否显示隐藏文件
        max_depth: 最大递归深度，None 表示无限
        current_depth: 当前递归深度（内部使用）
    """
    if max_depth is not None and current_depth >= max_depth:
        return

    items = list_directory(path, show_hidden)

    indent = "  " * current_depth
    prefix = "├─ " if current_depth > 0 else ""

    for i, (name, item_type) in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└─ " if is_last else "├─ "

        full_path = Path(path) / name
        if item_type == 'dir':
            print(f"{indent}{connector}{name}/")
            # 递归打印子目录
            if max_depth is None or current_depth + 1 < max_depth:
                print_directory_tree(str(full_path), show_hidden, max_depth, current_depth + 1)
        else:
            print(f"{indent}{connector}{name}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='列出工作目录的所有文件和目录')
    parser.add_argument('path', nargs='?', default='.', help='要列出的目录路径（默认: 当前目录）')
    parser.add_argument('-a', '--all', action='store_true', help='显示隐藏文件')
    parser.add_argument('-t', '--tree', action='store_true', help='以树形结构显示')
    parser.add_argument('-d', '--depth', type=int, default=None,
                       help='树形结构的最大深度（默认: 无限制）')

    args = parser.parse_args()

    abs_path = Path(args.path).resolve()
    print(f"\n📁 目录: {abs_path}")
    print(f"{'='*60}\n")

    # 获取所有项用于统计
    items = list_directory(str(abs_path), args.all)

    if args.tree:
        print_directory_tree(str(abs_path), args.all, args.depth)
    else:
        if not items:
            print("(空目录)")
        else:
            dirs = [name for name, t in items if t == 'dir']
            files = [name for name, t in items if t == 'file']

            if dirs:
                print("📂 目录:")
                for d in dirs:
                    print(f"  {d}/")
                print()

            if files:
                print("📄 文件:")
                for f in files:
                    print(f"  {f}")

    print(f"\n总计: {len(items)} 项")


if __name__ == "__main__":
    main()
