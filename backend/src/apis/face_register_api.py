import os
import pickle
from typing import List

import cv2
import face_recognition
import numpy as np
from fastapi import APIRouter, UploadFile, File

from src.services.user.clustering import (
    update_user_clusters,
    visualize_clusters,
)
from src.services.user.storage import face_db
from src.constants import FACE_DATA_DIR

router = APIRouter()


# 얼굴 등록 API
@router.post("/register/{user_id}")
async def register_faces(user_id: int, files: List[UploadFile] = File(...)):

    encodings_list = []
    skipped_files = []  # 얼굴이 2개 이상인 파일 저장용

    for file in files:
        image_bytes = await file.read()  # 파일을 바이트로 읽기
        image_np = np.frombuffer(image_bytes, np.uint8)  # 바이트를 NumPy 배열로 변환
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)  # OpenCV 형식으로 변환

        # 얼굴 인식 및 특징 벡터 추출
        face_encodings = face_recognition.face_encodings(image)

        if not face_encodings:
            skipped_files.append(
                {
                    "filename": file.filename,
                    "detected_faces": 0,
                    "reason": "해당 사진에서 얼굴을 찾을 수 없음",
                }
            )
            continue  # 감지된 얼굴으면 건너뜀

        if len(face_encodings) > 1:
            skipped_files.append(
                {
                    "filename": file.filename,
                    "detected_faces": len(face_encodings),
                    "reason": f"해당 사진에서 {len(face_encodings)}개의 얼굴이 감지됨",
                }
            )
            continue  # 얼굴이 2개 이상이면 등록 안 함

        encodings_list.append(face_encodings[0])

    if not encodings_list:
        if skipped_files:
            return {
                "error": "등록 가능한 얼굴이 없습니다.",
                "skipped_files": skipped_files,
            }

    # 기존 데이터와 합치기
    if user_id in face_db:
        # 만약 기존 데이터가 리스트 형태라면 "raw" 키로 변환
        if isinstance(face_db[user_id], list):
            face_db[user_id] = {"raw": face_db[user_id]}

        face_db[user_id]["raw"].extend(encodings_list)
    else:
        face_db[user_id] = {"raw": encodings_list}

    # 얼굴 등록 후 클러스터링 업데이트
    cluster_msg = update_user_clusters(face_db, user_id)

    # 얼굴 벡터 데이터를 파일로 저장
    save_path = os.path.join(FACE_DATA_DIR, f"face_{user_id}.pkl")
    with open(save_path, "wb") as f:
        pickle.dump(face_db[user_id], f)  # 사용자 데이터(딕셔너리) 전체 전체 저장

    new_encoding = encodings_list[0]  # 새로 등록한 얼굴 벡터

    # 기존 얼굴 데이터와 유사도 비교
    similarity_results = []
    for existing_user_id, data in face_db.items():
        raw_vectors = data.get("raw", [])
        if raw_vectors:
            distances = face_recognition.face_distance(raw_vectors, new_encoding)
            min_distance = float(np.min(distances))
            similarity_results.append(
                {"user_id": existing_user_id, "min_distance": min_distance}
            )

    return {
        "message": f"{user_id}번 사용자의 얼굴 {len(files)}개 중 {len(encodings_list)}개 등록 완료!",
        "cluster_msg": cluster_msg,  # 클러스터링 결과 메시지 포함
        "skipped_files": skipped_files,
        "similarity_results": similarity_results,  # 기존 얼굴과 유사도 출력
    }


# 클러스터링 시각화 API (얼굴 등록)
@router.get("/visualize_clusters/{user_id}")
async def get_cluster_visualization(user_id: int):
    return visualize_clusters(face_db, user_id)
