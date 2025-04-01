import os
from typing import List, Dict

import cv2
import face_recognition
import numpy as np
import hdbscan
from fastapi import UploadFile


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
    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, metric='cosine')
    # 클러스터 번호를 리턴 (노이즈는 -1)
    labels = clusterer.fit_predict(all_face_encodings)

    clustered_result = {}
    for idx, label in enumerate(labels):
        info = face_image_map[idx]
        if label == -1:
            clustered_result.setdefault("noise", []).append(info)
        else:
            clustered_result.setdefault(f"person_{label}", []).append(info)

    return {
        "num_faces": len(all_face_encodings),
        "num_clusters": len(set(labels)) - (1 if -1 in labels else 0),
        "num_noise": list(labels).count(-1),
        "clusters": clustered_result,
    }
