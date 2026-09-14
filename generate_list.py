#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_list.py —— 扫描本目录，生成两个文件：

  files.json  —— 网页的下载清单（收录目录里的所有文件）
  update.json —— APP「检查更新」的数据（从文件名自动识别最新版本）

用法：
    python3 generate_list.py     # macOS / Linux
    python generate_list.py      # Windows

规则：
    - 只收录「本文件所在目录」里的文件，不进入子文件夹。
    - 网站自身文件（index.html、files.json、update.json、versions.json、本脚本、README.md 等）不会被收录。
    - 以 "." 开头的隐藏文件、系统垃圾文件不会被收录。
    - files.json：按修改时间倒序（新文件在前）。
    - update.json：只识别命名为「软件名_版本号.apk」的文件（例如 `qfmy查看器（重构版）_6.3.apk`），
      自动选择版本号最高的一个作为最新版；版本号格式支持 6.3 / 6.3.1 / 6.10。
    - 更新说明在 versions.json 里配置（可选）。
"""

import json
import os
import re
import hashlib
from datetime import datetime

# ====== 可按需修改的配置 ======
EXCLUDE_FILES = {
    "index.html",
    "files.json",
    "update.json",
    "versions.json",
    "generate_list.py",
    "README.md",
    "LICENSE",
    ".gitignore",
    "Thumbs.db",
    "desktop.ini",
}

DEFAULT_NOTES = "优化与修复，建议更新到最新版本。"

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


def ver_key(v):
    """把版本号字符串转成可比较的元组，非法格式返回 None。"""
    if not v or not re.match(r"^[0-9]+(\.[0-9]+)*$", v):
        return None
    return tuple(int(x) for x in v.split("."))


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_versions(base_dir):
    path = os.path.join(base_dir, "versions.json")
    if not os.path.isfile(path):
        print("[提示] 未找到 versions.json，将使用默认配置。")
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        apps = data.get("apps", {})
        return apps if isinstance(apps, dict) else {}
    except Exception as e:
        print("[警告] versions.json 解析失败：%s" % e)
        return {}


def pick_notes(notes_cfg, version):
    """取某个版本的更新说明。支持字符串或 {版本号:说明} 两种格式。"""
    if isinstance(notes_cfg, str) and notes_cfg.strip():
        return notes_cfg.strip()
    if isinstance(notes_cfg, dict):
        v = notes_cfg.get(version)
        if isinstance(v, str) and v.strip():
            return v.strip()
        d = notes_cfg.get("default")
        if isinstance(d, str) and d.strip():
            return d.strip()
    return DEFAULT_NOTES


def build_update_apps(base_dir, files):
    """根据文件名自动生成 update.json 的 apps 数据。"""
    apps_cfg = load_versions(base_dir)
    if not apps_cfg:
        apps_cfg = {"com.qfmy.qfmyckq": {"name": "qfmy查看器（重构版）"}}
    out = {}
    names = [item["name"] for item in files]
    for pkg, cfg in apps_cfg.items():
        if not isinstance(cfg, dict):
            continue
        app_name = cfg.get("name") or "qfmy查看器（重构版）"
        pattern = re.compile(r"^" + re.escape(app_name + "_") + r"([0-9]+(\.[0-9]+)*)\.apk$")
        best = None  # (ver_tuple, ver_str, filename)
        for name in names:
            m = pattern.match(name)
            if not m:
                continue
            key = ver_key(m.group(1))
            if key is None:
                continue
            if best is None or key > best[0]:
                best = (key, m.group(1), name)
        if best is None:
            print("[警告] 未找到符合命名格式的 APK：%s_版本号.apk" % app_name)
            continue
        ver_str = best[1]
        fname = best[2]
        fpath = os.path.join(base_dir, fname)
        try:
            size = os.path.getsize(fpath)
            md5 = md5_of(fpath)
        except Exception as e:
            print("[警告] 读取 %s 失败：%s" % (fname, e))
            continue
        out[pkg] = {
            "name": app_name,
            "versionName": ver_str,
            "file": fname,
            "size": size,
            "md5": md5,
            "notes": pick_notes(cfg.get("notes"), ver_str),
        }
        print("[OK] 识别到最新版：%s（%s，%s）" % (fname, ver_str, human_size(size)))
    return out


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

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---- files.json ----
    data = {
        "generated": now_str,
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

    # ---- update.json ----
    up_apps = build_update_apps(base_dir, entries)
    up_path = os.path.join(base_dir, "update.json")
    with open(up_path, "w", encoding="utf-8") as f:
        json.dump({"generated": now_str, "apps": up_apps}, f, ensure_ascii=False, indent=2)
    print("[OK] 已生成 %s（收录 %d 个应用的更新信息）" % (up_path, len(up_apps)))

    oversized = [item for item in entries if item["size"] > MAX_FILE_SIZE]
    if oversized:
        print()
        print("[警告] 以下文件超过 25 MB，Cloudflare Pages 可能无法部署，")
        print("       建议改用分卷压缩或网盘分享：")
        for item in oversized:
            print("  - %s (%s)" % (item["name"], human_size(item["size"])))


if __name__ == "__main__":
    main()
