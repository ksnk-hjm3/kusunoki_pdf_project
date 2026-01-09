import os
import shutil
from collections import defaultdict

# 整理対象のルートパス（デスクトップ）
ROOT = os.getcwd()

# 移動先フォルダ
FOLDERS = {
    "src": [".py"],
    "data": [".csv", ".json", ".xlsx"],
    "output": [".pdf"],
    "fonts": [".ttf", ".otf"],
    "unclassified": []
}

# フォルダ作成
for folder in FOLDERS:
    os.makedirs(os.path.join(ROOT, folder), exist_ok=True)

# 重複検出用
seen_files = defaultdict(list)

# 整理処理
for item in os.listdir(ROOT):
    path = os.path.join(ROOT, item)

    # __pycache__ 削除
    if os.path.isdir(path) and item == "__pycache__":
        shutil.rmtree(path)
        print(f"✅ Deleted: {item}")
        continue

    # フォルダはスキップ（pdf_reportsなどは手動で確認）
    if os.path.isdir(path):
        continue

    # 拡張子で分類
    ext = os.path.splitext(item)[1].lower()
    moved = False
    for folder, exts in FOLDERS.items():
        if ext in exts:
            dest = os.path.join(ROOT, folder, item)
            shutil.move(path, dest)
            print(f"📦 Moved: {item} → {folder}/")
            moved = True
            break

    # 重複検出
    seen_files[item].append(path)

    # 未分類ファイル
    if not moved:
        dest = os.path.join(ROOT, "unclassified", item)
        shutil.move(path, dest)
        print(f"❓ Unclassified: {item} → unclassified/")

# 重複ファイルの報告
print("\n🔍 Duplicate check:")
for name, paths in seen_files.items():
    if len(paths) > 1:
        print(f"⚠️ Duplicate: {name} → {paths}")
