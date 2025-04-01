from typing import List

import cv2
import face_recognition
import numpy as np
from fastapi import APIRouter, UploadFile, File

from src.services.person_album_clustering import (
    run_album_clustering,
    find_nearest_person,
)


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
