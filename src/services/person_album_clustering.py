import os
from typing import List, Dict

import cv2
import face_recognition
import numpy as np
import hdbscan
from fastapi import UploadFile
from scipy.spatial.distance import cosine
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.decomposition import PCA

from src.utils.file_io import load_json, save_json


ALBUM_DIR = os.path.join("src", "data", "album")
os.makedirs(ALBUM_DIR, exist_ok=True)

ENCODING_PATH = os.path.join(ALBUM_DIR, "face_encodings.npy")
METADATA_PATH = os.path.join(ALBUM_DIR, "face_data.json")
REPRESENTATIVES_PATH = os.path.join(ALBUM_DIR, "representatives.json")


# 초기 인물 클러스터링 (비지도 학습 기반, HDBSCAN)
async def run_album_clustering(files: List[UploadFile]) -> Dict:
    all_face_encodings = []  # 전체 얼굴 벡터
    face_image_map = []  # 얼굴 벡터에 해당하는 이미지 정보 (파일명, 얼굴 좌표)

    for file in files:
        image_bytes = await file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        face_locations = face_recognition.face_locations(image)
        encodings = face_recognition.face_encodings(image, face_locations)

        for loc, encoding in zip(face_locations, encodings):
            all_face_encodings.append(encoding)
            face_image_map.append(
                {
                    "file_name": file.filename,
                    "location": loc,  # (top, right, bottom, left)
                }
            )

    if not all_face_encodings:
        return {"message": "등록된 얼굴이 없습니다."}

    # 거리 행렬 생성 (cosine 거리 사용)
    distance_matrix = pairwise_distances(all_face_encodings, metric="cosine")

    # HDBSCAN 클러스터링 수행
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2, metric="precomputed"
    )  # 같은 사람이 최소 2번 이상 등장해야 클러스터로 인식
    labels = clusterer.fit_predict(
        distance_matrix
    )  # 클러스터 번호를 리턴 (노이즈는 -1)

    clustered_result = {}  # 사진 위치 정보 저장
    cluster_vectors = {}  # 실제 얼굴 벡터 데이터 저장 (계산용 데이터)

    for idx, label in enumerate(labels):
        info = face_image_map[idx]
        if label == -1:
            clustered_result.setdefault("noise", []).append(info)
        else:
            person_key = f"person_{label}"
            clustered_result.setdefault(person_key, []).append(info)
            cluster_vectors.setdefault(person_key, []).append(encoding)

    # 클러스터별 대표 벡터(평균값) 저장
    representatives = {}
    for person_id, vectors in cluster_vectors.items():
        mean_vector = np.mean(vectors, axis=0)
        representatives[person_id] = mean_vector.tolist()

    save_json(REPRESENTATIVES_PATH, representatives)

    return {
        "num_faces": len(all_face_encodings),
        "num_clusters": len(set(labels)) - (1 if -1 in labels else 0),
        "num_noise": list(labels).count(-1),
        "clusters": clustered_result,
        "representatives_saved": True,
    }


# 증분 인물 분류 (KNN 방식)
def find_nearest_person(
    new_encoding: np.ndarray, file_name: str, location, threshold: float = 0.45
) -> str:
    # 중복 얼굴 체크
    if is_duplicate_face(new_encoding):
        print(f"중복 얼굴 감지: {file_name}의 얼굴은 이미 존재합니다.")
        return "duplicate_person"

    reps = load_json(REPRESENTATIVES_PATH)

    closest_person = None
    closest_dist = float("inf")

    # 추가된 사진의 벡터와 기존 평균 벡터와 거리 비교
    for person_id, vector in reps.items():
        distance = cosine(new_encoding, vector)
        if distance < closest_dist:
            closest_person = person_id
            closest_dist = distance

    if closest_dist < threshold:
        person_id = closest_person
    else:
        person_id = get_new_person_id()

    # 대표 벡터와 face_data 갱신
    update_representative(person_id, new_encoding)
    add_face_record(new_encoding, file_name, location, person_id)

    return person_id


# 새로운 얼굴 추가 함수
def add_face_record(encoding: np.ndarray, file_name: str, location, person_id: str):
    # 중복 얼굴인지 확인
    if is_duplicate_face(encoding):
        return  # 중복이면 저장하지 않고 종료

    face_data = load_json(METADATA_PATH)

    new_id = get_next_face_id(face_data)
    face_data[new_id] = {
        "file_name": file_name,
        "location": location,
        "person_id": person_id,
        "encoding": encoding.tolist(),
    }

    save_json(METADATA_PATH, face_data)


# 대표 벡터 갱신 함수 (생성 or 갱신)
def update_representative(person_id: str, new_encoding: np.ndarray):
    reps = load_json(REPRESENTATIVES_PATH)

    if person_id in reps:
        prev_vector = np.array(reps[person_id])
        updated_vector = (prev_vector + new_encoding) / 2
        reps[person_id] = updated_vector.tolist()
    else:
        reps[person_id] = new_encoding.tolist()

    save_json(REPRESENTATIVES_PATH, reps)


# 새로운 사람 ID 생성
def get_new_person_id() -> str:
    reps = load_json(REPRESENTATIVES_PATH)
    existing = [
        int(k.replace("person_", "")) for k in reps.keys() if k.startswith("person_")
    ]
    next_id = max(existing + [-1]) + 1
    return f"person_{next_id}"


# 얼굴 단위 ID 생성
def get_next_face_id(face_data: dict) -> str:
    existing_ids = [int(k.replace("face_", "")) for k in face_data.keys()]
    next_id = max(existing_ids, default=-1) + 1
    return f"face_{next_id:04}"


# 기존 얼굴 벡터와 비교하여 중복 얼굴 체크 (유사도가 0.95 이상일 때만 중복 처리)
def is_duplicate_face(new_encoding: np.ndarray, threshold: float = 0.95) -> bool:
    face_data = load_json(METADATA_PATH)

    # PCA로 차원 축소
    face_encodings = np.array(
        [np.array(face_info["encoding"]) for face_info in face_data.values()]
    )
    # 저장된 얼굴 벡터 차원 축소
    reduced_encodings = reduce_dimensions(face_encodings, n_components=50)
    # 새로운 얼굴 벡터 차원 축소
    reduced_new_encoding = reduce_dimensions(np.array([new_encoding]), n_components=50)[
        0
    ]

    # 유사도 계산
    for saved_encoding in reduced_encodings:
        distance = cosine(saved_encoding, reduced_new_encoding)

        if distance < threshold:  # 유사도가 threshold보다 작으면 중복으로 간주
            return True

    return False


# PCA를 사용하여 얼굴 벡터 차원 축소
def reduce_dimensions(face_encodings: np.ndarray, n_components: int = 50) -> np.ndarray:
    pca = PCA(n_components=n_components)  # n_components 차원으로 축소
    reduced_encodings = pca.fit_transform(face_encodings)  # 얼굴 벡터 차원 축소
    return reduced_encodings


# 사용자 수정사항 반영(override 필드) 추가
def override_person(face_id: str, new_person_id: str) -> bool:
    face_data = load_json(METADATA_PATH)

    if face_id not in face_data:
        return False  # 존재하지 않는 face_id

    face_data[face_id]["override"] = new_person_id
    save_json(METADATA_PATH, face_data)
    return True
