from typing import List

import cv2
import face_recognition
import numpy as np
from fastapi import APIRouter, UploadFile, File, Query

from src.services.person_album_clustering import (
    run_album_clustering,
    save_clustered_faces,
    find_nearest_person,
    override_person,
)
from src.constants import TEMP_CLUSTER_PATH, TEMP_ENCODING_PATH
from src.utils.file_io import load_json


router = APIRouter()


# 인물별 앨범 API (초기 일괄 분류)
@router.post("/cluster")
async def cluster_album_faces(files: List[UploadFile] = File(...)):
    result = await run_album_clustering(files)
    return result


# 인물별 앨범 API (새로운 사진을 통한 실시간 인물 분류)
@router.post("/add_pictures")
async def add_pictures(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        image_bytes = await file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        face_locations = face_recognition.face_locations(image)
        encodings = face_recognition.face_encodings(image, face_locations)

        for encoding, loc in zip(encodings, face_locations):
            person_id = find_nearest_person(encoding, file.filename, loc)
            results.append(
                {
                    "predicted_person": person_id,
                    "location": loc,
                    "file_name": file.filename,
                }
            )

    return {"num_faces": len(results), "results": results}


# 사용자가 수동으로 인물 재지정
@router.post("/override_person")
async def manual_override_person(
    face_id: str = Query(..., description="ex. face_0003"),
    new_person_id: str = Query(..., description="ex. person_5"),
):
    success = override_person(face_id, new_person_id)

    if success:
        return {"message": f"{face_id} → {new_person_id}로 수동 재지정 완료되었습니다."}
    else:
        return {
            "error": f"{face_id}가 존재하지 않습니다. 유효한 face_id를 확인해주세요."
        }


# 클러스터링 결과 저장
@router.post("/save_cluster")
async def save_cluster_api():
    cluster_data = load_json(TEMP_CLUSTER_PATH)
    full_encodings = load_json(TEMP_ENCODING_PATH)

    return save_clustered_faces(cluster_data, full_encodings)
