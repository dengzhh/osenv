import os

def list_files():
    """列出工作目录的所有文件和目录"""
    print(f"当前工作目录: {os.getcwd()}")
    print("\n文件列表:")

    items = sorted(os.listdir('.'))
    for item in items:
        if os.path.isdir(item):
            print(f"  [目录] {item}")
        else:
            print(f"  [文件] {item}")

if __name__ == "__main__":
    list_files()
