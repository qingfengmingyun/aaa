#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_list.py —— 扫描本目录，生成 files.json（网页的下载清单）。

用法：
    python3 generate_list.py     # macOS / Linux
    python generate_list.py      # Windows

规则：
    - 只收录「本文件所在目录」里的文件，不进入子文件夹。
    - 网站自身文件（index.html、files.json、本脚本、README.md 等）不会被收录。
    - 以 "." 开头的隐藏文件、系统垃圾文件不会被收录。
    - 按修改时间倒序排列（新文件在前）。
"""

import json
import os
from datetime import datetime

# ====== 可按需修改的配置 ======
# 不收录的文件（网站自身文件）
EXCLUDE_FILES = {
    "index.html",
    "files.json",
    "generate_list.py",
    "README.md",
    "LICENSE",
    ".gitignore",
    "Thumbs.db",
    "desktop.ini",
}

# Cloudflare Pages 单文件大小上限（25 MiB），超过会给出提醒
MAX_FILE_SIZE = 25 * 1024 * 1024
# ==============================


def human_size(n):
    """把字节数转成人类可读的字符串，例如 "3.4 MB"。"""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(n)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    if i == 0:
        return "%d %s" % (int(size), units[i])
    return "%.1f %s" % (size, units[i])


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    entries = []

    for name in os.listdir(base_dir):
        if name in EXCLUDE_FILES or name.startswith("."):
            continue
        path = os.path.join(base_dir, name)
        if not os.path.isfile(path):
            continue

        st = os.stat(path)
        entries.append({
            "name": name,
            "size": st.st_size,
            "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "_mtime": st.st_mtime,
        })

    # 最近更新的排在前面
    entries.sort(key=lambda item: item["_mtime"], reverse=True)
    for item in entries:
        del item["_mtime"]

    data = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(entries),
        "files": entries,
    }

    out_path = os.path.join(base_dir, "files.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("[OK] 已生成 %s" % out_path)
    print("[OK] 共收录 %d 个文件：" % len(entries))
    for item in entries:
        print("  - %s (%s)" % (item["name"], human_size(item["size"])))

    oversized = [item for item in entries if item["size"] > MAX_FILE_SIZE]
    if oversized:
        print()
        print("[警告] 以下文件超过 25 MB，Cloudflare Pages 可能无法部署，")
        print("       建议改用分卷压缩或网盘分享：")
        for item in oversized:
            print("  - %s (%s)" % (item["name"], human_size(item["size"])))


if __name__ == "__main__":
    main()
