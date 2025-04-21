import os
import pickle
from typing import List

import cv2
import face_recognition
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from src.services.user.clustering import (
    update_user_clusters,
    visualize_clusters,
)
from src.services.user.register import extract_frames_from_video, augment_image
from src.services.user.storage import face_db
from src.services.user.insightface_wrapper import face_engine
from src.constants import FACE_DATA_DIR, FRAME_IMAGE_DIR, AUG_IMAGE_DIR

router = APIRouter()


# 사진 기반 얼굴 등록 API
@router.post("/register/{user_id}")
async def register_faces(user_id: int, files: List[UploadFile] = File(...)):

    encodings_list = []
    skipped_files = []  # 얼굴이 2개 이상인 파일 저장용

    for file in files:
        image_bytes = await file.read()  # 파일을 바이트로 읽기
        image_np = np.frombuffer(image_bytes, np.uint8)  # 바이트를 NumPy 배열로 변환
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)  # OpenCV 형식으로 변환

        # 얼굴 인식 및 특징 벡터 추출
        faces = face_engine.get_faces(image)

        if not faces:
            skipped_files.append(
                {
                    "filename": file.filename,
                    "detected_faces": 0,
                    "reason": "해당 사진에서 얼굴을 찾을 수 없음",
                }
            )
            continue  # 감지된 얼굴으면 건너뜀

        if len(faces) > 1:
            skipped_files.append(
                {
                    "filename": file.filename,
                    "detected_faces": len(faces),
                    "reason": f"해당 사진에서 {len(faces)}개의 얼굴이 감지됨",
                }
            )
            continue  # 얼굴이 2개 이상이면 등록 안 함

        embedding = face_engine.get_embedding(faces[0])
        encodings_list.append(embedding)

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
        pickle.dump(face_db[user_id], f)

    new_encoding = encodings_list[0]

    # 기존 얼굴 데이터와 유사도 비교
    similarity_results = []
    for existing_user_id, data in face_db.items():
        raw_vectors = data.get("raw", [])
        if raw_vectors:
            sims = [
                float(face_engine.cosine_similarity(vec, new_encoding))
                for vec in raw_vectors
            ]
            max_sim = max(sims)
            similarity_results.append(
                {"user_id": existing_user_id, "cosine_similarity": max_sim}
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


# 영상 기반 얼굴 등록 API
@router.post("/register_video/{user_id}")
async def register_faces_from_video(user_id: int, file: UploadFile = File(...)):
    # 파일 확장자 확인
    allowed_exts = (".mp4", ".webm", ".mov", ".avi", ".mkv")
    if not file.filename.lower().endswith(allowed_exts):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원되지 않는 파일 형식입니다. 영상(mp4, webm 등)만 업로드 가능합니다.",
        )

    # MIME 타입 확인
    if not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원되지 않는 파일 형식입니다. video 타입만 업로드 가능합니다.",
        )

    video_bytes = await file.read()

    # 프레임 추출
    frames = extract_frames_from_video(video_bytes)

    encodings_list = []
    skipped = 0

    # 저장 경로 준비
    frame_dir = os.path.join(FRAME_IMAGE_DIR, str(user_id))
    aug_dir = os.path.join(AUG_IMAGE_DIR, str(user_id))
    os.makedirs(frame_dir, exist_ok=True)
    os.makedirs(aug_dir, exist_ok=True)

    # 데이터 증강
    for i, frame in enumerate(frames):
        # 프레임 저장
        frame_path = os.path.join(frame_dir, f"frame_{i:03d}.jpg")
        cv2.imwrite(frame_path, frame)

        augmented_images = augment_image(frame)

        for j, img in enumerate(augmented_images):
            # 증강 이미지 저장
            aug_path = os.path.join(aug_dir, f"frame{i}_aug{j}.jpg")
            cv2.imwrite(aug_path, img)

            # 얼굴 인코딩
            locations = face_recognition.face_locations(img)
            encodings = face_recognition.face_encodings(
                img, known_face_locations=locations
            )

            if len(encodings) == 1:
                encodings_list.append(encodings[0])
            else:
                skipped += 1

    if not encodings_list:
        return {"error": "등록 가능한 얼굴이 없습니다.", "skipped": skipped}

    # 기존 사용자 얼굴 데이터와 병합
    if user_id in face_db:
        if isinstance(face_db[user_id], list):
            face_db[user_id] = {"raw": face_db[user_id]}
        face_db[user_id]["raw"].extend(encodings_list)
    else:
        face_db[user_id] = {"raw": encodings_list}

    # KMeans 클러스터링 수행
    cluster_msg = update_user_clusters(face_db, user_id)

    # 저장
    save_path = os.path.join(FACE_DATA_DIR, f"face_{user_id}.pkl")
    with open(save_path, "wb") as f:
        pickle.dump(face_db[user_id], f)

    return {
        "message": f"✅ 사용자 {user_id} 얼굴 {len(encodings_list)}개 등록 완료!",
        "skipped": skipped,
        "cluster_msg": cluster_msg,
    }
