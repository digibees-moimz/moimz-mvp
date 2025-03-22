from fastapi import APIRouter, UploadFile, File
from typing import List
import face_recognition
import numpy as np
import os
import pickle
import cv2

router = APIRouter()


face_db = {}  # 얼굴 데이터 저장 - 임시
FACE_DATA_DIR = os.path.join("src", "face_data")  # 얼굴 데이터 저장 폴더 경로 설정
os.makedirs(FACE_DATA_DIR, exist_ok=True)  # 얼굴 벡터 파일 저장 디렉토리 생성


# 저장된 얼굴 벡터 파일들을 불러오는 로직
def load_faces_from_files():
    for file in os.listdir(FACE_DATA_DIR):
        # "face_00.pkl" 형식의 파일 찾기
        if file.startswith("face_") and file.endswith(".pkl"):
            try:
                # 파일명에서 user_id 추출
                user_id = int(file.split("_")[1].split(".")[0])
                with open(os.path.join(FACE_DATA_DIR, file), "rb") as f:
                    face_db[user_id] = pickle.load(f)  # 얼굴 벡터 복원
                print(f"✅ {user_id}번 사용자의 얼굴 데이터를 불러왔습니다.")
            except Exception as e:
                print(f"⚠️ {file} 로딩 실패: {e}")


# 서버 시작 시, 저장된 벡터 파일들을 불러옴
load_faces_from_files()


# 얼굴 등록 API
@router.post("/register_faces/{user_id}")
async def register_faces(
    user_id: int, files: List[UploadFile] = File(...)
):  # 다중 이미지 업로드 받기
    encodings_list = []

    for file in files:
        image_bytes = await file.read()  # 파일을 바이트로 읽기
        image_np = np.frombuffer(image_bytes, np.uint8)  # 바이트를 NumPy 배열로 변환
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)  # OpenCV 형식으로 변환

        # 얼굴 인식 및 특징 벡터 추출
        face_encodings = face_recognition.face_encodings(image)
        if not face_encodings:
            continue
        encodings_list.append(face_encodings[0])

    if not encodings_list:
        return {"error": "업로드된 이미지에서 얼굴을 찾을 수 없습니다."}

    # 기존 데이터와 합치기
    if user_id in face_db:
        face_db[user_id].extend(encodings_list)
    else:
        face_db[user_id] = encodings_list

    new_encoding = encodings_list[0]  # 새로 등록한 얼굴 벡터

    # 기존 얼굴 데이터와 유사도 비교
    similarity_results = []
    for existing_user_id, saved_encodings in face_db.items():
        distances = face_recognition.face_distance(saved_encodings, new_encoding)
        min_distance = float(np.min(distances))
        similarity_results.append(
            {"user_id": existing_user_id, "min_distance": min_distance}
        )

    # 얼굴 벡터를 파일로 저장 (나중에 서버를 재시작해도 얼굴 데이터가 유지됨) - 임시
    save_path = os.path.join(FACE_DATA_DIR, f"face_{user_id}.pkl")
    with open(save_path, "wb") as f:
        pickle.dump(face_db[user_id], f)  # 리스트 전체 저장

    return {
        "message": f"{user_id}번 사용자의 얼굴 {len(encodings_list)}개 등록 완료!",
        "similarity_results": similarity_results,  # 기존 얼굴과 유사도 출력
    }


# 출석체크 API
@router.post("/check_attendance")
async def check_attendance(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image_np = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # 얼굴 감지
    unknown_encodings = face_recognition.face_encodings(image)
    if not unknown_encodings:
        return {"message": "사진에서 얼굴을 찾을 수 없습니다."}

    present_users = set()

    for unknown_encoding in unknown_encodings:
        closest_user = None
        min_distance = 0.45  # 거리 기준 (0.4~0.6이 보통)

        # 등록된 얼굴 데이터 리스트와 비교
        for user_id, known_encodings in face_db.items():
            distances = face_recognition.face_distance(known_encodings, unknown_encoding)
            if len(distances) == 0:
                continue
            min_dist = float(np.min(distances))

            # 얼굴 벡터 간 유사도 검사
            if min_dist < min_distance:
                min_distance = min_dist  # 벡터 최소 거리 갱신
                closest_user = user_id

        if closest_user is not None:
            present_users.add(closest_user)

    if present_users:
        return {
            "출석자 ID 명단": list(present_users),
            "출석 인원 수": len(present_users),
        }
    else:
        return {"message": "출석한 사람 없음"}
