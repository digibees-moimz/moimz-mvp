from os.path import exists
from typing import List, Dict

import cv2
import face_recognition
import numpy as np
import hdbscan
from fastapi import UploadFile
from collections import deque
from scipy.spatial.distance import cosine
from sklearn.metrics.pairwise import pairwise_distances

from src.utils.file_io import load_json, save_json
from src.constants import (
    METADATA_PATH,
    REPRESENTATIVES_PATH,
    TEMP_CLUSTER_PATH,
    TEMP_ENCODING_PATH,
    RECENT_VECTOR_COUNT,
)


async def add_incremental_faces(files: List[UploadFile]) -> Dict:
    face_image_map = load_json(TEMP_ENCODING_PATH, [])
    clustered_result = load_json(TEMP_CLUSTER_PATH, {})
    results = []

    for file in files:
        image_bytes = await file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        face_locations = face_recognition.face_locations(image)
        encodings = face_recognition.face_encodings(image, face_locations)

        for encoding, loc in zip(encodings, face_locations):
            if is_duplicate_face(encoding, file.filename, loc):
                print(f"중복 얼굴 건너뜀: {file.filename}, 위치 {loc}")
                continue

            # 최근접 대표 벡터 기반 분류
            person_id = find_nearest_person(
                encoding, file.filename, loc, save_to_storage=False  # TEMP에만 저장
            )

            # 얼굴 ID 생성
            face_id = get_next_temp_face_id(face_image_map)

            # TEMP 저장용 레코드
            face_record = {
                "file_name": file.filename,
                "location": loc,
                "face_id": face_id,
                "predicted_person": person_id,
                "encoding": encoding.tolist(),
            }

            # TEMP_ENCODING_PATH에 저장
            face_image_map.append(face_record)

            # TEMP_CLUSTER_PATH에 저장
            clustered_result.setdefault(person_id, []).append(
                {
                    "file_name": file.filename,
                    "location": loc,
                    "face_id": face_id,
                }
            )

            results.append(
                {
                    "predicted_person": person_id,
                    "location": loc,
                    "file_name": file.filename,
                }
            )

    # 저장
    save_json(TEMP_ENCODING_PATH, face_image_map)
    save_json(TEMP_CLUSTER_PATH, clustered_result)

    return {"num_faces": len(results), "results": results}


# 클러스터 결과만 반환 (저장은 안함) - 비지도 학습 기반, HDBSCAN
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
            if is_duplicate_face(encoding, file.filename, loc):
                print(f"중복 얼굴 건너뜀: {file.filename}, 위치 {loc}")
                continue

            all_face_encodings.append(encoding)
            face_image_map.append(
                {
                    "file_name": file.filename,
                    "location": loc,  # (top, right, bottom, left)
                    "encoding": encoding.tolist(),  # 다음 단계에 전달
                }
            )

    if not all_face_encodings:
        return {"message": "등록된 얼굴이 없습니다."}

    # HDBSCAN 클러스터링 수행
    distance_matrix = pairwise_distances(all_face_encodings, metric="cosine")
    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, metric="precomputed")
    labels = clusterer.fit_predict(distance_matrix)

    clustered_result = {}  # 사진 위치 정보 저장
    used_ids = []
    if exists(TEMP_CLUSTER_PATH):
        try:
            prev_data = load_json(TEMP_CLUSTER_PATH)
            for person_faces in prev_data.values():
                for face in person_faces:
                    fid = face.get("face_id")
                    if fid and fid.startswith("face_"):
                        used_ids.append(int(fid.replace("face_", "")))
        except:
            pass

    current_id = max(used_ids + [-1]) + 1
    cluster_vectors = {}  # 실제 얼굴 벡터 데이터 저장 (계산용 데이터)

    for idx, label in enumerate(labels):
        info = face_image_map[idx]
        cluster_key = "noise" if label == -1 else f"person_{label}"

        face_id = f"face_{current_id:04}"
        current_id += 1
        
        info["face_id"] = face_id
        info["predicted_person"] = cluster_key 
        
        # 저장 대상 필드만 반환 (encoding 제외)
        clustered_result.setdefault(cluster_key, []).append(
            {
                "file_name": info["file_name"],
                "location": info["location"],
                "face_id": face_id,
            }
        )

        # 벡터 저장 (noise는 제외)
        if cluster_key != "noise":
            cluster_vectors.setdefault(cluster_key, []).append(all_face_encodings[idx])

    # 이전 override 정보를 불러옴
    try:
        previous_data = load_json(TEMP_CLUSTER_PATH)
    except FileNotFoundError:
        previous_data = {}

    # override 정보를 clustered_result에 병합
    for person_key, faces in clustered_result.items():
        for face in faces:
            target_file = face.get("file_name")
            target_loc = face.get("location")
            # 기존 temp 데이터에 override가 존재할 경우 덮어쓰기
            for prev_faces in previous_data.values():
                for prev_face in prev_faces:
                    if (
                        prev_face.get("file_name") == target_file
                        and prev_face.get("location") == target_loc
                        and prev_face.get("override")
                    ):
                        face["override"] = prev_face["override"]

    # 클러스터별 대표 벡터(평균값) 저장
    representatives = {}
    for person_id, vectors in cluster_vectors.items():
        mean_vector = np.mean(vectors, axis=0)
        representatives[person_id] = mean_vector.tolist()

    save_json(REPRESENTATIVES_PATH, representatives)

    # 임시 저장
    save_json(TEMP_CLUSTER_PATH, clustered_result)
    save_json(TEMP_ENCODING_PATH, face_image_map)

    return {
        "num_faces": len(all_face_encodings),
        "num_clusters": len(set(labels)) - (1 if -1 in labels else 0),
        "num_noise": list(labels).count(-1),
        "clusters": clustered_result,
        "representatives_saved": True,
    }


# 클러스터 결과를 실제로 저장하는 함수
def save_clustered_faces(
    cluster_data: Dict[str, List[Dict]], full_encodings: List[Dict]
) -> Dict:
    face_data = load_json(METADATA_PATH)

    new_faces = {}
    for person_id, faces in cluster_data.items():
        if person_id == "noise":
            continue  # 노이즈는 저장하지 않음

        for face in faces:
            file_name = face["file_name"]
            location = face["location"]

            # encoding 찾기
            encoding = next(
                (
                    e["encoding"]
                    for e in full_encodings
                    if e["file_name"] == file_name and e["location"] == location
                ),
                None,
            )
            if encoding is None:
                continue  # 못 찾으면 skip

            face_id = get_next_face_id(face_data)
            face_data[face_id] = {
                "file_name": file_name,
                "location": location,
                "person_id": person_id,
                "encoding": (
                    encoding if isinstance(encoding, list) else encoding.tolist()
                ),
            }
            new_faces[face_id] = face_data[face_id]

    save_json(METADATA_PATH, face_data)
    return {"saved_faces": new_faces}


# 증분 인물 분류 (KNN 방식)
def find_nearest_person(
    new_encoding: np.ndarray,
    file_name: str,
    location,
    threshold: float = 0.45,
    save_to_storage: bool = True,
) -> str:
    # 중복 얼굴 체크
    if is_duplicate_face(new_encoding, file_name, location):
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

    # 조건부 저장
    if save_to_storage:
        update_representative(person_id, new_encoding)
        add_face_record(new_encoding, file_name, location, person_id)

    return person_id


# 새로운 얼굴 추가 함수
def add_face_record(encoding: np.ndarray, file_name: str, location, person_id: str):
    # 중복 얼굴인지 확인
    if is_duplicate_face(encoding, file_name, location):
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


# 대표 벡터 갱신 함수 (최근 N개의 벡터를 평균)
def update_representative(person_id: str, new_encoding: np.ndarray):
    # 벡터 히스토리 불러오기 (없으면 새로 생성)
    if REPRESENTATIVES_PATH.exists():
        data = load_json(REPRESENTATIVES_PATH)
    else:
        data = {}

    # 히스토리 키 설정
    history_key = f"{person_id}_history"
    history_list = data.get(history_key, [])

    # deque로 변환해서 최대 길이 제한
    vector_history = deque(history_list, maxlen=RECENT_VECTOR_COUNT)
    vector_history.append(new_encoding.tolist())

    # 대표 벡터는 최근 N개 평균
    new_mean = np.mean(np.array(vector_history), axis=0)

    # 저장
    data[person_id] = new_mean.tolist()
    data[history_key] = list(vector_history)

    save_json(REPRESENTATIVES_PATH, data)


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


# 얼굴 단위 임시 ID 생성
def get_next_temp_face_id(temp_face_data: list) -> str:
    existing_ids = [
        int(face["face_id"].replace("face_", ""))
        for face in temp_face_data
        if "face_id" in face
    ]
    next_id = max(existing_ids, default=-1) + 1
    return f"face_{next_id:04}"


# 중복 얼굴 체크 (유사도가 0.95 이상일 때만 중복 처리)
def is_duplicate_face(
    new_encoding: np.ndarray, file_name: str, location, threshold: float = 0.95
) -> bool:

    for source_path in [METADATA_PATH, TEMP_ENCODING_PATH]:
        face_data = load_json(source_path)

        if not face_data:
            return False

        for face_info in (
            face_data.values() if isinstance(face_data, dict) else face_data
        ):
            saved_encoding = np.array(face_info["encoding"])
            similarity = 1 - cosine(new_encoding, saved_encoding)

            # 완전히 같은 사진인 경우 (파일명 + 위치까지 같음)
            if (
                face_info["file_name"] == file_name
                and face_info["location"] == location
            ):
                return True

            # 인물 유사도가 매우 높을 경우
            if similarity > threshold:
                return True

    return False  # 중복 아님


# 사용자 수정사항 반영(override 필드) 추가
def override_person(face_id: str, new_person_id: str) -> bool:
    # 1. 먼저 정식 저장 데이터에서 찾기
    face_data = load_json(METADATA_PATH)
    if face_id in face_data:
        face_data[face_id]["override"] = new_person_id
        save_json(METADATA_PATH, face_data)
        return True

    # 2. 임시 클러스터 데이터에서 찾기
    if exists(TEMP_CLUSTER_PATH):
        temp_data = load_json(TEMP_CLUSTER_PATH)
        updated = False

        for person_key, faces in temp_data.items():
            for face in faces:
                if face.get("face_id") == face_id:
                    face["override"] = new_person_id
                    updated = True

        if updated:
            save_json(TEMP_CLUSTER_PATH, temp_data)
            return True

    return False  # 어디에도 없음
