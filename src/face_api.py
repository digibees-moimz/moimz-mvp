from fastapi import APIRouter, UploadFile, File
import face_recognition
import numpy as np
import os
import pickle
import cv2

router = APIRouter()

# 얼굴 데이터 저장 - 임시
face_db = {}


# 얼굴 등록 API (파일 업로드 필수)
@router.post("/register_face/{user_id}")
async def register_face(user_id: int, file: UploadFile = File(...)):
    image_bytes = await file.read()  # 파일을 바이트로 읽기
    image_np = np.frombuffer(image_bytes, np.uint8)  # 바이트를 NumPy 배열로 변환
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)  # OpenCV 형식으로 변환

    # 얼굴 인식 및 특징 벡터 추출
    face_encodings = face_recognition.face_encodings(image)
    if not face_encodings:
        return {"error": "얼굴을 찾을 수 없습니다."}

    new_encoding = face_encodings[0]  # 새로 등록한 얼굴 벡터

    # 기존 얼굴 데이터와 유사도 비교
    similarity_results = []
    for existing_user_id, saved_encoding in face_db.items():
        distance = face_recognition.face_distance([saved_encoding], new_encoding)[0]
        similarity_results.append({"user_id": existing_user_id, "distance": distance})

    # 얼굴 벡터를 파일로 저장 (나중에 서버를 재시작해도 얼굴 데이터가 유지됨) - 임시
    face_db[user_id] = new_encoding
    with open(f"face_{user_id}.pkl", "wb") as f:
        pickle.dump(new_encoding, f)

    return {
        "message": f"{user_id} 얼굴 등록 완료!",
        "similarity_results": similarity_results,  # 기존 얼굴과 유사도 출력
    }


# 서버 시작 시, 저장된 얼굴 벡터 파일들을 불러오는 로직
def load_faces_from_files():
    for file in os.listdir():
        # "face_00.pkl" 형식의 파일 찾기
        if file.startswith("face_") and file.endswith(".pkl"):
            try:
                # 파일명에서 user_id 추출
                user_id = int(file.split("_")[1].split(".")[0])
                with open(file, "rb") as f:
                    face_db[user_id] = pickle.load(f)  # 얼굴 벡터 복원
                print(f"✅ {user_id}번 사용자의 얼굴 데이터를 불러왔습니다.")
            except Exception as e:
                print(f"⚠️ {file} 로딩 실패: {e}")


# 모듈이 처음 import 될 때 자동 실행
load_faces_from_files()
