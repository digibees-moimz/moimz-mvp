import time

import cv2
import numpy as np
from fastapi import UploadFile

from src.services.user.storage import face_db
from src.services.user.insightface_wrapper import face_engine


# 출석체크 확인
async def run_attendance_check(file: UploadFile):
    start_time = time.time()  # ⏱ 시작 시간 기록

    image_bytes = await file.read()
    image_np = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # 단체 사진에서 얼굴 감지 및 벡터 추출
    faces = face_engine.get_faces(image)
    if not faces:
        return {"message": "사진에서 얼굴을 찾을 수 없습니다."}

    unknown_encodings = [face_engine.get_embedding(f) for f in faces]
    all_matches = []

    # 모든 (unknown 얼굴, 등록된 얼굴) 조합 거리 계산
    for unknown_id, unknown_encoding in enumerate(unknown_encodings):
        for user_id, user_data in face_db.items():
            raw_vectors = user_data.get("raw", [])
            clusters = user_data.get("clusters", None)

            # 클러스터링된 경우
            if clusters:
                centroids = np.array(clusters["centroids"])
                labels = clusters["labels"]

                # 코사인 유사도로 가장 가까운 클러스터 선택
                sims = [
                    face_engine.cosine_similarity(centroid, unknown_encoding)
                    for centroid in centroids
                ]
                closest_cluster_idx = int(np.argmax(sims))

                # 해당 클러스터에 속한 raw 벡터들만 비교
                selected_vectors = [
                    raw_vectors[i]
                    for i, label in enumerate(labels)
                    if label == closest_cluster_idx  # 가장 가까운 클러스터 선택
                ]

            else:
                # 클러스터가 없으면 전체 raw 벡터와 비교
                selected_vectors = raw_vectors

            if not selected_vectors:
                continue

            # 벡터들과 실제 거리 계산
            for known_encoding in selected_vectors:
                sim = face_engine.cosine_similarity(known_encoding, unknown_encoding)
                all_matches.append(
                    {"unknown_id": unknown_id, "user_id": user_id, "similarity": sim}
                )

    # 거리 기준 정렬 (유사한 조합부터 차례대로 검사하기 위함)
    all_matches.sort(key=lambda x: x["similarity"], reverse=True)

    matched_users = set()  # 출석된 user_id들 저장 (중복 방지용)
    matched_unknowns = set()  # 단체 사진 속 얼굴들 중 이미 매칭된 얼굴
    attendance_results = []  # 최종 출석 결과 저장

    for match in all_matches:
        if match["similarity"] < 0.4:
            break  # 정렬되었기 때문에 유사도가 기준값을 넘어가면 더이상 확인할 필요 없음

        if match["user_id"] in matched_users:
            continue
        if match["unknown_id"] in matched_unknowns:
            continue

        matched_users.add(match["user_id"])
        matched_unknowns.add(match["unknown_id"])
        attendance_results.append(
            {"user_id": match["user_id"], "similarity": float(match["similarity"])}
        )

    end_time = time.time()
    duration = round(end_time - start_time, 3)

    if attendance_results:
        return {
            "출석자 ID 명단": attendance_results,
            "출석 인원 수": len(attendance_results),
            "실행 시간 (초)": duration,
        }
    else:
        return {
            "message": "출석한 사람 없음",
            "실행 시간 (초)": duration,
        }
