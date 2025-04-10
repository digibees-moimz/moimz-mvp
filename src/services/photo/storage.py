import os
import cv2
import uuid
import hashlib
from datetime import datetime

import numpy as np
from fastapi import UploadFile

from src.constants import ALBUM_DIR, IMAGE_HASH_PATH
from src.utils.file_io import load_json, save_json


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


# 이미지 해시 구하기
def get_image_hash(image_bytes: bytes) -> str:
    return hashlib.md5(image_bytes).hexdigest()


# 이미지 파일 중복 검사
def is_duplicate_image(image_bytes: bytes) -> bool:
    image_hash = get_image_hash(image_bytes)
    hash_list = load_json(IMAGE_HASH_PATH, [])

    if not isinstance(hash_list, list):
        hash_list = []

    if image_hash in hash_list:
        return True  # 중복
    else:
        hash_list.append(image_hash)
        save_json(IMAGE_HASH_PATH, hash_list)
        return False
