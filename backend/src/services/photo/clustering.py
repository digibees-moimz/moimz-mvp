import os
import uuid
import pickle
from datetime import datetime
from typing import List

import cv2
import numpy as np
import face_recognition
from fastapi import UploadFile
from scipy.spatial.distance import cosine

from src.utils.file_io import load_json, save_json
from src.constants import METADATA_PATH, REPRESENTATIVES_PATH, ALBUM_DIR, FACE_DATA_DIR


RECENT_VECTOR_COUNT = 20  # 대표 벡터 계산 시 사용하는 벡터 개수


def generate_filename(original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[-1]
    uid = uuid.uuid4().hex[:8]
    date = datetime.now().strftime("%Y%m%d")
    return f"{date}_{uid}{ext}"


def save_image(file: UploadFile, image_np: np.ndarray, filename: str):
    save_dir = os.path.join(ALBUM_DIR, "uploaded")
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, filename)
    cv2.imwrite(path, image_np)


# 인물별 클러스터링
async def process_and_classify_faces(files: List[UploadFile]) -> List[dict]:
    metadata = load_json(METADATA_PATH, {})
    representatives = load_json(REPRESENTATIVES_PATH, {})
    override_map = {}

    for face in metadata.values():
        if "override" in face:
            origin = face.get("person_id")
            new = face.get("override")
            if origin != new:  # 자가 참조 방지
                override_map[origin] = new

    if not representatives:
        print("📥 대표 벡터가 없음 → 출석 체크용 얼굴 불러오기")
        representatives.update(load_attendance_representatives())

    results = []

    for file in files:
        image_bytes = await file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        # 파일명 중복 방지 및 사진 저장
        filename = generate_filename(file.filename)
        save_image(file, image, filename)

        face_locations = face_recognition.face_locations(image)
        encodings = face_recognition.face_encodings(image, face_locations)

        for loc, encoding in zip(face_locations, encodings):
            person_id = find_matching_person_id(encoding, representatives)

            if person_id in override_map:
                original = person_id
                person_id = override_map[person_id]

                # 기존 대표 벡터 및 history 제거
                print(f"override된 {original}의 대표 벡터 제거")
                representatives.pop(original, None)
                representatives.pop(f"{original}_history", None)

            face_id = get_next_face_id(metadata)
            metadata[face_id] = {
                "file_name": filename,
                "location": loc,
                "encoding": encoding.tolist(),
                "person_id": person_id,
            }

            update_representative(person_id, encoding, representatives)

            results.append(
                {
                    "face_id": face_id,
                    "file_name": filename,
                    "location": loc,
                    "person_id": person_id,
                }
            )

    save_json(METADATA_PATH, metadata)
    save_json(REPRESENTATIVES_PATH, representatives)
    return results


def find_matching_person_id(
    new_encoding: np.ndarray, reps: dict, threshold: float = 0.12
) -> str:
    best_match = None
    best_dist = float("inf")

    for person_id, vec in reps.items():
        if person_id.endswith("_history"):
            continue

        vec = np.array(vec, dtype=np.float32).flatten()

        # ✅ 벡터 유효성 검사 추가
        if vec.shape != (128,) or np.any(np.isnan(vec)) or np.any(np.isinf(vec)):
            print(f"🚫 {person_id} 대표 벡터가 손상됨. 건너뜀.")
            continue

        dist = cosine(new_encoding, vec)

        # ✅ dist 값 유효성 검사
        if np.isnan(dist) or np.isinf(dist):
            print(f"🚫 유사도 계산 결과가 유효하지 않음. 건너뜀.")
            continue

        print(f"🧠 비교 대상 {person_id} 벡터, 거리: {dist:.4f}")

        if dist < best_dist:
            best_dist = dist
            best_match = person_id

    print(
        f"📏 최종 거리: {best_dist:.4f}, 매칭 대상: {best_match} → {'✅ 기존 인물' if best_dist < threshold else '🆕 새 인물'}"
    )

    if best_dist < threshold:
        return best_match
    else:
        print(f"⚠️ 새 사람 생성됨: 거리 {best_dist:.4f} > threshold {threshold}")
        return get_new_person_id(reps)


# 대표 벡터 갱신 함수 (최근 N개의 벡터를 평균)
def update_representative(person_id: str, new_encoding: np.ndarray, reps: dict):
    from collections import deque

    history_key = f"{person_id}_history"
    history = reps.get(history_key, [])
    dq = deque(history, maxlen=RECENT_VECTOR_COUNT)
    dq.append(new_encoding.tolist())

    reps[history_key] = list(dq)

    # medoid 방식으로 대표 벡터 지정
    rep_vec = get_medoid_vector(dq)
    reps[person_id] = rep_vec


def get_medoid_vector(encoding_list: List[List[float]]) -> List[float]:
    if not encoding_list:
        print("⚠️ encoding_list 비어 있음. 빈 벡터 반환.")
        return [0.0] * 128  # fallback

    enc_np = np.array(encoding_list)

    # 각 벡터 간 거리 행렬
    dist_matrix = np.linalg.norm(enc_np[:, None] - enc_np, axis=2)
    dist_sums = np.sum(dist_matrix, axis=1)

    medoid_index = np.argmin(dist_sums)
    return enc_np[medoid_index].tolist()


# 새로운 사람 ID 생성
def get_new_person_id(reps: dict) -> str:
    existing = [
        int(k.replace("person_", ""))
        for k in reps
        if k.startswith("person_") and not k.endswith("_history")
    ]
    next_id = max(existing + [-1]) + 1
    return f"person_{next_id}"


# 얼굴 단위 ID 생성
def get_next_face_id(data: dict) -> str:
    existing = [
        int(k.replace("face_", "")) for k in data.keys() if k.startswith("face_")
    ]
    next_id = max(existing + [-1]) + 1
    return f"face_{next_id:04}"


# 출석체크용 `.pkl` 얼굴 데이터 → 대표 벡터 로딩 함수
def load_attendance_representatives() -> dict:
    """
    출석 체크용 얼굴 데이터를 기반으로 대표 벡터를 계산하여 반환함
    - person_id 기준으로 평균 벡터를 계산하여 대표 벡터로 사용
    - 최근 N개의 벡터는 history로 함께 저장
    """
    reps = {}

    for file in os.listdir(FACE_DATA_DIR):
        if not file.startswith("face_") or not file.endswith(".pkl"):
            continue

        user_id = file.split("_")[1].split(".")[0]
        path = os.path.join(FACE_DATA_DIR, file)

        with open(path, "rb") as f:
            user_data = pickle.load(f)

            # 구조가 리스트면 호환 처리
            encodings = user_data["raw"] if isinstance(user_data, dict) else user_data

            enc_list = encodings[-RECENT_VECTOR_COUNT:]
            mean_vec = np.mean(enc_list, axis=0)

            reps[f"person_{user_id}"] = mean_vec.tolist()
            reps[f"person_{user_id}_history"] = [e.tolist() for e in enc_list]

    return reps
