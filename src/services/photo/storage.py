import os
import cv2
import uuid
from datetime import datetime

import numpy as np
from fastapi import UploadFile

from src.constants import ALBUM_DIR


# 업로드 이미지 저장
def save_image_to_album(file: UploadFile, image_np: np.ndarray, unique_filename) -> str:
    save_dir = os.path.join(ALBUM_DIR, "uploaded")
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, unique_filename)

    cv2.imwrite(save_path, image_np)

    return unique_filename  # 저장된 파일명을 반환


def get_image_path(file_name: str) -> str:
    return os.path.join(ALBUM_DIR, "uploaded", file_name)


# 파일명 변경
def generate_unique_filename(original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[-1]
    uid = uuid.uuid4().hex[:8]
    date = datetime.now().strftime("%Y%m%d")
    return f"{date}_{uid}{ext}"
