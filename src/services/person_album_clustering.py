import os
import json
from typing import List, Dict

import cv2
import face_recognition
import numpy as np
import hdbscan
from fastapi import UploadFile
from scipy.spatial.distance import cosine


ALBUM_DIR = os.path.join("src", "data", "album")
os.makedirs(ALBUM_DIR, exist_ok=True)

ENCODING_PATH = os.path.join(ALBUM_DIR, "face_encodings.npy")
METADATA_PATH = os.path.join(ALBUM_DIR, "face_data.json")
REPRESENTATIVES_PATH = os.path.join(ALBUM_DIR, "representatives.json")


# 인물별 앨범
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

    # HDBSCAN 클러스터링 수행

    # 같은 사람이 최소 2번 이상 등장해야 클러스터로 인식
    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, metric="cosine")
    # 클러스터 번호를 리턴 (노이즈는 -1)
    labels = clusterer.fit_predict(all_face_encodings)

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

    with open(REPRESENTATIVES_PATH, "w") as f:
        json.dump(representatives, f, indent=2)

    return {
        "num_faces": len(all_face_encodings),
        "num_clusters": len(set(labels)) - (1 if -1 in labels else 0),
        "num_noise": list(labels).count(-1),
        "clusters": clustered_result,
        "representatives_saved": True,
    }


# KNN 방식의 인물 분류
def find_nearest_person(new_encoding: np.ndarray, threshold: float = 0.45) -> str:
    with open(REPRESENTATIVES_PATH, "r") as f:
        reps = json.load(f)

    closest_person = None
    closest_dist = float("inf")

    # 추가된 사진의 벡터와 기존 평균 벡터와 거리 비교
    for person_id, vector in reps.items():
        distance = cosine(new_encoding, vector)
        if distance < closest_dist:
            closest_person = person_id
            closest_dist = distance

    if closest_dist < threshold:
        return closest_person
    else:
        return "new_person"
