import os
import shutil

def normalize_package_content(package_content_path):
    """
    若 package_content 下只有一個子目錄（例如 amf），
    則將該目錄內容提升一層
    """
    entries = os.listdir(package_content_path)
    full_paths = [os.path.join(package_content_path, e) for e in entries]

    # 只剩一個資料夾，且是目錄
    if len(full_paths) == 1 and os.path.isdir(full_paths[0]):
        inner_dir = full_paths[0]

        for item in os.listdir(inner_dir):
            shutil.move(
                os.path.join(inner_dir, item),
                os.path.join(package_content_path, item)
            )

        shutil.rmtree(inner_dir)